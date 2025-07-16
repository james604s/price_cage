#!/usr/bin/env python3
"""
Test script for Center-SP crawler
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.crawlers.center_sp_crawler import CenterSPCrawler
from src.parsers.sports_equipment.center_sp_parser import CenterSPParser


def test_center_sp_crawler():
    """Test Center-SP crawler functionality"""
    print("Testing Center-SP Crawler...")
    
    # Initialize crawler
    crawler = CenterSPCrawler()
    
    # Test basic functionality
    print(f"Base URL: {crawler.base_url}")
    print(f"Brand: {crawler.brand}")
    
    # Test category normalization
    test_categories = [
        "ボクシング", "boxing", "グローブ", "martial arts",
        "トレーニング", "プロテクター", "ウェア"
    ]
    
    print("\nTesting category normalization:")
    for category in test_categories:
        normalized = crawler._normalize_category(category)
        print(f"  {category} -> {normalized}")
    
    # Test price extraction
    test_prices = [
        "¥15,800円", "15800円(税込)", "価格：12,000円",
        "定価 25,000円", "¥8,500"
    ]
    
    print("\nTesting price extraction:")
    for price in test_prices:
        extracted = crawler._extract_price(price)
        print(f"  {price} -> {extracted}")
    
    # Test URL validation
    test_urls = [
        "https://www.center-sp.co.jp/ec/product/123",
        "https://www.center-sp.co.jp/ec/item/456",
        "https://www.center-sp.co.jp/ec/category/boxing",
        "https://www.center-sp.co.jp/ec/detail.php?id=789"
    ]
    
    print("\nTesting URL validation:")
    for url in test_urls:
        is_product = crawler._is_product_url(url)
        is_category = crawler._is_category_url(url)
        print(f"  {url} -> Product: {is_product}, Category: {is_category}")


def test_center_sp_parser():
    """Test Center-SP parser functionality"""
    print("\n" + "="*50)
    print("Testing Center-SP Parser...")
    
    # Initialize parser
    parser = CenterSPParser()
    
    # Test product data
    test_product = {
        'name': 'NEW ボクシンググローブ 16oz レッド [BG-001]',
        'price': '¥15,800円(税込)',
        'description': '''
        プロ仕様のボクシンググローブ。本革製で耐久性抜群。
        サイズ：16オンス、カラー：レッド/ブラック
        素材：レザー、重量：16oz
        ''',
        'product_url': 'https://www.center-sp.co.jp/ec/product/boxing/bg-001',
        'specifications': {
            'サイズ': '16オンス',
            'カラー': 'レッド、ブラック',
            '素材': 'レザー',
            '重量': '16oz',
            'ブランド': 'Center-SP',
            '原産国': '日本'
        }
    }
    
    print("Testing product parsing...")
    result = parser.normalize_product_data(test_product)
    
    print("\nParsed Product Data:")
    for key, value in result.items():
        print(f"  {key}: {value}")
    
    # Test individual parsing functions
    print("\nTesting individual parsing functions:")
    
    # Test name parsing
    test_names = [
        "NEW ボクシンググローブ 16oz レッド [BG-001]",
        "SALE 格闘技プロテクター (在庫あり)",
        "限定 トレーニングウェア XL"
    ]
    
    print("\nName parsing:")
    for name in test_names:
        parsed = parser.parse_product_name(name)
        print(f"  {name} -> {parsed}")
    
    # Test size extraction
    test_size_texts = [
        "サイズ：S、M、L、XL",
        "16オンス グローブ",
        "フリーサイズ ウェア",
        "28cmシューズ"
    ]
    
    print("\nSize extraction:")
    for text in test_size_texts:
        sizes = parser.extract_size_info(text)
        print(f"  {text} -> {sizes}")
    
    # Test color extraction
    test_color_texts = [
        "カラー：レッド、ブラック",
        "色：青、白",
        "黒色のグローブ",
        "ピンクのウェア"
    ]
    
    print("\nColor extraction:")
    for text in test_color_texts:
        colors = parser.extract_color_info(text)
        print(f"  {text} -> {colors}")


def test_integration():
    """Test integration between crawler and parser"""
    print("\n" + "="*50)
    print("Testing Integration...")
    
    # Create sample product info (as if from crawler)
    from src.crawlers.base_crawler import ProductInfo
    
    product_info = ProductInfo(
        name="ボクシンググローブ 14oz ブラック",
        brand="Center-SP",
        price=18500.0,
        currency="JPY",
        category="boxing",
        description="プロ仕様のボクシンググローブ。レザー製で耐久性に優れています。",
        image_url="https://www.center-sp.co.jp/ec/images/bg-001.jpg",
        product_url="https://www.center-sp.co.jp/ec/product/bg-001",
        availability=True,
        specifications={
            'サイズ': '14オンス',
            'カラー': 'ブラック',
            '素材': 'レザー'
        }
    )
    
    # Convert to dict for parser
    product_dict = {
        'name': product_info.name,
        'price': f"¥{product_info.price}",
        'description': product_info.description,
        'product_url': product_info.product_url,
        'specifications': product_info.specifications
    }
    
    # Parse with parser
    parser = CenterSPParser()
    parsed_result = parser.normalize_product_data(product_dict)
    
    print("Integration test result:")
    for key, value in parsed_result.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    try:
        test_center_sp_crawler()
        test_center_sp_parser()
        test_integration()
        print("\n" + "="*50)
        print("All tests completed successfully!")
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()