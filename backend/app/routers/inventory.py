"""
Product inventory management endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, require_role
from app.core.database import get_db
from app.models import User, Product, ProductSizeSpec, Brand, UserRole, BrandStatus
from app.schemas import (
    ProductCreate,
    ProductResponse,
    ProductSizeSpecCreate,
    ProductSizeSpecResponse,
)

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: ProductCreate,
    current_user: User = Depends(require_role(UserRole.BRAND)),
    db: AsyncSession = Depends(get_db),
) -> ProductResponse:
    """
    Create a new product (Brand Partner only).

    Requires brand_id from user's brand account.
    """
    # Get brand for this user
    stmt = select(Brand).where(Brand.user_id == current_user.user_id)
    result = await db.execute(stmt)
    brand = result.scalar_one_or_none()

    if not brand:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not associated with a brand"
        )

    # Brand must be approved by an admin before it can list products.
    if brand.status != BrandStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your brand is pending admin approval and cannot list products yet.",
        )

    # Create product
    new_product = Product(
        brand_id=brand.brand_id,
        sku=product.sku,
        name=product.name,
        description=product.description,
        price=product.price,
        image_url=str(product.image_url) if product.image_url else None,
        garment_image_url=str(product.garment_image_url) if product.garment_image_url else None,
        gender_target=product.gender_target,
        dominant_color_hex=product.dominant_color_hex,
    )
    db.add(new_product)
    await db.flush()  # get product_id before adding size specs

    # Persist any inline size specs (validated) so the product ships with sizes.
    created_specs = []
    for spec in product.size_specs:
        spec.validate_ranges()
        new_spec = ProductSizeSpec(
            product_id=new_product.product_id,
            size_label=spec.size_label,
            stock_quantity=spec.stock_quantity,
            chest_min=spec.chest_min,
            chest_max=spec.chest_max,
            waist_min=spec.waist_min,
            waist_max=spec.waist_max,
            hips_min=spec.hips_min,
            hips_max=spec.hips_max,
            inseam_min=spec.inseam_min,
            inseam_max=spec.inseam_max,
            shoulder_width_min=spec.shoulder_width_min,
            shoulder_width_max=spec.shoulder_width_max,
        )
        db.add(new_spec)
        created_specs.append(new_spec)

    await db.commit()
    await db.refresh(new_product)

    return ProductResponse(
        product_id=new_product.product_id,
        brand_id=new_product.brand_id,
        sku=new_product.sku,
        name=new_product.name,
        description=new_product.description,
        price=new_product.price,
        image_url=new_product.image_url,
        garment_image_url=new_product.garment_image_url,
        gender_target=new_product.gender_target,
        dominant_color_hex=new_product.dominant_color_hex,
        size_specs=[
            ProductSizeSpecResponse(
                spec_id=s.spec_id,
                product_id=s.product_id,
                size_label=s.size_label,
                stock_quantity=s.stock_quantity,
                chest_min=s.chest_min,
                chest_max=s.chest_max,
                waist_min=s.waist_min,
                waist_max=s.waist_max,
                hips_min=s.hips_min,
                hips_max=s.hips_max,
                inseam_min=s.inseam_min,
                inseam_max=s.inseam_max,
                shoulder_width_min=s.shoulder_width_min,
                shoulder_width_max=s.shoulder_width_max,
            )
            for s in created_specs
        ],
        created_at=new_product.created_at.isoformat(),
        updated_at=new_product.updated_at.isoformat(),
    )


@router.post("/products/{product_id}/sizes", response_model=ProductSizeSpecResponse, status_code=status.HTTP_201_CREATED)
async def add_size_spec(
    product_id: str,
    size_spec: ProductSizeSpecCreate,
    current_user: User = Depends(require_role(UserRole.BRAND)),
    db: AsyncSession = Depends(get_db),
) -> ProductSizeSpecResponse:
    """
    Add a size specification to a product (Brand Partner only).
    """
    # Get product
    from uuid import UUID
    stmt = select(Product).where(Product.product_id == UUID(product_id))
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Verify brand ownership
    stmt = select(Brand).where(Brand.brand_id == product.brand_id)
    result = await db.execute(stmt)
    brand = result.scalar_one_or_none()

    if not brand or brand.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this product")

    # Validate ranges
    size_spec.validate_ranges()

    # Create size spec
    new_spec = ProductSizeSpec(
        product_id=product.product_id,
        size_label=size_spec.size_label,
        stock_quantity=size_spec.stock_quantity,
        chest_min=size_spec.chest_min,
        chest_max=size_spec.chest_max,
        waist_min=size_spec.waist_min,
        waist_max=size_spec.waist_max,
        hips_min=size_spec.hips_min,
        hips_max=size_spec.hips_max,
        inseam_min=size_spec.inseam_min,
        inseam_max=size_spec.inseam_max,
        shoulder_width_min=size_spec.shoulder_width_min,
        shoulder_width_max=size_spec.shoulder_width_max,
    )
    db.add(new_spec)
    await db.commit()
    await db.refresh(new_spec)

    return ProductSizeSpecResponse(
        spec_id=new_spec.spec_id,
        product_id=new_spec.product_id,
        size_label=new_spec.size_label,
        stock_quantity=new_spec.stock_quantity,
        chest_min=new_spec.chest_min,
        chest_max=new_spec.chest_max,
        waist_min=new_spec.waist_min,
        waist_max=new_spec.waist_max,
        hips_min=new_spec.hips_min,
        hips_max=new_spec.hips_max,
        inseam_min=new_spec.inseam_min,
        inseam_max=new_spec.inseam_max,
        shoulder_width_min=new_spec.shoulder_width_min,
        shoulder_width_max=new_spec.shoulder_width_max,
    )


@router.get("/products", response_model=List[ProductResponse])
async def list_products(
    page: int = 1,
    page_size: int = 20,
    gender: str = None,
    size_label: str = None,
    chest: float = None,
    waist: float = None,
    hips: float = None,
    inseam: float = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ProductResponse]:
    """
    List products with optional filtering by gender, size label, or measurements.
    """
    from uuid import UUID

    # Public catalog only shows products from admin-approved brands.
    stmt = (
        select(Product)
        .join(Brand, Brand.brand_id == Product.brand_id)
        .where(Brand.status == BrandStatus.APPROVED)
        .options(selectinload(Product.size_specs))
    )

    # Filter by gender (default to user's gender if shopper)
    if current_user.role == UserRole.SHOPPER:
        from app.models import UserProfile
        profile_stmt = select(UserProfile).where(UserProfile.user_id == current_user.user_id)
        profile_result = await db.execute(profile_stmt)
        user_profile = profile_result.scalar_one_or_none()

        if gender is None and user_profile:
            # Default to user's gender
            from app.models.enums import Gender, GenderTarget
            gender_map = {
                Gender.MALE: [GenderTarget.MALE, GenderTarget.UNISEX],
                Gender.FEMALE: [GenderTarget.FEMALE, GenderTarget.UNISEX],
                Gender.NON_BINARY: [GenderTarget.MALE, GenderTarget.FEMALE, GenderTarget.UNISEX],
            }
            gender_targets = gender_map.get(user_profile.gender, [])
            stmt = stmt.where(Product.gender_target.in_(gender_targets))

    # Explicit gender query param (overrides the shopper default above).
    if gender is not None:
        from app.models.enums import GenderTarget
        try:
            stmt = stmt.where(Product.gender_target == GenderTarget(gender.lower()))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid gender filter")

    # Size search: keep only products that have at least one size spec matching
    # the requested label and/or covering the given measurements (Requirement 9).
    spec_conditions = []
    if size_label:
        spec_conditions.append(ProductSizeSpec.size_label == size_label)
    if chest is not None:
        spec_conditions.append(
            and_(ProductSizeSpec.chest_min <= chest, ProductSizeSpec.chest_max >= chest)
        )
    if waist is not None:
        spec_conditions.append(
            and_(ProductSizeSpec.waist_min <= waist, ProductSizeSpec.waist_max >= waist)
        )
    if hips is not None:
        spec_conditions.append(
            and_(ProductSizeSpec.hips_min <= hips, ProductSizeSpec.hips_max >= hips)
        )
    if inseam is not None:
        spec_conditions.append(
            and_(ProductSizeSpec.inseam_min <= inseam, ProductSizeSpec.inseam_max >= inseam)
        )

    if spec_conditions:
        matching_specs = (
            select(ProductSizeSpec.product_id)
            .where(and_(*spec_conditions))
            .distinct()
        )
        stmt = stmt.where(Product.product_id.in_(matching_specs))

    # Apply pagination
    offset = (page - 1) * page_size
    stmt = stmt.offset(offset).limit(page_size)

    result = await db.execute(stmt)
    products = result.scalars().all()

    return [
        ProductResponse(
            product_id=p.product_id,
            brand_id=p.brand_id,
            sku=p.sku,
            name=p.name,
            description=p.description,
            price=p.price,
            image_url=p.image_url,
            garment_image_url=p.garment_image_url,
            gender_target=p.gender_target,
            dominant_color_hex=p.dominant_color_hex,
            size_specs=[
                ProductSizeSpecResponse(
                    spec_id=spec.spec_id,
                    product_id=spec.product_id,
                    size_label=spec.size_label,
                    stock_quantity=spec.stock_quantity,
                    chest_min=spec.chest_min,
                    chest_max=spec.chest_max,
                    waist_min=spec.waist_min,
                    waist_max=spec.waist_max,
                    hips_min=spec.hips_min,
                    hips_max=spec.hips_max,
                    inseam_min=spec.inseam_min,
                    inseam_max=spec.inseam_max,
                    shoulder_width_min=spec.shoulder_width_min,
                    shoulder_width_max=spec.shoulder_width_max,
                )
                for spec in p.size_specs
            ],
            created_at=p.created_at.isoformat(),
            updated_at=p.updated_at.isoformat(),
        )
        for p in products
    ]


@router.get("/my-products", response_model=List[ProductResponse])
async def list_my_products(
    current_user: User = Depends(require_role(UserRole.BRAND)),
    db: AsyncSession = Depends(get_db),
) -> List[ProductResponse]:
    """List the calling brand's own products (Requirement 8.5)."""
    brand_stmt = select(Brand).where(Brand.user_id == current_user.user_id)
    brand_result = await db.execute(brand_stmt)
    brand = brand_result.scalar_one_or_none()
    if not brand:
        # No brand record yet -> no products.
        return []

    stmt = (
        select(Product)
        .where(Product.brand_id == brand.brand_id)
        .options(selectinload(Product.size_specs))
    )
    result = await db.execute(stmt)
    products = result.scalars().all()

    return [
        ProductResponse(
            product_id=p.product_id,
            brand_id=p.brand_id,
            sku=p.sku,
            name=p.name,
            description=p.description,
            price=p.price,
            image_url=p.image_url,
            garment_image_url=p.garment_image_url,
            gender_target=p.gender_target,
            dominant_color_hex=p.dominant_color_hex,
            size_specs=[
                ProductSizeSpecResponse(
                    spec_id=spec.spec_id,
                    product_id=spec.product_id,
                    size_label=spec.size_label,
                    stock_quantity=spec.stock_quantity,
                    chest_min=spec.chest_min,
                    chest_max=spec.chest_max,
                    waist_min=spec.waist_min,
                    waist_max=spec.waist_max,
                    hips_min=spec.hips_min,
                    hips_max=spec.hips_max,
                    inseam_min=spec.inseam_min,
                    inseam_max=spec.inseam_max,
                    shoulder_width_min=spec.shoulder_width_min,
                    shoulder_width_max=spec.shoulder_width_max,
                )
                for spec in p.size_specs
            ],
            created_at=p.created_at.isoformat(),
            updated_at=p.updated_at.isoformat(),
        )
        for p in products
    ]


