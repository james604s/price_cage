# Price Cage User Manual

## Table of Contents
1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Quick Start](#quick-start)
5. [API Usage](#api-usage)
6. [Web Scraping](#web-scraping)
7. [Data Analysis](#data-analysis)
8. [Monitoring](#monitoring)
9. [Troubleshooting](#troubleshooting)
10. [Advanced Usage](#advanced-usage)

## Introduction

Price Cage is a comprehensive multi-site web scraping system designed to track prices for fighting gear and streetwear products. It provides real-time price monitoring, historical data analysis, and visualization capabilities.

### Key Features
- **Multi-site scraping**: Supports multiple e-commerce websites
- **Real-time monitoring**: Track price changes as they happen
- **Historical analysis**: Analyze price trends over time
- **REST API**: Complete FastAPI backend service
- **Data visualization**: Interactive charts and dashboards
- **Scalable architecture**: Docker-based deployment

## Installation

### Prerequisites
- Python 3.11+
- Docker and Docker Compose
- PostgreSQL
- Redis

### Method 1: Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd price_cage
   ```

2. **Setup environment variables**
   ```bash
   cp .env.example .env
   # Edit .env file with your configuration
   ```

3. **Start services**
   ```bash
   docker-compose up -d
   ```

4. **Initialize database**
   ```bash
   docker-compose exec api python scripts/setup_database.py --action init
   ```

### Method 2: Local Development

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup database**
   ```bash
   # Make sure PostgreSQL is running
   python scripts/setup_database.py --action init
   ```

3. **Start the API server**
   ```bash
   uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Configuration

### Environment Variables

Create a `.env` file from `.env.example` and configure:

```env
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/price_cage

# API Settings
API_HOST=0.0.0.0
API_PORT=8000

# Crawler Settings
CRAWLER_DELAY=1.0
CRAWLER_TIMEOUT=30

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Security
SECRET_KEY=your-secret-key-here
```

### Site Configuration

Configure target websites in `src/config/settings.py`:

```python
FIGHTING_GEAR_SITES = {
    "venum": {
        "base_url": "https://www.venum.com",
        "categories": ["/boxing-gloves", "/mma-gloves"],
        "selectors": {
            "product_list": ".product-item",
            "product_name": ".product-name",
            "product_price": ".price"
        }
    }
}

SPORTS_EQUIPMENT_SITES = {
    "center_sp": {
        "base_url": "https://www.center-sp.co.jp/ec/",
        "categories": ["boxing", "martial_arts", "training"],
        "selectors": {
            "product_list": ".product-link",
            "product_name": "h1, .product-name",
            "product_price": ".price, .product-price"
        },
        "currency": "JPY",
        "language": "ja"
    }
}
```

## Quick Start

### 1. Health Check
```bash
curl http://localhost:8000/health
```

### 2. Run Your First Scrape
```bash
# Scrape all sites
python scripts/run_crawler.py --type all

# Scrape specific sites
python scripts/run_crawler.py --sites venum supreme center-sp

# Scrape specific types
python scripts/run_crawler.py --type center_sp

# Use async mode for faster scraping
python scripts/run_crawler.py --type all --async
```

### 3. Access API Documentation
Open http://localhost:8000/docs in your browser

### 4. Query Products
```bash
# Get all products
curl http://localhost:8000/api/v1/products/

# Filter by category
curl "http://localhost:8000/api/v1/products/?category=boxing_gloves"

# Filter by price range
curl "http://localhost:8000/api/v1/products/?min_price=50&max_price=200"
```

## API Usage

### Authentication
Currently, the API doesn't require authentication for basic operations. For production use, implement proper authentication.

### Endpoints

#### Products
- `GET /api/v1/products/` - List all products
- `GET /api/v1/products/{id}` - Get specific product
- `GET /api/v1/products/{id}/price-history` - Get price history
- `POST /api/v1/products/` - Create new product
- `PUT /api/v1/products/{id}` - Update product
- `DELETE /api/v1/products/{id}` - Delete product

#### Brands
- `GET /api/v1/brands/` - List all brands
- `GET /api/v1/brands/{id}` - Get specific brand
- `POST /api/v1/brands/` - Create new brand

#### Analytics
- `GET /api/v1/analytics/price-trends` - Get price trend analysis
- `GET /api/v1/analytics/brand-performance` - Get brand performance metrics
- `GET /api/v1/analytics/category-stats` - Get category statistics

### Request Examples

#### Get Products with Filters
```bash
curl -X GET "http://localhost:8000/api/v1/products/" \
  -H "Content-Type: application/json" \
  -G \
  -d "category=boxing_gloves" \
  -d "brand=venum" \
  -d "min_price=50" \
  -d "max_price=200" \
  -d "limit=10"
```

#### Create New Product
```bash
curl -X POST "http://localhost:8000/api/v1/products/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Boxing Gloves Pro",
    "brand_id": "brand-uuid-here",
    "website_id": "website-uuid-here",
    "category": "boxing_gloves",
    "current_price": 89.99,
    "currency": "USD",
    "source_url": "https://example.com/product"
  }'
```

#### Get Price History
```bash
curl -X GET "http://localhost:8000/api/v1/products/{product_id}/price-history" \
  -H "Content-Type: application/json" \
  -G \
  -d "days=30"
```

## Web Scraping

### Basic Scraping Commands

#### Run All Crawlers
```bash
# Synchronous mode
python scripts/run_crawler.py --type all

# Asynchronous mode (faster)
python scripts/run_crawler.py --type all --async
```

#### Run Specific Types
```bash
# Fighting gear only
python scripts/run_crawler.py --type fighting_gear

# Streetwear only
python scripts/run_crawler.py --type streetwear
```

#### Run Specific Sites
```bash
# Single site
python scripts/run_crawler.py --sites venum

# Multiple sites
python scripts/run_crawler.py --sites venum supreme bape
```

### Scheduled Scraping
```bash
# Run in scheduler mode (every hour)
python scripts/run_crawler.py --schedule
```

### Adding New Sites

1. **Create a new parser** in `src/parsers/[category]/[site]_parser.py`:
   ```python
   class NewSiteParser(BaseParser):
       def __init__(self):
           super().__init__(
               site_name="newsite",
               base_url="https://newsite.com",
               category="fighting_gear"
           )
       
       def get_category_urls(self) -> List[str]:
           return ["https://newsite.com/category1"]
       
       def parse_product_list(self, soup: BeautifulSoup) -> List[str]:
           # Implementation here
           pass
       
       def parse_product_detail(self, soup: BeautifulSoup, product_url: str) -> Optional[ProductInfo]:
           # Implementation here
           pass
   ```

2. **Add site configuration** in `src/config/settings.py`

3. **Update the crawler** to include the new parser

## Data Analysis

### Price Trend Analysis
```python
from src.analytics.price_analyzer import PriceAnalyzer
from src.database.connection import get_db

analyzer = PriceAnalyzer()

# Analyze price trends for a specific product
with get_db() as db:
    trends = analyzer.analyze_price_trends(
        product_id="product-uuid",
        days=30,
        db=db
    )
    print(trends)
```

### Generate Visualizations
```python
from src.analytics.visualizer import DataVisualizer

visualizer = DataVisualizer()

# Create price trend chart
price_data = [
    {"recorded_at": "2024-01-01", "price": 89.99},
    {"recorded_at": "2024-01-02", "price": 85.99},
    # ... more data
]

chart_html = visualizer.create_price_trend_chart(
    price_data,
    title="Product Price Trend",
    interactive=True
)
```

### API Analytics Endpoints
```bash
# Get price trends
curl "http://localhost:8000/api/v1/analytics/price-trends?product_id=uuid&days=30"

# Get brand performance
curl "http://localhost:8000/api/v1/analytics/brand-performance?brand=venum"

# Get category statistics
curl "http://localhost:8000/api/v1/analytics/category-stats?category=boxing_gloves"
```

## Monitoring

### Service Health
```bash
# Check API health
curl http://localhost:8000/health

# Check service status
docker-compose ps
```

### Logs
```bash
# View API logs
docker-compose logs -f api

# View crawler logs
docker-compose logs -f crawler

# View all logs
docker-compose logs -f
```

### Metrics (with Prometheus)
- Access Prometheus: http://localhost:9090
- Access Grafana: http://localhost:3000 (admin/admin)

### Database Monitoring
```bash
# Check database connections
docker-compose exec postgres psql -U price_cage_user -d price_cage -c "SELECT * FROM pg_stat_activity;"

# Check table sizes
docker-compose exec postgres psql -U price_cage_user -d price_cage -c "SELECT schemaname,tablename,attname,avg_width,n_distinct,correlation FROM pg_stats;"
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Issues
```bash
# Check database status
docker-compose ps postgres

# Reset database
python scripts/setup_database.py --action reset --force

# Check database logs
docker-compose logs postgres
```

#### 2. Scraping Issues
```bash
# Check if site is accessible
curl -I https://target-site.com

# Increase delay between requests
# Edit .env: CRAWLER_DELAY=2.0

# Check crawler logs
docker-compose logs crawler
```

#### 3. Memory Issues
```bash
# Check memory usage
docker stats

# Increase memory limits in docker-compose.yml
services:
  api:
    deploy:
      resources:
        limits:
          memory: 1G
```

#### 4. API Not Responding
```bash
# Check API status
curl http://localhost:8000/health

# Restart API service
docker-compose restart api

# Check API logs
docker-compose logs api
```

### Debug Mode
```bash
# Run with debug logging
export LOG_LEVEL=DEBUG
python scripts/run_crawler.py --type all

# Run API in debug mode
export DEBUG=true
uvicorn src.api.main:app --reload --log-level debug
```

## Advanced Usage

### Custom Scraping Logic

#### Implement Custom Parser
```python
class CustomParser(BaseParser):
    def __init__(self):
        super().__init__(
            site_name="custom_site",
            base_url="https://custom-site.com",
            category="custom_category"
        )
    
    def get_category_urls(self) -> List[str]:
        return ["https://custom-site.com/products"]
    
    def parse_product_list(self, soup: BeautifulSoup) -> List[str]:
        links = soup.find_all('a', class_='product-link')
        return [self.normalize_url(link.get('href')) for link in links]
    
    def parse_product_detail(self, soup: BeautifulSoup, product_url: str) -> Optional[ProductInfo]:
        name = soup.find('h1', class_='product-title').text.strip()
        price_text = soup.find('span', class_='price').text.strip()
        price = self.extract_numeric_value(price_text)
        
        return ProductInfo(
            name=name,
            brand="Custom Brand",
            price=price,
            currency="USD",
            product_url=product_url,
            category="custom_category"
        )
```

### Batch Processing
```python
from src.storage.data_processor import DataProcessor

processor = DataProcessor()

# Process products in batches
products = [product1, product2, product3]  # List of ProductInfo objects
result = processor.process_products(products)
print(f"Processed: {result['processed']}, Errors: {result['errors']}")
```

### Custom Analytics
```python
from src.analytics.price_analyzer import PriceAnalyzer

class CustomAnalyzer(PriceAnalyzer):
    def custom_analysis(self, product_id: str, db: Session) -> dict:
        # Custom analysis logic
        pass
```

### API Extensions
```python
# Add custom endpoints in src/api/routers/custom.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database.connection import get_db

router = APIRouter()

@router.get("/custom-endpoint")
def custom_endpoint(db: Session = Depends(get_db)):
    # Custom logic
    return {"message": "Custom endpoint"}
```

### Performance Optimization

#### Database Optimization
```sql
-- Add indexes for better query performance
CREATE INDEX idx_products_category_price ON products(category, current_price);
CREATE INDEX idx_price_history_product_date ON price_history(product_id, recorded_at);
```

#### Caching
```python
# Use Redis for caching
import redis
from src.config.settings import settings

redis_client = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    db=settings.redis_db
)

# Cache product data
redis_client.setex(f"product:{product_id}", 3600, product_json)
```

#### Async Processing
```python
# Use async for better performance
async def process_products_async(products: List[ProductInfo]):
    tasks = [process_single_product(product) for product in products]
    await asyncio.gather(*tasks)
```

### Deployment

#### Production Deployment
```bash
# Use production docker-compose
docker-compose -f docker-compose.prod.yml up -d

# Scale services
docker-compose up -d --scale api=3 --scale crawler=2
```

#### Kubernetes Deployment
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: price-cage-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: price-cage-api
  template:
    metadata:
      labels:
        app: price-cage-api
    spec:
      containers:
      - name: api
        image: price-cage:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: price-cage-secrets
              key: database-url
```

### Backup and Recovery

#### Database Backup
```bash
# Create backup
docker-compose exec postgres pg_dump -U price_cage_user price_cage > backup.sql

# Restore backup
docker-compose exec -T postgres psql -U price_cage_user price_cage < backup.sql
```

#### Data Export
```bash
# Export products to CSV
python scripts/data_export.py --format csv --output products.csv

# Export price history
python scripts/data_export.py --format json --table price_history --output price_history.json
```

---

For more information, please refer to the [API documentation](http://localhost:8000/docs) or contact the development team.