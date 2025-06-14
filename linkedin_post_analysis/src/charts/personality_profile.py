#!/usr/bin/env python3
"""
Personality Profile Analysis
Creates Big Five and Partner traits radar charts and comparison visualizations
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from data_loader import load_and_merge_data, get_data_summary

def create_big_five_radar(summary):
    """Create Big Five personality radar chart"""
    traits = list(summary['personality_averages'].keys())
    values = list(summary['personality_averages'].values())
    
    # Add first value at end to close the radar chart
    traits_closed = traits + [traits[0]]
    values_closed = values + [values[0]]
    
    fig = go.Figure()
    
    # Add the main profile
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=traits_closed,
        fill='toself',
        name='Your Profile',
        line_color='#2E86AB',
        fillcolor='rgba(46, 134, 171, 0.3)',
        line_width=3
    ))
    
    # Add average benchmarks (typical scores around 3.0)
    benchmark_values = [3.0] * len(traits) + [3.0]
    fig.add_trace(go.Scatterpolar(
        r=benchmark_values,
        theta=traits_closed,
        fill='toself',
        name='Average Benchmark',
        line_color='#A23B72',
        fillcolor='rgba(162, 59, 114, 0.1)',
        line_width=2,
        line_dash='dash'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5],
                tickvals=[1, 2, 3, 4, 5],
                ticktext=['1', '2', '3', '4', '5'],
                gridcolor='lightgray'
            ),
            angularaxis=dict(
                tickfont_size=14,
                rotation=90
            )
        ),
        title={
            'text': "🧠 Big Five Personality Profile",
            'x': 0.5,
            'font': {'size': 20}
        },
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        ),
        height=500,
        margin=dict(t=80, b=100, l=50, r=50)
    )
    
    return fig

def create_partner_traits_radar(summary):
    """Create Partner traits radar chart"""
    traits = list(summary['partner_averages'].keys())
    values = list(summary['partner_averages'].values())
    
    # Format trait names for display
    trait_labels = [trait.replace('_', ' ').title() for trait in traits]
    
    # Add first value at end to close the radar chart
    traits_closed = trait_labels + [trait_labels[0]]
    values_closed = values + [values[0]]
    
    fig = go.Figure()
    
    # Add the main profile
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=traits_closed,
        fill='toself',
        name='Partnership Profile',
        line_color='#F18F01',
        fillcolor='rgba(241, 143, 1, 0.3)',
        line_width=3
    ))
    
    # Add ideal partner benchmark (higher scores for partnership)
    ideal_values = [4.0] * len(traits) + [4.0]
    fig.add_trace(go.Scatterpolar(
        r=ideal_values,
        theta=traits_closed,
        fill='toself',
        name='Ideal Partner',
        line_color='#2E86AB',
        fillcolor='rgba(46, 134, 171, 0.1)',
        line_width=2,
        line_dash='dash'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5],
                tickvals=[1, 2, 3, 4, 5],
                ticktext=['1', '2', '3', '4', '5'],
                gridcolor='lightgray'
            ),
            angularaxis=dict(
                tickfont_size=12,
                rotation=90
            )
        ),
        title={
            'text': "🤝 Partnership Traits Profile",
            'x': 0.5,
            'font': {'size': 20}
        },
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        ),
        height=500,
        margin=dict(t=80, b=100, l=50, r=50)
    )
    
    return fig

def create_trait_comparison_bars(summary):
    """Create trait comparison bar chart"""
    # Combine all traits
    all_traits = {}
    
    # Big Five traits
    for trait, score in summary['personality_averages'].items():
        all_traits[f"Big5: {trait.title()}"] = score
    
    # Partner traits
    for trait, score in summary['partner_averages'].items():
        all_traits[f"Partner: {trait.replace('_', ' ').title()}"] = score
    
    # Sort by score descending
    sorted_traits = dict(sorted(all_traits.items(), key=lambda x: x[1], reverse=True))
    
    # Create color mapping
    colors = ['#2E86AB' if 'Big5' in trait else '#F18F01' for trait in sorted_traits.keys()]
    
    fig = go.Figure(go.Bar(
        y=list(sorted_traits.keys()),
        x=list(sorted_traits.values()),
        orientation='h',
        marker_color=colors,
        text=[f"{v:.1f}" for v in sorted_traits.values()],
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Score: %{x:.1f}/5<extra></extra>'
    ))
    
    fig.update_layout(
        title="📊 All Traits Ranked by Strength",
        title_x=0.5,
        title_font_size=20,
        xaxis_title="Score (1-5)",
        yaxis_title="Traits",
        height=600,
        margin=dict(l=200, r=100, t=80, b=50),
        plot_bgcolor='white',
        font=dict(size=11),
        xaxis=dict(range=[0, 5])
    )
    
    fig.update_xaxes(showgrid=True, gridcolor='lightgray')
    fig.update_yaxes(showgrid=False)
    
    return fig

def create_personality_insights(summary):
    """Create personality insights and interpretations"""
    # Identify strongest and weakest traits
    all_scores = {**summary['personality_averages'], **summary['partner_averages']}
    strongest_trait = max(all_scores, key=all_scores.get)
    weakest_trait = min(all_scores, key=all_scores.get)
    
    # Calculate composite scores
    partnership_score = np.mean([
        summary['partner_averages']['integrity_trust'],
        summary['partner_averages']['reliability'], 
        summary['partner_averages']['collaboration']
    ])
    
    leadership_score = np.mean([
        summary['partner_averages']['strategic_thinking'],
        summary['personality_averages']['openness'],
        summary['partner_averages']['leadership']
    ])
    
    creativity_score = np.mean([
        summary['personality_averages']['openness'],
        summary['partner_averages']['adaptability'],
        summary['partner_averages']['risk_tolerance']
    ])
    
    # Create insights visualization
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            "Partnership Readiness", "Leadership Potential", 
            "Creative Innovation", "Trait Balance"
        ],
        specs=[[{"type": "indicator"}, {"type": "indicator"}],
               [{"type": "indicator"}, {"type": "bar"}]]
    )
    
    # Partnership gauge
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=partnership_score,
        number={"suffix": "/5", "font": {"size": 24}},
        gauge={
            "axis": {"range": [0, 5]},
            "bar": {"color": "#2E86AB"},
            "steps": [
                {"range": [0, 2.5], "color": "lightcoral"},
                {"range": [2.5, 3.5], "color": "yellow"},
                {"range": [3.5, 5], "color": "lightgreen"}
            ]
        },
        title={"text": "Partnership Score", "font": {"size": 14}}
    ), row=1, col=1)
    
    # Leadership gauge  
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=leadership_score,
        number={"suffix": "/5", "font": {"size": 24}},
        gauge={
            "axis": {"range": [0, 5]},
            "bar": {"color": "#F18F01"},
            "steps": [
                {"range": [0, 2.5], "color": "lightcoral"},
                {"range": [2.5, 3.5], "color": "yellow"},
                {"range": [3.5, 5], "color": "lightgreen"}
            ]
        },
        title={"text": "Leadership Potential", "font": {"size": 14}}
    ), row=1, col=2)
    
    # Creativity gauge
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=creativity_score,
        number={"suffix": "/5", "font": {"size": 24}},
        gauge={
            "axis": {"range": [0, 5]},
            "bar": {"color": "#A23B72"},
            "steps": [
                {"range": [0, 2.5], "color": "lightcoral"},
                {"range": [2.5, 3.5], "color": "yellow"},
                {"range": [3.5, 5], "color": "lightgreen"}
            ]
        },
        title={"text": "Creative Innovation", "font": {"size": 14}}
    ), row=2, col=1)
    
    # Trait balance bar
    balance_data = {
        'Highest': all_scores[strongest_trait],
        'Average': np.mean(list(all_scores.values())),
        'Lowest': all_scores[weakest_trait]
    }
    
    fig.add_trace(go.Bar(
        x=list(balance_data.keys()),
        y=list(balance_data.values()),
        marker_color=['#2E86AB', '#F18F01', '#A23B72'],
        text=[f"{v:.1f}" for v in balance_data.values()],
        textposition='outside'
    ), row=2, col=2)
    
    fig.update_layout(
        height=600,
        title_text="🎯 Personality Insights & Composite Scores",
        title_x=0.5,
        title_font_size=20,
        showlegend=False,
        margin=dict(t=80, b=50, l=50, r=50)
    )
    
    return fig, {
        'strongest_trait': strongest_trait,
        'weakest_trait': weakest_trait,
        'partnership_score': partnership_score,
        'leadership_score': leadership_score,
        'creativity_score': creativity_score
    }

def generate_personality_profile():
    """Generate complete personality profile analysis"""
    print("🔄 Loading data...")
    df = load_and_merge_data()
    summary = get_data_summary(df)
    
    print("🧠 Creating Big Five radar...")
    big_five_fig = create_big_five_radar(summary)
    
    print("🤝 Creating Partner traits radar...")
    partner_fig = create_partner_traits_radar(summary)
    
    print("📊 Creating trait comparison...")
    comparison_fig = create_trait_comparison_bars(summary)
    
    print("🎯 Generating insights...")
    insights_fig, insights_data = create_personality_insights(summary)
    
    # Create HTML template
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Content-Personality Analysis: Personality Profile</title>
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
            .trait-highlight {{
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
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🧠 Personality Profile Analysis</h1>
            <h2>Deep Dive into Content Creator Psychology</h2>
            <p>Analysis based on {summary['total_posts']} LinkedIn posts</p>
        </div>
        
        <div class="insights">
            <h3>🎯 Key Personality Insights</h3>
            <div class="trait-highlight">
                <div class="score">{insights_data['strongest_trait'].replace('_', ' ').title()}</div>
                <div>Strongest Trait</div>
                                 <small>Score: {max(list(summary['personality_averages'].values()) + list(summary['partner_averages'].values())):.1f}/5</small>
            </div>
            <div class="trait-highlight">
                <div class="score">{insights_data['partnership_score']:.1f}/5</div>
                <div>Partnership Readiness</div>
                <small>Trust + Reliability + Collaboration</small>
            </div>
            <div class="trait-highlight">
                <div class="score">{insights_data['leadership_score']:.1f}/5</div>
                <div>Leadership Potential</div>
                <small>Strategy + Openness + Leadership</small>
            </div>
            <div class="trait-highlight">
                <div class="score">{insights_data['creativity_score']:.1f}/5</div>
                <div>Creative Innovation</div>
                <small>Openness + Adaptability + Risk Taking</small>
            </div>
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
            <div class="chart-container">
                <div id="big-five-chart"></div>
            </div>
            <div class="chart-container">
                <div id="partner-chart"></div>
            </div>
        </div>
        
        <div class="chart-container">
            <div id="comparison-chart"></div>
        </div>
        
        <div class="chart-container">
            <div id="insights-chart"></div>
        </div>
        
        <script>
            Plotly.newPlot('big-five-chart', {big_five_fig.to_json()});
            Plotly.newPlot('partner-chart', {partner_fig.to_json()});
            Plotly.newPlot('comparison-chart', {comparison_fig.to_json()});
            Plotly.newPlot('insights-chart', {insights_fig.to_json()});
        </script>
    </body>
    </html>
    """
    
    # Save to HTML file
    with open('personality_profile.html', 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print("✅ Personality profile saved to 'personality_profile.html'")
    return df, summary

if __name__ == "__main__":
    generate_personality_profile() 