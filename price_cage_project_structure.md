# Price Cage - 多網站爬蟲專案結構

## 專案概述
專門爬取格鬥用品和潮流衣物的多網站爬蟲系統，包含資料處理、API 服務和數據分析功能。

## 專案目錄結構
```
price_cage/
├── src/
│   ├── crawlers/              # 爬蟲核心模組
│   │   ├── __init__.py
│   │   ├── base_crawler.py    # 基礎爬蟲類別
│   │   ├── fighting_gear_crawler.py  # 格鬥用品爬蟲
│   │   ├── streetwear_crawler.py     # 潮流衣物爬蟲
│   │   └── scheduler.py       # 任務調度器
│   ├── parsers/              # 網站解析器
│   │   ├── __init__.py
│   │   ├── base_parser.py    # 基礎解析器
│   │   ├── fighting_gear/    # 格鬥用品解析器
│   │   │   ├── __init__.py
│   │   │   ├── venum_parser.py
│   │   │   ├── tatami_parser.py
│   │   │   └── hayabusa_parser.py
│   │   └── streetwear/       # 潮流衣物解析器
│   │       ├── __init__.py
│   │       ├── supreme_parser.py
│   │       ├── bape_parser.py
│   │       └── stussy_parser.py
│   ├── database/             # 資料庫模組
│   │   ├── __init__.py
│   │   ├── models.py         # SQLAlchemy 模型
│   │   ├── connection.py     # 資料庫連接
│   │   └── migrations/       # 資料庫遷移
│   ├── api/                  # FastAPI 後端
│   │   ├── __init__.py
│   │   ├── main.py          # API 主程式
│   │   ├── routers/         # API 路由
│   │   │   ├── __init__.py
│   │   │   ├── products.py
│   │   │   ├── brands.py
│   │   │   └── analytics.py
│   │   └── schemas/         # Pydantic 模型
│   │       ├── __init__.py
│   │       ├── product.py
│   │       └── brand.py
│   ├── storage/             # 資料存儲處理
│   │   ├── __init__.py
│   │   ├── data_processor.py
│   │   └── file_handler.py
│   ├── analytics/           # 數據分析模組
│   │   ├── __init__.py
│   │   ├── price_analyzer.py
│   │   ├── trend_analyzer.py
│   │   └── visualizer.py
│   ├── utils/               # 工具函數
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   ├── helpers.py
│   │   └── validators.py
│   └── config/              # 配置文件
│       ├── __init__.py
│       ├── settings.py
│       └── site_configs.py
├── tests/                   # 測試文件
│   ├── __init__.py
│   ├── test_crawlers/
│   ├── test_parsers/
│   ├── test_api/
│   └── test_analytics/
├── scripts/                 # 腳本工具
│   ├── run_crawler.py
│   ├── setup_database.py
│   └── data_export.py
├── docs/                    # 文檔
│   ├── API.md
│   ├── DEPLOYMENT.md
│   └── DEVELOPMENT.md
├── requirements.txt         # Python 依賴
├── docker-compose.yml      # Docker 配置
├── Dockerfile
├── .env.example            # 環境變數範例
├── .gitignore
└── README.md
```

## 主要功能模組

### 1. 爬蟲模組 (crawlers/)
- **base_crawler.py**: 基礎爬蟲類別，提供通用功能
- **fighting_gear_crawler.py**: 格鬥用品專用爬蟲
- **streetwear_crawler.py**: 潮流衣物專用爬蟲
- **scheduler.py**: 任務調度和管理

### 2. 解析器模組 (parsers/)
- 針對不同網站的專門解析器
- 支援格鬥用品網站：Venum、Tatami、Hayabusa
- 支援潮流衣物網站：Supreme、BAPE、Stussy

### 3. 資料庫模組 (database/)
- PostgreSQL 資料庫模型設計
- 產品、品牌、價格歷史等資料表
- 資料庫遷移管理

### 4. API 模組 (api/)
- FastAPI 後端服務
- RESTful API 設計
- 產品查詢、品牌管理、數據分析接口

### 5. 數據分析模組 (analytics/)
- 價格趨勢分析
- 品牌熱度分析
- 資料視覺化工具

## 技術堆疊

### 爬蟲技術
- **requests**: HTTP 請求處理
- **BeautifulSoup4**: HTML 解析
- **Selenium**: 動態網頁處理
- **aiohttp**: 異步爬蟲

### 資料庫
- **PostgreSQL**: 主要資料庫
- **SQLAlchemy**: ORM 框架
- **Alembic**: 資料庫遷移

### API 框架
- **FastAPI**: 高效能 API 框架
- **Pydantic**: 資料驗證和序列化
- **Uvicorn**: ASGI 服務器

### 數據分析
- **Pandas**: 資料處理
- **NumPy**: 數值計算
- **Matplotlib**: 基礎圖表
- **Plotly**: 互動式圖表
- **Seaborn**: 統計圖表

### 其他工具
- **Celery**: 任務隊列
- **Redis**: 快取和消息佇列
- **Docker**: 容器化部署
- **pytest**: 單元測試

## 資料庫設計

### 主要資料表
1. **products** - 產品資訊
2. **brands** - 品牌資訊
3. **categories** - 產品分類
4. **price_history** - 價格歷史
5. **websites** - 網站資訊
6. **crawl_logs** - 爬蟲日誌

## 部署和運行

### 開發環境
```bash
# 安裝依賴
pip install -r requirements.txt

# 設置環境變數
cp .env.example .env

# 初始化資料庫
python scripts/setup_database.py

# 運行爬蟲
python scripts/run_crawler.py

# 啟動 API 服務
uvicorn src.api.main:app --reload
```

### 生產環境
```bash
# 使用 Docker
docker-compose up -d
```

## 後續擴展
- 支援更多網站和產品類別
- 實時價格監控和警報
- 機器學習價格預測
- 移動端應用開發
- 數據 ETL 管道優化