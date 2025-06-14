#!/usr/bin/env python3
"""
Consistency Analysis - Phase 4
Analyzes trait stability, volatility, and identifies outlier posts
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from scipy import stats
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_loader import load_and_merge_data, get_data_summary

def calculate_trait_volatility(df):
    """Calculate volatility scores for each trait"""
    trait_cols = [col for col in df.columns if col.startswith(('big5_', 'partner_')) and df[col].dtype in ['int64', 'float64']]
    
    volatility_scores = {}
    for trait in trait_cols:
        volatility_scores[trait] = {
            'std_dev': df[trait].std(),
            'coefficient_variation': df[trait].std() / df[trait].mean() if df[trait].mean() != 0 else 0,
            'range': df[trait].max() - df[trait].min(),
            'iqr': df[trait].quantile(0.75) - df[trait].quantile(0.25)
        }
    
    return volatility_scores

def calculate_stability_index(df):
    """Calculate overall persona stability index"""
    trait_cols = [col for col in df.columns if col.startswith(('big5_', 'partner_')) and df[col].dtype in ['int64', 'float64']]
    
    # Calculate average coefficient of variation across all traits
    cv_scores = []
    for trait in trait_cols:
        if df[trait].mean() != 0:
            cv = df[trait].std() / df[trait].mean()
            cv_scores.append(cv)
    
    avg_cv = np.mean(cv_scores)
    
    # Stability index: inverse of average CV, scaled 0-100
    # Lower CV = higher stability
    stability_index = max(0, 100 - (avg_cv * 100))
    
    return stability_index, avg_cv

def detect_outlier_posts(df):
    """Identify posts that deviate >2σ from personal norm"""
    trait_cols = [col for col in df.columns if col.startswith(('big5_', 'partner_')) and df[col].dtype in ['int64', 'float64']]
    
    outlier_posts = []
    
    for idx, row in df.iterrows():
        post_deviations = []
        
        for trait in trait_cols:
            trait_mean = df[trait].mean()
            trait_std = df[trait].std()
            
            if trait_std > 0:  # Avoid division by zero
                z_score = abs((row[trait] - trait_mean) / trait_std)
                post_deviations.append(z_score)
        
        # Check if any trait deviates >2σ
        max_deviation = max(post_deviations) if post_deviations else 0
        avg_deviation = np.mean(post_deviations) if post_deviations else 0
        
        if max_deviation > 2.0:
            outlier_posts.append({
                'post_id': row['post_id'],
                'max_deviation': max_deviation,
                'avg_deviation': avg_deviation,
                'outlier_traits': [trait for trait, dev in zip(trait_cols, post_deviations) if dev > 2.0]
            })
    
    return outlier_posts

def create_trait_boxplots(df):
    """Create box plots for each trait showing distribution"""
    trait_cols = [col for col in df.columns if col.startswith(('big5_', 'partner_')) and df[col].dtype in ['int64', 'float64']]
    
    # Separate Big Five and Partner traits
    big5_traits = [col for col in trait_cols if col.startswith('big5_')]
    partner_traits = [col for col in trait_cols if col.startswith('partner_')]
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=['Big Five Personality Traits Distribution', 'Partner Traits Distribution'],
        vertical_spacing=0.15
    )
    
    # Big Five box plots
    for trait in big5_traits:
        trait_name = trait.replace('big5_', '').title()
        fig.add_trace(go.Box(
            y=df[trait],
            name=trait_name,
            boxpoints='outliers',
            marker_color='#2E86AB',
            line_color='#2E86AB'
        ), row=1, col=1)
    
    # Partner traits box plots
    for trait in partner_traits:
        trait_name = trait.replace('partner_', '').replace('_', ' ').title()
        fig.add_trace(go.Box(
            y=df[trait],
            name=trait_name,
            boxpoints='outliers',
            marker_color='#F18F01',
            line_color='#F18F01'
        ), row=2, col=1)
    
    fig.update_layout(
        height=800,
        title_text="📊 Trait Distribution Analysis (Box Plots)",
        title_x=0.5,
        title_font_size=20,
        showlegend=False,
        margin=dict(t=80, b=50, l=50, r=50)
    )
    
    fig.update_yaxes(title_text="Score (1-5)", range=[0.5, 5.5])
    
    return fig

def create_volatility_dashboard(volatility_scores):
    """Create volatility scores visualization"""
    traits = list(volatility_scores.keys())
    std_devs = [volatility_scores[trait]['std_dev'] for trait in traits]
    cv_scores = [volatility_scores[trait]['coefficient_variation'] for trait in traits]
    
    # Format trait names for display
    trait_names = [trait.replace('big5_', 'Big5: ').replace('partner_', 'Partner: ').replace('_', ' ').title() for trait in traits]
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=['Standard Deviation (Volatility)', 'Coefficient of Variation (Relative Volatility)'],
        horizontal_spacing=0.15
    )
    
    # Standard deviation bars
    colors_std = ['#2E86AB' if 'Big5' in name else '#F18F01' for name in trait_names]
    fig.add_trace(go.Bar(
        y=trait_names,
        x=std_devs,
        orientation='h',
        marker_color=colors_std,
        text=[f"{v:.2f}" for v in std_devs],
        textposition='outside',
        name='Std Dev'
    ), row=1, col=1)
    
    # Coefficient of variation bars
    colors_cv = ['#A23B72' if 'Big5' in name else '#C73E1D' for name in trait_names]
    fig.add_trace(go.Bar(
        y=trait_names,
        x=cv_scores,
        orientation='h',
        marker_color=colors_cv,
        text=[f"{v:.2f}" for v in cv_scores],
        textposition='outside',
        name='CV'
    ), row=1, col=2)
    
    fig.update_layout(
        height=600,
        title_text="📈 Trait Volatility Analysis",
        title_x=0.5,
        title_font_size=20,
        showlegend=False,
        margin=dict(t=80, b=50, l=200, r=100)
    )
    
    fig.update_xaxes(title_text="Standard Deviation", row=1, col=1)
    fig.update_xaxes(title_text="Coefficient of Variation", row=1, col=2)
    
    return fig

def create_stability_gauge(stability_index, avg_cv):
    """Create stability index gauge"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=stability_index,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Persona Stability Index", 'font': {'size': 24}},
        delta={'reference': 80, 'increasing': {'color': "green"}, 'decreasing': {'color': "red"}},
        gauge={
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': "#2E86AB"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 50], 'color': 'lightcoral'},
                {'range': [50, 70], 'color': 'yellow'},
                {'range': [70, 85], 'color': 'lightgreen'},
                {'range': [85, 100], 'color': 'green'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        },
        number={'font': {'size': 40}}
    ))
    
    fig.update_layout(
        height=400,
        title_text=f"🎯 Overall Consistency Score<br><sub>Average CV: {avg_cv:.3f}</sub>",
        title_x=0.5,
        title_font_size=20,
        margin=dict(t=100, b=50, l=50, r=50)
    )
    
    return fig

