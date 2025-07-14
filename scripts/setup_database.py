#!/usr/bin/env python3
"""
資料庫設置腳本
"""
import sys
from pathlib import Path
import argparse

# 添加專案根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.connection import db_manager
from src.database.models import Base, Brand, Website
from src.utils.logger import get_logger
from src.config.settings import CrawlerConfig


def init_database():
    """初始化資料庫"""
    logger = get_logger("database_setup")
    
    try:
        logger.info("正在初始化資料庫...")
        
        # 創建所有表格
        db_manager.create_tables()
        
        logger.info("資料庫表格創建完成")
        
        # 插入基礎數據
        insert_base_data()
        
        logger.info("資料庫初始化完成")
        
    except Exception as e:
        logger.error(f"資料庫初始化失敗: {e}")
        raise


def insert_base_data():
    """插入基礎數據"""
    logger = get_logger("database_setup")
    
    with db_manager.get_session() as session:
        # 插入格鬥用品品牌
        fighting_gear_brands = [
            ("Venum", "Venum", "fighting_gear", "https://www.venum.com", "France"),
            ("Tatami", "Tatami Fightwear", "fighting_gear", "https://www.tatamifightwear.com", "UK"),
            ("Hayabusa", "Hayabusa", "fighting_gear", "https://www.hayabusafight.com", "Canada"),
        ]
        
        for brand_data in fighting_gear_brands:
            existing_brand = session.query(Brand).filter(Brand.name == brand_data[0]).first()
            if not existing_brand:
                brand = Brand(
                    name=brand_data[0],
                    display_name=brand_data[1],
                    category=brand_data[2],
                    website_url=brand_data[3],
                    country=brand_data[4]
                )
                session.add(brand)
                logger.info(f"添加品牌: {brand_data[0]}")
        
        # 插入潮流衣物品牌
        streetwear_brands = [
            ("Supreme", "Supreme", "streetwear", "https://www.supremenewyork.com", "USA"),
            ("BAPE", "A Bathing Ape", "streetwear", "https://www.bape.com", "Japan"),
            ("Stussy", "Stussy", "streetwear", "https://www.stussy.com", "USA"),
        ]
        
        for brand_data in streetwear_brands:
            existing_brand = session.query(Brand).filter(Brand.name == brand_data[0]).first()
            if not existing_brand:
                brand = Brand(
                    name=brand_data[0],
                    display_name=brand_data[1],
                    category=brand_data[2],
                    website_url=brand_data[3],
                    country=brand_data[4]
                )
                session.add(brand)
                logger.info(f"添加品牌: {brand_data[0]}")
        
        session.commit()
        
        # 插入網站配置
        insert_website_configs(session)


def insert_website_configs(session):
    """插入網站配置"""
    logger = get_logger("database_setup")
    
    # 格鬥用品網站
    for site_name, config in CrawlerConfig.FIGHTING_GEAR_SITES.items():
        brand = session.query(Brand).filter(Brand.name.ilike(f"%{site_name}%")).first()
        if brand:
            existing_website = session.query(Website).filter(Website.domain == config['base_url'].replace('https://', '').replace('http://', '')).first()
            if not existing_website:
                website = Website(
                    name=site_name.title(),
                    domain=config['base_url'].replace('https://', '').replace('http://', ''),
                    base_url=config['base_url'],
                    brand_id=brand.id,
                    crawler_config=config
                )
                session.add(website)
                logger.info(f"添加網站: {site_name}")
    
    # 潮流衣物網站
    for site_name, config in CrawlerConfig.STREETWEAR_SITES.items():
        brand = session.query(Brand).filter(Brand.name.ilike(f"%{site_name}%")).first()
        if brand:
            existing_website = session.query(Website).filter(Website.domain == config['base_url'].replace('https://', '').replace('http://', '')).first()
            if not existing_website:
                website = Website(
                    name=site_name.title(),
                    domain=config['base_url'].replace('https://', '').replace('http://', ''),
                    base_url=config['base_url'],
                    brand_id=brand.id,
                    crawler_config=config
                )
                session.add(website)
                logger.info(f"添加網站: {site_name}")
    
    session.commit()


def reset_database():
    """重置資料庫"""
    logger = get_logger("database_setup")
    
    try:
        logger.warning("正在重置資料庫...")
        
        # 刪除所有表格
        db_manager.drop_tables()
        
        # 重新創建表格
        db_manager.create_tables()
        
        # 插入基礎數據
        insert_base_data()
        
        logger.info("資料庫重置完成")
        
    except Exception as e:
        logger.error(f"資料庫重置失敗: {e}")
        raise


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='Price Cage 資料庫設置')
    parser.add_argument(
        '--action',
        choices=['init', 'reset'],
        default='init',
        help='操作類型'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='強制執行操作'
    )
    
    args = parser.parse_args()
    
    try:
        if args.action == 'init':
            init_database()
        elif args.action == 'reset':
            if args.force or input("確定要重置資料庫嗎? (y/N): ").lower() == 'y':
                reset_database()
            else:
                print("操作已取消")
                
    except KeyboardInterrupt:
        print("\n操作已中斷")
    except Exception as e:
        print(f"操作失敗: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()