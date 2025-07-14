"""
價格分析模組
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc

from ..database.models import Product, PriceHistory, Brand
from ..database.connection import get_db
from ..utils.logger import get_logger


class PriceAnalyzer:
    """價格分析器"""
    
    def __init__(self):
        self.logger = get_logger("price_analyzer")
    
    def analyze_price_trends(self, 
                           product_id: str = None,
                           category: str = None,
                           brand: str = None,
                           days: int = 30,
                           db: Session = None) -> Dict[str, Any]:
        """分析價格趨勢"""
        if not db:
            raise ValueError("數據庫連接不能為空")
        
        try:
            # 構建查詢
            query = db.query(PriceHistory).join(Product)
            
            # 日期篩選
            from_date = datetime.now() - timedelta(days=days)
            query = query.filter(PriceHistory.recorded_at >= from_date)
            
            # 額外篩選條件
            if product_id:
                query = query.filter(Product.id == product_id)
            if category:
                query = query.filter(Product.category == category)
            if brand:
                query = query.join(Brand).filter(Brand.name == brand)
            
            # 獲取價格歷史數據
            price_history = query.order_by(PriceHistory.recorded_at).all()
            
            if not price_history:
                return {"error": "無可用的價格歷史數據"}
            
            # 轉換為 DataFrame
            df = pd.DataFrame([{
                'product_id': ph.product_id,
                'price': ph.price,
                'recorded_at': ph.recorded_at,
                'availability': ph.availability
            } for ph in price_history])
            
            # 分析結果
            analysis = {
                'period_days': days,
                'total_records': len(df),
                'price_statistics': self._calculate_price_statistics(df),
                'trend_analysis': self._analyze_trend(df),
                'volatility_analysis': self._analyze_volatility(df),
                'availability_analysis': self._analyze_availability(df)
            }
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"價格趨勢分析失敗: {e}")
            return {"error": str(e)}
    
    def _calculate_price_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """計算價格統計資料"""
        return {
            'min_price': float(df['price'].min()),
            'max_price': float(df['price'].max()),
            'avg_price': float(df['price'].mean()),
            'median_price': float(df['price'].median()),
            'std_price': float(df['price'].std()),
            'price_range': float(df['price'].max() - df['price'].min())
        }
    
    def _analyze_trend(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析價格趨勢"""
        # 按日期分組計算平均價格
        df['date'] = pd.to_datetime(df['recorded_at']).dt.date
        daily_avg = df.groupby('date')['price'].mean().reset_index()
        
        if len(daily_avg) < 2:
            return {"trend": "insufficient_data"}
        
        # 計算趨勢線斜率
        x = np.arange(len(daily_avg))
        y = daily_avg['price'].values
        slope, intercept = np.polyfit(x, y, 1)
        
        # 判斷趨勢
        if abs(slope) < 0.01:
            trend = "stable"
        elif slope > 0:
            trend = "rising"
        else:
            trend = "falling"
        
        # 計算趨勢強度
        correlation = np.corrcoef(x, y)[0, 1]
        
        return {
            'trend': trend,
            'slope': float(slope),
            'correlation': float(correlation),
            'trend_strength': abs(float(correlation)),
            'daily_averages': daily_avg.to_dict('records')
        }
    
    def _analyze_volatility(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析價格波動性"""
        # 計算價格變化率
        df_sorted = df.sort_values('recorded_at')
        price_changes = df_sorted['price'].pct_change().dropna()
        
        if len(price_changes) == 0:
            return {"volatility": 0, "classification": "stable"}
        
        volatility = float(price_changes.std())
        
        # 波動性分類
        if volatility < 0.05:
            classification = "low"
        elif volatility < 0.15:
            classification = "medium"
        else:
            classification = "high"
        
        return {
            'volatility': volatility,
            'classification': classification,
            'max_change': float(price_changes.abs().max()),
            'avg_change': float(price_changes.abs().mean())
        }
    
    def _analyze_availability(self, df: pd.DataFrame) -> Dict[str, Any]:
        """分析庫存可用性"""
        availability_counts = df['availability'].value_counts()
        total_records = len(df)
        
        availability_stats = {}
        for status, count in availability_counts.items():
            availability_stats[status] = {
                'count': int(count),
                'percentage': float(count / total_records * 100)
            }
        
        return {
            'availability_distribution': availability_stats,
            'stock_out_frequency': availability_stats.get('out_of_stock', {}).get('percentage', 0)
        }
    
    def compare_products(self, 
                        product_ids: List[str], 
                        days: int = 30,
                        db: Session = None) -> Dict[str, Any]:
        """比較多個產品的價格"""
        if not db:
            raise ValueError("數據庫連接不能為空")
        
        try:
            comparison_results = {}
            
            for product_id in product_ids:
                analysis = self.analyze_price_trends(
                    product_id=product_id,
                    days=days,
                    db=db
                )
                
                if 'error' not in analysis:
                    comparison_results[product_id] = analysis
            
            # 計算比較統計
            if len(comparison_results) > 1:
                comparison_stats = self._calculate_comparison_stats(comparison_results)
                comparison_results['comparison_summary'] = comparison_stats
            
            return comparison_results
            
        except Exception as e:
            self.logger.error(f"產品比較分析失敗: {e}")
            return {"error": str(e)}
    
    def _calculate_comparison_stats(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """計算比較統計"""
        prices = []
        trends = []
        
        for product_id, analysis in results.items():
            if isinstance(analysis, dict) and 'price_statistics' in analysis:
                prices.append(analysis['price_statistics']['avg_price'])
                trends.append(analysis['trend_analysis']['trend'])
        
        return {
            'avg_price_comparison': {
                'lowest': min(prices) if prices else 0,
                'highest': max(prices) if prices else 0,
                'average': sum(prices) / len(prices) if prices else 0
            },
            'trend_summary': {
                'rising': trends.count('rising'),
                'falling': trends.count('falling'),
                'stable': trends.count('stable')
            }
        }
    
    def get_price_alerts(self, 
                        threshold_percentage: float = 10.0,
                        db: Session = None) -> List[Dict[str, Any]]:
        """獲取價格變動警報"""
        if not db:
            raise ValueError("數據庫連接不能為空")
        
        try:
            alerts = []
            
            # 查詢最近24小時的價格變動
            yesterday = datetime.now() - timedelta(hours=24)
            
            # 獲取每個產品的最新價格和前一個價格
            products = db.query(Product).filter(Product.is_active == True).all()
            
            for product in products:
                recent_prices = db.query(PriceHistory).filter(
                    PriceHistory.product_id == product.id,
                    PriceHistory.recorded_at >= yesterday
                ).order_by(desc(PriceHistory.recorded_at)).limit(2).all()
                
                if len(recent_prices) >= 2:
                    current_price = recent_prices[0].price
                    previous_price = recent_prices[1].price
                    
                    if previous_price > 0:
                        change_percentage = ((current_price - previous_price) / previous_price) * 100
                        
                        if abs(change_percentage) >= threshold_percentage:
                            alerts.append({
                                'product_id': str(product.id),
                                'product_name': product.name,
                                'current_price': current_price,
                                'previous_price': previous_price,
                                'change_percentage': round(change_percentage, 2),
                                'alert_type': 'price_increase' if change_percentage > 0 else 'price_decrease',
                                'timestamp': recent_prices[0].recorded_at
                            })
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"價格警報生成失敗: {e}")
            return []