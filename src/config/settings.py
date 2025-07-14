"""
應用程式設定配置
"""
import os
from typing import Optional, List
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """應用程式設定"""
    
    # 基本設定
    app_name: str = "Price Cage"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # 資料庫設定
    database_url: str = Field(
        default="postgresql://user:password@localhost:5432/price_cage",
        env="DATABASE_URL"
    )
    database_echo: bool = False
    
    # API 設定
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1
    api_reload: bool = False
    
    # 爬蟲設定
    crawler_delay: float = 1.0
    crawler_timeout: int = 30
    crawler_retries: int = 3
    crawler_user_agents: List[str] = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    ]
    
    # Redis 設定
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db: int = 0
    
    # Celery 設定
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/0"
    
    # 日誌設定
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: Optional[str] = None
    
    # 安全設定
    secret_key: str = Field(
        default="your-secret-key-here",
        env="SECRET_KEY"
    )
    allowed_hosts: List[str] = ["*"]
    
    # 存儲設定
    storage_path: str = "./data"
    image_storage_path: str = "./data/images"
    
    # 外部API設定
    proxy_enabled: bool = False
    proxy_http: Optional[str] = None
    proxy_https: Optional[str] = None
    
    # 監控設定
    enable_metrics: bool = True
    metrics_port: int = 9090
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


class CrawlerConfig:
    """爬蟲配置"""
    
    # 格鬥用品網站配置
    FIGHTING_GEAR_SITES = {
        "venum": {
            "base_url": "https://www.venum.com",
            "categories": [
                "/boxing-gloves",
                "/mma-gloves",
                "/shin-guards",
                "/mouthguards"
            ],
            "selectors": {
                "product_list": ".product-item",
                "product_link": ".product-item a",
                "product_name": ".product-name",
                "product_price": ".price",
                "product_image": ".product-image img"
            }
        },
        "tatami": {
            "base_url": "https://www.tatamifightwear.com",
            "categories": [
                "/gis",
                "/rashguards",
                "/shorts",
                "/accessories"
            ],
            "selectors": {
                "product_list": ".product-item",
                "product_link": ".product-item a",
                "product_name": ".product-title",
                "product_price": ".price",
                "product_image": ".product-image img"
            }
        },
        "hayabusa": {
            "base_url": "https://www.hayabusafight.com",
            "categories": [
                "/boxing-gloves",
                "/mma-gloves",
                "/shin-guards",
                "/headgear"
            ],
            "selectors": {
                "product_list": ".product-item",
                "product_link": ".product-item a",
                "product_name": ".product-name",
                "product_price": ".price",
                "product_image": ".product-image img"
            }
        }
    }
    
    # 潮流衣物網站配置
    STREETWEAR_SITES = {
        "supreme": {
            "base_url": "https://www.supremenewyork.com",
            "categories": [
                "/shop/all/jackets",
                "/shop/all/shirts",
                "/shop/all/t-shirts",
                "/shop/all/sweatshirts"
            ],
            "selectors": {
                "product_list": ".product",
                "product_link": ".product a",
                "product_name": ".product-name",
                "product_price": ".price",
                "product_image": ".product-image img"
            }
        },
        "bape": {
            "base_url": "https://www.bape.com",
            "categories": [
                "/men/tops",
                "/men/bottoms",
                "/men/outerwear",
                "/accessories"
            ],
            "selectors": {
                "product_list": ".product-item",
                "product_link": ".product-item a",
                "product_name": ".product-name",
                "product_price": ".price",
                "product_image": ".product-image img"
            }
        },
        "stussy": {
            "base_url": "https://www.stussy.com",
            "categories": [
                "/mens/tops",
                "/mens/bottoms",
                "/mens/outerwear",
                "/accessories"
            ],
            "selectors": {
                "product_list": ".product-item",
                "product_link": ".product-item a",
                "product_name": ".product-name",
                "product_price": ".price",
                "product_image": ".product-image img"
            }
        }
    }


# 全域設定實例
settings = Settings()
crawler_config = CrawlerConfig()