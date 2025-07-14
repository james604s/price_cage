"""
Supreme 潮流衣物網站解析器
"""
import re
from typing import List, Optional
from bs4 import BeautifulSoup

from ..base_parser import BaseParser
from ...crawlers.base_crawler import ProductInfo


class SupremeParser(BaseParser):
    """Supreme 網站解析器"""
    
    def __init__(self):
        super().__init__(
            site_name="supreme",
            base_url="https://www.supremenewyork.com",
            category="streetwear"
        )
    
    def get_category_urls(self) -> List[str]:
        """獲取分類頁面 URL"""
        return [
            f"{self.base_url}/shop/all/jackets",
            f"{self.base_url}/shop/all/shirts",
            f"{self.base_url}/shop/all/t-shirts",
            f"{self.base_url}/shop/all/sweatshirts",
            f"{self.base_url}/shop/all/tops-sweaters",
            f"{self.base_url}/shop/all/pants",
            f"{self.base_url}/shop/all/shorts",
            f"{self.base_url}/shop/all/hats",
            f"{self.base_url}/shop/all/bags",
            f"{self.base_url}/shop/all/accessories"
        ]
    
    def parse_product_list(self, soup: BeautifulSoup) -> List[str]:
        """解析產品列表頁面"""
        product_urls = []
        
        # Supreme 使用特殊的產品連結結構
        product_links = soup.find_all('a', href=re.compile(r'/shop/'))
        
        for link in product_links:
            href = link.get('href')
            if href and '/shop/' in href:
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
            name_elem = soup.find('h1', {'id': 'name'})
            if not name_elem:
                name_elem = soup.find('h1', class_='product-name')
            
            if not name_elem:
                self.logger.warning(f"無法找到產品名稱: {product_url}")
                return None
            
            name = name_elem.get_text().strip()
            
            # 解析價格
            price_elem = soup.find('span', {'id': 'price'})
            if not price_elem:
                price_elem = soup.find('span', class_='price')
            
            if not price_elem:
                self.logger.warning(f"無法找到價格: {product_url}")
                return None
            
            price_text = price_elem.get_text().strip()
            price = self._extract_price(price_text)
            
            # 解析庫存狀態
            availability = "unknown"
            # Supreme 的庫存狀態通常在 JavaScript 中，需要特殊處理
            sold_out_elem = soup.find('span', class_='sold-out')
            if sold_out_elem:
                availability = "out_of_stock"
            else:
                # 檢查是否有尺寸選項
                size_select = soup.find('select', {'name': 'size'})
                if size_select:
                    available_options = size_select.find_all('option', {'disabled': False})
                    if available_options:
                        availability = "in_stock"
                    else:
                        availability = "out_of_stock"
            
            # 解析產品圖片
            image_url = None
            img_elem = soup.find('img', {'id': 'img'})
            if img_elem:
                image_url = img_elem.get('src')
                if image_url and image_url.startswith('/'):
                    image_url = f"{self.base_url}{image_url}"
            
            # 解析產品描述
            description = None
            desc_elem = soup.find('div', {'id': 'description'})
            if desc_elem:
                description = desc_elem.get_text().strip()
            
            # 解析尺寸選項
            size_options = []
            size_select = soup.find('select', {'name': 'size'})
            if size_select:
                for option in size_select.find_all('option'):
                    size_text = option.get_text().strip()
                    value = option.get('value')
                    if size_text and value and size_text.lower() not in ['choose', 'select']:
                        size_options.append(size_text)
            
            # 解析顏色選項
            color_options = []
            color_select = soup.find('select', {'name': 'color'})
            if color_select:
                for option in color_select.find_all('option'):
                    color_text = option.get_text().strip()
                    value = option.get('value')
                    if color_text and value and color_text.lower() not in ['choose', 'select']:
                        color_options.append(color_text)
            
            # 確定產品分類
            category = self._determine_category(name, product_url)
            
            return ProductInfo(
                name=name,
                brand="Supreme",
                price=price,
                currency="USD",
                original_price=None,  # Supreme 很少有折扣
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
        # 移除貨幣符號和逗號
        price_clean = re.sub(r'[^\d.]', '', price_text)
        try:
            return float(price_clean)
        except ValueError:
            return 0.0
    
    def _determine_category(self, name: str, url: str) -> str:
        """根據產品名稱和URL確定分類"""
        name_lower = name.lower()
        url_lower = url.lower()
        
        if 'jacket' in name_lower or 'jacket' in url_lower:
            return "jackets"
        elif 'shirt' in name_lower and 't-shirt' not in name_lower:
            return "shirts"
        elif 't-shirt' in name_lower or 'tee' in name_lower:
            return "t_shirts"
        elif 'sweatshirt' in name_lower or 'hoodie' in name_lower:
            return "hoodies"
        elif 'pant' in name_lower or 'jean' in name_lower:
            return "pants"
        elif 'short' in name_lower:
            return "shorts"
        elif 'hat' in name_lower or 'cap' in name_lower or 'beanie' in name_lower:
            return "hats"
        elif 'bag' in name_lower or 'backpack' in name_lower:
            return "bags"
        else:
            return "accessories"