def create_outlier_analysis(outlier_posts, df):
    """Create outlier posts analysis"""
    if not outlier_posts:
        # No outliers found
        fig = go.Figure()
        fig.add_annotation(
            text="🎉 No Outlier Posts Found!<br>All posts are within 2σ of personal norm",
            xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle',
            showarrow=False,
            font=dict(size=20, color="green")
        )
        fig.update_layout(
            height=300,
            title_text="🔍 Outlier Detection Results",
            title_x=0.5,
            title_font_size=20
        )
        return fig
    
    # Create scatter plot of outlier posts
    post_ids = [int(post['post_id']) for post in outlier_posts]
    max_deviations = [post['max_deviation'] for post in outlier_posts]
    avg_deviations = [post['avg_deviation'] for post in outlier_posts]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=post_ids,
        y=max_deviations,
        mode='markers+text',
        marker=dict(
            size=[d*5 for d in avg_deviations],  # Size based on average deviation
            color=max_deviations,
            colorscale='Reds',
            showscale=True,
            colorbar=dict(title="Max Deviation (σ)")
        ),
        text=[f"Post {pid}" for pid in post_ids],
        textposition="top center",
        hovertemplate='<b>Post %{x}</b><br>Max Deviation: %{y:.2f}σ<br>Avg Deviation: %{customdata:.2f}σ<extra></extra>',
        customdata=avg_deviations,
        name='Outlier Posts'
    ))
    
    # Add 2σ threshold line
    fig.add_hline(y=2.0, line_dash="dash", line_color="red", 
                  annotation_text="2σ Threshold", annotation_position="bottom right")
    
    fig.update_layout(
        height=400,
        title_text=f"🚨 Outlier Posts Analysis ({len(outlier_posts)} found)",
        title_x=0.5,
        title_font_size=20,
        xaxis_title="Post ID",
        yaxis_title="Maximum Deviation (σ)",
        margin=dict(t=80, b=50, l=50, r=50)
    )
    
    return fig

