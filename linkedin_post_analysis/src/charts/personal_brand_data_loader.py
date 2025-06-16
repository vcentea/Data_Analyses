#!/usr/bin/env python3
"""
Personal Brand Data Loader
Handles data processing and schema definitions for personal brand analysis
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PersonalBrandDataLoader:
    """
    Data loader and processor for personal brand analysis
    """
    
    def __init__(self):
        """Initialize the data loader with schema definitions"""
        self.brand_personality_traits = [
            'authenticity', 'consistency', 'expertise_demonstration', 
            'thought_leadership', 'relatability'
        ]
        
        self.customer_acquisition_traits = [
            'trust_building', 'value_delivery', 'call_to_action_effectiveness', 
            'social_proof', 'audience_engagement'
        ]
        
        self.growth_indicators = [
            'follower_growth_catalyst', 'viral_potential', 'shareability', 
            'conversion_intent', 'brand_recall'
        ]
        
        self.content_categories = [
            'educational', 'promotional', 'personal_story', 'industry_insights',
            'product_showcase', 'behind_scenes', 'testimonials', 'trending_topics'
        ]
        
        self.behavioral_flags = [
            'over_promotion', 'authenticity_gaps', 'audience_disconnect', 
            'controversial_content'
        ]
        
        self.all_metrics = (
            self.brand_personality_traits + 
            self.customer_acquisition_traits + 
            self.growth_indicators + 
            self.behavioral_flags
        )
        
        self.data = None
        self.processed_data = {}
    
    def _map_psychological_to_brand_metrics(self):
        """Map psychological traits to personal brand metrics"""
        if self.data is None:
            return
        
        # Brand Personality Traits (derived from Big Five + flags)
        if 'big_five.conscientiousness' in self.data.columns:
            self.data['authenticity'] = (self.data['big_five.conscientiousness'] + 
                                        (5 - self.data.get('flags.self_promotion', 0).astype(int))) / 2
        
        if 'big_five.conscientiousness' in self.data.columns:
            self.data['consistency'] = self.data['big_five.conscientiousness']
        
        if 'big_five.openness' in self.data.columns:
            self.data['expertise_demonstration'] = (self.data['big_five.openness'] + 
                                                   self.data.get('partner_traits.strategic_thinking', 3)) / 2
        
        if 'partner_traits.leadership' in self.data.columns:
            self.data['thought_leadership'] = self.data['partner_traits.leadership']
        
        if 'big_five.agreeableness' in self.data.columns:
            self.data['relatability'] = (self.data['big_five.agreeableness'] + 
                                        self.data.get('flags.humility', 0).astype(int)) / 2
        
        # Customer Acquisition Traits (derived from partner traits)
        if 'partner_traits.integrity_trust' in self.data.columns:
            self.data['trust_building'] = self.data['partner_traits.integrity_trust']
        
        if 'partner_traits.reliability' in self.data.columns:
            self.data['value_delivery'] = self.data['partner_traits.reliability']
        
        if 'big_five.extraversion' in self.data.columns:
            self.data['call_to_action_effectiveness'] = self.data['big_five.extraversion']
        
        if 'partner_traits.integrity_trust' in self.data.columns:
            self.data['social_proof'] = (self.data['partner_traits.integrity_trust'] + 
                                        self.data.get('partner_traits.reliability', 3)) / 2
        
        if 'big_five.extraversion' in self.data.columns:
            self.data['audience_engagement'] = (self.data['big_five.extraversion'] + 
                                              self.data.get('big_five.agreeableness', 3)) / 2
        
        # Growth Indicators (estimated from traits)
        if 'big_five.extraversion' in self.data.columns:
            self.data['follower_growth_catalyst'] = (self.data['big_five.extraversion'] + 
                                                    self.data.get('partner_traits.leadership', 3)) / 2
        
        if 'big_five.openness' in self.data.columns:
            self.data['viral_potential'] = (self.data['big_five.openness'] + 
                                          (5 - self.data.get('flags.controversial', 0).astype(int))) / 2
        
        if 'big_five.agreeableness' in self.data.columns:
            self.data['shareability'] = self.data['big_five.agreeableness']
        
        if 'partner_traits.strategic_thinking' in self.data.columns:
            self.data['conversion_intent'] = self.data['partner_traits.strategic_thinking']
        
        if 'big_five.conscientiousness' in self.data.columns:
            self.data['brand_recall'] = self.data['big_five.conscientiousness']
        
        # Content Categories (basic mapping - could be enhanced with topic analysis)
        self.data['educational'] = 1  # Default baseline
        self.data['promotional'] = self.data.get('flags.self_promotion', 0).astype(int)
        self.data['personal_story'] = self.data.get('flags.humility', 0).astype(int)
        self.data['industry_insights'] = (self.data.get('big_five.openness', 3) > 3.5).astype(int)
        self.data['product_showcase'] = self.data.get('flags.self_promotion', 0).astype(int)
        self.data['behind_scenes'] = self.data.get('flags.humility', 0).astype(int)
        self.data['testimonials'] = (self.data.get('partner_traits.integrity_trust', 3) > 4).astype(int)
        self.data['trending_topics'] = (self.data.get('big_five.openness', 3) > 4).astype(int)
        
        # Behavioral Flags (derived from existing flags)
        self.data['over_promotion'] = self.data.get('flags.self_promotion', 0).astype(int)
        self.data['authenticity_gaps'] = (5 - self.data.get('big_five.conscientiousness', 3)).clip(0, 5)
        self.data['audience_disconnect'] = (5 - self.data.get('big_five.agreeableness', 3)).clip(0, 5)
        self.data['controversial_content'] = self.data.get('flags.controversial', 0).astype(int)
        
        logger.info("Successfully mapped psychological traits to personal brand metrics")
        
    def load_data(self, data_file: str) -> pd.DataFrame:
        """
        Load data from various file formats
        
        Args:
            data_file: Path to the data file (CSV, Excel, JSON, JSONL)
            
        Returns:
            pd.DataFrame: Loaded data
        """
        try:
            file_path = Path(data_file)
            file_ext = file_path.suffix.lower()
            
            logger.info(f"Loading data from {data_file} (format: {file_ext})")
            
            if file_ext == '.csv':
                self.data = pd.read_csv(data_file)
            elif file_ext in ['.xlsx', '.xls']:
                self.data = pd.read_excel(data_file)
            elif file_ext == '.json':
                with open(data_file, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                self.data = pd.json_normalize(json_data)
            elif file_ext == '.jsonl':
                json_lines = []
                with open(data_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            json_lines.append(json.loads(line))
                self.data = pd.json_normalize(json_lines)
                
                # Map existing psychological traits to personal brand metrics
                self._map_psychological_to_brand_metrics()
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")
            
            logger.info(f"Successfully loaded {len(self.data)} records")
            return self.data
            
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            raise
    
    def validate_data_schema(self) -> Dict[str, bool]:
        """
        Validate that the loaded data contains required columns
        
        Returns:
            Dict[str, bool]: Validation results for each metric category
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        validation_results = {}
        columns = self.data.columns.tolist()
        
        # Check brand personality traits
        brand_traits_present = [col for col in self.brand_personality_traits if col in columns]
        validation_results['brand_personality_traits'] = len(brand_traits_present) > 0
        
        # Check customer acquisition traits
        acquisition_traits_present = [col for col in self.customer_acquisition_traits if col in columns]
        validation_results['customer_acquisition_traits'] = len(acquisition_traits_present) > 0
        
        # Check growth indicators
        growth_indicators_present = [col for col in self.growth_indicators if col in columns]
        validation_results['growth_indicators'] = len(growth_indicators_present) > 0
        
        # Check content categories
        content_categories_present = [col for col in self.content_categories if col in columns]
        validation_results['content_categories'] = len(content_categories_present) > 0
        
        # Check behavioral flags
        behavioral_flags_present = [col for col in self.behavioral_flags if col in columns]
        validation_results['behavioral_flags'] = len(behavioral_flags_present) > 0
        
        # Check for timestamp/date column
        date_columns = ['date', 'timestamp', 'created_at', 'post_date', 'published_date']
        date_col_present = any(col in columns for col in date_columns)
        validation_results['date_column'] = date_col_present
        
        logger.info(f"Schema validation results: {validation_results}")
        return validation_results
    
    def prepare_time_series_data(self, date_column: str = None) -> pd.DataFrame:
        """
        Prepare data for time-series analysis
        
        Args:
            date_column: Name of the date column (auto-detected if None)
            
        Returns:
            pd.DataFrame: Data with proper datetime index
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        # Auto-detect date column if not provided
        if date_column is None:
            date_columns = ['date', 'timestamp', 'created_at', 'post_date', 'published_date']
            for col in date_columns:
                if col in self.data.columns:
                    date_column = col
                    break
        
        if date_column is None or date_column not in self.data.columns:
            logger.warning("No date column found. Creating artificial time periods.")
            # Create artificial time periods based on row order
            self.data['time_period'] = pd.cut(range(len(self.data)), bins=5, labels=['Q1', 'Q2', 'Q3', 'Q4', 'Recent'])
            return self.data
        
        # Convert to datetime
        self.data[date_column] = pd.to_datetime(self.data[date_column])
        self.data = self.data.sort_values(date_column)
        
        # Create time periods
        date_range = self.data[date_column].max() - self.data[date_column].min()
        period_length = date_range / 5
        
        self.data['time_period'] = pd.cut(
            self.data[date_column], 
            bins=5, 
            labels=['Historical_1', 'Historical_2', 'Mid_Period', 'Recent_1', 'Recent']
        )
        
        logger.info("Time series data prepared successfully")
        return self.data
    
    def calculate_correlation_matrix(self, metrics: List[str] = None) -> pd.DataFrame:
        """
        Calculate correlation matrix for brand and growth metrics
        
        Args:
            metrics: List of metrics to include (uses default set if None)
            
        Returns:
            pd.DataFrame: Correlation matrix
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        if metrics is None:
            # Use core metrics for correlation analysis
            core_metrics = [
                'authenticity', 'consistency', 'expertise_demonstration',
                'trust_building', 'value_delivery', 'audience_engagement',
                'follower_growth_catalyst', 'conversion_intent'
            ]
            # Filter to only include metrics that exist in the data
            metrics = [m for m in core_metrics if m in self.data.columns]
        
        if len(metrics) < 2:
            logger.warning("Insufficient metrics for correlation analysis")
            return pd.DataFrame()
        
        correlation_matrix = self.data[metrics].corr()
        
        logger.info(f"Correlation matrix calculated for {len(metrics)} metrics")
        return correlation_matrix
    
    def calculate_kpi_scores(self) -> Dict[str, float]:
        """
        Calculate KPI scores for the dashboard
        
        Returns:
            Dict[str, float]: KPI scores as percentages
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        kpi_scores = {}
        
        # Brand Authenticity Score
        authenticity_metrics = ['authenticity', 'consistency', 'relatability']
        available_auth_metrics = [m for m in authenticity_metrics if m in self.data.columns]
        if available_auth_metrics:
            kpi_scores['brand_authenticity_score'] = self.data[available_auth_metrics].mean().mean() * 20  # Scale to 0-100
        
        # Growth Execution Rate
        growth_metrics = ['follower_growth_catalyst', 'viral_potential', 'conversion_intent']
        available_growth_metrics = [m for m in growth_metrics if m in self.data.columns]
        if available_growth_metrics:
            kpi_scores['growth_execution_rate'] = self.data[available_growth_metrics].mean().mean() * 20
        
        # Content Authority Level
        authority_metrics = ['expertise_demonstration', 'thought_leadership', 'value_delivery']
        available_authority_metrics = [m for m in authority_metrics if m in self.data.columns]
        if available_authority_metrics:
            kpi_scores['content_authority_level'] = self.data[available_authority_metrics].mean().mean() * 20
        
        # Customer Acquisition Readiness
        acquisition_metrics = ['trust_building', 'call_to_action_effectiveness', 'social_proof']
        available_acquisition_metrics = [m for m in acquisition_metrics if m in self.data.columns]
        if available_acquisition_metrics:
            kpi_scores['customer_acquisition_readiness'] = self.data[available_acquisition_metrics].mean().mean() * 20
        
        # Audience Engagement Quality
        engagement_metrics = ['audience_engagement', 'shareability', 'brand_recall']
        available_engagement_metrics = [m for m in engagement_metrics if m in self.data.columns]
        if available_engagement_metrics:
            kpi_scores['audience_engagement_quality'] = self.data[available_engagement_metrics].mean().mean() * 20
        
        # Brand Risk Score (lower is better)
        risk_metrics = ['over_promotion', 'authenticity_gaps', 'audience_disconnect', 'controversial_content']
        available_risk_metrics = [m for m in risk_metrics if m in self.data.columns]
        if available_risk_metrics:
            kpi_scores['brand_risk_score'] = self.data[available_risk_metrics].mean().mean() * 20
        
        logger.info(f"KPI scores calculated: {list(kpi_scores.keys())}")
        return kpi_scores
    
    def calculate_trend_changes(self) -> Dict[str, float]:
        """
        Calculate trend changes between historical and recent periods
        
        Returns:
            Dict[str, float]: Percentage changes for key metrics
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        if 'time_period' not in self.data.columns:
            self.prepare_time_series_data()
        
        trend_changes = {}
        
        # Define metrics to track
        trend_metrics = {
            'thought_leadership': 'thought_leadership',
            'authenticity_gaps': 'authenticity_gaps',
            'conversion_intent': 'conversion_intent',
            'over_promotion': 'over_promotion',
            'audience_engagement': 'audience_engagement',
            'viral_potential': 'viral_potential'
        }
        
        # Calculate changes between historical and recent periods
        historical_data = self.data[self.data['time_period'].isin(['Historical_1', 'Historical_2'])]
        recent_data = self.data[self.data['time_period'].isin(['Recent_1', 'Recent'])]
        
        for metric_name, column_name in trend_metrics.items():
            if column_name in self.data.columns:
                historical_avg = historical_data[column_name].mean() if len(historical_data) > 0 else 0
                recent_avg = recent_data[column_name].mean() if len(recent_data) > 0 else 0
                
                if historical_avg > 0:
                    change_percent = ((recent_avg - historical_avg) / historical_avg) * 100
                else:
                    change_percent = 0
                
                trend_changes[metric_name] = round(change_percent, 1)
        
        logger.info(f"Trend changes calculated for {len(trend_changes)} metrics")
        return trend_changes
    
    def calculate_brand_growth_potential_score(self) -> Dict[str, float]:
        """
        Calculate overall Brand Growth Potential Score (out of 100)
        
        Returns:
            Dict[str, float]: Overall score and component scores
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        component_scores = {}
        
        # Brand authenticity and consistency (25%)
        auth_metrics = ['authenticity', 'consistency']
        available_auth = [m for m in auth_metrics if m in self.data.columns]
        if available_auth:
            component_scores['brand_authenticity_consistency'] = self.data[available_auth].mean().mean() * 20
        else:
            component_scores['brand_authenticity_consistency'] = 0
        
        # Customer acquisition effectiveness (25%)
        acq_metrics = ['trust_building', 'value_delivery', 'call_to_action_effectiveness']
        available_acq = [m for m in acq_metrics if m in self.data.columns]
        if available_acq:
            component_scores['customer_acquisition_effectiveness'] = self.data[available_acq].mean().mean() * 20
        else:
            component_scores['customer_acquisition_effectiveness'] = 0
        
        # Content authority and expertise (25%)
        auth_metrics = ['expertise_demonstration', 'thought_leadership']
        available_auth = [m for m in auth_metrics if m in self.data.columns]
        if available_auth:
            component_scores['content_authority_expertise'] = self.data[available_auth].mean().mean() * 20
        else:
            component_scores['content_authority_expertise'] = 0
        
        # Growth momentum and viral potential (25%)
        growth_metrics = ['follower_growth_catalyst', 'viral_potential', 'conversion_intent']
        available_growth = [m for m in growth_metrics if m in self.data.columns]
        if available_growth:
            component_scores['growth_momentum_viral_potential'] = self.data[available_growth].mean().mean() * 20
        else:
            component_scores['growth_momentum_viral_potential'] = 0
        
        # Calculate overall score (weighted average)
        overall_score = sum(component_scores.values()) / 4
        
        result = {
            'overall_score': round(overall_score, 1),
            **{k: round(v, 1) for k, v in component_scores.items()}
        }
        
        logger.info(f"Brand Growth Potential Score: {result['overall_score']}/100")
        return result
    
    def get_content_category_distribution(self) -> Dict[str, int]:
        """
        Get distribution of content categories
        
        Returns:
            Dict[str, int]: Category counts
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        category_distribution = {}
        
        for category in self.content_categories:
            if category in self.data.columns:
                # Assuming binary indicators (1/0) or boolean values
                category_distribution[category] = int(self.data[category].sum())
        
        logger.info(f"Content category distribution calculated for {len(category_distribution)} categories")
        return category_distribution
    
    def calculate_risk_assessment(self) -> Dict[str, float]:
        """
        Calculate risk assessment metrics
        
        Returns:
            Dict[str, float]: Risk percentages for each behavioral flag
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        risk_assessment = {}
        total_posts = len(self.data)
        
        for flag in self.behavioral_flags:
            if flag in self.data.columns:
                flag_count = self.data[flag].sum()
                risk_percentage = (flag_count / total_posts) * 100 if total_posts > 0 else 0
                risk_assessment[flag] = round(risk_percentage, 1)
        
        logger.info(f"Risk assessment calculated for {len(risk_assessment)} behavioral flags")
        return risk_assessment
    
    def get_processed_data_summary(self) -> Dict[str, any]:
        """
        Get a comprehensive summary of all processed data
        
        Returns:
            Dict[str, any]: Complete data summary for dashboard
        """
        if self.data is None:
            raise ValueError("No data loaded. Call load_data() first.")
        
        summary = {
            'total_posts': len(self.data),
            'date_range': self._get_date_range(),
            'kpi_scores': self.calculate_kpi_scores(),
            'trend_changes': self.calculate_trend_changes(),
            'brand_growth_score': self.calculate_brand_growth_potential_score(),
            'content_distribution': self.get_content_category_distribution(),
            'risk_assessment': self.calculate_risk_assessment(),
            'correlation_matrix': self.calculate_correlation_matrix().to_dict(),
            'available_metrics': [col for col in self.all_metrics if col in self.data.columns]
        }
        
        logger.info("Complete data summary generated")
        return summary
    
    def _get_date_range(self) -> Dict[str, str]:
        """Get date range information"""
        date_columns = ['date', 'timestamp', 'created_at', 'post_date', 'published_date']
        
        for col in date_columns:
            if col in self.data.columns:
                try:
                    dates = pd.to_datetime(self.data[col])
                    return {
                        'start_date': dates.min().strftime('%Y-%m-%d'),
                        'end_date': dates.max().strftime('%Y-%m-%d'),
                        'date_column': col
                    }
                except:
                    continue
        
        return {
            'start_date': 'Unknown',
            'end_date': 'Unknown',
            'date_column': 'None'
        }

def load_personal_brand_data(data_file: str) -> PersonalBrandDataLoader:
    """
    Convenience function to load and process personal brand data
    
    Args:
        data_file: Path to the data file
        
    Returns:
        PersonalBrandDataLoader: Loaded and processed data
    """
    loader = PersonalBrandDataLoader()
    loader.load_data(data_file)
    loader.validate_data_schema()
    loader.prepare_time_series_data()
    
    return loader 