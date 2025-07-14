# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Price Cage is a multi-website crawler system specifically designed for scraping price information of fighting gear and streetwear products. The system includes data processing, API services, data analysis, and visualization features.

## Core Commands

### Development Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env file with correct configuration values

# Initialize database
python scripts/setup_database.py --action init

# Start development server
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

### Crawler Operations
```bash
# Run all crawlers
python scripts/run_crawler.py --type all

# Run specific type crawlers
python scripts/run_crawler.py --type fighting_gear
python scripts/run_crawler.py --type streetwear

# Run specific site crawlers
python scripts/run_crawler.py --sites venum supreme

# Use async mode
python scripts/run_crawler.py --type all --async

# Scheduler mode (continuous running)
python scripts/run_crawler.py --schedule
```

### Database Management
```bash
# Initialize database
python scripts/setup_database.py --action init

# Reset database
python scripts/setup_database.py --action reset --force
```

### Docker 操作
```bash
# 構建和啟動服務
docker-compose up -d

# 查看服務狀態
docker-compose ps

# 查看日誌
docker-compose logs -f api

# 停止服務
docker-compose down
```

### 測試
```bash
# 運行所有測試
pytest tests/

# 運行特定測試
pytest tests/test_crawlers/

# 生成測試覆蓋率報告
pytest --cov=src tests/
```

## 專案架構

### 核心模組結構
- `src/crawlers/` - 爬蟲核心模組，包含基礎爬蟲類別和特定網站爬蟲
- `src/parsers/` - 網站解析器，負責解析不同網站的HTML結構
- `src/database/` - 資料庫模組，包含ORM模型、連接管理和遷移
- `src/api/` - FastAPI後端服務，提供RESTful API接口
- `src/analytics/` - 數據分析模組，包含價格分析和視覺化工具
- `src/storage/` - 資料存儲處理模組
- `src/utils/` - 工具函數和配置管理

### 資料庫設計
主要資料表：
- `brands` - 品牌資訊
- `websites` - 網站配置
- `products` - 產品資訊
- `price_history` - 價格歷史記錄
- `crawl_logs` - 爬蟲執行日誌
- `product_analytics` - 產品分析數據

### 爬蟲架構
- **BaseCrawler** - 基礎爬蟲抽象類別，提供通用功能
- **FightingGearCrawler** - 格鬥用品專用爬蟲
- **StreetwearCrawler** - 潮流衣物專用爬蟲
- **BaseParser** - 基礎解析器抽象類別
- 各網站特定解析器（VenumParser, SupremeParser等）

### API 設計
RESTful API接口：
- `/api/v1/products/` - 產品管理
- `/api/v1/brands/` - 品牌管理
- `/api/v1/analytics/` - 數據分析
- `/health` - 健康檢查
- `/docs` - API文檔

## 開發流程

### 添加新網站爬蟲
1. 在 `src/parsers/` 對應分類目錄下創建新的解析器
2. 繼承 `BaseParser` 並實現必要方法
3. 在 `src/config/settings.py` 中添加網站配置
4. 更新對應的爬蟲類別以支援新網站
5. 在資料庫中添加品牌和網站記錄

### 添加新的數據分析功能
1. 在 `src/analytics/` 中創建新的分析模組
2. 實現分析邏輯和視覺化功能
3. 在 `src/api/routers/analytics.py` 中添加API端點
4. 更新前端儀表板以顯示新的分析結果

### 資料庫遷移
1. 修改 `src/database/models.py` 中的模型
2. 生成遷移腳本（如果使用Alembic）
3. 執行遷移以更新資料庫結構

## 配置管理

### 環境變數
主要配置在 `.env` 文件中：
- `DATABASE_URL` - PostgreSQL資料庫連接URL
- `REDIS_HOST` - Redis服務器地址
- `CRAWLER_DELAY` - 爬蟲請求間隔
- `LOG_LEVEL` - 日誌等級

### 網站配置
在 `src/config/settings.py` 的 `CrawlerConfig` 類別中：
- `FIGHTING_GEAR_SITES` - 格鬥用品網站配置
- `STREETWEAR_SITES` - 潮流衣物網站配置

## 部署

### 開發環境
使用 `uvicorn` 運行FastAPI應用程式
```bash
uvicorn src.api.main:app --reload
```

### 生產環境
使用 Docker Compose 進行容器化部署
```bash
docker-compose up -d
```

包含以下服務：
- API服務 (FastAPI)
- 資料庫 (PostgreSQL)
- 快取 (Redis)
- 任務隊列 (Celery)
- 監控 (Prometheus + Grafana)

## 監控和日誌

### 日誌系統
使用結構化日誌記錄：
- 爬蟲執行日誌
- API請求日誌
- 錯誤和異常日誌

### 監控指標
- 爬蟲執行狀態和統計
- API響應時間和錯誤率
- 資料庫連接和查詢性能
- 系統資源使用情況

## 注意事項

### 爬蟲倫理
- 遵守robots.txt規則
- 設置適當的請求間隔
- 避免對目標網站造成過大負擔
- 只爬取公開可見的資訊

### 資料處理
- 定期清理過期的價格歷史數據
- 實施資料驗證和清洗
- 處理重複和異常資料

### 擴展性
系統設計支援：
- 水平擴展（多個爬蟲實例）
- 新網站和產品類別的添加
- 分散式任務處理
- 快取和性能優化

### 安全性
- 不在代碼中硬編碼敏感資訊
- 使用環境變數管理配置
- 實施適當的API認證和授權
- 定期更新依賴以修復安全漏洞