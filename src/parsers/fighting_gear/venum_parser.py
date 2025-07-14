"""
Venum 格鬥用品網站解析器
"""
import re
from typing import List, Optional
from bs4 import BeautifulSoup

from ..base_parser import BaseParser
from ...crawlers.base_crawler import ProductInfo


class VenumParser(BaseParser):
    """Venum 網站解析器"""
    
    def __init__(self):
        super().__init__(
            site_name="venum",
            base_url="https://www.venum.com",
            category="fighting_gear"
        )
    
    def get_category_urls(self) -> List[str]:
        """獲取分類頁面 URL"""
        return [
            f"{self.base_url}/boxing-gloves",
            f"{self.base_url}/mma-gloves",
            f"{self.base_url}/shin-guards",
            f"{self.base_url}/mouthguards",
            f"{self.base_url}/headgear",
            f"{self.base_url}/rashguards",
            f"{self.base_url}/shorts",
            f"{self.base_url}/t-shirts"
        ]
    
    def parse_product_list(self, soup: BeautifulSoup) -> List[str]:
        """解析產品列表頁面"""
        product_urls = []
        
        # 查找產品連結
        product_links = soup.find_all('a', class_='product-item-link')
        if not product_links:
            # 備用選擇器
            product_links = soup.find_all('a', href=re.compile(r'/products/'))
        
        for link in product_links:
            href = link.get('href')
            if href:
                if href.startswith('/'):
                    product_url = f"{self.base_url}{href}"
                else:
                    product_url = href
                product_urls.append(product_url)
        
        return list(set(product_urls))  # 去重
    
    def parse_product_detail(self, soup: BeautifulSoup, product_url: str) -> Optional[ProductInfo]:
        """解析產品詳情頁面"""
        try:
            # 解析產品名稱
            name_elem = soup.find('h1', class_='product-name')
            if not name_elem:
                name_elem = soup.find('h1', class_='page-title')
            
            if not name_elem:
                self.logger.warning(f"無法找到產品名稱: {product_url}")
                return None
            
            name = name_elem.get_text().strip()
            
            # 解析價格
            price_elem = soup.find('span', class_='regular-price')
            if not price_elem:
                price_elem = soup.find('span', class_='price')
            
            if not price_elem:
                self.logger.warning(f"無法找到價格: {product_url}")
                return None
            
            price_text = price_elem.get_text().strip()
            price = self._extract_price(price_text)
            
            # 解析原價（如果有折扣）
            original_price = None
            old_price_elem = soup.find('span', class_='old-price')
            if old_price_elem:
                original_price_text = old_price_elem.get_text().strip()
                original_price = self._extract_price(original_price_text)
            
            # 解析庫存狀態
            availability = "unknown"
            stock_elem = soup.find('div', class_='stock-status')
            if stock_elem:
                stock_text = stock_elem.get_text().strip().lower()
                if 'in stock' in stock_text or 'available' in stock_text:
                    availability = "in_stock"
                elif 'out of stock' in stock_text or 'sold out' in stock_text:
                    availability = "out_of_stock"
            
            # 解析產品圖片
            image_url = None
            img_elem = soup.find('img', class_='product-image-main')
            if img_elem:
                image_url = img_elem.get('src')
                if image_url and image_url.startswith('/'):
                    image_url = f"{self.base_url}{image_url}"
            
            # 解析產品描述
            description = None
            desc_elem = soup.find('div', class_='product-description')
            if desc_elem:
                description = desc_elem.get_text().strip()
            
            # 解析尺寸選項
            size_options = []
            size_selector = soup.find('select', {'name': 'size'})
            if size_selector:
                for option in size_selector.find_all('option'):
                    size_text = option.get_text().strip()
                    if size_text and size_text.lower() not in ['choose', 'select']:
                        size_options.append(size_text)
            
            # 解析顏色選項
            color_options = []
            color_swatches = soup.find_all('div', class_='color-swatch')
            for swatch in color_swatches:
                color_name = swatch.get('data-color') or swatch.get('title')
                if color_name:
                    color_options.append(color_name)
            
            # 確定產品分類
            category = self._determine_category(name, product_url)
            
            return ProductInfo(
                name=name,
                brand="Venum",
                price=price,
                currency="USD",
                original_price=original_price,
                availability=availability,
                image_url=image_url,
                product_url=product_url,
                category=category,
                description=description,
                size_options=size_options,
                color_options=color_options
            )
            
        except Exception as e:
            self.logger.error(f"解析產品詳情失敗 {product_url}: {e}")
            return None
    
    def _extract_price(self, price_text: str) -> float:
        """從價格文本中提取數字"""
        price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
        if price_match:
            return float(price_match.group())
        return 0.0
    
    def _determine_category(self, name: str, url: str) -> str:
        """根據產品名稱和URL確定分類"""
        name_lower = name.lower()
        url_lower = url.lower()
        
        if 'boxing' in name_lower or 'boxing' in url_lower:
            return "boxing_gloves"
        elif 'mma' in name_lower or 'mma' in url_lower:
            return "mma_gloves"
        elif 'shin' in name_lower or 'shin' in url_lower:
            return "shin_guards"
        elif 'head' in name_lower or 'headgear' in url_lower:
            return "headgear"
        elif 'mouth' in name_lower or 'mouthguard' in url_lower:
            return "mouthguards"
        elif 'rash' in name_lower or 'rashguard' in url_lower:
            return "rash_guards"
        elif 'short' in name_lower:
            return "shorts"
        elif 't-shirt' in name_lower or 'tshirt' in name_lower:
            return "t_shirts"
        else:
            return "fighting_gear"