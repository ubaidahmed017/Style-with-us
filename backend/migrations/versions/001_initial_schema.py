"""Initial schema creation - create all core tables and indexes

Revision ID: 001
Revises:
Create Date: 2026-06-24 15:39:21.111000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ENUM types
    userRole_enum = postgresql.ENUM('shopper', 'brand', 'admin', name='userrole')
    userRole_enum.create(op.get_bind())

    gender_enum = postgresql.ENUM('male', 'female', 'non_binary', name='gender')
    gender_enum.create(op.get_bind())

    genderTarget_enum = postgresql.ENUM('male', 'female', 'unisex', name='gendertarget')
    genderTarget_enum.create(op.get_bind())

    bodyShape_enum = postgresql.ENUM('hourglass', 'pear', 'apple', 'rectangle', 'inverted_triangle', name='bodyshape')
    bodyShape_enum.create(op.get_bind())

    skinTonePalette_enum = postgresql.ENUM('warm_spring', 'warm_autumn', 'cool_summer', 'cool_winter', 'neutral_light', 'neutral_deep', name='skinTonepalette')
    skinTonePalette_enum.create(op.get_bind())

    unitPreference_enum = postgresql.ENUM('metric', 'imperial', name='unitpreference')
    unitPreference_enum.create(op.get_bind())

    mlJobStatus_enum = postgresql.ENUM('uploaded', 'queued', 'processing', 'completed', 'failed', name='mljobstatus')
    mlJobStatus_enum.create(op.get_bind())

    orderStatus_enum = postgresql.ENUM('pending', 'confirmed', 'shipped', 'cancelled', name='orderstatus')
    orderStatus_enum.create(op.get_bind())

    # Create users table
    op.create_table(
        'users',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('firebase_uid', sa.String(128), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('role', userRole_enum, nullable=False, server_default='shopper'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('user_id'),
        sa.UniqueConstraint('firebase_uid', name='uq_users_firebase_uid'),
        sa.UniqueConstraint('email', name='uq_users_email'),
    )
    op.create_index('idx_users_firebase_uid', 'users', ['firebase_uid'])

    # Create user_profiles table
    op.create_table(
        'user_profiles',
        sa.Column('profile_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('gender', gender_enum, nullable=False),
        sa.Column('height_cm', sa.Float(), nullable=True),
        sa.Column('weight_kg', sa.Float(), nullable=True),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('chest_cm', sa.Float(), nullable=True),
        sa.Column('waist_cm', sa.Float(), nullable=True),
        sa.Column('hips_cm', sa.Float(), nullable=True),
        sa.Column('inseam_cm', sa.Float(), nullable=True),
        sa.Column('shoulder_width_cm', sa.Float(), nullable=True),
        sa.Column('body_shape', bodyShape_enum, nullable=True),
        sa.Column('skin_tone_hex', sa.String(7), nullable=True),
        sa.Column('skin_tone_palette', skinTonePalette_enum, nullable=True),
        sa.Column('unit_preference', unitPreference_enum, nullable=False, server_default='metric'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('profile_id'),
        sa.UniqueConstraint('user_id', name='uq_user_profiles_user_id'),
    )
    op.create_index('idx_user_profiles_user_id', 'user_profiles', ['user_id'])

    # Create brands table
    op.create_table(
        'brands',
        sa.Column('brand_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_name', sa.String(255), nullable=False),
        sa.Column('logo_url', sa.String(1024), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('brand_id'),
        sa.UniqueConstraint('user_id', name='uq_brands_user_id'),
    )
    op.create_index('idx_brands_user_id', 'brands', ['user_id'])

    # Create products table
    op.create_table(
        'products',
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('brand_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sku', sa.String(100), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.String(2000), nullable=True),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('image_url', sa.String(1024), nullable=True),
        sa.Column('garment_image_url', sa.String(1024), nullable=True),
        sa.Column('gender_target', genderTarget_enum, nullable=False),
        sa.Column('dominant_color_hex', sa.String(7), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['brand_id'], ['brands.brand_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('product_id'),
        sa.UniqueConstraint('sku', name='uq_products_sku'),
    )
    op.create_index('idx_products_brand_id', 'products', ['brand_id'])
    op.create_index('idx_products_gender_target', 'products', ['gender_target'])

    # Create product_size_specs table
    op.create_table(
        'product_size_specs',
        sa.Column('spec_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('size_label', sa.String(20), nullable=False),
        sa.Column('stock_quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('chest_min', sa.Float(), nullable=False),
        sa.Column('chest_max', sa.Float(), nullable=False),
        sa.Column('waist_min', sa.Float(), nullable=False),
        sa.Column('waist_max', sa.Float(), nullable=False),
        sa.Column('hips_min', sa.Float(), nullable=False),
        sa.Column('hips_max', sa.Float(), nullable=False),
        sa.Column('inseam_min', sa.Float(), nullable=True),
        sa.Column('inseam_max', sa.Float(), nullable=True),
        sa.Column('shoulder_width_min', sa.Float(), nullable=True),
        sa.Column('shoulder_width_max', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.product_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('spec_id'),
    )
    op.create_index('idx_product_size_specs_product_id', 'product_size_specs', ['product_id'])
    op.create_index('idx_product_size_specs_product_size', 'product_size_specs', ['product_id', 'size_label'])

    # Create orders table
    op.create_table(
        'orders',
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('total_amount', sa.Float(), nullable=False),
        sa.Column('status', orderStatus_enum, nullable=False, server_default='pending'),
        sa.Column('payment_intent_id', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('order_id'),
    )
    op.create_index('idx_orders_user_id', 'orders', ['user_id'])
    op.create_index('idx_orders_status', 'orders', ['status'])

    # Create order_items table
    op.create_table(
        'order_items',
        sa.Column('item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('size_spec_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('price_at_purchase', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.order_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.product_id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['size_spec_id'], ['product_size_specs.spec_id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('item_id'),
    )
    op.create_index('idx_order_items_order_id', 'order_items', ['order_id'])
    op.create_index('idx_order_items_product_id', 'order_items', ['product_id'])

    # Create ml_jobs table
    op.create_table(
        'ml_jobs',
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_type', sa.String(50), nullable=False),
        sa.Column('status', mlJobStatus_enum, nullable=False, server_default='uploaded'),
        sa.Column('input_image_url', sa.String(1024), nullable=True),
        sa.Column('result_url', sa.String(1024), nullable=True),
        sa.Column('error_message', sa.String(1024), nullable=True),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.product_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('job_id'),
    )
    op.create_index('idx_ml_jobs_user_id', 'ml_jobs', ['user_id'])
    op.create_index('idx_ml_jobs_status', 'ml_jobs', ['status'])
    op.create_index('idx_ml_jobs_user_status', 'ml_jobs', ['user_id', 'status'])


def downgrade() -> None:
    # Drop tables in reverse order of creation
    op.drop_table('ml_jobs')
    op.drop_table('order_items')
    op.drop_table('orders')
    op.drop_table('product_size_specs')
    op.drop_table('products')
    op.drop_table('brands')
    op.drop_table('user_profiles')
    op.drop_table('users')

    # Drop ENUM types
    orderStatus_enum = postgresql.ENUM('pending', 'confirmed', 'shipped', 'cancelled', name='orderstatus')
    orderStatus_enum.drop(op.get_bind())

    mlJobStatus_enum = postgresql.ENUM('uploaded', 'queued', 'processing', 'completed', 'failed', name='mljobstatus')
    mlJobStatus_enum.drop(op.get_bind())

    unitPreference_enum = postgresql.ENUM('metric', 'imperial', name='unitpreference')
    unitPreference_enum.drop(op.get_bind())

    skinTonePalette_enum = postgresql.ENUM('warm_spring', 'warm_autumn', 'cool_summer', 'cool_winter', 'neutral_light', 'neutral_deep', name='skinTonepalette')
    skinTonePalette_enum.drop(op.get_bind())

    bodyShape_enum = postgresql.ENUM('hourglass', 'pear', 'apple', 'rectangle', 'inverted_triangle', name='bodyshape')
    bodyShape_enum.drop(op.get_bind())

    genderTarget_enum = postgresql.ENUM('male', 'female', 'unisex', name='gendertarget')
    genderTarget_enum.drop(op.get_bind())

    gender_enum = postgresql.ENUM('male', 'female', 'non_binary', name='gender')
    gender_enum.drop(op.get_bind())

    userRole_enum = postgresql.ENUM('shopper', 'brand', 'admin', name='userrole')
    userRole_enum.drop(op.get_bind())
