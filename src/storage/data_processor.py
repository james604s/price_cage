"""
Data processor for handling scraped product data
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from ..crawlers.base_crawler import ProductInfo
from ..database.connection import db_manager
from ..database.models import Product, Brand, Website, PriceHistory
from ..utils.logger import get_logger


class DataProcessor:
    """Process and store scraped product data"""
    
    def __init__(self):
        self.logger = get_logger("data_processor")
    
    def process_products(self, products: List[ProductInfo]) -> Dict[str, Any]:
        """Process and store product data"""
        if not products:
            return {"processed": 0, "errors": 0}
        
        processed_count = 0
        error_count = 0
        
        with db_manager.get_session() as session:
            for product_info in products:
                try:
                    self._process_single_product(session, product_info)
                    processed_count += 1
                except Exception as e:
                    self.logger.error(f"Failed to process product {product_info.name}: {e}")
                    error_count += 1
        
        self.logger.info(f"Processed {processed_count} products, {error_count} errors")
        return {"processed": processed_count, "errors": error_count}
    
    def _process_single_product(self, session: Session, product_info: ProductInfo):
        """Process a single product"""
        # Find or create brand
        brand = session.query(Brand).filter(Brand.name == product_info.brand).first()
        if not brand:
            brand = Brand(
                name=product_info.brand,
                display_name=product_info.brand,
                category="fighting_gear" if "fighting" in product_info.category.lower() else "streetwear"
            )
            session.add(brand)
            session.flush()
        
        # Find or create website
        website = session.query(Website).filter(Website.domain.like(f"%{product_info.product_url.split('/')[2]}%")).first()
        if not website:
            domain = product_info.product_url.split('/')[2]
            website = Website(
                name=domain,
                domain=domain,
                base_url=f"https://{domain}",
                brand_id=brand.id
            )
            session.add(website)
            session.flush()
        
        # Check if product exists
        existing_product = session.query(Product).filter(
            Product.source_url == product_info.product_url
        ).first()
        
        if existing_product:
            # Update existing product
            existing_product.current_price = product_info.price
            existing_product.original_price = product_info.original_price
            existing_product.availability = product_info.availability
            existing_product.image_urls = [product_info.image_url] if product_info.image_url else []
            existing_product.primary_image_url = product_info.image_url
            existing_product.size_options = product_info.size_options or []
            existing_product.color_options = product_info.color_options or []
            existing_product.last_scraped = datetime.now()
            existing_product.updated_at = datetime.now()
            
            # Add price history
            price_history = PriceHistory(
                product_id=existing_product.id,
                price=product_info.price,
                original_price=product_info.original_price,
                currency=product_info.currency,
                availability=product_info.availability,
                recorded_at=datetime.now()
            )
            session.add(price_history)
            
        else:
            # Create new product
            new_product = Product(
                name=product_info.name,
                brand_id=brand.id,
                website_id=website.id,
                category=product_info.category,
                description=product_info.description,
                current_price=product_info.price,
                original_price=product_info.original_price,
                currency=product_info.currency,
                availability=product_info.availability,
                size_options=product_info.size_options or [],
                color_options=product_info.color_options or [],
                image_urls=[product_info.image_url] if product_info.image_url else [],
                primary_image_url=product_info.image_url,
                source_url=product_info.product_url,
                last_scraped=datetime.now()
            )
            session.add(new_product)
            session.flush()
            
            # Add initial price history
            price_history = PriceHistory(
                product_id=new_product.id,
                price=product_info.price,
                original_price=product_info.original_price,
                currency=product_info.currency,
                availability=product_info.availability,
                recorded_at=datetime.now()
            )
            session.add(price_history)
        
        session.commit()
    
    def clean_old_data(self, days_to_keep: int = 30):
        """Clean old price history data"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        with db_manager.get_session() as session:
            deleted_count = session.query(PriceHistory).filter(
                PriceHistory.recorded_at < cutoff_date
            ).delete()
            
            session.commit()
            self.logger.info(f"Cleaned {deleted_count} old price history records")
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get processing statistics"""
        with db_manager.get_session() as session:
            total_products = session.query(Product).count()
            total_brands = session.query(Brand).count()
            total_websites = session.query(Website).count()
            total_price_records = session.query(PriceHistory).count()
            
            return {
                "total_products": total_products,
                "total_brands": total_brands,
                "total_websites": total_websites,
                "total_price_records": total_price_records
            }