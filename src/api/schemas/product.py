"""
產品相關的 Pydantic 模型
"""
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class ProductBase(BaseModel):
    """產品基礎模型"""
    name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., min_length=1, max_length=50)
    subcategory: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    model_number: Optional[str] = Field(None, max_length=100)
    sku: Optional[str] = Field(None, max_length=100)
    current_price: Optional[float] = Field(None, ge=0)
    original_price: Optional[float] = Field(None, ge=0)
    currency: str = Field(default="USD", max_length=10)
    availability: str = Field(default="unknown", max_length=20)
    stock_quantity: Optional[int] = Field(None, ge=0)
    size_options: Optional[List[str]] = None
    color_options: Optional[List[str]] = None
    image_urls: Optional[List[str]] = None
    primary_image_url: Optional[str] = Field(None, max_length=500)
    source_url: str = Field(..., max_length=500)
    metadata: Optional[dict] = None
    is_active: bool = True


class ProductCreate(ProductBase):
    """創建產品的模型"""
    brand_id: UUID
    website_id: UUID


class ProductUpdate(BaseModel):
    """更新產品的模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    subcategory: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    model_number: Optional[str] = Field(None, max_length=100)
    sku: Optional[str] = Field(None, max_length=100)
    current_price: Optional[float] = Field(None, ge=0)
    original_price: Optional[float] = Field(None, ge=0)
    currency: Optional[str] = Field(None, max_length=10)
    availability: Optional[str] = Field(None, max_length=20)
    stock_quantity: Optional[int] = Field(None, ge=0)
    size_options: Optional[List[str]] = None
    color_options: Optional[List[str]] = None
    image_urls: Optional[List[str]] = None
    primary_image_url: Optional[str] = Field(None, max_length=500)
    source_url: Optional[str] = Field(None, max_length=500)
    metadata: Optional[dict] = None
    is_active: Optional[bool] = None


class ProductResponse(BaseModel):
    """產品響應模型"""
    id: UUID
    name: str
    brand_id: UUID
    website_id: UUID
    category: str
    subcategory: Optional[str]
    description: Optional[str]
    model_number: Optional[str]
    sku: Optional[str]
    current_price: Optional[float]
    original_price: Optional[float]
    currency: str
    availability: str
    stock_quantity: Optional[int]
    size_options: Optional[List[str]]
    color_options: Optional[List[str]]
    image_urls: Optional[List[str]]
    primary_image_url: Optional[str]
    source_url: str
    metadata: Optional[dict]
    is_active: bool
    last_scraped: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    """產品列表響應模型"""
    products: List[ProductResponse]
    total: int
    skip: int
    limit: int


class PriceHistoryResponse(BaseModel):
    """價格歷史響應模型"""
    id: UUID
    product_id: UUID
    price: float
    original_price: Optional[float]
    currency: str
    availability: str
    stock_quantity: Optional[int]
    recorded_at: datetime
    
    class Config:
        from_attributes = True


class ProductSearchRequest(BaseModel):
    """產品搜尋請求模型"""
    query: str = Field(..., min_length=1, max_length=255)
    category: Optional[str] = None
    brand: Optional[str] = None
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    availability: Optional[str] = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class ProductStatistics(BaseModel):
    """產品統計模型"""
    total_products: int
    active_products: int
    categories: dict
    brands: dict
    average_price: float
    price_range: dict