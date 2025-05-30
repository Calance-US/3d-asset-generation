import os
import json
import boto3
import redis
import aiohttp
from typing import List, Dict, Optional
from ..config.settings import settings
from pathlib import Path

class ModelRepository:
    def __init__(self):
        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY
        )
        
        # Initialize Redis client
        self.redis_client = redis.from_url(settings.REDIS_URL)
        
        # Initialize Sketchfab API session
        self.sketchfab_session = aiohttp.ClientSession(
            headers={'Authorization': f'Token {settings.SKETCHFAB_API_KEY}'}
        )

        self.models_dir = Path(__file__).parent.parent.parent / "models"
        self.models_dir.mkdir(exist_ok=True)

    async def get_model_url(self, model_name: str, subject: str) -> str:
        """Get the URL for a 3D model, trying different sources in order."""
        # Try Redis cache first
        cached_url = self.redis_client.get(f"model:{subject}:{model_name}")
        if cached_url:
            return cached_url.decode('utf-8')
        
        # Try S3
        s3_url = await self._get_s3_model_url(model_name, subject)
        if s3_url:
            self.redis_client.setex(
                f"model:{subject}:{model_name}",
                3600,  # Cache for 1 hour
                s3_url
            )
            return s3_url
        
        # Try Sketchfab
        sketchfab_url = await self._get_sketchfab_model_url(model_name, subject)
        if sketchfab_url:
            self.redis_client.setex(
                f"model:{subject}:{model_name}",
                3600,
                sketchfab_url
            )
            return sketchfab_url
        
        # Return fallback model
        return settings.FALLBACK_MODELS.get(subject, settings.FALLBACK_MODELS["physics"])

    async def _get_s3_model_url(self, model_name: str, subject: str) -> Optional[str]:
        """Get model URL from S3 bucket."""
        try:
            key = f"models/{subject}/{model_name}.glb"
            self.s3_client.head_object(Bucket=settings.S3_BUCKET_NAME, Key=key)
            return self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': settings.S3_BUCKET_NAME, 'Key': key},
                ExpiresIn=3600
            )
        except:
            return None

    async def _get_sketchfab_model_url(self, model_name: str, subject: str) -> Optional[str]:
        """Get model URL from Sketchfab."""
        try:
            # Search for the model
            search_url = f"https://api.sketchfab.com/v3/search?type=models&q={model_name}+{subject}&downloadable=true"
            async with self.sketchfab_session.get(search_url) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('results'):
                        model_uid = data['results'][0]['uid']
                        
                        # Get model download URL
                        model_url = f"https://api.sketchfab.com/v3/models/{model_uid}/download"
                        async with self.sketchfab_session.get(model_url) as model_response:
                            if model_response.status == 200:
                                model_data = await model_response.json()
                                return model_data.get('gltf', {}).get('url')
            return None
        except Exception as e:
            print(f"Error fetching from Sketchfab: {e}")
            return None

    async def cache_model(self, model_name: str, subject: str, model_url: str):
        """Cache a model URL in Redis."""
        self.redis_client.setex(
            f"model:{subject}:{model_name}",
            3600,
            model_url
        )

    async def get_available_models(self, subject: str) -> List[str]:
        """Get list of available models for a subject."""
        # For now, return a simple list
        return ["circuit", "battery", "resistor"]

    async def close(self):
        """Close any open connections."""
        await self.sketchfab_session.close()
        self.redis_client.close() 