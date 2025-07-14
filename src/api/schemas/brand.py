"""
Brand-related Pydantic models
"""
from typing import List, Optional
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class BrandBase(BaseModel):
    """Brand base model"""
    name: str = Field(..., min_length=1, max_length=100)
    display_name: Optional[str] = Field(None, max_length=100)
    category: str = Field(..., min_length=1, max_length=50)
    website_url: Optional[str] = Field(None, max_length=255)
    logo_url: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    country: Optional[str] = Field(None, max_length=50)
    is_active: bool = True


class BrandCreate(BrandBase):
    """Create brand model"""
    pass


class BrandUpdate(BaseModel):
    """Update brand model"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    display_name: Optional[str] = Field(None, max_length=100)
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    website_url: Optional[str] = Field(None, max_length=255)
    logo_url: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    country: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


class BrandResponse(BaseModel):
    """Brand response model"""
    id: UUID
    name: str
    display_name: Optional[str]
    category: str
    website_url: Optional[str]
    logo_url: Optional[str]
    description: Optional[str]
    country: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class BrandListResponse(BaseModel):
    """Brand list response model"""
    brands: List[BrandResponse]
    total: int
    skip: int
    limit: int


class BrandWithStats(BrandResponse):
    """Brand with statistics"""
    product_count: int
    avg_price: float
    min_price: float
    max_price: float