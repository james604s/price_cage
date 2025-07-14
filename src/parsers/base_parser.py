"""
基礎解析器抽象類別
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from bs4 import BeautifulSoup

from ..utils.logger import get_logger
from ..crawlers.base_crawler import ProductInfo


class BaseParser(ABC):
    """基礎解析器抽象類別"""
    
    def __init__(self, site_name: str, base_url: str, category: str):
        self.site_name = site_name
        self.base_url = base_url
        self.category = category
        self.logger = get_logger(f"parser.{site_name}")
    
    @abstractmethod
    def get_category_urls(self) -> List[str]:
        """獲取分類頁面URL列表"""
        pass
    
    @abstractmethod
    def parse_product_list(self, soup: BeautifulSoup) -> List[str]:
        """解析產品列表頁面，返回產品URL列表"""
        pass
    
    @abstractmethod
    def parse_product_detail(self, soup: BeautifulSoup, product_url: str) -> Optional[ProductInfo]:
        """解析產品詳情頁面"""
        pass
    
    def clean_text(self, text: str) -> str:
        """清理文本"""
        if not text:
            return ""
        return text.strip().replace('\n', ' ').replace('\t', ' ')
    
    def extract_numeric_value(self, text: str) -> float:
        """從文本中提取數值"""
        import re
        if not text:
            return 0.0
        
        # 移除非數字字符，保留小數點
        numeric_text = re.sub(r'[^\d.]', '', text)
        try:
            return float(numeric_text)
        except ValueError:
            return 0.0
    
    def normalize_url(self, url: str) -> str:
        """標準化URL"""
        if not url:
            return ""
        
        if url.startswith('//'):
            return f"https:{url}"
        elif url.startswith('/'):
            return f"{self.base_url}{url}"
        elif not url.startswith('http'):
            return f"{self.base_url}/{url}"
        else:
            return url