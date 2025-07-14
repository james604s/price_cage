"""
Brand-related API routes
"""
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from ...database.connection import get_db
from ...database.models import Brand, Product
from ..schemas.brand import BrandResponse, BrandListResponse, BrandCreate, BrandUpdate


router = APIRouter()


@router.get("/", response_model=BrandListResponse)
async def get_brands(
    skip: int = Query(0, ge=0, description="Number of brands to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of brands to return"),
    category: Optional[str] = Query(None, description="Brand category"),
    search: Optional[str] = Query(None, description="Search keywords"),
    db: Session = Depends(get_db)
):
    """Get brand list"""
    query = db.query(Brand)
    
    # Filter conditions
    if category:
        query = query.filter(Brand.category == category)
    
    if search:
        query = query.filter(Brand.name.ilike(f"%{search}%"))
    
    # Pagination
    total = query.count()
    brands = query.offset(skip).limit(limit).all()
    
    return BrandListResponse(
        brands=brands,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{brand_id}", response_model=BrandResponse)
async def get_brand(
    brand_id: UUID,
    db: Session = Depends(get_db)
):
    """Get specific brand"""
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    return BrandResponse.from_orm(brand)


@router.get("/{brand_id}/products")
async def get_brand_products(
    brand_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get products for specific brand"""
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    products = db.query(Product).filter(
        Product.brand_id == brand_id
    ).offset(skip).limit(limit).all()
    
    total = db.query(Product).filter(Product.brand_id == brand_id).count()
    
    return {
        "brand_id": brand_id,
        "brand_name": brand.name,
        "products": products,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.post("/", response_model=BrandResponse)
async def create_brand(
    brand: BrandCreate,
    db: Session = Depends(get_db)
):
    """Create new brand"""
    # Check if brand already exists
    existing_brand = db.query(Brand).filter(Brand.name == brand.name).first()
    
    if existing_brand:
        raise HTTPException(status_code=400, detail="Brand already exists")
    
    # Create brand
    db_brand = Brand(**brand.dict())
    db.add(db_brand)
    db.commit()
    db.refresh(db_brand)
    
    return BrandResponse.from_orm(db_brand)


@router.put("/{brand_id}", response_model=BrandResponse)
async def update_brand(
    brand_id: UUID,
    brand_update: BrandUpdate,
    db: Session = Depends(get_db)
):
    """Update brand"""
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # Update brand data
    for field, value in brand_update.dict(exclude_unset=True).items():
        setattr(brand, field, value)
    
    brand.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(brand)
    
    return BrandResponse.from_orm(brand)


@router.delete("/{brand_id}")
async def delete_brand(
    brand_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete brand"""
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # Check if brand has products
    product_count = db.query(Product).filter(Product.brand_id == brand_id).count()
    if product_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete brand with {product_count} products"
        )
    
    db.delete(brand)
    db.commit()
    
    return {"message": "Brand deleted successfully"}


@router.get("/{brand_id}/stats")
async def get_brand_stats(
    brand_id: UUID,
    db: Session = Depends(get_db)
):
    """Get brand statistics"""
    brand = db.query(Brand).filter(Brand.id == brand_id).first()
    
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not found")
    
    # Get product statistics
    products_query = db.query(Product).filter(Product.brand_id == brand_id)
    
    total_products = products_query.count()
    active_products = products_query.filter(Product.is_active == True).count()
    
    # Price statistics
    prices = [p.current_price for p in products_query.all() if p.current_price]
    
    if prices:
        avg_price = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)
    else:
        avg_price = min_price = max_price = 0
    
    return {
        "brand_id": brand_id,
        "brand_name": brand.name,
        "total_products": total_products,
        "active_products": active_products,
        "avg_price": round(avg_price, 2),
        "min_price": min_price,
        "max_price": max_price
    }