"""
數據視覺化模組
"""
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from io import BytesIO
import base64

from ..utils.logger import get_logger


class DataVisualizer:
    """數據視覺化器"""
    
    def __init__(self):
        self.logger = get_logger("data_visualizer")
        
        # 設置中文字型支援
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        
        # 設置 Seaborn 樣式
        sns.set_style("whitegrid")
        sns.set_palette("husl")
    
    def create_price_trend_chart(self, 
                               price_data: List[Dict[str, Any]],
                               title: str = "價格趨勢圖",
                               interactive: bool = True) -> str:
        """創建價格趨勢圖表"""
        try:
            if not price_data:
                return self._create_empty_chart_message("無可用數據")
            
            df = pd.DataFrame(price_data)
            df['recorded_at'] = pd.to_datetime(df['recorded_at'])
            
            if interactive:
                return self._create_interactive_price_chart(df, title)
            else:
                return self._create_static_price_chart(df, title)
                
        except Exception as e:
            self.logger.error(f"價格趨勢圖表創建失敗: {e}")
            return self._create_error_chart(str(e))
    
    def _create_interactive_price_chart(self, df: pd.DataFrame, title: str) -> str:
        """創建互動式價格圖表"""
        fig = go.Figure()
        
        # 添加價格線
        fig.add_trace(go.Scatter(
            x=df['recorded_at'],
            y=df['price'],
            mode='lines+markers',
            name='價格',
            line=dict(color='blue', width=2),
            marker=dict(size=4)
        ))
        
        # 添加趨勢線
        if len(df) > 1:
            z = np.polyfit(range(len(df)), df['price'], 1)
            p = np.poly1d(z)
            fig.add_trace(go.Scatter(
                x=df['recorded_at'],
                y=p(range(len(df))),
                mode='lines',
                name='趨勢線',
                line=dict(color='red', width=1, dash='dash')
            ))
        
        # 設置圖表布局
        fig.update_layout(
            title=title,
            xaxis_title="時間",
            yaxis_title="價格 (USD)",
            hovermode='x unified',
            template='plotly_white'
        )
        
        return fig.to_html(include_plotlyjs='cdn')
    
    def _create_static_price_chart(self, df: pd.DataFrame, title: str) -> str:
        """創建靜態價格圖表"""
        plt.figure(figsize=(12, 6))
        
        # 繪製價格線
        plt.plot(df['recorded_at'], df['price'], 
                marker='o', linewidth=2, markersize=4)
        
        # 添加趨勢線
        if len(df) > 1:
            z = np.polyfit(range(len(df)), df['price'], 1)
            p = np.poly1d(z)
            plt.plot(df['recorded_at'], p(range(len(df))), 
                    'r--', alpha=0.7, label='趨勢線')
        
        plt.title(title)
        plt.xlabel("時間")
        plt.ylabel("價格 (USD)")
        plt.xticks(rotation=45)
        plt.legend()
        plt.tight_layout()
        
        # 轉換為 base64 字符串
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return f'<img src="data:image/png;base64,{image_base64}" alt="{title}">'
    
    def create_price_comparison_chart(self, 
                                    comparison_data: Dict[str, Any],
                                    title: str = "產品價格比較") -> str:
        """創建價格比較圖表"""
        try:
            if not comparison_data:
                return self._create_empty_chart_message("無比較數據")
            
            # 準備數據
            products = []
            prices = []
            
            for product_id, data in comparison_data.items():
                if isinstance(data, dict) and 'price_statistics' in data:
                    products.append(product_id[:8])  # 使用前8位ID
                    prices.append(data['price_statistics']['avg_price'])
            
            if not products:
                return self._create_empty_chart_message("無有效比較數據")
            
            # 創建互動式柱狀圖
            fig = go.Figure(data=[
                go.Bar(
                    x=products,
                    y=prices,
                    text=[f'${price:.2f}' for price in prices],
                    textposition='auto',
                    marker_color='skyblue'
                )
            ])
            
            fig.update_layout(
                title=title,
                xaxis_title="產品",
                yaxis_title="平均價格 (USD)",
                template='plotly_white'
            )
            
            return fig.to_html(include_plotlyjs='cdn')
            
        except Exception as e:
            self.logger.error(f"價格比較圖表創建失敗: {e}")
            return self._create_error_chart(str(e))
    
    def create_category_distribution_chart(self, 
                                         category_data: Dict[str, int],
                                         title: str = "產品分類分佈") -> str:
        """創建分類分佈圖表"""
        try:
            if not category_data:
                return self._create_empty_chart_message("無分類數據")
            
            # 創建餅圖
            fig = go.Figure(data=[
                go.Pie(
                    labels=list(category_data.keys()),
                    values=list(category_data.values()),
                    hole=0.3,
                    textinfo='label+percent',
                    textposition='auto'
                )
            ])
            
            fig.update_layout(
                title=title,
                template='plotly_white'
            )
            
            return fig.to_html(include_plotlyjs='cdn')
            
        except Exception as e:
            self.logger.error(f"分類分佈圖表創建失敗: {e}")
            return self._create_error_chart(str(e))
    
    def create_brand_performance_chart(self, 
                                     brand_data: Dict[str, Dict[str, Any]],
                                     title: str = "品牌表現分析") -> str:
        """創建品牌表現圖表"""
        try:
            if not brand_data:
                return self._create_empty_chart_message("無品牌數據")
            
            brands = list(brand_data.keys())
            avg_prices = [data.get('avg_price', 0) for data in brand_data.values()]
            product_counts = [data.get('product_count', 0) for data in brand_data.values()]
            
            # 創建雙軸圖表
            fig = make_subplots(
                rows=1, cols=1,
                secondary_y=True,
                subplot_titles=[title]
            )
            
            # 添加平均價格柱狀圖
            fig.add_trace(
                go.Bar(
                    x=brands,
                    y=avg_prices,
                    name="平均價格",
                    marker_color='lightblue'
                ),
                secondary_y=False,
            )
            
            # 添加產品數量線圖
            fig.add_trace(
                go.Scatter(
                    x=brands,
                    y=product_counts,
                    mode='lines+markers',
                    name="產品數量",
                    line=dict(color='red', width=2),
                    marker=dict(size=8)
                ),
                secondary_y=True,
            )
            
            # 設置軸標籤
            fig.update_xaxes(title_text="品牌")
            fig.update_yaxes(title_text="平均價格 (USD)", secondary_y=False)
            fig.update_yaxes(title_text="產品數量", secondary_y=True)
            
            fig.update_layout(template='plotly_white')
            
            return fig.to_html(include_plotlyjs='cdn')
            
        except Exception as e:
            self.logger.error(f"品牌表現圖表創建失敗: {e}")
            return self._create_error_chart(str(e))
    
    def create_availability_heatmap(self, 
                                  availability_data: Dict[str, Dict[str, float]],
                                  title: str = "庫存狀態熱力圖") -> str:
        """創建庫存狀態熱力圖"""
        try:
            if not availability_data:
                return self._create_empty_chart_message("無庫存數據")
            
            # 準備數據
            df = pd.DataFrame(availability_data).T
            
            # 創建熱力圖
            fig = go.Figure(data=go.Heatmap(
                z=df.values,
                x=df.columns,
                y=df.index,
                colorscale='RdYlGn',
                text=df.values,
                texttemplate='%{text:.1f}%',
                textfont={"size": 10},
                colorbar=dict(title="百分比")
            ))
            
            fig.update_layout(
                title=title,
                xaxis_title="庫存狀態",
                yaxis_title="產品/品牌",
                template='plotly_white'
            )
            
            return fig.to_html(include_plotlyjs='cdn')
            
        except Exception as e:
            self.logger.error(f"庫存熱力圖創建失敗: {e}")
            return self._create_error_chart(str(e))
    
    def create_dashboard(self, 
                        dashboard_data: Dict[str, Any],
                        title: str = "Price Cage 儀表板") -> str:
        """創建儀表板"""
        try:
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{title}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .dashboard {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
                    .chart-container {{ border: 1px solid #ddd; padding: 15px; border-radius: 8px; }}
                    .header {{ text-align: center; margin-bottom: 30px; }}
                    .full-width {{ grid-column: 1 / -1; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>{title}</h1>
                    <p>生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                
                <div class="dashboard">
            """
            
            # 添加各種圖表
            if 'price_trend' in dashboard_data:
                html_content += f"""
                    <div class="chart-container full-width">
                        <h3>價格趨勢</h3>
                        {dashboard_data['price_trend']}
                    </div>
                """
            
            if 'category_distribution' in dashboard_data:
                html_content += f"""
                    <div class="chart-container">
                        <h3>分類分佈</h3>
                        {dashboard_data['category_distribution']}
                    </div>
                """
            
            if 'brand_performance' in dashboard_data:
                html_content += f"""
                    <div class="chart-container">
                        <h3>品牌表現</h3>
                        {dashboard_data['brand_performance']}
                    </div>
                """
            
            if 'availability_heatmap' in dashboard_data:
                html_content += f"""
                    <div class="chart-container full-width">
                        <h3>庫存狀態</h3>
                        {dashboard_data['availability_heatmap']}
                    </div>
                """
            
            html_content += """
                </div>
            </body>
            </html>
            """
            
            return html_content
            
        except Exception as e:
            self.logger.error(f"儀表板創建失敗: {e}")
            return self._create_error_chart(str(e))
    
    def _create_empty_chart_message(self, message: str) -> str:
        """創建空圖表訊息"""
        return f"""
        <div style="text-align: center; padding: 50px; border: 1px solid #ddd; border-radius: 8px;">
            <h3>暫無數據</h3>
            <p>{message}</p>
        </div>
        """
    
    def _create_error_chart(self, error_message: str) -> str:
        """創建錯誤圖表"""
        return f"""
        <div style="text-align: center; padding: 50px; border: 1px solid #f44336; border-radius: 8px; background-color: #ffebee;">
            <h3>圖表生成錯誤</h3>
            <p>{error_message}</p>
        </div>
        """