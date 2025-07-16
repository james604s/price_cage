#!/usr/bin/env python3
"""
Center-SP Product Parser
Specialized parser for Center-SP sports equipment products
"""

import re
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..base_parser import BaseParser


class CenterSPParser(BaseParser):
    """Parser for Center-SP sports equipment products"""
    
    def __init__(self):
        super().__init__()
        self.site_name = "Center-SP"
        self.base_url = "https://www.center-sp.co.jp/ec/"
        
        # Japanese-specific parsing patterns
        self.japanese_size_patterns = {
            'XS': ['XS', 'エックスエス'],
            'S': ['S', 'エス', 'スモール'],
            'M': ['M', 'エム', 'ミディアム'],
            'L': ['L', 'エル', 'ラージ'],
            'XL': ['XL', 'エックスエル'],
            'XXL': ['XXL', '2XL', 'エックスエックスエル'],
            'フリー': ['フリー', 'FREE', 'フリーサイズ']
        }
        
        # Japanese color patterns
        self.japanese_color_patterns = {
            'black': ['黒', 'ブラック', 'black'],
            'white': ['白', 'ホワイト', 'white'],
            'red': ['赤', 'レッド', 'red'],
            'blue': ['青', 'ブルー', 'blue'],
            'green': ['緑', 'グリーン', 'green'],
            'yellow': ['黄', 'イエロー', 'yellow'],
            'pink': ['ピンク', 'pink'],
            'purple': ['紫', 'パープル', 'purple'],
            'orange': ['オレンジ', 'orange'],
            'brown': ['茶色', 'ブラウン', 'brown'],
            'gray': ['グレー', 'グレイ', 'gray', 'grey'],
            'silver': ['シルバー', 'silver'],
            'gold': ['ゴールド', 'gold']
        }
        
        # Weight patterns for boxing gloves
        self.weight_patterns = {
            'oz': r'(\d+)\s*(?:oz|オンス|ounce)',
            'g': r'(\d+)\s*(?:g|グラム|gram)',
            'kg': r'(\d+)\s*(?:kg|キログラム|kilogram)'
        }
    
    def parse_product_name(self, raw_name: str) -> str:
        """Parse and clean product name"""
        if not raw_name:
            return ""
        
        # Remove extra whitespace and normalize
        name = re.sub(r'\s+', ' ', raw_name.strip())
        
        # Remove common prefixes/suffixes
        name = re.sub(r'^(NEW|新商品|限定|SALE)\s*', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\s*(在庫あり|在庫なし|予約)$', '', name, flags=re.IGNORECASE)
        
        # Remove product codes at the end
        name = re.sub(r'\s*[\[\(]?[A-Z0-9\-]+[\]\)]?$', '', name)
        
        return name.strip()
    
    def parse_price(self, price_text: str) -> float:
        """Parse price from Japanese text"""
        if not price_text:
            return 0.0
        
        # Remove Japanese currency symbols and text
        price_text = re.sub(r'[¥円税込税別価格定価本体価格]', '', price_text)
        price_text = re.sub(r'[,\s]', '', price_text)
        
        # Extract numeric value
        price_match = re.search(r'(\d+)', price_text)
        if price_match:
            return float(price_match.group(1))
        
        return 0.0
    
    def parse_description(self, raw_description: str) -> str:
        """Parse and clean product description"""
        if not raw_description:
            return ""
        
        # Remove HTML tags if present
        description = re.sub(r'<[^>]+>', '', raw_description)
        
        # Normalize whitespace
        description = re.sub(r'\s+', ' ', description.strip())
        
        # Remove common promotional text
        promotional_patterns = [
            r'送料無料.*?円以上',
            r'平日.*?時までの注文で翌日発送',
            r'代引き手数料.*?円',
            r'クレジットカード.*?可能'
        ]
        
        for pattern in promotional_patterns:
            description = re.sub(pattern, '', description, flags=re.IGNORECASE)
        
        return description.strip()
    
    def extract_size_info(self, text: str) -> List[str]:
        """Extract size information from text"""
        sizes = []
        
        if not text:
            return sizes
        
        text_lower = text.lower()
        
        # Check for each size pattern
        for size, patterns in self.japanese_size_patterns.items():
            for pattern in patterns:
                if pattern.lower() in text_lower:
                    if size not in sizes:
                        sizes.append(size)
                    break
        
        # Look for numeric sizes (for gloves, shoes, etc.)
        numeric_sizes = re.findall(r'(\d+(?:\.\d+)?)\s*(?:cm|センチ|inch|インチ|号)', text)
        for size in numeric_sizes:
            size_str = f"{size}"
            if size_str not in sizes:
                sizes.append(size_str)
        
        return sizes
    
    def extract_color_info(self, text: str) -> List[str]:
        """Extract color information from text"""
        colors = []
        
        if not text:
            return colors
        
        text_lower = text.lower()
        
        # Check for each color pattern
        for color, patterns in self.japanese_color_patterns.items():
            for pattern in patterns:
                if pattern.lower() in text_lower:
                    if color not in colors:
                        colors.append(color)
                    break
        
        return colors
    
    def extract_weight_info(self, text: str) -> Dict[str, str]:
        """Extract weight information (important for boxing gloves)"""
        weight_info = {}
        
        if not text:
            return weight_info
        
        # Check for weight patterns
        for unit, pattern in self.weight_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                weight_info[unit] = matches[0]
        
        return weight_info
    
    def extract_material_info(self, text: str) -> List[str]:
        """Extract material information"""
        materials = []
        
        if not text:
            return materials
        
        # Common materials in Japanese and English
        material_patterns = [
            r'レザー|leather|皮革',
            r'合成皮革|synthetic leather|フェイクレザー',
            r'ナイロン|nylon',
            r'ポリエステル|polyester',
            r'コットン|cotton|綿',
            r'ウール|wool',
            r'ゴム|rubber|ラバー',
            r'フォーム|foam',
            r'メッシュ|mesh',
            r'ビニール|vinyl|PVC'
        ]
        
        text_lower = text.lower()
        
        for pattern in material_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                # Extract the matched material
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    material = match.group(0)
                    if material not in materials:
                        materials.append(material)
        
        return materials
    
    def categorize_product(self, name: str, description: str, url: str = "") -> str:
        """Categorize product based on name, description, and URL"""
        combined_text = f"{name} {description} {url}".lower()
        
        # Boxing equipment
        if any(keyword in combined_text for keyword in [
            'ボクシング', 'boxing', 'グローブ', 'glove', 'パンチング', 'punching'
        ]):
            return 'boxing'
        
        # Martial arts
        elif any(keyword in combined_text for keyword in [
            '格闘技', 'martial', '空手', 'karate', '柔道', 'judo', 
            '柔術', 'jujitsu', 'テコンドー', 'taekwondo'
        ]):
            return 'martial_arts'
        
        # Training equipment
        elif any(keyword in combined_text for keyword in [
            'トレーニング', 'training', 'フィットネス', 'fitness', 
            'ダンベル', 'dumbbell', 'バーベル', 'barbell'
        ]):
            return 'training'
        
        # Protective gear
        elif any(keyword in combined_text for keyword in [
            'プロテクター', 'protector', 'protective', 'ヘッドギア', 'headgear',
            'マウスピース', 'mouthpiece', 'ガード', 'guard'
        ]):
            return 'protective_gear'
        
        # Apparel
        elif any(keyword in combined_text for keyword in [
            'ウェア', 'wear', 'シューズ', 'shoes', 'Tシャツ', 'shirt',
            'パンツ', 'pants', 'ショーツ', 'shorts'
        ]):
            return 'apparel'
        
        # Default category
        else:
            return 'equipment'
    
    def parse_specifications(self, specs_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Parse raw specifications into structured format"""
        parsed_specs = {}
        
        for key, value in specs_dict.items():
            if not value:
                continue
                
            key_lower = key.lower()
            
            # Size specifications
            if any(size_key in key_lower for size_key in ['サイズ', 'size', '寸法']):
                parsed_specs['sizes'] = self.extract_size_info(str(value))
            
            # Color specifications
            elif any(color_key in key_lower for color_key in ['色', 'color', 'カラー']):
                parsed_specs['colors'] = self.extract_color_info(str(value))
            
            # Weight specifications
            elif any(weight_key in key_lower for weight_key in ['重量', 'weight', '重さ']):
                parsed_specs['weight'] = self.extract_weight_info(str(value))
            
            # Material specifications
            elif any(material_key in key_lower for material_key in ['素材', 'material', '材質']):
                parsed_specs['materials'] = self.extract_material_info(str(value))
            
            # Brand specifications
            elif any(brand_key in key_lower for brand_key in ['ブランド', 'brand', 'メーカー']):
                parsed_specs['brand'] = str(value).strip()
            
            # Country of origin
            elif any(origin_key in key_lower for origin_key in ['原産国', 'origin', '製造国']):
                parsed_specs['origin'] = str(value).strip()
            
            # Keep original key-value for other specs
            else:
                parsed_specs[key] = str(value).strip()
        
        return parsed_specs
    
    def normalize_product_data(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize product data for consistency"""
        normalized = {}
        
        # Basic information
        normalized['name'] = self.parse_product_name(product_data.get('name', ''))
        normalized['price'] = self.parse_price(str(product_data.get('price', '')))
        normalized['description'] = self.parse_description(product_data.get('description', ''))
        normalized['category'] = self.categorize_product(
            normalized['name'], 
            normalized['description'], 
            product_data.get('product_url', '')
        )
        
        # Extract additional information from name and description
        combined_text = f"{normalized['name']} {normalized['description']}"
        normalized['sizes'] = self.extract_size_info(combined_text)
        normalized['colors'] = self.extract_color_info(combined_text)
        normalized['weight'] = self.extract_weight_info(combined_text)
        normalized['materials'] = self.extract_material_info(combined_text)
        
        # Parse specifications if available
        if 'specifications' in product_data:
            spec_info = self.parse_specifications(product_data['specifications'])
            normalized.update(spec_info)
        
        # Preserve original fields
        for key in ['brand', 'currency', 'image_url', 'product_url', 'availability']:
            if key in product_data:
                normalized[key] = product_data[key]
        
        # Add timestamp
        normalized['parsed_at'] = datetime.now().isoformat()
        
        return normalized


if __name__ == "__main__":
    # Test the parser
    parser = CenterSPParser()
    
    # Test data
    test_product = {
        'name': 'NEW ボクシンググローブ 16oz レッド [BG-001]',
        'price': '¥15,800円(税込)',
        'description': 'プロ仕様のボクシンググローブ。本革製で耐久性抜群。サイズ：16オンス、カラー：レッド/ブラック',
        'specifications': {
            'サイズ': '16オンス',
            'カラー': 'レッド、ブラック',
            '素材': 'レザー',
            '重量': '16oz'
        }
    }
    
    result = parser.normalize_product_data(test_product)
    
    print("Normalized Product Data:")
    for key, value in result.items():
        print(f"{key}: {value}")