"""
Analytics API routes
"""
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ...database.connection import get_db
from ...analytics.price_analyzer import PriceAnalyzer
from ...analytics.visualizer import DataVisualizer


router = APIRouter()


@router.get("/price-trends")
async def get_price_trends(
    product_id: Optional[UUID] = Query(None, description="Product ID"),
    category: Optional[str] = Query(None, description="Product category"),
    brand: Optional[str] = Query(None, description="Brand name"),
    days: int = Query(30, ge=1, le=365, description="Number of days"),
    db: Session = Depends(get_db)
):
    """Get price trend analysis"""
    analyzer = PriceAnalyzer()
    
    analysis = analyzer.analyze_price_trends(
        product_id=str(product_id) if product_id else None,
        category=category,
        brand=brand,
        days=days,
        db=db
    )
    
    return analysis


@router.get("/price-alerts")
async def get_price_alerts(
    threshold: float = Query(10.0, ge=0.1, le=100.0, description="Price change threshold percentage"),
    db: Session = Depends(get_db)
):
    """Get price change alerts"""
    analyzer = PriceAnalyzer()
    
    alerts = analyzer.get_price_alerts(
        threshold_percentage=threshold,
        db=db
    )
    
    return {"alerts": alerts, "count": len(alerts)}


@router.get("/compare-products")
async def compare_products(
    product_ids: List[UUID] = Query(..., description="List of product IDs to compare"),
    days: int = Query(30, ge=1, le=365, description="Number of days"),
    db: Session = Depends(get_db)
):
    """Compare multiple products"""
    analyzer = PriceAnalyzer()
    
    product_ids_str = [str(pid) for pid in product_ids]
    
    comparison = analyzer.compare_products(
        product_ids=product_ids_str,
        days=days,
        db=db
    )
    
    return comparison


@router.get("/visualizations/price-trends")
async def get_price_trend_chart(
    product_id: Optional[UUID] = Query(None, description="Product ID"),
    category: Optional[str] = Query(None, description="Product category"),
    brand: Optional[str] = Query(None, description="Brand name"),
    days: int = Query(30, ge=1, le=365, description="Number of days"),
    interactive: bool = Query(True, description="Generate interactive chart"),
    db: Session = Depends(get_db)
):
    """Get price trend visualization"""
    analyzer = PriceAnalyzer()
    visualizer = DataVisualizer()
    
    # Get price data
    analysis = analyzer.analyze_price_trends(
        product_id=str(product_id) if product_id else None,
        category=category,
        brand=brand,
        days=days,
        db=db
    )
    
    if 'error' in analysis:
        raise HTTPException(status_code=404, detail=analysis['error'])
    
    # Generate visualization
    price_data = analysis.get('trend_analysis', {}).get('daily_averages', [])
    
    chart_html = visualizer.create_price_trend_chart(
        price_data=price_data,
        title=f"Price Trends - {days} days",
        interactive=interactive
    )
    
    return {"chart": chart_html, "data": analysis}


@router.get("/category-stats")
async def get_category_stats(
    db: Session = Depends(get_db)
):
    """Get category statistics"""
    from ...database.models import Product
    
    # Get product count by category
    category_stats = db.query(
        Product.category,
        db.func.count(Product.id).label('product_count'),
        db.func.avg(Product.current_price).label('avg_price'),
        db.func.min(Product.current_price).label('min_price'),
        db.func.max(Product.current_price).label('max_price')
    ).group_by(Product.category).all()
    
    results = []
    for stat in category_stats:
        results.append({
            "category": stat.category,
            "product_count": stat.product_count,
            "avg_price": round(float(stat.avg_price or 0), 2),
            "min_price": float(stat.min_price or 0),
            "max_price": float(stat.max_price or 0)
        })
    
    return {"categories": results}


@router.get("/brand-performance")
async def get_brand_performance(
    brand: Optional[str] = Query(None, description="Specific brand name"),
    db: Session = Depends(get_db)
):
    """Get brand performance metrics"""
    from ...database.models import Product, Brand
    
    query = db.query(
        Brand.name,
        db.func.count(Product.id).label('product_count'),
        db.func.avg(Product.current_price).label('avg_price'),
        db.func.count(
            db.case([(Product.availability == 'in_stock', 1)])
        ).label('in_stock_count')
    ).join(Product).group_by(Brand.name)
    
    if brand:
        query = query.filter(Brand.name.ilike(f"%{brand}%"))
    
    results = query.all()
    
    brand_stats = []
    for result in results:
        brand_stats.append({
            "brand": result.name,
            "product_count": result.product_count,
            "avg_price": round(float(result.avg_price or 0), 2),
            "in_stock_count": result.in_stock_count,
            "stock_rate": round(
                (result.in_stock_count / result.product_count) * 100, 1
            ) if result.product_count > 0 else 0
        })
    
    return {"brands": brand_stats}


@router.get("/dashboard")
async def get_dashboard(
    db: Session = Depends(get_db)
):
    """Get dashboard data"""
    from ...database.models import Product, Brand, PriceHistory
    
    # Basic statistics
    total_products = db.query(Product).count()
    total_brands = db.query(Brand).count()
    total_price_records = db.query(PriceHistory).count()
    
    # Recent activity
    recent_products = db.query(Product).order_by(
        Product.created_at.desc()
    ).limit(5).all()
    
    # Price alerts
    analyzer = PriceAnalyzer()
    alerts = analyzer.get_price_alerts(threshold_percentage=10.0, db=db)
    
    return {
        "statistics": {
            "total_products": total_products,
            "total_brands": total_brands,
            "total_price_records": total_price_records,
            "recent_alerts": len(alerts)
        },
        "recent_products": [
            {
                "id": str(p.id),
                "name": p.name,
                "price": p.current_price,
                "created_at": p.created_at
            } for p in recent_products
        ],
        "alerts": alerts[:5]  # Show only first 5 alerts
    }


@router.get("/visualizations/dashboard")
async def get_dashboard_charts(
    db: Session = Depends(get_db)
):
    """Get dashboard visualizations"""
    visualizer = DataVisualizer()
    
    # Get category distribution
    category_stats = db.query(
        Product.category,
        db.func.count(Product.id).label('count')
    ).group_by(Product.category).all()
    
    category_data = {stat.category: stat.count for stat in category_stats}
    
    # Get brand performance
    brand_stats = db.query(
        Brand.name,
        db.func.count(Product.id).label('product_count'),
        db.func.avg(Product.current_price).label('avg_price')
    ).join(Product).group_by(Brand.name).all()
    
    brand_data = {
        stat.name: {
            "product_count": stat.product_count,
            "avg_price": float(stat.avg_price or 0)
        } for stat in brand_stats
    }
    
    # Generate charts
    dashboard_data = {
        "category_distribution": visualizer.create_category_distribution_chart(
            category_data, "Product Categories"
        ),
        "brand_performance": visualizer.create_brand_performance_chart(
            brand_data, "Brand Performance"
        )
    }
    
    # Generate complete dashboard
    dashboard_html = visualizer.create_dashboard(
        dashboard_data,
        title="Price Cage Analytics Dashboard"
    )
    
    return {"dashboard": dashboard_html, "charts": dashboard_data}