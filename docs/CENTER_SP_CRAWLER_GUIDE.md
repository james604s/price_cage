# Center-SP Crawler Guide

## Overview

The Center-SP crawler is designed to scrape products from https://www.center-sp.co.jp/ec/, a Japanese sports equipment store specializing in boxing, martial arts, and training gear.

## Features

- **Japanese Language Support**: Handles Japanese text parsing and normalization
- **Multi-Category Support**: Boxing, martial arts, training equipment, protective gear, apparel
- **Price Extraction**: Handles Japanese Yen (¥) price formats
- **Specification Parsing**: Extracts product specifications like size, color, material, weight
- **SEO-Friendly**: Respects robots.txt and implements proper rate limiting

## Supported Product Categories

### Boxing Equipment
- Boxing gloves (various weights in oz)
- Punching bags
- Boxing shoes
- Boxing trunks and shorts
- Hand wraps and tape

### Martial Arts Gear
- Karate equipment
- Judo uniforms and belts
- Jujitsu gear
- Taekwondo equipment
- MMA training gear

### Training Equipment
- Fitness gear
- Strength training equipment
- Cardio equipment
- Training accessories

### Protective Gear
- Headgear
- Mouthpieces
- Shin guards
- Chest protectors
- Groin protectors

### Apparel
- Sports clothing
- Training wear
- Athletic shoes
- Accessories

## Usage

### Basic Usage

```bash
# Run Center-SP crawler only
python scripts/run_crawler.py --type center_sp

# Run specific site
python scripts/run_crawler.py --sites center-sp

# Run with async mode
python scripts/run_crawler.py --type center_sp --async
```

### API Usage

```python
from src.crawlers.center_sp_crawler import CenterSPCrawler

# Initialize crawler
crawler = CenterSPCrawler()

# Crawl all products
products = crawler.crawl_all()

# Crawl specific categories
products = crawler.crawl_all(categories=['boxing', 'martial_arts'])

# Async crawling
products = await crawler.crawl_all_async()
```

## Configuration

### Environment Variables

```env
# Crawler settings
CRAWLER_DELAY=2.0  # Delay between requests (seconds)
CRAWLER_TIMEOUT=30  # Request timeout (seconds)
CRAWLER_USER_AGENT="Mozilla/5.0 (compatible; Price Cage Bot)"

# Japanese text handling
JAPANESE_ENCODING=utf-8
PRICE_CURRENCY=JPY
```

### Site-Specific Settings

```python
CENTER_SP_CONFIG = {
    "base_url": "https://www.center-sp.co.jp/ec/",
    "currency": "JPY",
    "language": "ja",
    "selectors": {
        "product_list": ".product-link, a[href*='product']",
        "product_name": "h1, .product-name, .item-name",
        "product_price": ".price, .product-price, .item-price",
        "product_image": ".product-image img, .item-image img",
        "product_description": ".product-description, .item-description"
    },
    "category_mapping": {
        "boxing": ["ボクシング", "boxing", "gloves", "グローブ"],
        "martial_arts": ["格闘技", "martial arts", "karate", "空手"],
        "training": ["トレーニング", "training", "フィットネス"],
        "protective_gear": ["プロテクター", "protective", "protector"],
        "apparel": ["ウェア", "apparel", "clothing", "シューズ"]
    }
}
```

## Data Structure

### Product Information

```python
{
    "name": "ボクシンググローブ 16oz ブラック",
    "brand": "Center-SP",
    "price": 18500.0,
    "currency": "JPY",
    "category": "boxing",
    "description": "プロ仕様のボクシンググローブ。本革製で耐久性抜群。",
    "image_url": "https://www.center-sp.co.jp/ec/images/product123.jpg",
    "product_url": "https://www.center-sp.co.jp/ec/product/123",
    "availability": True,
    "specifications": {
        "size": ["16oz"],
        "colors": ["black"],
        "materials": ["leather"],
        "weight": {"oz": "16"},
        "brand": "Center-SP",
        "origin": "Japan"
    }
}
```

### Parsed Specifications

The crawler extracts and normalizes the following specifications:

- **Size**: Various formats (S/M/L, oz, cm, etc.)
- **Color**: Japanese and English color names
- **Material**: Leather, synthetic, cotton, etc.
- **Weight**: Boxing glove weights in oz/g
- **Brand**: Product brand information
- **Origin**: Country of manufacture

