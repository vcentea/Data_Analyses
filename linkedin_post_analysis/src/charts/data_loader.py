#!/usr/bin/env python3
"""
Data Loader for Content-Personality Analysis
Loads and merges personality data (JSONL) with engagement data (CSV)
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

def load_personality_data(jsonl_path: str = "results.jsonl") -> pd.DataFrame:
    """Load personality data from JSONL file"""
    data = []
    
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                record = json.loads(line)
                
                # Flatten the nested structure
                flat_record = {
                    'post_id': record.get('post_id', ''),
                    'topic_tags': record.get('topic_tags', []),
                    'topic_count': len(record.get('topic_tags', [])),
                }
                
                # Add Big Five traits
                big_five = record.get('big_five', {})
                for trait, score in big_five.items():
                    flat_record[f'big5_{trait}'] = score
                
                # Add Partner traits
                partner = record.get('partner_traits', {})
                for trait, score in partner.items():
                    flat_record[f'partner_{trait}'] = score
                
                # Add flags
                flags = record.get('flags', {})
                for flag, value in flags.items():
                    flat_record[f'flag_{flag}'] = value
                
                # Add evidence (for text analysis later)
                evidence = record.get('evidence', {})
                for trait, text in evidence.items():
                    flat_record[f'evidence_{trait}'] = text
                
                data.append(flat_record)
                
            except json.JSONDecodeError:
                continue
    
    df = pd.DataFrame(data)
    df['post_id'] = df['post_id'].astype(str)
    
    return df

def load_engagement_data(data_path: str = "charlie posts_parsed BIG .csv") -> pd.DataFrame:
    """Load engagement data from CSV or Excel file"""
    file_path = Path(data_path)
    file_ext = file_path.suffix.lower()
    
    if file_ext in ['.xlsx', '.xls']:
        # Load Excel file
        df = pd.read_excel(data_path)
    else:
        # Load CSV file with various encodings and separators
        try:
            df = pd.read_csv(data_path, sep=';', encoding='utf-8')
        except (UnicodeDecodeError, pd.errors.ParserError):
            try:
                df = pd.read_csv(data_path, sep=';', encoding='latin-1')
            except (UnicodeDecodeError, pd.errors.ParserError):
                try:
                    df = pd.read_csv(data_path, sep=';', encoding='cp1252')
                except (UnicodeDecodeError, pd.errors.ParserError):
                    try:
                        df = pd.read_csv(data_path, sep=';', encoding='iso-8859-1')
                    except (UnicodeDecodeError, pd.errors.ParserError):
                        # Try with comma separator as fallback
                        try:
                            df = pd.read_csv(data_path, encoding='utf-8')
                        except UnicodeDecodeError:
                            df = pd.read_csv(data_path, encoding='latin-1')
    
    # Handle different column naming patterns
    if 'post_number' in df.columns:
        # vlad_posts_processed.xlsx format
        df = df.rename(columns={
            'post_number': 'post_id',
            'comment_count': 'comments',
            'like_count': 'likes',
            'combined_engagement': 'combined'
        })
        # Convert float post_id to int then to string (1.0 -> 1 -> '1')
        df['post_id'] = df['post_id'].fillna(0).astype(int).astype(str)
    else:
        # Charlie format - create post_id from row index
        df['post_id'] = (df.index + 3).astype(str)  # Row 0 becomes post_id 3
    
    # Clean engagement data  
    df['comments'] = pd.to_numeric(df['comments'], errors='coerce').fillna(0)
    df['likes'] = pd.to_numeric(df['likes'], errors='coerce').fillna(0) 
    df['combined'] = pd.to_numeric(df['combined'], errors='coerce').fillna(0)
    
    # Calculate engagement metrics
    df['engagement_rate'] = df['combined'] / df['combined'].max() * 100
    df['comment_rate'] = df['comments'] / df['combined'] * 100
    df['like_rate'] = df['likes'] / df['combined'] * 100
    
    return df[['post_id', 'post_text', 'comments', 'likes', 'combined', 
              'engagement_rate', 'comment_rate', 'like_rate']]

def create_composite_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Create composite personality scores"""
    # Partnership Compatibility
    partnership_cols = ['partner_integrity_trust', 'partner_reliability', 'partner_collaboration']
    df['partnership_compatibility'] = df[partnership_cols].mean(axis=1)
    
    # Thought Leadership
    leadership_cols = ['partner_strategic_thinking', 'big5_openness', 'partner_leadership']
    df['thought_leadership'] = df[leadership_cols].mean(axis=1)
    
    # Brand Consistency (inverse of trait volatility)
    trait_cols = [col for col in df.columns if col.startswith(('big5_', 'partner_')) and df[col].dtype in ['int64', 'float64']]
    df['trait_volatility'] = df[trait_cols].std(axis=1)
    df['brand_consistency'] = 5 - df['trait_volatility']  # Inverse relationship
    
    # Professional Risk Score
    risk_weights = {'flag_controversial': 2, 'flag_aggressive_language': 2, 'flag_self_promotion': 1}
    df['professional_risk'] = 0
    for flag, weight in risk_weights.items():
        if flag in df.columns:
            df['professional_risk'] += df[flag].astype(int) * weight
    
    return df

