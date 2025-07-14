"""
Product-related API routes
"""
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from ...database.connection import get_db
from ...database.models import Product, Brand, PriceHistory
from ..schemas.product import ProductResponse, ProductListResponse, ProductCreate, ProductUpdate


router = APIRouter()


@router.get("/", response_model=ProductListResponse)
async def get_products(
    skip: int = Query(0, ge=0, description="Number of products to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of products to return"),
    category: Optional[str] = Query(None, description="Product category"),
    brand: Optional[str] = Query(None, description="Brand name"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    availability: Optional[str] = Query(None, description="Availability status"),
    search: Optional[str] = Query(None, description="Search keywords"),
    sort_by: str = Query("updated_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    db: Session = Depends(get_db)
):
    """Get product list"""
    query = db.query(Product).join(Brand)
    
    # Filter conditions
    if category:
        query = query.filter(Product.category == category)
    
    if brand:
        query = query.filter(Brand.name.ilike(f"%{brand}%"))
    
    if min_price is not None:
        query = query.filter(Product.current_price >= min_price)
    
    if max_price is not None:
        query = query.filter(Product.current_price <= max_price)
    
    if availability:
        query = query.filter(Product.availability == availability)
    
    if search:
        query = query.filter(
            or_(
                Product.name.ilike(f"%{search}%"),
                Product.description.ilike(f"%{search}%")
            )
        )
    
    # Sorting
    if hasattr(Product, sort_by):
        order_column = getattr(Product, sort_by)
        if sort_order.lower() == "desc":
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(order_column)
    
    # Pagination
    total = query.count()
    products = query.offset(skip).limit(limit).all()
    
    return ProductListResponse(
        products=products,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    db: Session = Depends(get_db)
):
    """獲取單個產品詳情"""
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="產品未找到")
    
    return ProductResponse.from_orm(product)


@router.get("/{product_id}/price-history")
async def get_product_price_history(
    product_id: UUID,
    days: int = Query(30, ge=1, le=365, description="天數"),
    db: Session = Depends(get_db)
):
    """獲取產品價格歷史"""
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="產品未找到")
    
    from_date = datetime.now() - timedelta(days=days)
    
    price_history = db.query(PriceHistory).filter(
        and_(
            PriceHistory.product_id == product_id,
            PriceHistory.recorded_at >= from_date
        )
    ).order_by(PriceHistory.recorded_at).all()
    
    return {
        "product_id": product_id,
        "history": price_history,
        "period_days": days
    }


@router.post("/", response_model=ProductResponse)
async def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db)
):
    """創建新產品"""
    # 檢查品牌是否存在
    brand = db.query(Brand).filter(Brand.id == product.brand_id).first()
    if not brand:
        raise HTTPException(status_code=400, detail="品牌不存在")
    
    # 檢查產品是否已存在
    existing_product = db.query(Product).filter(
        and_(
            Product.website_id == product.website_id,
            Product.source_url == product.source_url
        )
    ).first()
    
    if existing_product:
        raise HTTPException(status_code=400, detail="產品已存在")
    
    # 創建產品
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    
    return ProductResponse.from_orm(db_product)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    product_update: ProductUpdate,
    db: Session = Depends(get_db)
):
    """更新產品"""
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="產品未找到")
    
    # 更新產品資料
    for field, value in product_update.dict(exclude_unset=True).items():
        setattr(product, field, value)
    
    product.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(product)
    
    return ProductResponse.from_orm(product)


@router.delete("/{product_id}")
async def delete_product(
    product_id: UUID,
    db: Session = Depends(get_db)
):
    """刪除產品"""
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="產品未找到")
    
    db.delete(product)
    db.commit()
    
    return {"message": "產品已刪除"}


@router.get("/category/{category}")
async def get_products_by_category(
    category: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """根據分類獲取產品"""
    products = db.query(Product).filter(
        Product.category == category
    ).offset(skip).limit(limit).all()
    
    total = db.query(Product).filter(Product.category == category).count()
    
    return {
        "category": category,
        "products": products,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/search/similar/{product_id}")
async def get_similar_products(
    product_id: UUID,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """獲取相似產品"""
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="產品未找到")
    
    # 尋找相似產品（同品牌、同分類）
    similar_products = db.query(Product).filter(
        and_(
            Product.id != product_id,
            Product.brand_id == product.brand_id,
            Product.category == product.category
        )
    ).limit(limit).all()
    
    return {
        "product_id": product_id,
        "similar_products": similar_products
    }