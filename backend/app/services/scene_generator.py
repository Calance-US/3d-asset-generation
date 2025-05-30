from typing import List, Dict, Any
import json
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from ..config.settings import settings
from openai import AsyncOpenAI

class SceneGenerator:
    def __init__(self):
        self.system_prompt = """You are an expert in creating educational 3D visualizations using Three.js.
        Create interactive, educational 3D scenes that help students understand scientific concepts.
        Use proper lighting, camera controls, and interactive elements.
        Return only the complete HTML code with embedded Three.js."""
        
        self.llm = ChatOpenAI(
            model="gpt-4-turbo-preview",
            temperature=0,
            api_key=settings.OPENAI_API_KEY
        )
        
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        self.scene_generation_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at creating interactive 3D educational scenes using Three.js.
            Given the following information:
            1. Scene description
            2. Available 3D models and their URLs
            3. Required animations and interactions
            
            Generate a complete Three.js scene that:
            1. Loads and displays the 3D models
            2. Implements the required animations
            3. Adds appropriate lighting and camera controls
            4. Includes educational labels and annotations
            5. Handles user interactions
            
            Return only the JavaScript code for the scene, which will be inserted into the HTML template."""),
            ("user", "{scene_context}")
        ])

    async def generate_scene(self, prompt: str, model_urls: Dict[str, str], animations: List[str], context: Dict) -> str:
        """Generate a Three.js scene based on the prompt and context."""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
            )
            
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating scene: {e}")
            return "<div>Error generating scene</div>"

    async def generate_scene_from_context(self, 
                           scene_description: str,
                           model_urls: Dict[str, str],
                           animations: List[str],
                           context: Dict[str, Any]) -> str:
        """Generate a Three.js scene based on the provided information."""
        try:
            # Prepare the scene context
            scene_context = {
                "description": scene_description,
                "models": model_urls,
                "animations": animations,
                "context": context
            }
            
            # Generate the scene code
            response = await self.llm.ainvoke(
                self.scene_generation_prompt.format_messages(scene_context=json.dumps(scene_context))
            )
            
            # Format the scene code
            scene_code = self._format_scene_code(response.content)
            
            # Insert the scene code into the template
            return settings.THREE_JS_TEMPLATE.format(scene_code=scene_code)
            
        except Exception as e:
            print(f"Error generating scene: {e}")
            return self._generate_fallback_scene()

    def _format_scene_code(self, code: str) -> str:
        """Format and clean up the generated scene code."""
        # Remove any markdown code block markers
        code = code.replace("```javascript", "").replace("```", "")
        
        # Add error handling
        code = f"""
        try {{
            {code}
        }} catch (error) {{
            console.error('Error in scene:', error);
            document.body.innerHTML = '<div style="color: red; padding: 20px;">Error loading scene: ' + error.message + '</div>';
        }}
        """
        
        return code

    def _generate_fallback_scene(self) -> str:
        """Generate a simple fallback scene when the main generation fails."""
        fallback_code = """
        // Create a simple scene with a cube
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        const renderer = new THREE.WebGLRenderer();
        renderer.setSize(window.innerWidth, window.innerHeight);
        document.body.appendChild(renderer.domElement);

        // Add a simple cube
        const geometry = new THREE.BoxGeometry();
        const material = new THREE.MeshPhongMaterial({ color: 0x00ff00 });
        const cube = new THREE.Mesh(geometry, material);
        scene.add(cube);

        // Add lighting
        const light = new THREE.DirectionalLight(0xffffff, 1);
        light.position.set(1, 1, 1);
        scene.add(light);
        scene.add(new THREE.AmbientLight(0x404040));

        // Position camera
        camera.position.z = 5;

        // Add controls
        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;

        // Animation loop
        function animate() {
            requestAnimationFrame(animate);
            cube.rotation.x += 0.01;
            cube.rotation.y += 0.01;
            controls.update();
            renderer.render(scene, camera);
        }
        animate();

        // Handle window resize
        window.addEventListener('resize', () => {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        });
        """
        
        return settings.THREE_JS_TEMPLATE.format(scene_code=fallback_code) 