@router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    product_update: ProductCreate,
    current_user: User = Depends(require_role(UserRole.BRAND)),
    db: AsyncSession = Depends(get_db),
) -> ProductResponse:
    """
    Update a product (Brand Partner only, must own the brand).
    """
    from uuid import UUID

    # Get product
    stmt = select(Product).where(Product.product_id == UUID(product_id))
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Verify brand ownership
    stmt = select(Brand).where(Brand.brand_id == product.brand_id)
    result = await db.execute(stmt)
    brand = result.scalar_one_or_none()

    if not brand or brand.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this product")

    # Update product
    product.name = product_update.name
    product.description = product_update.description
    product.price = product_update.price
    product.image_url = str(product_update.image_url) if product_update.image_url else product.image_url
    product.garment_image_url = str(product_update.garment_image_url) if product_update.garment_image_url else product.garment_image_url
    product.gender_target = product_update.gender_target
    product.dominant_color_hex = product_update.dominant_color_hex

    await db.commit()
    await db.refresh(product)

    return ProductResponse(
        product_id=product.product_id,
        brand_id=product.brand_id,
        sku=product.sku,
        name=product.name,
        description=product.description,
        price=product.price,
        image_url=product.image_url,
        garment_image_url=product.garment_image_url,
        gender_target=product.gender_target,
        dominant_color_hex=product.dominant_color_hex,
        size_specs=[],
        created_at=product.created_at.isoformat(),
        updated_at=product.updated_at.isoformat(),
    )


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str,
    current_user: User = Depends(require_role(UserRole.BRAND)),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a product (Brand Partner only, must own the brand).
    """
    from uuid import UUID

    # Get product
    stmt = select(Product).where(Product.product_id == UUID(product_id))
    result = await db.execute(stmt)
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Verify brand ownership
    stmt = select(Brand).where(Brand.brand_id == product.brand_id)
    result = await db.execute(stmt)
    brand = result.scalar_one_or_none()

    if not brand or brand.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this product")

    # Delete product (cascades delete size specs and order items)
    await db.delete(product)
    await db.commit()

