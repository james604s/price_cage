#!/usr/bin/env python3
"""
Center-SP Sports Equipment Crawler
Crawls https://www.center-sp.co.jp/ec/ for boxing and martial arts equipment
"""

import asyncio
import re
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .base_crawler import BaseCrawler, ProductInfo


class CenterSPCrawler(BaseCrawler):
    """Crawler for Center-SP sports equipment website"""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://www.center-sp.co.jp/ec/"
        self.brand = "Center-SP"
        
        # Category mapping for better organization
        self.category_mapping = {
            'boxing': ['ボクシング', 'boxing', 'gloves', 'グローブ'],
            'martial_arts': ['格闘技', 'martial arts', 'karate', '空手'],
            'training': ['トレーニング', 'training', 'フィットネス'],
            'protective_gear': ['プロテクター', 'protective', 'protector'],
            'apparel': ['ウェア', 'apparel', 'clothing', 'シューズ'],
            'equipment': ['用品', 'equipment', 'accessories']
        }
    
    def _normalize_category(self, category_text: str) -> str:
        """Normalize category text to standard format"""
        category_text = category_text.lower().strip()
        
        for standard_category, keywords in self.category_mapping.items():
            for keyword in keywords:
                if keyword.lower() in category_text:
                    return standard_category
        
        return 'other'
    
    def _extract_price(self, price_text: str) -> float:
        """Extract price from Japanese text"""
        if not price_text:
            return 0.0
        
        # Remove common Japanese price prefixes/suffixes
        price_text = re.sub(r'[¥円税込価格定価]', '', price_text)
        price_text = re.sub(r'[,\s]', '', price_text)
        
        # Extract numeric value
        price_match = re.search(r'(\d+)', price_text)
        if price_match:
            return float(price_match.group(1))
        
        return 0.0
    
    def _get_product_urls(self, category_url: str) -> List[str]:
        """Get product URLs from category page"""
        product_urls = []
        
        try:
            self.logger.info(f"Fetching category page: {category_url}")
            self.driver.get(category_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Look for product links
            product_links = self.driver.find_elements(
                By.CSS_SELECTOR, 
                "a[href*='product'], a[href*='item'], .product-link, .item-link"
            )
            
            for link in product_links:
                href = link.get_attribute('href')
                if href and self._is_product_url(href):
                    full_url = urljoin(self.base_url, href)
                    if full_url not in product_urls:
                        product_urls.append(full_url)
            
            # Handle pagination if exists
            try:
                next_page = self.driver.find_element(
                    By.CSS_SELECTOR, 
                    "a[href*='page']:contains('次へ'), a[href*='page']:contains('Next'), .pagination-next"
                )
                if next_page:
                    next_url = next_page.get_attribute('href')
                    if next_url:
                        product_urls.extend(self._get_product_urls(next_url))
            except NoSuchElementException:
                pass
                
        except TimeoutException:
            self.logger.error(f"Timeout loading category page: {category_url}")
        except Exception as e:
            self.logger.error(f"Error fetching product URLs from {category_url}: {e}")
        
        return product_urls
    
    def _is_product_url(self, url: str) -> bool:
        """Check if URL is a product page"""
        product_indicators = [
            'product', 'item', 'detail', 'goods', 
            'p_', 'i_', 'detail.php', 'product.php'
        ]
        
        url_lower = url.lower()
        return any(indicator in url_lower for indicator in product_indicators)
    
    def _extract_product_info(self, product_url: str) -> Optional[ProductInfo]:
        """Extract product information from product page"""
        try:
            self.logger.info(f"Extracting product info from: {product_url}")
            self.driver.get(product_url)
            
            # Wait for product page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Extract product name
            name_selectors = [
                'h1', '.product-name', '.item-name', '.product-title',
                '#product-name', '#item-name', '.main-title'
            ]
            
            name = None
            for selector in name_selectors:
                try:
                    name_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    name = name_element.text.strip()
                    if name:
                        break
                except NoSuchElementException:
                    continue
            
            if not name:
                self.logger.warning(f"Could not extract product name from {product_url}")
                return None
            
            # Extract price
            price_selectors = [
                '.price', '.product-price', '.item-price', '#price',
                '.price-value', '.cost', '.yen', '[class*="price"]'
            ]
            
            price = 0.0
            for selector in price_selectors:
                try:
                    price_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    price_text = price_element.text.strip()
                    price = self._extract_price(price_text)
                    if price > 0:
                        break
                except NoSuchElementException:
                    continue
            
            # Extract image URL
            image_url = None
            try:
                img_element = self.driver.find_element(
                    By.CSS_SELECTOR, 
                    '.product-image img, .item-image img, .main-image img, img[src*="product"], img[src*="item"]'
                )
                image_url = img_element.get_attribute('src')
                if image_url:
                    image_url = urljoin(self.base_url, image_url)
            except NoSuchElementException:
                pass
            
            # Extract description
            description_selectors = [
                '.product-description', '.item-description', '.description',
                '.product-detail', '.item-detail', '.detail-text'
            ]
            
            description = ""
            for selector in description_selectors:
                try:
                    desc_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    description = desc_element.text.strip()
                    if description:
                        break
                except NoSuchElementException:
                    continue
            
            # Determine category from URL or page content
            category = self._determine_category(product_url, name, description)
            
            # Extract specifications if available
            specs = self._extract_specifications()
            
            return ProductInfo(
                name=name,
                brand=self.brand,
                price=price,
                currency="JPY",
                category=category,
                description=description,
                image_url=image_url,
                product_url=product_url,
                availability=True,  # Assume available if listed
                specifications=specs
            )
            
        except TimeoutException:
            self.logger.error(f"Timeout loading product page: {product_url}")
        except Exception as e:
            self.logger.error(f"Error extracting product info from {product_url}: {e}")
        
        return None
    
    def _determine_category(self, url: str, name: str, description: str) -> str:
        """Determine product category based on URL and content"""
        combined_text = f"{url} {name} {description}".lower()
        
        # Check for specific category keywords
        if any(keyword in combined_text for keyword in ['ボクシング', 'boxing', 'glove', 'グローブ']):
            return 'boxing'
        elif any(keyword in combined_text for keyword in ['格闘技', 'martial', 'karate', '空手']):
            return 'martial_arts'
        elif any(keyword in combined_text for keyword in ['トレーニング', 'training', 'fitness']):
            return 'training'
        elif any(keyword in combined_text for keyword in ['プロテクター', 'protective', 'protector']):
            return 'protective_gear'
        elif any(keyword in combined_text for keyword in ['ウェア', 'apparel', 'clothing', 'shoe']):
            return 'apparel'
        else:
            return 'equipment'
    
    def _extract_specifications(self) -> Dict[str, Any]:
        """Extract product specifications if available"""
        specs = {}
        
        try:
            # Look for specification table or list
            spec_selectors = [
                '.specifications', '.spec-table', '.product-specs',
                '.detail-table', '.product-info-table'
            ]
            
            for selector in spec_selectors:
                try:
                    spec_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    # Extract table data
                    rows = spec_element.find_elements(By.CSS_SELECTOR, 'tr')
                    for row in rows:
                        cells = row.find_elements(By.CSS_SELECTOR, 'td, th')
                        if len(cells) >= 2:
                            key = cells[0].text.strip()
                            value = cells[1].text.strip()
                            if key and value:
                                specs[key] = value
                    
                    if specs:
                        break
                        
                except NoSuchElementException:
                    continue
        
        except Exception as e:
            self.logger.error(f"Error extracting specifications: {e}")
        
        return specs
    
    def _get_category_urls(self) -> List[str]:
        """Get category URLs from main page"""
        category_urls = []
        
        try:
            self.logger.info("Fetching main category URLs")
            self.driver.get(self.base_url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Look for category links
            category_selectors = [
                'nav a', '.category-link', '.menu-item a', 
                '.navigation a', 'a[href*="category"]'
            ]
            
            for selector in category_selectors:
                try:
                    links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for link in links:
                        href = link.get_attribute('href')
                        if href and self._is_category_url(href):
                            full_url = urljoin(self.base_url, href)
                            if full_url not in category_urls:
                                category_urls.append(full_url)
                except NoSuchElementException:
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error fetching category URLs: {e}")
        
        return category_urls
    
    def _is_category_url(self, url: str) -> bool:
        """Check if URL is a category page"""
        category_indicators = [
            'category', 'cat', 'genre', 'section', 'type',
            'boxing', 'martial', 'training', 'equipment'
        ]
        
        url_lower = url.lower()
        return any(indicator in url_lower for indicator in category_indicators)
    
    def crawl_all(self, categories: Optional[List[str]] = None) -> List[ProductInfo]:
        """Crawl all products from specified categories"""
        products = []
        
        try:
            self.setup_driver()
            
            # Get category URLs
            category_urls = self._get_category_urls()
            
            # If no categories found, try direct product search
            if not category_urls:
                self.logger.warning("No category URLs found, trying direct product search")
                category_urls = [self.base_url]
            
            # Filter categories if specified
            if categories:
                filtered_urls = []
                for cat in categories:
                    filtered_urls.extend([
                        url for url in category_urls 
                        if cat.lower() in url.lower()
                    ])
                category_urls = filtered_urls or category_urls
            
            # Crawl each category
            for category_url in category_urls:
                self.logger.info(f"Crawling category: {category_url}")
                
                # Get product URLs from category
                product_urls = self._get_product_urls(category_url)
                
                # Extract product info
                for product_url in product_urls:
                    product_info = self._extract_product_info(product_url)
                    if product_info:
                        products.append(product_info)
                        self.logger.info(f"Extracted: {product_info.name} - ¥{product_info.price}")
                    
                    # Rate limiting
                    time.sleep(1)
                
                # Break between categories
                time.sleep(2)
                
        except Exception as e:
            self.logger.error(f"Error during crawling: {e}")
        finally:
            self.cleanup_driver()
        
        self.logger.info(f"Crawling completed. Total products: {len(products)}")
        return products
    
    async def crawl_all_async(self, categories: Optional[List[str]] = None) -> List[ProductInfo]:
        """Async version of crawl_all"""
        # For now, run the sync version in a thread
        # Could be improved with async Selenium alternatives
        return await asyncio.get_event_loop().run_in_executor(
            None, self.crawl_all, categories
        )


if __name__ == "__main__":
    # Test the crawler
    crawler = CenterSPCrawler()
    products = crawler.crawl_all()
    
    for product in products[:5]:  # Show first 5 products
        print(f"Name: {product.name}")
        print(f"Price: ¥{product.price}")
        print(f"Category: {product.category}")
        print(f"URL: {product.product_url}")
        print("-" * 50)