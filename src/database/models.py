"""
資料庫模型定義
使用 SQLAlchemy ORM 定義資料表結構
"""
from datetime import datetime
from enum import Enum
from typing import Optional, List

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, Text, 
    ForeignKey, Index, UniqueConstraint, CheckConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSON
import uuid

Base = declarative_base()


class ProductCategory(str, Enum):
    """產品分類枚舉"""
    FIGHTING_GEAR = "fighting_gear"
    STREETWEAR = "streetwear"
    BOXING_GLOVES = "boxing_gloves"
    MMA_GLOVES = "mma_gloves"
    SHIN_GUARDS = "shin_guards"
    HEADGEAR = "headgear"
    RASH_GUARDS = "rash_guards"
    SHORTS = "shorts"
    T_SHIRTS = "t_shirts"
    HOODIES = "hoodies"
    JACKETS = "jackets"
    ACCESSORIES = "accessories"


class AvailabilityStatus(str, Enum):
    """庫存狀態枚舉"""
    IN_STOCK = "in_stock"
    OUT_OF_STOCK = "out_of_stock"
    LIMITED_STOCK = "limited_stock"
    PREORDER = "preorder"
    DISCONTINUED = "discontinued"
    UNKNOWN = "unknown"


class Brand(Base):
    """品牌表"""
    __tablename__ = "brands"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    display_name = Column(String(100))
    category = Column(String(50), nullable=False)  # fighting_gear, streetwear
    website_url = Column(String(255))
    logo_url = Column(String(255))
    description = Column(Text)
    country = Column(String(50))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 關聯關係
    products = relationship("Product", back_populates="brand")
    websites = relationship("Website", back_populates="brand")
    
    def __repr__(self):
        return f"<Brand(name='{self.name}', category='{self.category}')>"


class Website(Base):
    """網站表"""
    __tablename__ = "websites"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    domain = Column(String(100), nullable=False, unique=True)
    base_url = Column(String(255), nullable=False)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id"))
    is_active = Column(Boolean, default=True)
    crawler_config = Column(JSON)  # 儲存爬蟲配置
    last_crawled = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 關聯關係
    brand = relationship("Brand", back_populates="websites")
    products = relationship("Product", back_populates="website")
    crawl_logs = relationship("CrawlLog", back_populates="website")
    
    def __repr__(self):
        return f"<Website(name='{self.name}', domain='{self.domain}')>"


class Product(Base):
    """產品表"""
    __tablename__ = "products"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    brand_id = Column(UUID(as_uuid=True), ForeignKey("brands.id"), nullable=False)
    website_id = Column(UUID(as_uuid=True), ForeignKey("websites.id"), nullable=False)
    category = Column(String(50), nullable=False)
    subcategory = Column(String(50))
    
    # 產品詳情
    description = Column(Text)
    model_number = Column(String(100))
    sku = Column(String(100))
    
    # 價格相關
    current_price = Column(Float)
    original_price = Column(Float)
    currency = Column(String(10), default="USD")
    
    # 庫存狀態
    availability = Column(String(20), default=AvailabilityStatus.UNKNOWN)
    stock_quantity = Column(Integer)
    
    # 產品選項
    size_options = Column(ARRAY(String))
    color_options = Column(ARRAY(String))
    
    # 媒體相關
    image_urls = Column(ARRAY(String))
    primary_image_url = Column(String(500))
    
    # 爬蟲相關
    source_url = Column(String(500), nullable=False)
    last_scraped = Column(DateTime, default=datetime.utcnow)
    
    # 元數據
    metadata = Column(JSON)  # 儲存額外的產品資訊
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 關聯關係
    brand = relationship("Brand", back_populates="products")
    website = relationship("Website", back_populates="products")
    price_history = relationship("PriceHistory", back_populates="product")
    
    # 索引
    __table_args__ = (
        Index("idx_product_brand_category", "brand_id", "category"),
        Index("idx_product_website", "website_id"),
        Index("idx_product_price", "current_price"),
        Index("idx_product_availability", "availability"),
        Index("idx_product_updated", "updated_at"),
        UniqueConstraint("website_id", "source_url", name="uq_website_source_url"),
    )
    
    def __repr__(self):
        return f"<Product(name='{self.name}', brand='{self.brand.name}', price={self.current_price})>"


