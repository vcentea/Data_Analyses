#!/usr/bin/env python3
"""
Engagement Analysis Module
Analyzes engagement patterns, viral potential, and audience insights
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.figure_factory as ff
from collections import Counter
from datetime import datetime, timedelta
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

from data_loader import load_and_merge_data

def calculate_engagement_metrics(df):
    """Calculate comprehensive engagement metrics"""
    metrics = {}
    
    # Basic engagement stats
    metrics['total_posts'] = len(df)
    metrics['total_likes'] = df['likes'].sum()
    metrics['total_comments'] = df['comments'].sum()
    metrics['total_engagement'] = df['combined'].sum()
    
    # Average metrics
    metrics['avg_likes'] = df['likes'].mean()
    metrics['avg_comments'] = df['comments'].mean()
    metrics['avg_engagement'] = df['combined'].mean()
    
    # Engagement rate calculations
    metrics['like_to_comment_ratio'] = metrics['total_likes'] / (metrics['total_comments'] + 1)
    metrics['high_engagement_posts'] = len(df[df['combined'] > df['combined'].quantile(0.8)])
    metrics['viral_posts'] = len(df[df['combined'] > df['combined'].quantile(0.95)])
    
    # Engagement consistency
    metrics['engagement_std'] = df['combined'].std()
    metrics['engagement_cv'] = metrics['engagement_std'] / metrics['avg_engagement']
    
    return metrics

def analyze_viral_potential(df):
    """Analyze factors that contribute to viral potential"""
    # Define viral posts (top 10% by engagement)
    viral_threshold = df['combined'].quantile(0.9)
    viral_posts = df[df['combined'] >= viral_threshold]
    regular_posts = df[df['combined'] < viral_threshold]
    
    viral_analysis = {}
    
    # Personality traits comparison
    personality_traits = ['big5_openness', 'big5_conscientiousness', 'big5_extraversion', 
                         'big5_agreeableness', 'big5_neuroticism']
    
    for trait in personality_traits:
        if trait in df.columns:
            viral_avg = viral_posts[trait].mean()
            regular_avg = regular_posts[trait].mean()
            viral_analysis[f'{trait}_viral'] = viral_avg
            viral_analysis[f'{trait}_regular'] = regular_avg
            viral_analysis[f'{trait}_difference'] = viral_avg - regular_avg
    
    # Content characteristics
    viral_analysis['viral_threshold'] = viral_threshold
    viral_analysis['viral_count'] = len(viral_posts)
    viral_analysis['viral_percentage'] = (len(viral_posts) / len(df)) * 100
    
    # Topic analysis for viral posts
    viral_topics = []
    for topics in viral_posts['topic_tags']:
        if isinstance(topics, list):
            viral_topics.extend(topics)
        else:
            viral_topics.extend(str(topics).split(', '))
    
    viral_analysis['top_viral_topics'] = dict(Counter(viral_topics).most_common(10))
    
    return viral_analysis, viral_posts, regular_posts

def analyze_engagement_patterns(df):
    """Analyze engagement patterns over time and content"""
    patterns = {}
    
    # Engagement distribution analysis
    patterns['engagement_quartiles'] = {
        'Q1': df['combined'].quantile(0.25),
        'Q2': df['combined'].quantile(0.5),
        'Q3': df['combined'].quantile(0.75),
        'Q4': df['combined'].quantile(0.95)
    }
    
    # Content type engagement (if available in data)
    if 'content_type' in df.columns:
        patterns['engagement_by_type'] = df.groupby('content_type')['combined'].agg(['mean', 'std', 'count']).to_dict()
    
    # Engagement vs personality correlation
    correlations = {}
    engagement_col = 'combined'
    
    personality_cols = [col for col in df.columns if col.startswith('big5_') or col.startswith('partner_')]
    for col in personality_cols:
        if df[col].dtype in ['float64', 'int64'] and not df[col].isna().all():
            corr = df[engagement_col].corr(df[col])
            if not np.isnan(corr):
                correlations[col] = corr
    
    patterns['personality_correlations'] = correlations
    
    # Peak engagement analysis
    top_10_percent = df.nlargest(int(len(df) * 0.1), 'combined')
    patterns['peak_engagement_traits'] = {
        'avg_openness': top_10_percent['big5_openness'].mean() if 'big5_openness' in df.columns else 0,
        'avg_extraversion': top_10_percent['big5_extraversion'].mean() if 'big5_extraversion' in df.columns else 0,
        'avg_agreeableness': top_10_percent['big5_agreeableness'].mean() if 'big5_agreeableness' in df.columns else 0,
    }
    
    return patterns

def analyze_audience_insights(df):
    """Analyze audience engagement patterns and preferences"""
    insights = {}
    
    # Comment-to-like ratio analysis (proxy for audience depth)
    df['comment_like_ratio'] = df['comments'] / (df['likes'] + 1)
    
    insights['avg_comment_like_ratio'] = df['comment_like_ratio'].mean()
    insights['high_discussion_posts'] = len(df[df['comment_like_ratio'] > df['comment_like_ratio'].quantile(0.8)])
    
    # Engagement velocity (posts that got high engagement early)
    # Simulate this with post ordering as time proxy
    df_with_index = df.copy().reset_index()
    df_with_index['post_order'] = df_with_index.index
    
    # Early posts vs later posts engagement
    early_posts = df_with_index[df_with_index['post_order'] < len(df) * 0.3]
    later_posts = df_with_index[df_with_index['post_order'] >= len(df) * 0.7]
    
    insights['early_avg_engagement'] = early_posts['combined'].mean()
    insights['later_avg_engagement'] = later_posts['combined'].mean()
    insights['engagement_growth'] = insights['later_avg_engagement'] - insights['early_avg_engagement']
    
    # Audience preference analysis based on high-engagement content
    high_engagement = df[df['combined'] > df['combined'].quantile(0.75)]
    
    # Extract preferred topics
    preferred_topics = []
    for topics in high_engagement['topic_tags']:
        if isinstance(topics, list):
            preferred_topics.extend(topics)
        else:
            preferred_topics.extend(str(topics).split(', '))
    
    insights['preferred_topics'] = dict(Counter(preferred_topics).most_common(8))
    
    # Engagement consistency score
    insights['consistency_score'] = 1 / (df['combined'].std() / df['combined'].mean() + 0.1)
    
    return insights

def create_engagement_visualizations(df, metrics, viral_analysis, patterns, audience_insights):
    """Create comprehensive engagement analysis visualizations"""
    
    # Create subplot layout
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=[
            "Engagement Distribution",
            "Viral vs Regular Post Traits",
            "Engagement vs Personality Correlations",
            "Audience Engagement Patterns",
            "Content Performance Matrix",
            "Engagement Evolution"
        ],
        specs=[
            [{"type": "histogram"}, {"type": "bar"}],
            [{"type": "bar"}, {"type": "scatter"}],
            [{"type": "heatmap"}, {"type": "scatter"}]
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.1
    )
    
    # 1. Engagement Distribution
    fig.add_trace(
        go.Histogram(
            x=df['combined'],
            nbinsx=30,
            marker_color='lightblue',
            name="Engagement Distribution"
        ),
        row=1, col=1
    )
    
    # 2. Viral vs Regular Post Traits
    if viral_analysis:
        traits = ['big5_openness', 'big5_extraversion', 'big5_agreeableness']
        viral_scores = [viral_analysis.get(f'{trait}_viral', 3) for trait in traits]
        regular_scores = [viral_analysis.get(f'{trait}_regular', 3) for trait in traits]
        
        fig.add_trace(
            go.Bar(
                x=[trait.replace('big5_', '').title() for trait in traits],
                y=viral_scores,
                name="Viral Posts",
                marker_color='red'
            ),
            row=1, col=2
        )
        
        fig.add_trace(
            go.Bar(
                x=[trait.replace('big5_', '').title() for trait in traits],
                y=regular_scores,
                name="Regular Posts",
                marker_color='blue'
            ),
            row=1, col=2
        )
    
    # 3. Personality Correlations with Engagement
    if patterns.get('personality_correlations'):
        corr_data = patterns['personality_correlations']
        corr_traits = list(corr_data.keys())[:8]  # Top 8 correlations
        corr_values = [corr_data[trait] for trait in corr_traits]
        colors = ['green' if x > 0 else 'red' for x in corr_values]
        
        fig.add_trace(
            go.Bar(
                x=[trait.replace('big5_', '').replace('partner_', '').title() for trait in corr_traits],
                y=corr_values,
                marker_color=colors,
                name="Personality Correlations"
            ),
            row=2, col=1
        )
    
    # 4. Audience Engagement Patterns
    engagement_categories = ['Low', 'Medium', 'High', 'Viral']
    engagement_counts = [
        len(df[df['combined'] <= df['combined'].quantile(0.25)]),
        len(df[(df['combined'] > df['combined'].quantile(0.25)) & (df['combined'] <= df['combined'].quantile(0.75))]),
        len(df[(df['combined'] > df['combined'].quantile(0.75)) & (df['combined'] <= df['combined'].quantile(0.95))]),
        len(df[df['combined'] > df['combined'].quantile(0.95)])
    ]
    
    fig.add_trace(
        go.Scatter(
            x=engagement_categories,
            y=engagement_counts,
            mode='markers+lines',
            marker=dict(size=15, color='orange'),
            line=dict(width=3),
            name="Engagement Levels"
        ),
        row=2, col=2
    )
    
    # 5. Content Performance Matrix (Engagement vs Traits)
    openness = df['big5_openness'] if 'big5_openness' in df.columns else np.random.normal(3, 0.5, len(df))
    extraversion = df['big5_extraversion'] if 'big5_extraversion' in df.columns else np.random.normal(3, 0.5, len(df))
    
    # Create performance matrix
    performance_matrix = np.zeros((5, 5))
    for i in range(5):
        for j in range(5):
            mask = ((openness >= i) & (openness < i+1) & 
                    (extraversion >= j) & (extraversion < j+1))
            if mask.sum() > 0:
                performance_matrix[i, j] = df[mask]['combined'].mean()
    
    fig.add_trace(
        go.Heatmap(
            z=performance_matrix,
            x=['Low', 'Low-Med', 'Medium', 'Med-High', 'High'],
            y=['Low', 'Low-Med', 'Medium', 'Med-High', 'High'],
            colorscale='Viridis',
            name="Performance Matrix"
        ),
        row=3, col=1
    )
    
    # 6. Engagement Evolution (simulated timeline)
    post_numbers = list(range(1, len(df) + 1))
    rolling_avg = df['combined'].rolling(window=20, min_periods=1).mean()
    
    fig.add_trace(
        go.Scatter(
            x=post_numbers,
            y=df['combined'],
            mode='markers',
            marker=dict(size=5, color='lightgray', opacity=0.6),
            name="Individual Posts"
        ),
        row=3, col=2
    )
    
    fig.add_trace(
        go.Scatter(
            x=post_numbers,
            y=rolling_avg,
            mode='lines',
            line=dict(width=3, color='red'),
            name="Rolling Average"
        ),
        row=3, col=2
    )
    
    # Update layout
    fig.update_layout(
        height=1200,
        title_text="📈 Comprehensive Engagement Analysis",
        title_x=0.5,
        showlegend=True,
        template="plotly_white"
    )
    
    return fig

def generate_engagement_insights(metrics, viral_analysis, patterns, audience_insights):
    """Generate actionable insights about engagement"""
    insights = []
    
    # Basic metrics insights
    insights.append(f"📊 Total Engagement: {metrics['total_engagement']:,.0f} across {metrics['total_posts']} posts")
    insights.append(f"💬 Comment Rate: {(metrics['total_comments']/metrics['total_posts']):.1f} comments per post")
    insights.append(f"👍 Like Rate: {(metrics['total_likes']/metrics['total_posts']):.1f} likes per post")
    
    # Viral potential insights
    if viral_analysis:
        insights.append(f"🚀 Viral Posts: {viral_analysis['viral_count']} posts ({viral_analysis['viral_percentage']:.1f}%) achieved viral status")
        
        if viral_analysis.get('top_viral_topics'):
            top_viral_topic = max(viral_analysis['top_viral_topics'].items(), key=lambda x: x[1])
            insights.append(f"🔥 Top Viral Topic: '{top_viral_topic[0]}' appears in {top_viral_topic[1]} viral posts")
    
    # Consistency insights
    if metrics['engagement_cv'] < 0.5:
        insights.append(f"✅ Highly Consistent: Engagement variability is {metrics['engagement_cv']:.2f} (very consistent)")
    elif metrics['engagement_cv'] > 1.0:
        insights.append(f"🎢 Variable Performance: High engagement variability ({metrics['engagement_cv']:.2f}) suggests mixed content success")
    
    # Audience insights
    if audience_insights:
        if audience_insights['engagement_growth'] > 0:
            insights.append(f"📈 Growing Audience: {audience_insights['engagement_growth']:.1f} improvement in later posts")
        
        if audience_insights.get('preferred_topics'):
            top_preferred = max(audience_insights['preferred_topics'].items(), key=lambda x: x[1])
            insights.append(f"🎯 Audience Favorite: '{top_preferred[0]}' consistently drives high engagement")
    
    return insights

def generate_engagement_analysis(data_file: str = None):
    """Generate complete engagement analysis"""
    print("Loading data for engagement analysis...")
    df = load_and_merge_data(data_file)
    
    print("Calculating engagement metrics...")
    metrics = calculate_engagement_metrics(df)
    
    print("Analyzing viral potential...")
    viral_analysis, viral_posts, regular_posts = analyze_viral_potential(df)
    
    print("Analyzing engagement patterns...")
    patterns = analyze_engagement_patterns(df)
    
    print("Analyzing audience insights...")
    audience_insights = analyze_audience_insights(df)
    
    print("Generating insights...")
    insights = generate_engagement_insights(metrics, viral_analysis, patterns, audience_insights)
    
    print("Creating visualizations...")
    fig = create_engagement_visualizations(df, metrics, viral_analysis, patterns, audience_insights)
    
    # Create comprehensive HTML report
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Engagement Analysis Dashboard</title>
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
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📈 Engagement Analysis Dashboard</h1>
                <p>Viral potential, audience insights, and performance patterns</p>
            </div>
            
            <div class="metrics">
                <div class="metric-card">
                    <div class="metric-value">{metrics['avg_engagement']:.1f}</div>
                    <div class="metric-label">Average Engagement</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{viral_analysis.get('viral_count', 0)}</div>
                    <div class="metric-label">Viral Posts</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{metrics['like_to_comment_ratio']:.1f}</div>
                    <div class="metric-label">Like/Comment Ratio</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{audience_insights.get('consistency_score', 0):.2f}</div>
                    <div class="metric-label">Consistency Score</div>
                </div>
            </div>
            
            <div id="plotly-div"></div>
            
            <div class="insights">
                <h3>🎯 Key Engagement Insights</h3>
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
    with open('engagement_analysis.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("✅ Engagement analysis saved to 'engagement_analysis.html'")
    print(f"📊 Analyzed {metrics['total_posts']} posts with {metrics['total_engagement']:,.0f} total engagement")
    print(f"🚀 Identified {viral_analysis.get('viral_count', 0)} viral posts")
    print(f"💡 Generated {len(insights)} actionable insights")

if __name__ == "__main__":
    import sys
    data_file = sys.argv[1] if len(sys.argv) > 1 else None
    generate_engagement_analysis(data_file) 