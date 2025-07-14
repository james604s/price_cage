"""
Base crawler class
Provides common crawler functionality and interface
"""
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

import aiohttp
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from fake_useragent import UserAgent

from ..utils.logger import get_logger
from ..config.settings import Settings


@dataclass
class ProductInfo:
    """Product information data class"""
    name: str
    brand: str
    price: float
    currency: str
    original_price: Optional[float] = None
    availability: str = "unknown"
    image_url: Optional[str] = None
    product_url: str = ""
    category: str = ""
    description: Optional[str] = None
    size_options: List[str] = None
    color_options: List[str] = None
    scraped_at: datetime = None
    
    def __post_init__(self):
        if self.scraped_at is None:
            self.scraped_at = datetime.now()
        if self.size_options is None:
            self.size_options = []
        if self.color_options is None:
            self.color_options = []


class BaseCrawler(ABC):
    """Base crawler abstract class"""
    
    def __init__(self, 
                 site_name: str,
                 base_url: str,
                 headers: Optional[Dict[str, str]] = None,
                 use_selenium: bool = False,
                 request_delay: float = 1.0):
        self.site_name = site_name
        self.base_url = base_url
        self.use_selenium = use_selenium
        self.request_delay = request_delay
        self.logger = get_logger(f"crawler.{site_name}")
        self.settings = Settings()
        
        # Setup request headers
        self.ua = UserAgent()
        self.headers = headers or {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        # Initialize session
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Selenium setup
        if self.use_selenium:
            self.driver = self._setup_selenium()
        else:
            self.driver = None
    
    def _setup_selenium(self) -> webdriver.Chrome:
        """Setup Selenium WebDriver"""
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument(f'--user-agent={self.ua.random}')
        
        try:
            driver = webdriver.Chrome(options=options)
            return driver
        except Exception as e:
            self.logger.error(f"Failed to setup Selenium: {e}")
            raise
    
    def get_page(self, url: str, timeout: int = 30) -> Optional[BeautifulSoup]:
        """Get webpage content"""
        try:
            if self.use_selenium:
                return self._get_page_selenium(url, timeout)
            else:
                return self._get_page_requests(url, timeout)
        except Exception as e:
            self.logger.error(f"Failed to get page {url}: {e}")
            return None
    
    def _get_page_requests(self, url: str, timeout: int) -> Optional[BeautifulSoup]:
        """Get webpage using requests"""
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            return soup
        except Exception as e:
            self.logger.error(f"Failed to get page with requests {url}: {e}")
            return None
    
    def _get_page_selenium(self, url: str, timeout: int) -> Optional[BeautifulSoup]:
        """Get webpage using Selenium"""
        try:
            self.driver.get(url)
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            return soup
        except Exception as e:
            self.logger.error(f"Failed to get page with Selenium {url}: {e}")
            return None
    
    async def get_page_async(self, url: str, timeout: int = 30) -> Optional[BeautifulSoup]:
        """異步取得網頁內容"""
        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.get(url, timeout=timeout) as response:
                    if response.status == 200:
                        html = await response.text()
                        return BeautifulSoup(html, 'html.parser')
                    else:
                        self.logger.error(f"HTTP 錯誤 {response.status} for {url}")
                        return None
        except Exception as e:
            self.logger.error(f"異步取得頁面失敗 {url}: {e}")
            return None
    
    @abstractmethod
    def parse_product_list(self, soup: BeautifulSoup) -> List[str]:
        """解析產品列表頁面，返回產品URL列表"""
        pass
    
    @abstractmethod
    def parse_product_detail(self, soup: BeautifulSoup, product_url: str) -> Optional[ProductInfo]:
        """解析產品詳情頁面"""
        pass
    
    @abstractmethod
    def get_category_urls(self) -> List[str]:
        """取得分類頁面URL列表"""
        pass
    
    def crawl_category(self, category_url: str) -> List[ProductInfo]:
        """爬取分類頁面的所有產品"""
        products = []
        
        # 取得分類頁面
        soup = self.get_page(category_url)
        if not soup:
            return products
        
        # 解析產品URL列表
        product_urls = self.parse_product_list(soup)
        self.logger.info(f"在 {category_url} 找到 {len(product_urls)} 個產品")
        
        # 爬取每個產品詳情
        for product_url in product_urls:
            try:
                # 延遲請求避免被封鎖
                asyncio.sleep(self.request_delay)
                
                product_soup = self.get_page(product_url)
                if product_soup:
                    product = self.parse_product_detail(product_soup, product_url)
                    if product:
                        products.append(product)
                        self.logger.info(f"成功爬取產品: {product.name}")
                    else:
                        self.logger.warning(f"無法解析產品: {product_url}")
                else:
                    self.logger.warning(f"無法取得產品頁面: {product_url}")
                    
            except Exception as e:
                self.logger.error(f"爬取產品失敗 {product_url}: {e}")
                continue
        
        return products
    
    async def crawl_category_async(self, category_url: str) -> List[ProductInfo]:
        """異步爬取分類頁面的所有產品"""
        products = []
        
        # 異步取得分類頁面
        soup = await self.get_page_async(category_url)
        if not soup:
            return products
        
        # 解析產品URL列表
        product_urls = self.parse_product_list(soup)
        self.logger.info(f"在 {category_url} 找到 {len(product_urls)} 個產品")
        
        # 異步爬取產品詳情
        tasks = []
        for product_url in product_urls:
            task = self._crawl_product_async(product_url)
            tasks.append(task)
        
        # 等待所有任務完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 處理結果
        for result in results:
            if isinstance(result, ProductInfo):
                products.append(result)
                self.logger.info(f"成功爬取產品: {result.name}")
            elif isinstance(result, Exception):
                self.logger.error(f"爬取產品失敗: {result}")
        
        return products
    
    async def _crawl_product_async(self, product_url: str) -> Optional[ProductInfo]:
        """異步爬取單個產品"""
        try:
            # 延遲請求
            await asyncio.sleep(self.request_delay)
            
            soup = await self.get_page_async(product_url)
            if soup:
                return self.parse_product_detail(soup, product_url)
        except Exception as e:
            self.logger.error(f"異步爬取產品失敗 {product_url}: {e}")
        
        return None
    
    def crawl_all(self) -> List[ProductInfo]:
        """爬取所有分類的產品"""
        all_products = []
        
        category_urls = self.get_category_urls()
        self.logger.info(f"開始爬取 {len(category_urls)} 個分類")
        
        for category_url in category_urls:
            try:
                products = self.crawl_category(category_url)
                all_products.extend(products)
                self.logger.info(f"分類 {category_url} 爬取完成，共 {len(products)} 個產品")
            except Exception as e:
                self.logger.error(f"爬取分類失敗 {category_url}: {e}")
        
        self.logger.info(f"爬取完成，共 {len(all_products)} 個產品")
        return all_products
    
    def __del__(self):
        """清理資源"""
        if hasattr(self, 'driver') and self.driver:
            try:
                self.driver.quit()
            except:
                pass
        
        if hasattr(self, 'session'):
            try:
                self.session.close()
            except:
                pass