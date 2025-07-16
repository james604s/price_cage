#!/usr/bin/env python3
"""
Crawler execution script
"""
import asyncio
import argparse
import sys
from pathlib import Path
from typing import List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.crawlers.fighting_gear_crawler import FightingGearCrawler
from src.crawlers.streetwear_crawler import StreetwearCrawler
from src.crawlers.center_sp_crawler import CenterSPCrawler
from src.database.connection import init_database
from src.storage.data_processor import DataProcessor
from src.utils.logger import get_logger


class CrawlerManager:
    """Crawler manager"""
    
    def __init__(self):
        self.logger = get_logger("crawler_manager")
        self.data_processor = DataProcessor()
        
        # Initialize crawlers
        self.crawlers = {
            'fighting_gear': FightingGearCrawler(),
            'streetwear': StreetwearCrawler(),
            'center_sp': CenterSPCrawler()
        }
    
    def run_crawler(self, 
                   crawler_type: str, 
                   sites: Optional[List[str]] = None,
                   async_mode: bool = False):
        """Run specified type of crawler"""
        if crawler_type not in self.crawlers:
            self.logger.error(f"Unsupported crawler type: {crawler_type}")
            return
        
        crawler = self.crawlers[crawler_type]
        
        try:
            self.logger.info(f"Starting {crawler_type} crawler")
            
            if async_mode:
                products = asyncio.run(crawler.crawl_all_async(sites))
            else:
                products = crawler.crawl_all(sites)
            
            self.logger.info(f"Crawler completed, got {len(products)} products")
            
            # Process and store data
            self.data_processor.process_products(products)
            
        except Exception as e:
            self.logger.error(f"Crawler execution failed: {e}")
            raise
    
    def run_all_crawlers(self, async_mode: bool = False):
        """Run all crawlers"""
        for crawler_type in self.crawlers.keys():
            try:
                self.run_crawler(crawler_type, async_mode=async_mode)
            except Exception as e:
                self.logger.error(f"Crawler {crawler_type} failed: {e}")
                continue
    
    def run_specific_sites(self, sites: List[str], async_mode: bool = False):
        """Run crawlers for specific sites"""
        fighting_gear_sites = ['venum', 'tatami', 'hayabusa']
        streetwear_sites = ['supreme', 'bape', 'stussy']
        center_sp_sites = ['center-sp', 'center_sp', 'centersp']
        
        for site in sites:
            if site in fighting_gear_sites:
                self.run_crawler('fighting_gear', [site], async_mode)
            elif site in streetwear_sites:
                self.run_crawler('streetwear', [site], async_mode)
            elif site in center_sp_sites:
                self.run_crawler('center_sp', [], async_mode)
            else:
                self.logger.warning(f"Unsupported site: {site}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Price Cage Crawler System')
    parser.add_argument(
        '--type', 
        choices=['fighting_gear', 'streetwear', 'center_sp', 'all'],
        default='all',
        help='Crawler type'
    )
    parser.add_argument(
        '--sites',
        nargs='+',
        help='Specify sites to crawl'
    )
    parser.add_argument(
        '--async',
        action='store_true',
        dest='async_mode',
        help='Use async mode'
    )
    parser.add_argument(
        '--init-db',
        action='store_true',
        help='Initialize database'
    )
    parser.add_argument(
        '--schedule',
        action='store_true',
        help='Run scheduler mode'
    )
    
    args = parser.parse_args()
    
    # Initialize database
    if args.init_db:
        print("Initializing database...")
        init_database()
        print("Database initialization completed")
    
    # Create crawler manager
    manager = CrawlerManager()
    
    try:
        if args.schedule:
            # Schedule mode - continuous running
            import schedule
            import time
            
            def job():
                manager.run_all_crawlers(async_mode=args.async_mode)
            
            # Run every hour
            schedule.every().hour.do(job)
            
            print("Scheduler mode started, running crawler every hour...")
            while True:
                schedule.run_pending()
                time.sleep(60)
        
        elif args.sites:
            # Run specific sites
            manager.run_specific_sites(args.sites, async_mode=args.async_mode)
        
        elif args.type == 'all':
            # Run all crawlers
            manager.run_all_crawlers(async_mode=args.async_mode)
        
        else:
            # Run specific type crawler
            manager.run_crawler(args.type, async_mode=args.async_mode)
            
    except KeyboardInterrupt:
        print("\nCrawler stopped")
    except Exception as e:
        print(f"Crawler execution error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()