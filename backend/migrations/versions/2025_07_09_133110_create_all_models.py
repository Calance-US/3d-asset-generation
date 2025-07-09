"""
2025_07_09_133110_create_all_models.py

Create all tables and relationships as defined in backend/app/models.py
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2025_07_09_133110'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # ### Main tables ###
    op.create_table(
        'ai_providers',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    op.create_table(
        'tag_categories',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('parent_category_id', sa.Integer(), sa.ForeignKey('tag_categories.id'), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('external_id', sa.String(), unique=True, nullable=False),
        sa.Column('provider', sa.String(), nullable=False, default='keycloak'),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('role', sa.String(), nullable=False, default='student'),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, default=False),
    )
    op.create_table(
        'prompts',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('topic', sa.String()),
        sa.Column('subject', sa.String()),
        sa.Column('content', sa.Text()),
        sa.Column('embedding', sa.JSON()),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('key_concepts', sa.Text(), nullable=True),
        sa.Column('education_level', sa.String(50), nullable=True),
        sa.Column('learning_objectives', sa.Text(), nullable=True),
        sa.Column('interactive_features', sa.Text(), nullable=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
    )
    op.create_table(
        'tags',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('category_id', sa.Integer(), sa.ForeignKey('tag_categories.id'), nullable=True),
        sa.Column('name', sa.String(), unique=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('is_deleted', sa.Boolean(), default=False),
    )
    op.create_table(
        'visualizations',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('topic', sa.String()),
        sa.Column('subject', sa.String()),
        sa.Column('html_content', sa.Text()),
        sa.Column('config', sa.JSON()),
        sa.Column('embedding', sa.JSON()),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.Column('generation_attempts', sa.Integer(), default=1),
        sa.Column('final_quality_score', sa.Numeric(3, 1), nullable=True),
        sa.Column('validation_errors_count', sa.Integer(), default=0),
    )
    op.create_table(
        'shared_content',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('owner_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('target_user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('content_type', sa.String(), nullable=False),
        sa.Column('content_id', sa.Integer(), nullable=False),
        sa.Column('permission_level', sa.String(), nullable=False, default='view'),
        sa.Column('shared_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
    )
    op.create_table(
        'gold_standard_upload_status',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.Column('status', sa.String(), default='pending'),
        sa.Column('result', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
    )
    op.create_table(
        'validation_errors',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('visualization_id', sa.Integer(), sa.ForeignKey('visualizations.id'), nullable=True),
        sa.Column('prompt_id', sa.Integer(), sa.ForeignKey('prompts.id'), nullable=True),
        sa.Column('phase', sa.String(50), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('error_type', sa.String(100), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('location', sa.String(200), nullable=True),
        sa.Column('context', sa.Text(), nullable=True),
        sa.Column('suggestion', sa.Text(), nullable=True),
        sa.Column('quality_score', sa.Numeric(3, 1), nullable=True),
        sa.Column('attempt_number', sa.Integer(), nullable=False, default=1),
        sa.Column('provider_id', sa.Integer(), sa.ForeignKey('ai_providers.id'), nullable=True),
        sa.Column('created_at', sa.DateTime()),
    )
    op.create_table(
        'snippet_metadata',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('snippet_hash', sa.String(), unique=True),
        sa.Column('snippet_type', sa.String()),
        sa.Column('summary', sa.String()),
        sa.Column('embedding_text', sa.String()),
        sa.Column('html_snippet', sa.String()),
        sa.Column('filename', sa.String()),
        sa.Column('upload_id', sa.String(36)),
        sa.Column('llm_version', sa.String()),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.Column('validation_status', sa.String()),
        sa.Column('validation_errors', sa.JSON()),
        sa.Column('retry_count', sa.Integer(), default=0),
        sa.Column('topic', sa.String()),
        sa.Column('key_concepts', sa.String()),
        sa.Column('education_level', sa.String()),
        sa.Column('learning_objectives', sa.String()),
        sa.Column('faiss_id', sa.BigInteger(), unique=True, nullable=True),
    )
    op.create_table(
        'async_tasks',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('task_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('request_data', sa.JSON(), nullable=False),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('progress_percentage', sa.Integer(), default=0),
        sa.Column('current_stage', sa.String(50), nullable=True),
        sa.Column('total_stages', sa.Integer(), default=1),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
    )
    op.create_table(
        'async_task_stages',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('task_id', sa.String(36), sa.ForeignKey('async_tasks.id'), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),
        sa.Column('order_index', sa.Integer(), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('progress_percentage', sa.Integer(), default=0),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
    )
    op.create_table(
        'local_3d_models',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('model_name', sa.String(100), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('file_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('subject', sa.String(50), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('model_type', sa.String(20), nullable=False, default='gltf'),
        sa.Column('has_animations', sa.Boolean(), default=False),
        sa.Column('has_textures', sa.Boolean(), default=False),
        sa.Column('has_materials', sa.Boolean(), default=False),
        sa.Column('triangle_count', sa.Integer(), nullable=True),
        sa.Column('vertex_count', sa.Integer(), nullable=True),
        sa.Column('usage_count', sa.Integer(), default=0),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
    )
    op.create_table(
        'chat_sessions',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('history_entry_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.Column('is_active', sa.Boolean(), default=True),
    )
    op.create_table(
        'chat_messages',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('chat_session_id', sa.String(36), sa.ForeignKey('chat_sessions.id'), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_type', sa.String(20), default='text'),
        sa.Column('timestamp', sa.DateTime()),
    )

    # ### Association tables (moved after main tables) ###
    op.create_table(
        'prompt_tags',
        sa.Column('prompt_id', sa.Integer(), sa.ForeignKey('prompts.id'), primary_key=True),
        sa.Column('tag_id', sa.Integer(), sa.ForeignKey('tags.id'), primary_key=True),
    )
    op.create_table(
        'visualization_tags',
        sa.Column('visualization_id', sa.Integer(), sa.ForeignKey('visualizations.id'), primary_key=True),
        sa.Column('tag_id', sa.Integer(), sa.ForeignKey('tags.id'), primary_key=True),
    )

    # Indexes for prompts
    op.create_index('ix_prompts_topic', 'prompts', ['topic'])
    op.create_index('ix_prompts_subject', 'prompts', ['subject'])
    # Indexes for tags
    op.create_index('ix_tags_name', 'tags', ['name'])
    # Indexes for visualizations
    op.create_index('ix_visualizations_topic', 'visualizations', ['topic'])
    op.create_index('ix_visualizations_subject', 'visualizations', ['subject'])
    # Indexes for local_3d_models
    op.create_index('ix_local_3d_models_model_name', 'local_3d_models', ['model_name'])
    op.create_index('ix_local_3d_models_category', 'local_3d_models', ['category'])
    op.create_index('ix_local_3d_models_subject', 'local_3d_models', ['subject'])
    # Indexes for chat_sessions
    op.create_index('ix_chat_sessions_history_entry_id', 'chat_sessions', ['history_entry_id'])
    op.create_index('ix_chat_sessions_user_id', 'chat_sessions', ['user_id'])
    # Indexes for chat_messages
    op.create_index('ix_chat_messages_chat_session_id', 'chat_messages', ['chat_session_id'])
    # Indexes for async_tasks
    op.create_index('ix_async_tasks_task_type', 'async_tasks', ['task_type'])
    op.create_index('ix_async_tasks_status', 'async_tasks', ['status'])
    op.create_index('ix_async_tasks_created_at', 'async_tasks', ['created_at'])
    op.create_index('ix_async_tasks_updated_at', 'async_tasks', ['updated_at'])
    # Indexes for async_task_stages
    op.create_index('ix_async_task_stages_task_id', 'async_task_stages', ['task_id'])
    # Indexes for snippet_metadata
    op.create_index('ix_snippet_metadata_snippet_hash', 'snippet_metadata', ['snippet_hash'])
    # Indexes for users
    op.create_index('ix_users_external_id', 'users', ['external_id'])
    # Indexes for gold_standard_upload_status
    op.create_index('ix_gold_standard_upload_status_id', 'gold_standard_upload_status', ['id'])
    # Indexes for validation_errors
    op.create_index('ix_validation_errors_phase', 'validation_errors', ['phase'])
    op.create_index('ix_validation_errors_severity', 'validation_errors', ['severity'])
    op.create_index('ix_validation_errors_error_type', 'validation_errors', ['error_type'])
    op.create_index('ix_validation_errors_created_at', 'validation_errors', ['created_at'])

def downgrade():
    op.drop_table('chat_messages')
    op.drop_table('chat_sessions')
    op.drop_table('local_3d_models')
    op.drop_table('async_task_stages')
    op.drop_table('async_tasks')
    op.drop_table('snippet_metadata')
    op.drop_table('validation_errors')
    op.drop_table('gold_standard_upload_status')
    op.drop_table('shared_content')
    op.drop_table('visualizations')
    op.drop_table('tags')
    op.drop_table('prompts')
    op.drop_table('users')
    op.drop_table('tag_categories')
    op.drop_table('ai_providers')
    op.drop_table('visualization_tags')
    op.drop_table('prompt_tags') 