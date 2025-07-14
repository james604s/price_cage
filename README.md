# Price Cage 🥊👕

多網站爬蟲系統，專門用於爬取格鬥用品和潮流衣物的價格資訊，提供完整的數據分析和視覺化功能。

## 功能特色

- 🕷️ **多網站爬蟲**: 支援格鬥用品和潮流衣物網站
- 📊 **價格追蹤**: 實時監控產品價格變動
- 🔍 **數據分析**: 價格趨勢、波動性分析
- 📈 **視覺化**: 互動式圖表和儀表板
- 🚀 **REST API**: 完整的 FastAPI 後端服務
- 🗄️ **PostgreSQL**: 可靠的資料庫存儲
- 🐳 **Docker**: 容器化部署
- 📱 **響應式**: 支援多設備訪問

## 支援的網站

### 格鬥用品
- [Venum](https://www.venum.com)
- [Tatami Fightwear](https://www.tatamifightwear.com)
- [Hayabusa](https://www.hayabusafight.com)

### 潮流衣物
- [Supreme](https://www.supremenewyork.com)
- [A Bathing Ape](https://www.bape.com)
- [Stussy](https://www.stussy.com)

## 快速開始

### 1. 克隆專案
```bash
git clone <repository-url>
cd price_cage
```

### 2. 環境設置
```bash
# 複製環境變數範例
cp .env.example .env

# 編輯 .env 文件，填入正確的配置
vim .env
```

### 3. 使用 Docker (推薦)
```bash
# 啟動所有服務
docker-compose up -d

# 檢查服務狀態
docker-compose ps

# 初始化資料庫
docker-compose exec api python scripts/setup_database.py --action init
```

### 4. 本地開發環境
```bash
# 安裝依賴
pip install -r requirements.txt

# 設置資料庫
python scripts/setup_database.py --action init

# 啟動開發服務器
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

## 使用說明

### 運行爬蟲
```bash
# 爬取所有網站
python scripts/run_crawler.py --type all

# 爬取特定類型
python scripts/run_crawler.py --type fighting_gear
python scripts/run_crawler.py --type streetwear

# 爬取特定網站
python scripts/run_crawler.py --sites venum supreme

# 異步模式
python scripts/run_crawler.py --type all --async
```

### API 使用
```bash
# 獲取所有產品
curl http://localhost:8000/api/v1/products/

# 根據分類搜尋
curl "http://localhost:8000/api/v1/products/?category=boxing_gloves"

# 價格範圍篩選
curl "http://localhost:8000/api/v1/products/?min_price=50&max_price=200"

# 查看 API 文檔
open http://localhost:8000/docs
```

### 儀表板
- **API 文檔**: http://localhost:8000/docs
- **健康檢查**: http://localhost:8000/health
- **Grafana 監控**: http://localhost:3000 (admin/admin)
- **Prometheus 指標**: http://localhost:9090

## 專案結構

```
price_cage/
├── src/
│   ├── crawlers/           # 爬蟲核心模組
│   ├── parsers/            # 網站解析器
│   ├── database/           # 資料庫模組
│   ├── api/                # FastAPI 後端
│   ├── analytics/          # 數據分析模組
│   ├── storage/            # 資料存儲處理
│   ├── utils/              # 工具函數
│   └── config/             # 配置文件
├── tests/                  # 測試文件
├── scripts/                # 執行腳本
├── docs/                   # 文檔
├── docker-compose.yml      # Docker 配置
├── requirements.txt        # Python 依賴
└── README.md
```

## 技術堆疊

### 後端
- **Python 3.11+**: 主要程式語言
- **FastAPI**: 高效能 Web 框架
- **PostgreSQL**: 主要資料庫
- **Redis**: 快取和消息佇列
- **Celery**: 分散式任務隊列
- **SQLAlchemy**: ORM 框架

### 爬蟲
- **BeautifulSoup4**: HTML 解析
- **Selenium**: 動態網頁處理
- **aiohttp**: 異步 HTTP 請求
- **requests**: 同步 HTTP 請求

### 數據分析
- **Pandas**: 資料處理
- **NumPy**: 數值計算
- **Matplotlib**: 圖表繪製
- **Plotly**: 互動式圖表
- **Seaborn**: 統計圖表

### 部署
- **Docker**: 容器化
- **Docker Compose**: 多服務編排
- **Prometheus**: 監控系統
- **Grafana**: 視覺化儀表板

## 開發指南

### 添加新網站
1. 在 `src/parsers/` 創建新的解析器
2. 繼承 `BaseParser` 實現必要方法
3. 在 `src/config/settings.py` 添加網站配置
4. 更新對應的爬蟲類別

### 添加新分析功能
1. 在 `src/analytics/` 創建分析模組
2. 在 `src/api/routers/analytics.py` 添加 API 端點
3. 更新前端儀表板

### 測試
```bash
# 運行所有測試
pytest tests/

# 測試覆蓋率
pytest --cov=src tests/
```

## 部署指南

### 開發環境
```bash
uvicorn src.api.main:app --reload
```

### 生產環境
```bash
# 使用 Docker Compose
docker-compose up -d

# 或使用 Kubernetes
kubectl apply -f k8s/
```

## 監控和日誌

### 日誌檔案
- 應用程式日誌: `logs/app.log`
- 爬蟲日誌: `logs/crawler.log`
- API 日誌: `logs/api.log`

### 監控指標
- 爬蟲執行狀態
- API 響應時間
- 資料庫性能
- 系統資源使用

## 常見問題

### Q: 爬蟲被網站封鎖怎麼辦？
A: 調整 `CRAWLER_DELAY` 設定，增加請求間隔時間，或使用代理服務器。

### Q: 如何添加新的產品分類？
A: 在 `src/database/models.py` 的 `ProductCategory` 枚舉中添加新分類。

### Q: 資料庫遷移如何處理？
A: 修改模型後使用 `python scripts/setup_database.py --action reset` 重置資料庫。

## 授權協議

本專案採用 MIT 授權協議 - 詳見 [LICENSE](LICENSE) 文件。

## 貢獻指南

歡迎提交 Issue 和 Pull Request！請確保：
1. 遵循代碼風格指南
2. 添加適當的測試
3. 更新相關文檔
4. 通過所有測試

## 聯絡資訊

- 作者：[Your Name]
- Email：[your.email@example.com]
- GitHub：[your-github-username]

---

⭐ 如果這個專案對您有幫助，請給我們一個星星！