#!/usr/bin/env python3
"""
Data Loader for Content-Personality Analysis
Loads and merges personality data (JSONL) with engagement data (CSV)
"""

import json
import pandas as pd
import numpy as np
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

def load_engagement_data(csv_path: str = "charlie posts_parsed BIG .csv") -> pd.DataFrame:
    """Load engagement data from CSV file"""
    try:
        df = pd.read_csv(csv_path, sep=';', encoding='utf-8')
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(csv_path, sep=';', encoding='latin-1')
        except UnicodeDecodeError:
            df = pd.read_csv(csv_path, sep=';', encoding='cp1252')
    
    # Create post_id to match with personality data (row 3 = post_id 3)
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

def load_and_merge_data() -> pd.DataFrame:
    """Main function to load and merge all data"""
    print("Loading personality data...")
    personality_df = load_personality_data()
    
    print("Loading engagement data...")
    engagement_df = load_engagement_data()
    
    print("Merging datasets...")
    merged_df = pd.merge(personality_df, engagement_df, on='post_id', how='inner')
    
    print("Creating composite scores...")
    merged_df = create_composite_scores(merged_df)
    
    print(f"✅ Loaded {len(merged_df)} posts with complete data")
    print(f"📊 Columns: {list(merged_df.columns)}")
    
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