def generate_consistency_analysis():
    """Generate complete consistency analysis"""
    print("🔄 Loading data for consistency analysis...")
    df = load_and_merge_data()
    
    print("📊 Calculating trait volatility...")
    volatility_scores = calculate_trait_volatility(df)
    
    print("🎯 Computing stability index...")
    stability_index, avg_cv = calculate_stability_index(df)
    
    print("🔍 Detecting outlier posts...")
    outlier_posts = detect_outlier_posts(df)
    
    print("📈 Creating visualizations...")
    boxplot_fig = create_trait_boxplots(df)
    volatility_fig = create_volatility_dashboard(volatility_scores)
    stability_fig = create_stability_gauge(stability_index, avg_cv)
    outlier_fig = create_outlier_analysis(outlier_posts, df)
    
    # Generate insights
    most_volatile_trait = max(volatility_scores.keys(), key=lambda x: volatility_scores[x]['std_dev'])
    most_stable_trait = min(volatility_scores.keys(), key=lambda x: volatility_scores[x]['std_dev'])
    
    # Create HTML template
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Content-Personality Analysis: Consistency Analysis</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f8f9fa;
            }}
            .header {{
                text-align: center;
                background: linear-gradient(135deg, #2E86AB, #A23B72);
                color: white;
                padding: 30px;
                margin: -20px -20px 20px -20px;
                border-radius: 0 0 15px 15px;
            }}
            .chart-container {{
                background: white;
                margin: 20px 0;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .insights {{
                background: linear-gradient(135deg, #f8f9fa, #e9ecef);
                padding: 20px;
                margin: 20px 0;
                border-radius: 10px;
                border-left: 5px solid #2E86AB;
            }}
            .metric {{
                display: inline-block;
                margin: 10px;
                padding: 15px;
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                text-align: center;
            }}
            .score {{
                font-size: 24px;
                font-weight: bold;
                color: #2E86AB;
            }}
            .grid-2 {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 Consistency Analysis</h1>
            <h2>Trait Stability & Volatility Assessment</h2>
            <p>Analysis of personality consistency across {len(df)} posts</p>
        </div>
        
        <div class="insights">
            <h3>🎯 Key Consistency Insights</h3>
            <div class="metric">
                <div class="score">{stability_index:.1f}/100</div>
                <div>Stability Index</div>
                <small>Overall consistency score</small>
            </div>
            <div class="metric">
                <div class="score">{len(outlier_posts)}</div>
                <div>Outlier Posts</div>
                <small>Posts >2σ from norm</small>
            </div>
            <div class="metric">
                <div class="score">{most_volatile_trait.replace('_', ' ').title()}</div>
                <div>Most Volatile</div>
                <small>σ = {volatility_scores[most_volatile_trait]['std_dev']:.2f}</small>
            </div>
            <div class="metric">
                <div class="score">{most_stable_trait.replace('_', ' ').title()}</div>
                <div>Most Stable</div>
                <small>σ = {volatility_scores[most_stable_trait]['std_dev']:.2f}</small>
            </div>
        </div>
        
        <div class="grid-2">
            <div class="chart-container">
                <div id="stability-chart"></div>
            </div>
            <div class="chart-container">
                <div id="outlier-chart"></div>
            </div>
        </div>
        
        <div class="chart-container">
            <div id="boxplot-chart"></div>
        </div>
        
        <div class="chart-container">
            <div id="volatility-chart"></div>
        </div>
        
        <script>
            Plotly.newPlot('stability-chart', {stability_fig.to_json()});
            Plotly.newPlot('outlier-chart', {outlier_fig.to_json()});
            Plotly.newPlot('boxplot-chart', {boxplot_fig.to_json()});
            Plotly.newPlot('volatility-chart', {volatility_fig.to_json()});
        </script>
    </body>
    </html>
    """
    
    # Save to HTML file
    with open('consistency_analysis.html', 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print("✅ Consistency analysis saved to 'consistency_analysis.html'")
    print(f"📊 Stability Index: {stability_index:.1f}/100")
    print(f"🚨 Outlier Posts: {len(outlier_posts)}")
    print(f"📈 Most Volatile: {most_volatile_trait} (σ={volatility_scores[most_volatile_trait]['std_dev']:.2f})")
    print(f"📉 Most Stable: {most_stable_trait} (σ={volatility_scores[most_stable_trait]['std_dev']:.2f})")
    
    return df, volatility_scores, stability_index, outlier_posts

if __name__ == "__main__":
    generate_consistency_analysis() 