def load_and_merge_data(data_file: str = None) -> pd.DataFrame:
    """Main function to load and merge all data"""
    if not data_file:
        raise ValueError("❌ Error: data_file parameter is required. No dummy data will be generated.")
    
    print(f"Loading data from {data_file}...")
    
    # Validate file exists
    from pathlib import Path
    if not Path(data_file).exists():
        raise FileNotFoundError(f"❌ Error: Data file '{data_file}' not found.")
    
    # Load based on file type
    data_path = Path(data_file).parent
    file_stem = Path(data_file).stem
    
    if data_file.endswith('.jsonl'):
        print("Loading personality data from JSONL...")
        personality_df = load_personality_data(data_file)
        
        # Look for companion engagement data files
        # First try common naming patterns (more specific first)
        companion_files = []
        
        if "results" in file_stem:
            base_name = file_stem.replace("_results", "").replace("results", "")
            companion_files.extend([
                data_path / f"{base_name}_posts_processed.xlsx",
                data_path / f"{base_name}_posts_processed.csv",
                data_path / f"{base_name}_posts.xlsx",
                data_path / f"{base_name}_posts.csv",
                data_path / f"{base_name}posts_parsed.csv",
                data_path / f"{base_name}posts_parsed.xlsx"
            ])
        
        # Then try same name with different extension
        companion_files.extend([
            data_path / f"{file_stem}.csv",
            data_path / f"{file_stem}.xlsx", 
            data_path / f"{file_stem}.xls"
        ])
        
        # Find the first existing companion file
        csv_file = None
        for candidate in companion_files:
            if candidate.exists():
                csv_file = candidate
                break
        
        # If no companion file found, look for any CSV/Excel in the directory
        if csv_file is None:
            csv_files = list(data_path.glob("*.csv")) + list(data_path.glob("*.xlsx")) + list(data_path.glob("*.xls"))
            csv_files = [f for f in csv_files if f.name != Path(data_file).name]  # Exclude the input file
            if csv_files:
                csv_file = csv_files[0]
        
        if csv_file is None:
            raise FileNotFoundError(f"❌ Error: No engagement data file (CSV/Excel) found in {data_path}")
        
        print(f"Loading engagement data from {csv_file}...")
        engagement_df = load_engagement_data(str(csv_file))
            
    elif data_file.endswith(('.csv', '.xlsx', '.xls')):
        print("Loading engagement data from CSV/Excel...")
        engagement_df = load_engagement_data(data_file)
        
        # Look for companion personality data files  
        # First try same name with .jsonl extension
        companion_files = [
            data_path / f"{file_stem}.jsonl"
        ]
        
        # Also try common naming patterns
        if "posts" in file_stem:
            base_name = file_stem.replace("_posts", "").replace("posts", "").replace("_processed", "").replace("_parsed", "")
            companion_files.extend([
                data_path / f"{base_name}_results.jsonl",
                data_path / f"{base_name}results.jsonl",
                data_path / "results.jsonl"
            ])
        
        # Find the first existing companion file
        jsonl_file = None
        for candidate in companion_files:
            if candidate.exists():
                jsonl_file = candidate
                break
        
        # If no companion file found, look for any JSONL in the directory
        if jsonl_file is None:
            jsonl_files = list(data_path.glob("*.jsonl"))
            if jsonl_files:
                jsonl_file = jsonl_files[0]
        
        if jsonl_file is None:
            raise FileNotFoundError(f"❌ Error: No personality data file (JSONL) found in {data_path}")
        
        print(f"Loading personality data from {jsonl_file}...")
        personality_df = load_personality_data(str(jsonl_file))
            
    else:
        raise ValueError(f"❌ Error: Unsupported file format. Expected .jsonl, .csv, .xlsx, or .xls")
    
    print("Merging datasets...")
    merged_df = pd.merge(personality_df, engagement_df, on='post_id', how='inner')
    
    if len(merged_df) == 0:
        raise ValueError("❌ Error: No matching post_id found between personality and engagement data.")
    
    print("Creating composite scores...")
    merged_df = create_composite_scores(merged_df)
    
    print(f"✅ Loaded {len(merged_df)} posts with real data")
    print(f"📊 Data source: {data_file}")
    print(f"📊 Columns: {len(merged_df.columns)} total")
    
    return merged_df

def get_data_summary(df: pd.DataFrame) -> Dict:
    """Get summary statistics for the dataset"""
    summary = {
        'total_posts': len(df),
        'avg_engagement': df['combined'].mean(),
        'top_topics': df['topic_tags'].explode().value_counts().head(5).to_dict(),
        'flag_percentages': {
            'self_promotion': (df['flag_self_promotion'].sum() / len(df) * 100),
            'controversial': (df['flag_controversial'].sum() / len(df) * 100),
            'humble': (df['flag_humility'].sum() / len(df) * 100),
            'aggressive': (df['flag_aggressive_language'].sum() / len(df) * 100),
        },
        'personality_averages': {
            'openness': df['big5_openness'].mean(),
            'conscientiousness': df['big5_conscientiousness'].mean(),
            'extraversion': df['big5_extraversion'].mean(),
            'agreeableness': df['big5_agreeableness'].mean(),
            'neuroticism': df['big5_neuroticism'].mean(),
        },
        'partner_averages': {
            'integrity_trust': df['partner_integrity_trust'].mean(),
            'reliability': df['partner_reliability'].mean(),
            'collaboration': df['partner_collaboration'].mean(),
            'adaptability': df['partner_adaptability'].mean(),
            'risk_tolerance': df['partner_risk_tolerance'].mean(),
            'strategic_thinking': df['partner_strategic_thinking'].mean(),
            'leadership': df['partner_leadership'].mean(),
        }
    }
    
    return summary

if __name__ == "__main__":
    # Test the data loading
    df = load_and_merge_data()
    summary = get_data_summary(df)
    
    print("\n📈 Data Summary:")
    print(f"Total posts: {summary['total_posts']}")
    print(f"Average engagement: {summary['avg_engagement']:.0f}")
    print(f"Self-promotion: {summary['flag_percentages']['self_promotion']:.1f}%")
    print(f"Controversial: {summary['flag_percentages']['controversial']:.1f}%") 