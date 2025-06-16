#!/usr/bin/env python3
"""
Trend Analysis Module
Analyzes temporal trends, content evolution, and predictive patterns
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.figure_factory as ff
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from scipy import stats
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

from data_loader import load_and_merge_data

def create_temporal_segments(df, n_segments=6):
    """Create temporal segments from post ordering"""
    df_sorted = df.copy().reset_index(drop=True)
    segment_size = len(df_sorted) // n_segments
    
    segments = {}
    for i in range(n_segments):
        start_idx = i * segment_size
        end_idx = start_idx + segment_size if i < n_segments - 1 else len(df_sorted)
        
        segment_df = df_sorted.iloc[start_idx:end_idx]
        segment_name = f"Period {i+1}"
        
        segments[segment_name] = {
            'data': segment_df,
            'start_post': start_idx + 1,
            'end_post': end_idx,
            'post_count': len(segment_df)
        }
    
    return segments

def analyze_engagement_trends(segments):
    """Analyze how engagement trends over time"""
    trends = {}
    
    # Calculate metrics for each segment
    for period, segment in segments.items():
        df = segment['data']
        
        trends[period] = {
            'avg_engagement': df['combined'].mean(),
            'avg_likes': df['likes'].mean(),
            'avg_comments': df['comments'].mean(),
            'engagement_std': df['combined'].std(),
            'post_count': len(df),
            'high_performers': len(df[df['combined'] > df['combined'].quantile(0.8)]),
            'viral_posts': len(df[df['combined'] > df['combined'].quantile(0.95)])
        }
    
    # Calculate trend direction
    periods = list(trends.keys())
    engagements = [trends[p]['avg_engagement'] for p in periods]
    
    # Linear regression for trend
    x = np.arange(len(periods)).reshape(-1, 1)
    y = np.array(engagements)
    model = LinearRegression().fit(x, y)
    
    trends['overall_trend'] = {
        'slope': model.coef_[0],
        'direction': 'increasing' if model.coef_[0] > 0 else 'decreasing',
        'r_squared': model.score(x, y),
        'trend_strength': abs(model.coef_[0])
    }
    
    return trends

def analyze_content_evolution(segments):
    """Analyze how content characteristics evolve over time"""
    evolution = {}
    
    for period, segment in segments.items():
        df = segment['data']
        
        # Topic analysis
        period_topics = []
        for topics in df['topic_tags']:
            if isinstance(topics, list):
                period_topics.extend(topics)
            else:
                period_topics.extend(str(topics).split(', '))
        
        top_topics = dict(Counter(period_topics).most_common(5))
        
        # Personality traits evolution
        personality_traits = {}
        trait_cols = [col for col in df.columns if col.startswith('big5_') or col.startswith('partner_')]
        for col in trait_cols:
            if df[col].dtype in ['float64', 'int64']:
                personality_traits[col] = df[col].mean()
        
        evolution[period] = {
            'top_topics': top_topics,
            'personality_traits': personality_traits,
            'content_diversity': len(set(period_topics)),
            'dominant_topic': max(top_topics.items(), key=lambda x: x[1])[0] if top_topics else 'None'
        }
    
    return evolution

def analyze_performance_patterns(df):
    """Analyze patterns in high-performing content"""
    patterns = {}
    
    # Define performance tiers
    high_performers = df[df['combined'] > df['combined'].quantile(0.8)]
    medium_performers = df[(df['combined'] > df['combined'].quantile(0.4)) & 
                          (df['combined'] <= df['combined'].quantile(0.8))]
    low_performers = df[df['combined'] <= df['combined'].quantile(0.4)]
    
    # Analyze each tier
    for tier_name, tier_df in [('High', high_performers), ('Medium', medium_performers), ('Low', low_performers)]:
        if len(tier_df) > 0:
            # Topic analysis
            tier_topics = []
            for topics in tier_df['topic_tags']:
                if isinstance(topics, list):
                    tier_topics.extend(topics)
                else:
                    tier_topics.extend(str(topics).split(', '))
            
            # Personality traits
            trait_means = {}
            trait_cols = [col for col in tier_df.columns if col.startswith('big5_') or col.startswith('partner_')]
            for col in trait_cols:
                if tier_df[col].dtype in ['float64', 'int64']:
                    trait_means[col] = tier_df[col].mean()
            
            patterns[tier_name] = {
                'count': len(tier_df),
                'avg_engagement': tier_df['combined'].mean(),
                'top_topics': dict(Counter(tier_topics).most_common(5)),
                'personality_profile': trait_means
            }
    
    return patterns

def predict_future_trends(trends, evolution):
    """Make predictions about future content performance"""
    predictions = {}
    
    # Engagement trend prediction
    periods = list(trends.keys())[:-1]  # Exclude 'overall_trend' key
    engagements = [trends[p]['avg_engagement'] for p in periods]
    
    if len(engagements) >= 3:
        # Simple linear prediction
        x = np.arange(len(periods))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, engagements)
        
        next_period_engagement = slope * len(periods) + intercept
        predictions['next_period_engagement'] = max(0, next_period_engagement)
        predictions['trend_confidence'] = r_value ** 2
        
        # Predict engagement direction
        if slope > 0.5:
            predictions['direction'] = 'Strong Growth'
        elif slope > 0:
            predictions['direction'] = 'Modest Growth'
        elif slope > -0.5:
            predictions['direction'] = 'Slight Decline'
        else:
            predictions['direction'] = 'Significant Decline'
    
    # Content evolution predictions
    recent_periods = list(evolution.keys())[-2:]  # Last 2 periods
    
    # Predict emerging topics
    if len(recent_periods) >= 2:
        recent_topics = set()
        for period in recent_periods:
            recent_topics.update(evolution[period]['top_topics'].keys())
        
        # Topics gaining momentum
        emerging_topics = []
        for topic in recent_topics:
            scores = []
            for period in recent_periods:
                scores.append(evolution[period]['top_topics'].get(topic, 0))
            
            if len(scores) >= 2 and scores[-1] > scores[-2]:
                emerging_topics.append(topic)
        
        predictions['emerging_topics'] = emerging_topics[:3]
    
    return predictions

def create_trend_visualizations(df, trends, evolution, patterns, predictions):
    """Create comprehensive trend analysis visualizations"""
    
    # Create subplot layout
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=[
            "Engagement Trends Over Time",
            "Content Evolution Timeline",
            "Performance Tier Analysis",
            "Topic Trend Heatmap",
            "Personality Trait Evolution",
            "Future Trend Predictions"
        ],
        specs=[
            [{"type": "scatter"}, {"type": "bar"}],
            [{"type": "bar"}, {"type": "heatmap"}],
            [{"type": "scatter"}, {"type": "bar"}]
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.1
    )
    
    # 1. Engagement Trends Over Time
    periods = [p for p in trends.keys() if p != 'overall_trend']
    avg_engagements = [trends[p]['avg_engagement'] for p in periods]
    viral_counts = [trends[p]['viral_posts'] for p in periods]
    
    fig.add_trace(
        go.Scatter(
            x=periods,
            y=avg_engagements,
            mode='lines+markers',
            name='Average Engagement',
            line=dict(color='blue', width=3),
            marker=dict(size=8)
        ),
        row=1, col=1
    )
    
    # Add trendline
    x_numeric = list(range(len(periods)))
    z = np.polyfit(x_numeric, avg_engagements, 1)
    p = np.poly1d(z)
    fig.add_trace(
        go.Scatter(
            x=periods,
            y=p(x_numeric),
            mode='lines',
            name='Trend Line',
            line=dict(color='red', dash='dash')
        ),
        row=1, col=1
    )
    
    # 2. Content Evolution - Topic Diversity
    diversity_scores = [evolution[p]['content_diversity'] for p in periods]
    fig.add_trace(
        go.Bar(
            x=periods,
            y=diversity_scores,
            name='Content Diversity',
            marker_color='green'
        ),
        row=1, col=2
    )
    
    # 3. Performance Tier Analysis
    if patterns:
        tier_names = list(patterns.keys())
        tier_counts = [patterns[tier]['count'] for tier in tier_names]
        tier_avg_engagement = [patterns[tier]['avg_engagement'] for tier in tier_names]
        
        fig.add_trace(
            go.Bar(
                x=tier_names,
                y=tier_counts,
                name='Post Count by Tier',
                marker_color=['red', 'orange', 'green'],
                yaxis='y'
            ),
            row=2, col=1
        )
    
    # 4. Topic Trend Heatmap
    # Create heatmap of topics over time
    all_topics = set()
    for period in periods:
        all_topics.update(evolution[period]['top_topics'].keys())
    
    top_topics = list(all_topics)[:10]  # Limit to top 10 topics
    
    heatmap_data = []
    for topic in top_topics:
        topic_trend = []
        for period in periods:
            topic_trend.append(evolution[period]['top_topics'].get(topic, 0))
        heatmap_data.append(topic_trend)
    
    if heatmap_data:
        fig.add_trace(
            go.Heatmap(
                z=heatmap_data,
                x=periods,
                y=top_topics,
                colorscale='Viridis',
                name="Topic Trends"
            ),
            row=2, col=2
        )
    
    # 5. Personality Trait Evolution
    if evolution:
        trait_names = ['big5_openness', 'big5_extraversion', 'big5_agreeableness']
        
        for trait in trait_names:
            trait_values = []
            for period in periods:
                trait_values.append(evolution[period]['personality_traits'].get(trait, 3))
            
            fig.add_trace(
                go.Scatter(
                    x=periods,
                    y=trait_values,
                    mode='lines+markers',
                    name=trait.replace('big5_', '').title(),
                    line=dict(width=2)
                ),
                row=3, col=1
            )
    
    # 6. Future Predictions
    if predictions:
        prediction_categories = ['Current Avg', 'Predicted Next']
        current_avg = df['combined'].mean()
        predicted_next = predictions.get('next_period_engagement', current_avg)
        
        fig.add_trace(
            go.Bar(
                x=prediction_categories,
                y=[current_avg, predicted_next],
                name='Engagement Prediction',
                marker_color=['blue', 'orange']
            ),
            row=3, col=2
        )
    
    # Update layout
    fig.update_layout(
        height=1200,
        title_text="📈 Comprehensive Trend Analysis",
        title_x=0.5,
        showlegend=True,
        template="plotly_white"
    )
    
    # Update x-axis labels for better readability
    fig.update_xaxes(tickangle=45, row=1, col=2)
    fig.update_xaxes(tickangle=45, row=3, col=1)
    
    return fig

def generate_trend_insights(trends, evolution, patterns, predictions):
    """Generate actionable insights about trends"""
    insights = []
    
    # Overall trend insights
    if 'overall_trend' in trends:
        trend_info = trends['overall_trend']
        direction = trend_info['direction']
        strength = trend_info['trend_strength']
        confidence = trend_info['r_squared']
        
        insights.append(f"📈 Overall Trend: {direction.title()} engagement with {strength:.2f} average change per period")
        insights.append(f"🎯 Trend Confidence: {confidence:.2f} (R²) - {'High' if confidence > 0.7 else 'Moderate' if confidence > 0.4 else 'Low'} reliability")
    
    # Content evolution insights
    if evolution:
        periods = list(evolution.keys())
        recent_diversity = evolution[periods[-1]]['content_diversity']
        early_diversity = evolution[periods[0]]['content_diversity']
        
        if recent_diversity > early_diversity:
            insights.append(f"🌟 Content Diversification: Topics expanded from {early_diversity} to {recent_diversity} categories")
        
        # Dominant topic evolution
        recent_topic = evolution[periods[-1]]['dominant_topic']
        insights.append(f"🏆 Current Focus: '{recent_topic}' is the dominant topic in recent content")
    
    # Performance patterns
    if patterns and 'High' in patterns:
        high_perf = patterns['High']
        if high_perf['top_topics']:
            top_high_topic = max(high_perf['top_topics'].items(), key=lambda x: x[1])
            insights.append(f"⚡ High-Performance Topic: '{top_high_topic[0]}' appears in {top_high_topic[1]} top-performing posts")
    
    # Future predictions
    if predictions:
        if 'direction' in predictions:
            insights.append(f"🔮 Future Outlook: {predictions['direction']} predicted for upcoming content")
        
        if 'emerging_topics' in predictions and predictions['emerging_topics']:
            emerging = ', '.join(predictions['emerging_topics'])
            insights.append(f"🚀 Emerging Topics: {emerging} showing growth momentum")
    
    # Performance tier insights
    if patterns:
        total_posts = sum(patterns[tier]['count'] for tier in patterns.keys())
        high_ratio = patterns.get('High', {}).get('count', 0) / total_posts * 100
        insights.append(f"📊 Performance Distribution: {high_ratio:.1f}% of posts achieve high engagement")
    
    return insights

def generate_trend_analysis(data_file: str = None):
    """Generate complete trend analysis"""
    print("Loading data for trend analysis...")
    df = load_and_merge_data(data_file)
    
    print("Creating temporal segments...")
    segments = create_temporal_segments(df)
    
    print("Analyzing engagement trends...")
    trends = analyze_engagement_trends(segments)
    
    print("Analyzing content evolution...")
    evolution = analyze_content_evolution(segments)
    
    print("Analyzing performance patterns...")
    patterns = analyze_performance_patterns(df)
    
    print("Making future predictions...")
    predictions = predict_future_trends(trends, evolution)
    
    print("Generating insights...")
    insights = generate_trend_insights(trends, evolution, patterns, predictions)
    
    print("Creating visualizations...")
    fig = create_trend_visualizations(df, trends, evolution, patterns, predictions)
    
    # Create comprehensive HTML report
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Trend Analysis Dashboard</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            .header {{ text-align: center; margin-bottom: 30px; }}
            .insights {{ background: #e8f4fd; padding: 20px; border-radius: 8px; margin: 20px 0; }}
            .insight-item {{ margin: 10px 0; padding: 10px; background: white; border-left: 4px solid #007acc; }}
            .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
            .metric-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }}
            .metric-value {{ font-size: 2em; font-weight: bold; }}
            .metric-label {{ font-size: 0.9em; opacity: 0.9; }}
            .prediction-box {{ background: linear-gradient(135deg, #ff7e5f 0%, #feb47b 100%); color: white; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📈 Trend Analysis Dashboard</h1>
                <p>Temporal patterns, content evolution, and future predictions</p>
            </div>
            
            <div class="metrics">
                <div class="metric-card">
                    <div class="metric-value">{trends.get('overall_trend', {}).get('direction', 'Stable').title()}</div>
                    <div class="metric-label">Overall Trend</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{len(segments)}</div>
                    <div class="metric-label">Time Periods</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{trends.get('overall_trend', {}).get('r_squared', 0):.2f}</div>
                    <div class="metric-label">Trend Confidence</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{len(patterns) if patterns else 0}</div>
                    <div class="metric-label">Performance Tiers</div>
                </div>
            </div>
            
            <div id="plotly-div"></div>
            
            {f'''
            <div class="prediction-box">
                <h3>🔮 Future Predictions</h3>
                <p><strong>Trend Direction:</strong> {predictions.get('direction', 'Stable')}</p>
                <p><strong>Predicted Next Period Engagement:</strong> {predictions.get('next_period_engagement', 0):.1f}</p>
                <p><strong>Emerging Topics:</strong> {', '.join(predictions.get('emerging_topics', ['None']))}</p>
            </div>
            ''' if predictions else ''}
            
            <div class="insights">
                <h3>🎯 Key Trend Insights</h3>
                {"".join([f'<div class="insight-item">{insight}</div>' for insight in insights])}
            </div>
        </div>
        
        <script>
            var plotlyData = {fig.to_json()};
            Plotly.newPlot('plotly-div', plotlyData.data, plotlyData.layout, {{responsive: true}});
        </script>
    </body>
    </html>
    """
    
    # Save the analysis
    with open('trend_analysis.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("✅ Trend analysis saved to 'trend_analysis.html'")
    print(f"📊 Analyzed {len(df)} posts across {len(segments)} time periods")
    print(f"📈 Trend direction: {trends.get('overall_trend', {}).get('direction', 'stable')}")
    print(f"🔮 Predictions generated with {trends.get('overall_trend', {}).get('r_squared', 0):.2f} confidence")

if __name__ == "__main__":
    import sys
    data_file = sys.argv[1] if len(sys.argv) > 1 else None
    generate_trend_analysis(data_file) 