#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Evolution Tracking - Phase 10
Time-series analysis of content & personality development with comprehensive metrics
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_loader import load_and_merge_data

def get_trend_interpretation(analysis):
    """Generate interpretation text for trend analysis"""
    name = analysis['name']
    trend = analysis['trend']
    change_pct = analysis['change_pct']
    
    if "Stable" in trend:
        return f"✅ {name} has remained consistent over time, showing reliable performance with minimal variation."
    elif "Strong Upward" in trend:
        return f"🚀 {name} shows significant improvement over time ({change_pct:+.1f}%), indicating strong positive development."
    elif "Moderate Upward" in trend:
        return f"📈 {name} demonstrates steady improvement over time ({change_pct:+.1f}%), showing positive growth trajectory."
    elif "Strong Downward" in trend:
        return f"⚠️ {name} shows concerning decline over time ({change_pct:+.1f}%), requiring attention and potential intervention."
    elif "Moderate Downward" in trend:
        return f"📉 {name} shows gradual decline over time ({change_pct:+.1f}%), worth monitoring for continued patterns."
    else:
        return f"📊 {name} shows minor fluctuations over time ({change_pct:+.1f}%), within normal variation range."

def generate_evolution_tracking():
    """Generate complete evolution tracking analysis"""
    print("Loading data for evolution tracking...")
    df = load_and_merge_data()
    
    # Sort by post_id for chronological analysis (REVERSE because data is newest to oldest)
    # Convert post_id to numeric for proper sorting, then reverse for chronological order
    df['post_id_numeric'] = df['post_id'].astype(int)
    df_sorted = df.sort_values('post_id_numeric', ascending=False).copy()  # Reverse: oldest first
    
    # Calculate rolling means for expanded key metrics
    window_size = 20
    key_traits = [
        # Big Five Personality Traits
        'big5_openness', 'big5_conscientiousness', 'big5_extraversion', 
        'big5_agreeableness', 'big5_neuroticism',
        # Partnership Traits
        'partner_integrity_trust', 'partner_reliability', 'partner_collaboration',
        'partner_adaptability', 'partner_risk_tolerance', 'partner_strategic_thinking',
        'partner_leadership',
        # Engagement Metrics
        'engagement_rate', 'comment_rate', 'like_rate',
        # Composite Scores
        'partnership_compatibility', 'thought_leadership', 'trait_volatility', 
        'brand_consistency', 'professional_risk'
    ]
    
    rolling_data = {}
    for trait in key_traits:
        if trait in df_sorted.columns:
            rolling_mean = df_sorted[trait].rolling(window=window_size, min_periods=5).mean()
            rolling_data[trait] = rolling_mean.dropna()
    
    # Simple drift detection
    drift_analysis = {}
    for trait in key_traits:
        if trait in rolling_data and len(rolling_data[trait]) > 10:
            values = rolling_data[trait].values
            x = np.arange(len(values)).reshape(-1, 1)
            
            model = LinearRegression()
            model.fit(x, values)
            
            slope = model.coef_[0]
            r_squared = model.score(x, values)
            
            drift_analysis[trait] = {
                'slope': slope,
                'r_squared': r_squared,
                'direction': 'increasing' if slope > 0 else 'decreasing' if slope < 0 else 'stable'
            }
    
    # Calculate maturation metrics (now correctly: early = oldest posts, late = newest posts)
    consistency_improvement = 0
    if 'brand_consistency' in df_sorted.columns:
        early_consistency = df_sorted['brand_consistency'].head(100).mean()  # Oldest posts (early career)
        late_consistency = df_sorted['brand_consistency'].tail(100).mean()   # Newest posts (recent)
        consistency_improvement = late_consistency - early_consistency
    
    # Overall stability (inverse of trait volatility)
    overall_stability = 1 / (1 + df['trait_volatility'].mean() / 100) if 'trait_volatility' in df.columns else 0.5
    
    # Maturation score
    maturation_score = (overall_stability * 50) + max(0, consistency_improvement)
    
    if maturation_score >= 60:
        maturation_stage = 'Mature'
    elif maturation_score >= 40:
        maturation_stage = 'Developing'
    else:
        maturation_stage = 'Early Stage'
    
    # Find most drifted trait
    most_drifted_trait = max(drift_analysis.keys(), 
                           key=lambda x: abs(drift_analysis[x]['slope'])) if drift_analysis else 'None'
    
    significant_drifts = sum(1 for analysis in drift_analysis.values() if abs(analysis['slope']) > 0.01)
    
    # Create separate charts for each trait
    trait_charts = []
    trait_analyses = []
    
    colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A994E', '#8E44AD', 
              '#1ABC9C', '#E74C3C', '#F39C12', '#27AE60', '#3498DB', '#9B59B6', 
              '#E67E22', '#16A085', '#2ECC71', '#34495E', '#7F8C8D', '#95A5A6']
    
    for i, trait in enumerate(key_traits):
        if trait in rolling_data and len(rolling_data[trait]) > 0:
            # Format trait name based on type
            if trait.startswith('big5_'):
                trait_name = f"B5: {trait.replace('big5_', '').replace('_', ' ').title()}"
            elif trait.startswith('partner_'):
                trait_name = f"Partner: {trait.replace('partner_', '').replace('_', ' ').title()}"
            elif trait in ['engagement_rate', 'comment_rate', 'like_rate']:
                trait_name = f"Engagement: {trait.replace('_', ' ').title()}"
            else:
                trait_name = trait.replace('_', ' ').title()
            
            # Create individual chart for this trait
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=list(range(len(rolling_data[trait]))),
                y=rolling_data[trait],
                mode='lines+markers',
                name=trait_name,
                line=dict(color=colors[i % len(colors)], width=3),
                marker=dict(size=4)
            ))
            
            # Add trend line if we have drift analysis
            if trait in drift_analysis:
                slope = drift_analysis[trait]['slope']
                r_squared = drift_analysis[trait]['r_squared']
                
                # Calculate trend line
                x_vals = list(range(len(rolling_data[trait])))
                y_start = rolling_data[trait].iloc[0]
                trend_line = [y_start + slope * x for x in x_vals]
                
                fig.add_trace(go.Scatter(
                    x=x_vals,
                    y=trend_line,
                    mode='lines',
                    name='Trend Line',
                    line=dict(color='red', width=2, dash='dash'),
                    opacity=0.7
                ))
            
            # Analyze trend
            trait_values = rolling_data[trait].values
            start_avg = trait_values[:10].mean() if len(trait_values) >= 10 else trait_values[0]
            end_avg = trait_values[-10:].mean() if len(trait_values) >= 10 else trait_values[-1]
            change = end_avg - start_avg
            change_pct = (change / start_avg) * 100 if start_avg != 0 else 0
            
            # Determine trend significance
            if abs(change_pct) < 2:
                trend_desc = "Stable"
                trend_icon = "📊"
                trend_color = "#6c757d"
            elif change_pct > 5:
                trend_desc = "Strong Upward Trend"
                trend_icon = "📈"
                trend_color = "#28a745"
            elif change_pct > 2:
                trend_desc = "Moderate Upward Trend"
                trend_icon = "📈"
                trend_color = "#28a745"
            elif change_pct < -5:
                trend_desc = "Strong Downward Trend"
                trend_icon = "📉"
                trend_color = "#dc3545"
            elif change_pct < -2:
                trend_desc = "Moderate Downward Trend"
                trend_icon = "📉"
                trend_color = "#dc3545"
            else:
                trend_desc = "Slight Variation"
                trend_icon = "📊"
                trend_color = "#ffc107"
            
            # Determine appropriate Y-axis range based on metric type
            if trait in ['engagement_rate', 'comment_rate', 'like_rate']:
                y_axis_title = "Rate (%)"
            elif trait in ['trait_volatility', 'professional_risk']:
                y_axis_title = "Score (0-100)"
            else:
                y_axis_title = "Score (1-5)"
            
            fig.update_layout(
                title=f"{trait_name} Evolution Over Time",
                title_x=0.5,
                title_font_size=16,
                xaxis_title="Time Progression (Oldest → Newest Posts)",
                yaxis_title=y_axis_title,
                width=800,
                height=400,
                hovermode='x unified',
                showlegend=True
            )
            
            trait_charts.append(fig)
            trait_analyses.append({
                'name': trait_name,
                'trend': trend_desc,
                'icon': trend_icon,
                'color': trend_color,
                'change': change,
                'change_pct': change_pct,
                'start_avg': start_avg,
                'end_avg': end_avg,
                'slope': drift_analysis[trait]['slope'] if trait in drift_analysis else 0,
                'r_squared': drift_analysis[trait]['r_squared'] if trait in drift_analysis else 0
            })
    
    # Create drift analysis chart
    if drift_analysis:
        drift_fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Drift Direction', 'Trend Strength'),
            specs=[[{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        traits = list(drift_analysis.keys())
        trait_names = []
        for trait in traits:
            if trait.startswith('big5_'):
                trait_names.append(f"B5: {trait.replace('big5_', '').replace('_', ' ').title()}")
            elif trait.startswith('partner_'):
                trait_names.append(f"P: {trait.replace('partner_', '').replace('_', ' ').title()}")
            elif trait in ['engagement_rate', 'comment_rate', 'like_rate']:
                trait_names.append(f"E: {trait.replace('_', ' ').title()}")
            else:
                trait_names.append(trait.replace('_', ' ').title())
        
        slopes = [drift_analysis[trait]['slope'] for trait in traits]
        r_squared = [drift_analysis[trait]['r_squared'] for trait in traits]
        
        # Drift direction (positive slopes up, negative slopes down)
        colors_drift = ['#28a745' if slope > 0 else '#dc3545' for slope in slopes]
        
        drift_fig.add_trace(
            go.Bar(
                x=trait_names,
                y=slopes,  # Use actual slopes (positive/negative) instead of absolute values
                name='Drift Direction',
                marker_color=colors_drift
            ),
            row=1, col=1
        )
        
        # R-squared values
        drift_fig.add_trace(
            go.Bar(
                x=trait_names,
                y=r_squared,
                name='Trend Strength',
                marker_color='#2E86AB'
            ),
            row=1, col=2
        )
        
        drift_fig.update_layout(
            title="Comprehensive Drift Analysis",
            title_x=0.5,
            title_font_size=20,
            height=500,
            showlegend=False
        )
        
        drift_fig.update_xaxes(tickangle=-45, row=1, col=1)
        drift_fig.update_xaxes(tickangle=-45, row=1, col=2)
    else:
        drift_fig = go.Figure().add_annotation(text="No drift data available", 
                                             xref="paper", yref="paper", x=0.5, y=0.5)
    
    # Create HTML template
    html_template = f"""<!DOCTYPE html>
<html>
<head>
    <title>Content-Personality Analysis: Evolution Tracking</title>
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
        .maturation-high {{ color: #28a745; }}
        .maturation-medium {{ color: #fd7e14; }}
        .maturation-low {{ color: #dc3545; }}
        .highlight {{
            background: #e3f2fd;
            border: 1px solid #2196f3;
            color: #1565c0;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }}
        .evolution {{
            background: #f3e5f5;
            border: 1px solid #9c27b0;
            color: #4a148c;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }}
        .trend-analysis {{
            margin-top: 15px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #007bff;
        }}
        .trend-header h4 {{
            margin: 0 0 10px 0;
            font-size: 1.1em;
        }}
        .trend-stats {{
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            margin-bottom: 10px;
        }}
        .trend-stats span {{
            background: white;
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 0.9em;
            border: 1px solid #dee2e6;
        }}
        .trend-interpretation {{
            font-style: italic;
            color: #495057;
            margin-top: 10px;
            padding: 10px;
            background: white;
            border-radius: 4px;
        }}
        .category-header {{
            background: linear-gradient(135deg, #6c757d, #495057);
            color: white;
            padding: 15px;
            margin: 30px 0 10px 0;
            border-radius: 8px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Evolution Tracking</h1>
        <h2>Comprehensive Time-Series Analysis</h2>
        <p>Personality traits, engagement metrics, and composite scores evolution over time</p>
    </div>
    
    <div class="insights">
        <h3>Evolution Tracking Summary</h3>
        <div class="metric">
            <div class="score maturation-{'high' if maturation_score >= 60 else 'medium' if maturation_score >= 40 else 'low'}">{maturation_score:.1f}</div>
            <div>Maturation Score</div>
            <small>{maturation_stage}</small>
        </div>
        <div class="metric">
            <div class="score">{significant_drifts}</div>
            <div>Significant Drifts</div>
            <small>Across all metrics</small>
        </div>
        <div class="metric">
            <div class="score">{overall_stability:.2f}</div>
            <div>Overall Stability</div>
            <small>Higher is better</small>
        </div>
        <div class="metric">
            <div class="score">{len(trait_charts)}</div>
            <div>Metrics Tracked</div>
            <small>Individual analyses</small>
        </div>
    </div>
    
    <div class="highlight">
        <strong>🔍 Evolution Insight:</strong> 
        Content maturation level: {maturation_stage} ({maturation_score:.1f}/100). 
        Most significant drift detected in {most_drifted_trait.replace('_', ' ').title()} metric. 
        {significant_drifts} metrics show notable evolution patterns across {len(trait_charts)} tracked parameters.
    </div>
    
    <div class="evolution">
        <strong>📈 Development Trajectory:</strong> 
        Overall stability: {overall_stability:.2f}. 
        Brand consistency evolution: {consistency_improvement:+.2f} points.
        Analysis based on {len(df)} posts with {window_size}-post rolling windows across personality, partnership, engagement, and composite metrics.
    </div>
    
    <div class="chart-container">
        <h3>📈 Individual Metric Evolution Analysis</h3>
        <p>Each chart shows the evolution of a specific metric over time with trend analysis and statistical significance.</p>
    </div>
    
    {''.join([f'''
    <div class="chart-container">
        <div id="trait-chart-{i}"></div>
        <div class="trend-analysis">
            <div class="trend-header" style="color: {analysis['color']};">
                <h4>{analysis['icon']} {analysis['name']}: {analysis['trend']}</h4>
            </div>
            <div class="trend-details">
                <div class="trend-stats">
                    <span><strong>Change:</strong> {analysis['change']:+.2f} points ({analysis['change_pct']:+.1f}%)</span>
                    <span><strong>Early Average:</strong> {analysis['start_avg']:.2f}</span>
                    <span><strong>Recent Average:</strong> {analysis['end_avg']:.2f}</span>
                    {f"<span><strong>Trend Strength (R²):</strong> {analysis['r_squared']:.3f}</span>" if analysis['r_squared'] > 0 else ""}
                </div>
                <div class="trend-interpretation">
                    {get_trend_interpretation(analysis)}
                </div>
            </div>
        </div>
    </div>
    ''' for i, analysis in enumerate(trait_analyses)])}
    
    <div class="chart-container">
        <h3>📊 Comprehensive Drift Analysis Summary</h3>
        <p>Overview of all metric trends showing direction and statistical strength.</p>
        <div id="drift-chart"></div>
    </div>
    
    <script>
        {''.join([f"Plotly.newPlot('trait-chart-{i}', {chart.to_json()});" for i, chart in enumerate(trait_charts)])}
        Plotly.newPlot('drift-chart', {drift_fig.to_json()});
    </script>
</body>
</html>"""
    
    # Save to HTML file
    with open('evolution_tracking.html', 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print("Evolution tracking analysis saved to 'evolution_tracking.html'")
    print(f"Maturation score: {maturation_score:.1f} ({maturation_stage})")
    print(f"Significant drifts: {significant_drifts}")
    print(f"Most drifted metric: {most_drifted_trait.replace('_', ' ').title()}")
    print(f"Overall stability: {overall_stability:.2f}")
    print(f"Total metrics analyzed: {len(trait_charts)}")
    
    return df_sorted

if __name__ == "__main__":
    generate_evolution_tracking() 