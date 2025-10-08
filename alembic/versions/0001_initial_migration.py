"""Initial migration

Revision ID: 0001
Revises: 
Create Date: 2024-12-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create site_configs table
    op.create_table('site_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('site_id', sa.String(length=50), nullable=False),
        sa.Column('site_name', sa.String(length=100), nullable=False),
        sa.Column('site_type', sa.Enum('mariachi', 'restaurant', 'ecommerce', 'services', 'general', name='sitetype'), nullable=True),
        sa.Column('primary_color', sa.String(length=7), nullable=True),
        sa.Column('secondary_color', sa.String(length=7), nullable=True),
        sa.Column('logo_url', sa.String(length=500), nullable=True),
        sa.Column('favicon_url', sa.String(length=500), nullable=True),
        sa.Column('max_discount_percentage', sa.Integer(), nullable=True),
        sa.Column('discount_per_action', sa.Integer(), nullable=True),
        sa.Column('sticker_expiration_days', sa.Integer(), nullable=True),
        sa.Column('points_per_video', sa.Integer(), nullable=True),
        sa.Column('points_per_like', sa.Integer(), nullable=True),
        sa.Column('points_per_comment', sa.Integer(), nullable=True),
        sa.Column('points_per_review', sa.Integer(), nullable=True),
        sa.Column('youtube_playlist_id', sa.String(length=100), nullable=True),
        sa.Column('video_progression_enabled', sa.Boolean(), nullable=True),
        sa.Column('instagram_required', sa.Boolean(), nullable=True),
        sa.Column('odoo_integration', sa.Boolean(), nullable=True),
        sa.Column('odoo_url', sa.String(length=500), nullable=True),
        sa.Column('odoo_database', sa.String(length=100), nullable=True),
        sa.Column('odoo_username', sa.String(length=100), nullable=True),
        sa.Column('odoo_password', sa.String(length=100), nullable=True),
        sa.Column('email_from', sa.String(length=100), nullable=True),
        sa.Column('email_signature', sa.Text(), nullable=True),
        sa.Column('welcome_message', sa.Text(), nullable=True),
        sa.Column('sticker_message', sa.Text(), nullable=True),
        sa.Column('video_completion_message', sa.Text(), nullable=True),
        sa.Column('allowed_domains', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('activo', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_site_configs_id'), 'site_configs', ['id'], unique=False)
    op.create_index(op.f('ix_site_configs_site_id'), 'site_configs', ['site_id'], unique=True)

    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('site_id', sa.String(length=50), nullable=False),
        sa.Column('nombre', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=100), nullable=False),
        sa.Column('telefono', sa.String(length=20), nullable=True),
        sa.Column('fecha_registro', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('puntos_acumulados', sa.Integer(), nullable=True),
        sa.Column('total_descuento', sa.Integer(), nullable=True),
        sa.Column('instagram_seguido', sa.Boolean(), nullable=True),
        sa.Column('instagram_user_id', sa.String(length=100), nullable=True),
        sa.Column('instagram_access_token', sa.String(length=500), nullable=True),
        sa.Column('reseñas_dejadas', sa.Integer(), nullable=True),
        sa.Column('videos_completados', sa.Integer(), nullable=True),
        sa.Column('stickers_generados', sa.Integer(), nullable=True),
        sa.Column('sincronizado_odoo', sa.Boolean(), nullable=True),
        sa.Column('id_odoo', sa.String(length=50), nullable=True),
        sa.Column('fecha_sincronizacion', sa.DateTime(timezone=True), nullable=True),
        sa.Column('activo', sa.Boolean(), nullable=True),
        sa.Column('verificado', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['site_id'], ['site_configs.site_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_site_id'), 'users', ['site_id'], unique=False)

    # Create stickers table
    op.create_table('stickers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('site_id', sa.String(length=50), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('tipo_sticker', sa.Enum('registro', 'instagram', 'reseña', 'video', 'engagement', name='stickertype'), nullable=False),
        sa.Column('codigo_descuento', sa.String(length=20), nullable=False),
        sa.Column('porcentaje_descuento', sa.Integer(), nullable=True),
        sa.Column('fecha_generacion', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('fecha_expiracion', sa.DateTime(timezone=True), nullable=False),
        sa.Column('usado', sa.Boolean(), nullable=True),
        sa.Column('fecha_uso', sa.DateTime(timezone=True), nullable=True),
        sa.Column('usado_por', sa.String(length=100), nullable=True),
        sa.Column('pdf_path', sa.String(length=500), nullable=True),
        sa.Column('qr_code_path', sa.String(length=500), nullable=True),
        sa.Column('sincronizado_odoo', sa.Boolean(), nullable=True),
        sa.Column('id_odoo', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['site_id'], ['site_configs.site_id'], ),
        sa.ForeignKeyConstraint(['usuario_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('codigo_descuento')
    )
    op.create_index(op.f('ix_stickers_codigo_descuento'), 'stickers', ['codigo_descuento'], unique=True)
    op.create_index(op.f('ix_stickers_id'), 'stickers', ['id'], unique=False)
    op.create_index(op.f('ix_stickers_site_id'), 'stickers', ['site_id'], unique=False)
    op.create_index(op.f('ix_stickers_usuario_id'), 'stickers', ['usuario_id'], unique=False)

    # Create videos table
    op.create_table('videos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('site_id', sa.String(length=50), nullable=False),
        sa.Column('orden', sa.Integer(), nullable=False),
        sa.Column('titulo', sa.String(length=200), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('categoria', sa.Enum('introduccion', 'servicios', 'eventos', 'testimonios', 'contacto', 'promocional', name='videocategory'), nullable=True),
        sa.Column('youtube_id', sa.String(length=50), nullable=False),
        sa.Column('youtube_url', sa.String(length=500), nullable=True),
        sa.Column('duracion_segundos', sa.Integer(), nullable=True),
        sa.Column('thumbnail_url', sa.String(length=500), nullable=True),
        sa.Column('puntos_por_completar', sa.Integer(), nullable=True),
        sa.Column('es_obligatorio', sa.Boolean(), nullable=True),
        sa.Column('activo', sa.Boolean(), nullable=True),
        sa.Column('tags', sa.Text(), nullable=True),
        sa.Column('metadata', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['site_id'], ['site_configs.site_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_videos_id'), 'videos', ['id'], unique=False)
    op.create_index(op.f('ix_videos_site_id'), 'videos', ['site_id'], unique=False)
    op.create_index(op.f('ix_videos_youtube_id'), 'videos', ['youtube_id'], unique=False)

    # Create video_completions table
    op.create_table('video_completions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('video_id', sa.Integer(), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('fecha_completado', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('tiempo_visualizacion', sa.Integer(), nullable=True),
        sa.Column('porcentaje_completado', sa.Integer(), nullable=True),
        sa.Column('puntos_obtenidos', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['usuario_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['video_id'], ['videos.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_video_completions_id'), 'video_completions', ['id'], unique=False)
    op.create_index(op.f('ix_video_completions_usuario_id'), 'video_completions', ['usuario_id'], unique=False)
    op.create_index(op.f('ix_video_completions_video_id'), 'video_completions', ['video_id'], unique=False)

    # Create interactions table
    op.create_table('interactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('site_id', sa.String(length=50), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('tipo_interaccion', sa.Enum('like', 'comentario', 'reseña', 'video_completado', 'sticker_generado', 'instagram_verificado', name='interactiontype'), nullable=False),
        sa.Column('contenido_id', sa.Integer(), nullable=True),
        sa.Column('contenido_tipo', sa.String(length=50), nullable=True),
        sa.Column('contenido', sa.Text(), nullable=True),
        sa.Column('calificacion', sa.Integer(), nullable=True),
        sa.Column('puntos_obtenidos', sa.Integer(), nullable=True),
        sa.Column('sticker_generado', sa.Boolean(), nullable=True),
        sa.Column('sticker_id', sa.Integer(), nullable=True),
        sa.Column('moderado', sa.Boolean(), nullable=True),
        sa.Column('aprobado', sa.Boolean(), nullable=True),
        sa.Column('fecha_moderacion', sa.DateTime(timezone=True), nullable=True),
        sa.Column('moderado_por', sa.String(length=100), nullable=True),
        sa.Column('metadata', sa.Text(), nullable=True),
        sa.Column('fecha_interaccion', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['site_id'], ['site_configs.site_id'], ),
        sa.ForeignKeyConstraint(['sticker_id'], ['stickers.id'], ),
        sa.ForeignKeyConstraint(['usuario_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_interactions_id'), 'interactions', ['id'], unique=False)
    op.create_index(op.f('ix_interactions_site_id'), 'interactions', ['site_id'], unique=False)
    op.create_index(op.f('ix_interactions_usuario_id'), 'interactions', ['usuario_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_interactions_usuario_id'), table_name='interactions')
    op.drop_index(op.f('ix_interactions_site_id'), table_name='interactions')
    op.drop_index(op.f('ix_interactions_id'), table_name='interactions')
    op.drop_table('interactions')
    op.drop_index(op.f('ix_video_completions_video_id'), table_name='video_completions')
    op.drop_index(op.f('ix_video_completions_usuario_id'), table_name='video_completions')
    op.drop_index(op.f('ix_video_completions_id'), table_name='video_completions')
    op.drop_table('video_completions')
    op.drop_index(op.f('ix_videos_youtube_id'), table_name='videos')
    op.drop_index(op.f('ix_videos_site_id'), table_name='videos')
    op.drop_index(op.f('ix_videos_id'), table_name='videos')
    op.drop_table('videos')
    op.drop_index(op.f('ix_stickers_usuario_id'), table_name='stickers')
    op.drop_index(op.f('ix_stickers_site_id'), table_name='stickers')
    op.drop_index(op.f('ix_stickers_id'), table_name='stickers')
    op.drop_index(op.f('ix_stickers_codigo_descuento'), table_name='stickers')
    op.drop_table('stickers')
    op.drop_index(op.f('ix_users_site_id'), table_name='users')
    op.drop_index(op.f('ix_users_id'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_site_configs_site_id'), table_name='site_configs')
    op.drop_index(op.f('ix_site_configs_id'), table_name='site_configs')
    op.drop_table('site_configs')