class PriceHistory(Base):
    """價格歷史表"""
    __tablename__ = "price_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    price = Column(Float, nullable=False)
    original_price = Column(Float)
    currency = Column(String(10), default="USD")
    availability = Column(String(20), nullable=False)
    stock_quantity = Column(Integer)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    
    # 關聯關係
    product = relationship("Product", back_populates="price_history")
    
    # 索引
    __table_args__ = (
        Index("idx_price_history_product", "product_id"),
        Index("idx_price_history_recorded", "recorded_at"),
        Index("idx_price_history_product_time", "product_id", "recorded_at"),
    )
    
    def __repr__(self):
        return f"<PriceHistory(product_id='{self.product_id}', price={self.price}, recorded_at='{self.recorded_at}')>"


class CrawlLog(Base):
    """爬蟲日誌表"""
    __tablename__ = "crawl_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    website_id = Column(UUID(as_uuid=True), ForeignKey("websites.id"), nullable=False)
    crawl_type = Column(String(50), nullable=False)  # category, product, full
    status = Column(String(20), nullable=False)  # success, failed, partial
    
    # 統計資訊
    total_products = Column(Integer, default=0)
    successful_products = Column(Integer, default=0)
    failed_products = Column(Integer, default=0)
    new_products = Column(Integer, default=0)
    updated_products = Column(Integer, default=0)
    
    # 執行資訊
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    duration_seconds = Column(Integer)
    
    # 錯誤資訊
    error_message = Column(Text)
    error_details = Column(JSON)
    
    # 關聯關係
    website = relationship("Website", back_populates="crawl_logs")
    
    # 索引
    __table_args__ = (
        Index("idx_crawl_log_website", "website_id"),
        Index("idx_crawl_log_start_time", "start_time"),
        Index("idx_crawl_log_status", "status"),
    )
    
    def __repr__(self):
        return f"<CrawlLog(website_id='{self.website_id}', status='{self.status}', start_time='{self.start_time}')>"


class ProductAnalytics(Base):
    """產品分析表"""
    __tablename__ = "product_analytics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    
    # 價格分析
    min_price = Column(Float)
    max_price = Column(Float)
    avg_price = Column(Float)
    price_volatility = Column(Float)  # 價格波動率
    
    # 庫存分析
    stock_out_frequency = Column(Integer, default=0)
    avg_stock_duration = Column(Integer)  # 平均庫存持續時間(天)
    
    # 趨勢分析
    price_trend = Column(String(20))  # rising, falling, stable
    popularity_score = Column(Float)  # 受歡迎程度分數
    
    # 統計週期
    analysis_period = Column(String(20))  # daily, weekly, monthly
    analysis_date = Column(DateTime, nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 關聯關係
    product = relationship("Product")
    
    # 索引
    __table_args__ = (
        Index("idx_analytics_product", "product_id"),
        Index("idx_analytics_date", "analysis_date"),
        Index("idx_analytics_period", "analysis_period"),
        UniqueConstraint("product_id", "analysis_period", "analysis_date", 
                        name="uq_product_analysis"),
    )
    
    def __repr__(self):
        return f"<ProductAnalytics(product_id='{self.product_id}', period='{self.analysis_period}')>"


class UserFavorite(Base):
    """用戶收藏表（為未來擴展準備）"""
    __tablename__ = "user_favorites"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(100), nullable=False)  # 用戶ID
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 關聯關係
    product = relationship("Product")
    
    # 索引
    __table_args__ = (
        Index("idx_favorite_user", "user_id"),
        Index("idx_favorite_product", "product_id"),
        UniqueConstraint("user_id", "product_id", name="uq_user_product_favorite"),
    )
    
    def __repr__(self):
        return f"<UserFavorite(user_id='{self.user_id}', product_id='{self.product_id}')>"


class PriceAlert(Base):
    """價格警報表（為未來擴展準備）"""
    __tablename__ = "price_alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(100), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    target_price = Column(Float, nullable=False)
    alert_type = Column(String(20), nullable=False)  # below, above
    is_active = Column(Boolean, default=True)
    is_triggered = Column(Boolean, default=False)
    triggered_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 關聯關係
    product = relationship("Product")
    
    # 索引
    __table_args__ = (
        Index("idx_alert_user", "user_id"),
        Index("idx_alert_product", "product_id"),
        Index("idx_alert_active", "is_active"),
        CheckConstraint("target_price > 0", name="chk_target_price_positive"),
    )
    
    def __repr__(self):
        return f"<PriceAlert(user_id='{self.user_id}', target_price={self.target_price})>"