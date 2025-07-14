"""
Streetwear crawler implementation
"""
from typing import List, Optional
from .base_crawler import BaseCrawler, ProductInfo
from ..parsers.streetwear.supreme_parser import SupremeParser
from ..utils.logger import get_logger


class StreetwearCrawler(BaseCrawler):
    """Streetwear products crawler"""
    
    def __init__(self):
        super().__init__(
            site_name="streetwear",
            base_url="https://example.com"
        )
        self.parsers = {
            'supreme': SupremeParser()
        }
        self.logger = get_logger("streetwear_crawler")
    
    def crawl_all(self, sites: Optional[List[str]] = None) -> List[ProductInfo]:
        """Crawl all streetwear sites"""
        all_products = []
        
        target_sites = sites or list(self.parsers.keys())
        
        for site in target_sites:
            if site in self.parsers:
                try:
                    parser = self.parsers[site]
                    category_urls = parser.get_category_urls()
                    
                    for category_url in category_urls:
                        products = self.crawl_category(category_url)
                        all_products.extend(products)
                        
                except Exception as e:
                    self.logger.error(f"Failed to crawl {site}: {e}")
                    continue
        
        return all_products
    
    async def crawl_all_async(self, sites: Optional[List[str]] = None) -> List[ProductInfo]:
        """Async crawl all streetwear sites"""
        all_products = []
        
        target_sites = sites or list(self.parsers.keys())
        
        for site in target_sites:
            if site in self.parsers:
                try:
                    parser = self.parsers[site]
                    category_urls = parser.get_category_urls()
                    
                    for category_url in category_urls:
                        products = await self.crawl_category_async(category_url)
                        all_products.extend(products)
                        
                except Exception as e:
                    self.logger.error(f"Failed to async crawl {site}: {e}")
                    continue
        
        return all_products