## Japanese Text Processing

### Price Parsing

The crawler handles various Japanese price formats:

- `¥15,800円` → 15800.0
- `15800円(税込)` → 15800.0
- `価格：12,000円` → 12000.0
- `定価 25,000円` → 25000.0

### Size Normalization

- `エス` → `S`
- `エム` → `M`
- `エル` → `L`
- `16オンス` → `16oz`
- `フリーサイズ` → `FREE`

### Color Translation

- `黒` → `black`
- `白` → `white`
- `赤` → `red`
- `青` → `blue`
- `ピンク` → `pink`

## Error Handling

### Common Issues

1. **Page Load Timeout**: Increase `CRAWLER_TIMEOUT` setting
2. **Rate Limiting**: Adjust `CRAWLER_DELAY` setting
3. **Japanese Encoding**: Ensure proper UTF-8 handling
4. **Product Not Found**: Check CSS selectors for updates

### Debug Mode

```bash
# Run with debug logging
LOG_LEVEL=DEBUG python scripts/run_crawler.py --type center_sp
```

## Performance Optimization

### Async Processing

```python
# Async crawling for better performance
products = await crawler.crawl_all_async()
```

### Caching

The crawler implements intelligent caching:

- Product URLs are cached to avoid duplicate requests
- Category pages are cached for 1 hour
- Product data is cached for 30 minutes

### Rate Limiting

Default settings respect the site's server:

- 2 seconds delay between requests
- 30 second timeout per request
- Maximum 10 concurrent requests

## Monitoring

### Metrics

The crawler provides the following metrics:

- **Products scraped**: Total number of products processed
- **Success rate**: Percentage of successful requests
- **Average response time**: Mean request duration
- **Error rate**: Percentage of failed requests

### Logging

```python
# Key log events
logger.info(f"Starting Center-SP crawler")
logger.info(f"Crawling category: {category_url}")
logger.info(f"Extracted: {product.name} - ¥{product.price}")
logger.error(f"Error extracting product: {error}")
```

## Troubleshooting

### Common Problems

1. **Empty Results**
   - Check if site structure has changed
   - Verify CSS selectors are current
   - Ensure proper JavaScript rendering

2. **Price Extraction Fails**
   - Check price format changes
   - Verify currency symbols
   - Update price regex patterns

3. **Japanese Text Issues**
   - Ensure UTF-8 encoding
   - Check font rendering
   - Verify character normalization

### Solutions

```bash
# Test specific product URL
python -c "
from src.crawlers.center_sp_crawler import CenterSPCrawler
crawler = CenterSPCrawler()
product = crawler._extract_product_info('https://www.center-sp.co.jp/ec/product/123')
print(product)
"

# Test parser separately
python -c "
from src.parsers.sports_equipment.center_sp_parser import CenterSPParser
parser = CenterSPParser()
result = parser.parse_product_name('NEW ボクシンググローブ 16oz レッド [BG-001]')
print(result)
"
```

## Updates and Maintenance

### Site Changes

Monitor for:
- CSS selector updates
- URL structure changes
- New product categories
- Price format changes

### Code Updates

Regular maintenance:
- Update Japanese text patterns
- Refresh product category mappings
- Optimize performance settings
- Add new product types

## Integration

### With Other Crawlers

```python
# Use with other crawlers
from src.crawlers.center_sp_crawler import CenterSPCrawler
from src.crawlers.fighting_gear_crawler import FightingGearCrawler

crawlers = [
    CenterSPCrawler(),
    FightingGearCrawler()
]

all_products = []
for crawler in crawlers:
    products = crawler.crawl_all()
    all_products.extend(products)
```

### With Analytics

```python
# Analyze Center-SP specific data
from src.analytics.price_analyzer import PriceAnalyzer

analyzer = PriceAnalyzer()
center_sp_products = analyzer.filter_by_brand("Center-SP")
price_trends = analyzer.analyze_price_trends(center_sp_products)
```

## Legal Considerations

- Respects robots.txt directives
- Implements proper rate limiting
- Does not overload the server
- For research and personal use only
- Check site terms of service before deployment

## Future Enhancements

- Machine learning for better product categorization
- Real-time price alerts
- Inventory tracking
- Multi-language support expansion
- Mobile app integration