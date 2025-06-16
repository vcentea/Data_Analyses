#!/usr/bin/env python3
"""
Personal Brand Analysis - Main Module
Coordinates all personal brand analysis functions and generates the dashboard
"""

import os
import sys
from pathlib import Path
import logging
from typing import Dict, List, Optional

# Add the parent directory to the path to import other modules
sys.path.append(str(Path(__file__).parent))

from personal_brand_data_loader import PersonalBrandDataLoader, load_personal_brand_data
from personal_brand_charts import generate_personal_brand_charts

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PersonalBrandAnalyzer:
    """
    Main analyzer class for personal brand analysis
    """
    
    def __init__(self, data_file: str):
        """
        Initialize the analyzer with data
        
        Args:
            data_file: Path to the data file
        """
        self.data_file = data_file
        self.data_loader = None
        self.analysis_results = {}
        
    def load_and_process_data(self) -> bool:
        """
        Load and process the data
        
        Returns:
            bool: Success status
        """
        try:
            logger.info(f"Loading personal brand data from {self.data_file}")
            self.data_loader = load_personal_brand_data(self.data_file)
            
            # Validate data schema
            validation_results = self.data_loader.validate_data_schema()
            
            if not any(validation_results.values()):
                logger.error("Data validation failed - no required metrics found")
                return False
            
            logger.info("Data loaded and validated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            return False
    
    def run_comprehensive_analysis(self) -> Dict[str, any]:
        """
        Run comprehensive personal brand analysis
        
        Returns:
            Dict[str, any]: Complete analysis results
        """
        if self.data_loader is None:
            raise ValueError("Data not loaded. Call load_and_process_data() first.")
        
        logger.info("Running comprehensive personal brand analysis")
        
        try:
            # Get complete data summary
            self.analysis_results = self.data_loader.get_processed_data_summary()
            
            # Add additional analysis components
            self.analysis_results.update({
                'chart_data': self._prepare_chart_data(),
                'insights': self._generate_insights(),
                'recommendations': self._generate_recommendations()
            })
            
            logger.info("Comprehensive analysis completed successfully")
            return self.analysis_results
            
        except Exception as e:
            logger.error(f"Error during analysis: {str(e)}")
            raise
    
    def _prepare_chart_data(self) -> Dict[str, any]:
        """
        Prepare data specifically formatted for charts
        
        Returns:
            Dict[str, any]: Chart-ready data
        """
        chart_data = {}
        
        # Chart 1: Growth Metrics Trend Analysis
        chart_data['growth_metrics_trend'] = self._prepare_growth_trend_data()
        
        # Chart 2: Brand & Growth Correlation Matrix
        chart_data['correlation_matrix'] = self._prepare_correlation_data()
        
        # Chart 3: Customer Acquisition Traits Radar
        chart_data['acquisition_radar'] = self._prepare_acquisition_radar_data()
        
        # Chart 4: Brand Growth Evolution Timeline
        chart_data['evolution_timeline'] = self._prepare_evolution_timeline_data()
        
        # Chart 5: Personal Brand Personality Profile
        chart_data['personality_profile'] = self._prepare_personality_profile_data()
        
        # Chart 6: Growth vs Brand Risk Analysis
        chart_data['risk_vs_growth'] = self._prepare_risk_growth_scatter_data()
        
        # Chart 7: Content Strategy Distribution
        chart_data['content_distribution'] = self._prepare_content_distribution_data()
        
        # Chart 8: Brand Evolution Over Time
        chart_data['brand_evolution'] = self._prepare_brand_evolution_data()
        
        # Chart 9: Brand Risk Indicators
        chart_data['risk_indicators'] = self._prepare_risk_indicators_data()
        
        # Chart 10: Audience Engagement Evolution
        chart_data['engagement_evolution'] = self._prepare_engagement_evolution_data()
        
        # Chart 11: Growth KPIs vs Industry Benchmarks
        chart_data['kpi_benchmarks'] = self._prepare_benchmark_data()
        
        # Chart 12: Customer Acquisition Readiness Breakdown
        chart_data['acquisition_readiness'] = self._prepare_acquisition_readiness_data()
        
        return chart_data
    
    def _prepare_growth_trend_data(self) -> Dict[str, any]:
        """Prepare data for growth metrics trend chart"""
        if self.data_loader.data is None:
            return {}
        
        growth_metrics = ['follower_growth_catalyst', 'viral_potential', 'conversion_intent', 'brand_recall', 'audience_engagement']
        available_metrics = [m for m in growth_metrics if m in self.data_loader.data.columns]
        
        if not available_metrics:
            return {}
        
        # Calculate historical vs recent averages
        historical_data = self.data_loader.data[self.data_loader.data['time_period'].isin(['Historical_1', 'Historical_2'])]
        recent_data = self.data_loader.data[self.data_loader.data['time_period'].isin(['Recent_1', 'Recent'])]
        
        chart_data = {
            'labels': [m.replace('_', ' ').title() for m in available_metrics],
            'historical': [],
            'recent': [],
            'changes': []
        }
        
        for metric in available_metrics:
            hist_avg = historical_data[metric].mean() if len(historical_data) > 0 else 0
            recent_avg = recent_data[metric].mean() if len(recent_data) > 0 else 0
            change = ((recent_avg - hist_avg) / hist_avg * 100) if hist_avg > 0 else 0
            
            chart_data['historical'].append(round(hist_avg * 20, 1))  # Scale to 0-100
            chart_data['recent'].append(round(recent_avg * 20, 1))
            chart_data['changes'].append(round(change, 1))
        
        return chart_data
    
    def _prepare_correlation_data(self) -> Dict[str, any]:
        """Prepare data for correlation matrix heatmap"""
        correlation_matrix = self.data_loader.calculate_correlation_matrix()
        
        if correlation_matrix.empty:
            return {}
        
        return {
            'labels': correlation_matrix.columns.tolist(),
            'data': correlation_matrix.values.tolist()
        }
    
    def _prepare_acquisition_radar_data(self) -> Dict[str, any]:
        """Prepare data for customer acquisition traits radar"""
        acquisition_traits = ['trust_building', 'value_delivery', 'social_proof', 'call_to_action_effectiveness', 
                             'audience_engagement', 'expertise_demonstration', 'thought_leadership']
        
        available_traits = [t for t in acquisition_traits if t in self.data_loader.data.columns]
        
        if not available_traits:
            return {}
        
        chart_data = {
            'labels': [t.replace('_', ' ').title() for t in available_traits],
            'data': [],
            'benchmarks': []
        }
        
        for trait in available_traits:
            avg_score = self.data_loader.data[trait].mean() * 20  # Scale to 0-100
            benchmark = 75  # Optimal benchmark
            
            chart_data['data'].append(round(avg_score, 1))
            chart_data['benchmarks'].append(benchmark)
        
        return chart_data
    
    def _prepare_evolution_timeline_data(self) -> Dict[str, any]:
        """Prepare data for brand growth evolution timeline"""
        if 'time_period' not in self.data_loader.data.columns:
            return {}
        
        evolution_metrics = ['authenticity', 'consistency', 'thought_leadership']
        available_metrics = [m for m in evolution_metrics if m in self.data_loader.data.columns]
        
        if not available_metrics:
            return {}
        
        time_periods = ['Historical_1', 'Historical_2', 'Mid_Period', 'Recent_1', 'Recent']
        
        chart_data = {
            'labels': ['Q1', 'Q2', 'Q3', 'Q4', 'Recent'],
            'datasets': []
        }
        
        for metric in available_metrics:
            metric_data = []
            for period in time_periods:
                period_data = self.data_loader.data[self.data_loader.data['time_period'] == period]
                avg_score = period_data[metric].mean() * 20 if len(period_data) > 0 else 0
                metric_data.append(round(avg_score, 1))
            
            chart_data['datasets'].append({
                'label': metric.replace('_', ' ').title(),
                'data': metric_data
            })
        
        return chart_data
    
    def _prepare_personality_profile_data(self) -> Dict[str, any]:
        """Prepare data for personal brand personality profile"""
        personality_traits = ['authenticity', 'expertise_demonstration', 'relatability', 'consistency', 'thought_leadership']
        available_traits = [t for t in personality_traits if t in self.data_loader.data.columns]
        
        if not available_traits:
            return {}
        
        chart_data = {
            'labels': [t.replace('_', ' ').title() for t in available_traits],
            'data': []
        }
        
        for trait in available_traits:
            avg_score = self.data_loader.data[trait].mean() * 20  # Scale to 0-100
            chart_data['data'].append(round(avg_score, 1))
        
        return chart_data
    
    def _prepare_risk_growth_scatter_data(self) -> Dict[str, any]:
        """Prepare data for growth vs brand risk scatter plot"""
        risk_metrics = ['over_promotion', 'authenticity_gaps', 'audience_disconnect']
        growth_metrics = ['viral_potential', 'conversion_intent', 'follower_growth_catalyst']
        
        available_risk = [m for m in risk_metrics if m in self.data_loader.data.columns]
        available_growth = [m for m in growth_metrics if m in self.data_loader.data.columns]
        
        if not available_risk or not available_growth:
            return {}
        
        # Calculate aggregate risk and growth scores
        risk_score = self.data_loader.data[available_risk].mean(axis=1) * 100
        growth_score = self.data_loader.data[available_growth].mean(axis=1) * 100
        
        chart_data = {
            'data': [{'x': r, 'y': g} for r, g in zip(risk_score, growth_score)]
        }
        
        return chart_data
    
    def _prepare_content_distribution_data(self) -> Dict[str, any]:
        """Prepare data for content strategy distribution"""
        content_distribution = self.data_loader.get_content_category_distribution()
        
        if not content_distribution:
            return {}
        
        total_posts = sum(content_distribution.values())
        
        chart_data = {
            'labels': [k.replace('_', ' ').title() for k in content_distribution.keys()],
            'data': list(content_distribution.values()),
            'percentages': [round((v/total_posts)*100, 1) for v in content_distribution.values()]
        }
        
        return chart_data
    
    def _prepare_brand_evolution_data(self) -> Dict[str, any]:
        """Prepare data for brand evolution over time"""
        if 'time_period' not in self.data_loader.data.columns:
            return {}
        
        content_types = ['educational', 'promotional', 'personal_story', 'industry_insights']
        available_types = [t for t in content_types if t in self.data_loader.data.columns]
        
        if not available_types:
            return {}
        
        time_periods = ['Historical_1', 'Historical_2', 'Mid_Period', 'Recent_1', 'Recent']
        
        chart_data = {
            'labels': ['Q1', 'Q2', 'Q3', 'Q4', 'Recent'],
            'datasets': []
        }
        
        for content_type in available_types:
            type_data = []
            for period in time_periods:
                period_data = self.data_loader.data[self.data_loader.data['time_period'] == period]
                if len(period_data) > 0:
                    percentage = (period_data[content_type].sum() / len(period_data)) * 100
                else:
                    percentage = 0
                type_data.append(round(percentage, 1))
            
            chart_data['datasets'].append({
                'label': content_type.replace('_', ' ').title(),
                'data': type_data
            })
        
        return chart_data
    
    def _prepare_risk_indicators_data(self) -> Dict[str, any]:
        """Prepare data for brand risk indicators"""
        risk_assessment = self.data_loader.calculate_risk_assessment()
        
        if not risk_assessment:
            return {}
        
        chart_data = {
            'labels': [k.replace('_', ' ').title() for k in risk_assessment.keys()],
            'data': list(risk_assessment.values()),
            'colors': ['#ff6b6b' if v > 20 else '#ffd93d' if v > 10 else '#6bcf7f' for v in risk_assessment.values()]
        }
        
        return chart_data
    
    def _prepare_engagement_evolution_data(self) -> Dict[str, any]:
        """Prepare data for audience engagement evolution bubble chart"""
        if 'time_period' not in self.data_loader.data.columns:
            return {}
        
        engagement_col = 'audience_engagement'
        conversion_col = 'conversion_intent'
        
        if engagement_col not in self.data_loader.data.columns or conversion_col not in self.data_loader.data.columns:
            return {}
        
        # Group by time period
        historical_data = self.data_loader.data[self.data_loader.data['time_period'].isin(['Historical_1', 'Historical_2'])]
        recent_data = self.data_loader.data[self.data_loader.data['time_period'].isin(['Recent_1', 'Recent'])]
        
        chart_data = {
            'datasets': [
                {
                    'label': 'Historical',
                    'data': [{
                        'x': historical_data[engagement_col].mean() * 100,
                        'y': historical_data[conversion_col].mean() * 100,
                        'r': len(historical_data) / 10  # Bubble size based on content volume
                    }]
                },
                {
                    'label': 'Recent',
                    'data': [{
                        'x': recent_data[engagement_col].mean() * 100,
                        'y': recent_data[conversion_col].mean() * 100,
                        'r': len(recent_data) / 10
                    }]
                }
            ]
        }
        
        return chart_data
    
    def _prepare_benchmark_data(self) -> Dict[str, any]:
        """Prepare data for KPIs vs industry benchmarks"""
        kpi_metrics = ['authenticity', 'follower_growth_catalyst', 'expertise_demonstration', 
                      'trust_building', 'audience_engagement']
        available_metrics = [m for m in kpi_metrics if m in self.data_loader.data.columns]
        
        if not available_metrics:
            return {}
        
        chart_data = {
            'labels': [m.replace('_', ' ').title() for m in available_metrics],
            'actual': [],
            'benchmarks': []
        }
        
        benchmarks = {
            'authenticity': 80,
            'follower_growth_catalyst': 70,
            'expertise_demonstration': 85,
            'trust_building': 75,
            'audience_engagement': 65
        }
        
        for metric in available_metrics:
            actual_score = self.data_loader.data[metric].mean() * 20  # Scale to 0-100
            benchmark_score = benchmarks.get(metric, 75)
            
            chart_data['actual'].append(round(actual_score, 1))
            chart_data['benchmarks'].append(benchmark_score)
        
        return chart_data
    
    def _prepare_acquisition_readiness_data(self) -> Dict[str, any]:
        """Prepare data for customer acquisition readiness breakdown"""
        readiness_components = {
            'Trust Building': ['trust_building', 'authenticity'],
            'Value Delivery': ['value_delivery', 'expertise_demonstration'],
            'Social Proof': ['social_proof', 'audience_engagement'],
            'Content Quality': ['thought_leadership', 'consistency'],
            'Conversion Optimization': ['call_to_action_effectiveness', 'conversion_intent']
        }
        
        chart_data = {
            'labels': list(readiness_components.keys()),
            'data': []
        }
        
        for component, metrics in readiness_components.items():
            available_metrics = [m for m in metrics if m in self.data_loader.data.columns]
            if available_metrics:
                component_score = self.data_loader.data[available_metrics].mean().mean() * 20
                chart_data['data'].append(round(component_score, 1))
            else:
                chart_data['data'].append(0)
        
        return chart_data
    
    def _generate_insights(self) -> Dict[str, List[str]]:
        """Generate automated insights"""
        insights = {
            'strong_correlations': [],
            'acquisition_strengths': [],
            'growth_opportunities': [],
            'risk_mitigation': []
        }
        
        # Strong Brand Correlations
        correlation_matrix = self.data_loader.calculate_correlation_matrix()
        if not correlation_matrix.empty:
            # Find strongest correlations
            correlations = []
            for i in range(len(correlation_matrix.columns)):
                for j in range(i+1, len(correlation_matrix.columns)):
                    corr_value = correlation_matrix.iloc[i, j]
                    if abs(corr_value) > 0.5:  # Strong correlation threshold
                        correlations.append((
                            correlation_matrix.columns[i],
                            correlation_matrix.columns[j],
                            corr_value
                        ))
            
            correlations.sort(key=lambda x: abs(x[2]), reverse=True)
            for metric1, metric2, corr in correlations[:3]:
                direction = "positively" if corr > 0 else "negatively"
                insights['strong_correlations'].append(
                    f"{metric1.replace('_', ' ').title()} is {direction} correlated with {metric2.replace('_', ' ').title()} (r={corr:.2f})"
                )
        
        # Customer Acquisition Strengths
        kpi_scores = self.data_loader.calculate_kpi_scores()
        if 'customer_acquisition_readiness' in kpi_scores:
            score = kpi_scores['customer_acquisition_readiness']
            if score > 75:
                insights['acquisition_strengths'].append("Excellent customer acquisition readiness with strong trust-building capabilities")
            elif score > 60:
                insights['acquisition_strengths'].append("Good customer acquisition foundation with room for optimization")
            else:
                insights['acquisition_strengths'].append("Customer acquisition capabilities need significant improvement")
        
        # Growth Opportunities
        trend_changes = self.data_loader.calculate_trend_changes()
        declining_metrics = [k for k, v in trend_changes.items() if v < -5]
        if declining_metrics:
            insights['growth_opportunities'].append(f"Focus on improving: {', '.join(declining_metrics)}")
        
        # Risk Mitigation
        risk_assessment = self.data_loader.calculate_risk_assessment()
        high_risks = [k for k, v in risk_assessment.items() if v > 20]
        if high_risks:
            insights['risk_mitigation'].append(f"Address high-risk behaviors: {', '.join(high_risks)}")
        
        return insights
    
    def _generate_recommendations(self) -> Dict[str, List[str]]:
        """Generate actionable recommendations"""
        recommendations = {
            'content_strategy': [],
            'brand_strengthening': [],
            'acquisition_improvement': [],
            'risk_mitigation': []
        }
        
        # Content Strategy Recommendations
        content_dist = self.data_loader.get_content_category_distribution()
        if content_dist:
            total_posts = sum(content_dist.values())
            educational_pct = (content_dist.get('educational', 0) / total_posts) * 100
            
            if educational_pct < 30:
                recommendations['content_strategy'].append("Increase educational content to build authority and trust")
            
            promotional_pct = (content_dist.get('promotional', 0) / total_posts) * 100
            if promotional_pct > 20:
                recommendations['content_strategy'].append("Reduce promotional content to avoid over-promotion")
        
        # Brand Strengthening Recommendations
        kpi_scores = self.data_loader.calculate_kpi_scores()
        if 'brand_authenticity_score' in kpi_scores and kpi_scores['brand_authenticity_score'] < 70:
            recommendations['brand_strengthening'].append("Focus on authentic storytelling and consistent messaging")
        
        # Acquisition Improvement Recommendations
        if 'customer_acquisition_readiness' in kpi_scores and kpi_scores['customer_acquisition_readiness'] < 75:
            recommendations['acquisition_improvement'].append("Strengthen call-to-action effectiveness and social proof elements")
        
        # Risk Mitigation Recommendations
        risk_assessment = self.data_loader.calculate_risk_assessment()
        if risk_assessment.get('over_promotion', 0) > 15:
            recommendations['risk_mitigation'].append("Implement 80/20 rule: 80% value-driven content, 20% promotional")
        
        return recommendations

def generate_personal_brand_analysis(data_file: str = None) -> bool:
    """
    Main function to generate personal brand analysis
    
    Args:
        data_file: Path to the data file
        
    Returns:
        bool: Success status
    """
    try:
        if data_file is None:
            logger.error("No data file provided")
            return False
        
        # Initialize analyzer
        analyzer = PersonalBrandAnalyzer(data_file)
        
        # Load and process data
        if not analyzer.load_and_process_data():
            return False
        
        # Run comprehensive analysis
        results = analyzer.run_comprehensive_analysis()
        
        # Generate HTML dashboard
        dashboard_file = generate_personal_brand_charts(results, 'personal_brand_analysis.html')
        logger.info(f"HTML dashboard generated: {dashboard_file}")
        logger.info("Analysis completed successfully")
        logger.info(f"Overall Brand Growth Score: {results['brand_growth_score']['overall_score']}/100")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in personal brand analysis: {str(e)}")
        return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        data_file = sys.argv[1]
        generate_personal_brand_analysis(data_file)
    else:
        print("Usage: python personal_brand_analysis.py <data_file>") 