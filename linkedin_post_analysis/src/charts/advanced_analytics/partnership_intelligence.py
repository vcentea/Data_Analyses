#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Partnership Intelligence - Phase 9
Advanced partnership compatibility analysis and strategic alignment metrics
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_loader import load_and_merge_data

def generate_partnership_intelligence():
    """Generate complete partnership intelligence analysis"""
    print("Loading data for partnership intelligence...")
    df = load_and_merge_data()
    
    # Partnership trait analysis
    partner_traits = [col for col in df.columns if col.startswith('partner_')]
    trait_scores = {trait.replace('partner_', '').replace('_', ' ').title(): df[trait].mean() 
                   for trait in partner_traits}
    
    # Define benchmarks and interpretations
    benchmarks = {
        'Integrity Trust': {'excellent': 4.5, 'good': 3.5, 'needs_improvement': 2.5},
        'Reliability': {'excellent': 4.5, 'good': 3.5, 'needs_improvement': 2.5},
        'Collaboration': {'excellent': 4.0, 'good': 3.0, 'needs_improvement': 2.0},
        'Adaptability': {'excellent': 4.0, 'good': 3.0, 'needs_improvement': 2.0},
        'Risk Tolerance': {'excellent': 3.5, 'good': 2.5, 'needs_improvement': 1.5},
        'Strategic Thinking': {'excellent': 4.0, 'good': 3.0, 'needs_improvement': 2.0},
        'Leadership': {'excellent': 4.0, 'good': 3.0, 'needs_improvement': 2.0}
    }
    
    # Calculate overall partnership readiness
    overall_score = np.mean(list(trait_scores.values()))
    partnership_readiness = "Excellent" if overall_score >= 4.0 else "Good" if overall_score >= 3.0 else "Developing"
    
    # Create comprehensive partnership dashboard
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Partnership Skills Assessment', 'Skills vs Industry Benchmarks', 
                       'Partnership Readiness Matrix', 'Risk-Reward Profile'),
        specs=[[{"type": "bar"}, {"type": "scatter"}],
               [{"type": "scatter"}, {"type": "bar"}]]
    )
    
    # 1. Partnership Skills Bar Chart with color coding
    traits = list(trait_scores.keys())
    scores = list(trait_scores.values())
    colors = []
    for trait, score in trait_scores.items():
        if score >= benchmarks[trait]['excellent']:
            colors.append('#2E8B57')  # Green - Excellent
        elif score >= benchmarks[trait]['good']:
            colors.append('#FFD700')  # Gold - Good
        else:
            colors.append('#FF6B6B')  # Red - Needs Improvement
    
    fig.add_trace(
        go.Bar(x=traits, y=scores, marker_color=colors, name="Your Scores",
               text=[f"{s:.1f}" for s in scores], textposition='outside'),
        row=1, col=1
    )
    
    # 2. Benchmark Comparison
    for i, (trait, score) in enumerate(trait_scores.items()):
        fig.add_trace(
            go.Scatter(x=[benchmarks[trait]['excellent']], y=[i], 
                      mode='markers', marker=dict(color='green', size=12, symbol='diamond'),
                      name='Excellent' if i == 0 else '', showlegend=i==0),
            row=1, col=2
        )
        fig.add_trace(
            go.Scatter(x=[benchmarks[trait]['good']], y=[i], 
                      mode='markers', marker=dict(color='gold', size=10, symbol='circle'),
                      name='Good' if i == 0 else '', showlegend=i==0),
            row=1, col=2
        )
        fig.add_trace(
            go.Scatter(x=[score], y=[i], 
                      mode='markers', marker=dict(color='blue', size=14, symbol='star'),
                      name='Your Score' if i == 0 else '', showlegend=i==0),
            row=1, col=2
        )
    
    # 3. Partnership Readiness Matrix
    collaboration_score = trait_scores.get('Collaboration', 0)
    leadership_score = trait_scores.get('Leadership', 0)
    
    fig.add_trace(
        go.Scatter(x=[collaboration_score], y=[leadership_score],
                  mode='markers+text', marker=dict(color='red', size=20),
                  text=['YOU'], textposition='middle center',
                  name='Your Position'),
        row=2, col=1
    )
    
    # Add quadrant lines
    fig.add_hline(y=3.0, line_dash="dash", line_color="gray", row=2, col=1)
    fig.add_vline(x=3.0, line_dash="dash", line_color="gray", row=2, col=1)
    
    # 4. Risk-Reward Profile
    risk_tolerance = trait_scores.get('Risk Tolerance', 0)
    strategic_thinking = trait_scores.get('Strategic Thinking', 0)
    
    risk_categories = ['Conservative', 'Balanced', 'Aggressive']
    risk_values = [2.0, 3.0, 4.0]  # Example values
    your_risk_level = 'Conservative' if risk_tolerance < 2.5 else 'Balanced' if risk_tolerance < 3.5 else 'Aggressive'
    
    fig.add_trace(
        go.Bar(x=risk_categories, y=risk_values, 
               marker_color=['lightblue' if cat != your_risk_level else 'darkblue' for cat in risk_categories],
               name="Risk Profile"),
        row=2, col=2
    )
    
    # Update layout
    fig.update_layout(
        height=800,
        title_text="Partnership Intelligence Dashboard",
        title_x=0.5,
        title_font_size=24,
        showlegend=True
    )
    
    # Update axes
    fig.update_xaxes(title_text="Partnership Skills", row=1, col=1)
    fig.update_yaxes(title_text="Score (1-5)", row=1, col=1, range=[0, 5])
    
    fig.update_xaxes(title_text="Score (1-5)", row=1, col=2, range=[0, 5])
    fig.update_yaxes(title_text="Skills", row=1, col=2, ticktext=traits, tickvals=list(range(len(traits))))
    
    fig.update_xaxes(title_text="Collaboration Skills", row=2, col=1, range=[0, 5])
    fig.update_yaxes(title_text="Leadership Skills", row=2, col=1, range=[0, 5])
    
    fig.update_xaxes(title_text="Risk Profile", row=2, col=2)
    fig.update_yaxes(title_text="Preference Level", row=2, col=2)
    
    # Generate insights
    strengths = [trait for trait, score in trait_scores.items() 
                if score >= benchmarks[trait]['excellent']]
    development_areas = [trait for trait, score in trait_scores.items() 
                        if score < benchmarks[trait]['good']]
    
    # Create detailed HTML report
    html_template = f"""<!DOCTYPE html>
<html>
<head>
    <title>Partnership Intelligence Report</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f8f9fa;
            line-height: 1.6;
        }}
        .header {{
            text-align: center;
            background: linear-gradient(135deg, #2E86AB, #A23B72);
            color: white;
            padding: 40px;
            margin: -20px -20px 30px -20px;
            border-radius: 0 0 15px 15px;
        }}
        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .card {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            text-align: center;
            border-left: 5px solid #2E86AB;
        }}
        .score {{
            font-size: 36px;
            font-weight: bold;
            color: #2E86AB;
            margin: 10px 0;
        }}
        .chart-container {{
            background: white;
            margin: 30px 0;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        .insights {{
            background: linear-gradient(135deg, #f8f9fa, #e9ecef);
            padding: 30px;
            margin: 30px 0;
            border-radius: 15px;
            border-left: 5px solid #28a745;
        }}
        .insight-section {{
            margin: 20px 0;
        }}
        .strength {{
            color: #28a745;
            font-weight: bold;
        }}
        .development {{
            color: #dc3545;
            font-weight: bold;
        }}
        .recommendation {{
            background: #fff3cd;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #ffc107;
            margin: 10px 0;
        }}
        .legend {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin: 20px 0;
            flex-wrap: wrap;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🤝 Partnership Intelligence Report</h1>
        <h2>Strategic Compatibility & Collaboration Assessment</h2>
        <p>Comprehensive analysis of partnership readiness and strategic alignment capabilities</p>
    </div>
    
    <div class="summary-cards">
        <div class="card">
            <h3>Overall Partnership Score</h3>
            <div class="score">{overall_score:.1f}/5.0</div>
            <p><strong>{partnership_readiness}</strong> Partnership Readiness</p>
        </div>
        <div class="card">
            <h3>Top Strength</h3>
            <div class="score">{max(trait_scores.values()):.1f}</div>
            <p><strong>{max(trait_scores.keys(), key=trait_scores.get)}</strong></p>
        </div>
        <div class="card">
            <h3>Development Priority</h3>
            <div class="score">{min(trait_scores.values()):.1f}</div>
            <p><strong>{min(trait_scores.keys(), key=trait_scores.get)}</strong></p>
        </div>
        <div class="card">
            <h3>Partnership Risk Level</h3>
            <div class="score">{"Low" if overall_score >= 4.0 else "Medium" if overall_score >= 3.0 else "High"}</div>
            <p>Based on overall assessment</p>
        </div>
    </div>
    
    <div class="legend">
        <div class="legend-item">
            <div class="legend-color" style="background-color: #2E8B57;"></div>
            <span>Excellent (4.0+ for most skills)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #FFD700;"></div>
            <span>Good (3.0-3.9 for most skills)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background-color: #FF6B6B;"></div>
            <span>Needs Development (Below 3.0)</span>
        </div>
    </div>
    
    <div class="chart-container">
        <div id="partnership-dashboard"></div>
    </div>
    
    <div class="insights">
        <h3>🎯 Partnership Intelligence Insights</h3>
        
        <div class="insight-section">
            <h4>Key Strengths:</h4>
            <ul>
                {"".join([f"<li class='strength'>{strength}: Excellent partnership asset</li>" for strength in strengths]) if strengths else "<li>Focus on developing core partnership skills</li>"}
            </ul>
        </div>
        
        <div class="insight-section">
            <h4>Development Areas:</h4>
            <ul>
                {"".join([f"<li class='development'>{area}: Requires attention for optimal partnerships</li>" for area in development_areas]) if development_areas else "<li>All skills are at good or excellent levels</li>"}
            </ul>
        </div>
        
        <div class="insight-section">
            <h4>Strategic Recommendations:</h4>
            <div class="recommendation">
                <strong>Partnership Strategy:</strong> 
                {"Leverage your strong partnership skills to build strategic alliances. Focus on partnerships where your strengths complement others' capabilities." if overall_score >= 3.5 else "Develop core partnership skills before pursuing complex strategic alliances. Consider mentorship or partnership training programs."}
            </div>
            <div class="recommendation">
                <strong>Risk Management:</strong> 
                {"Your balanced risk profile makes you suitable for diverse partnership types. Consider both conservative and growth-oriented partnerships." if trait_scores.get('Risk Tolerance', 0) >= 2.5 and trait_scores.get('Risk Tolerance', 0) <= 3.5 else "Your risk profile suggests focusing on partnerships that align with your comfort level."}
            </div>
            <div class="recommendation">
                <strong>Leadership Role:</strong> 
                {"Your leadership skills position you well for leading partnership initiatives and collaborative projects." if trait_scores.get('Leadership', 0) >= 3.5 else "Consider developing leadership skills to enhance your partnership effectiveness and influence."}
            </div>
        </div>
        
        <div class="insight-section">
            <h4>Partnership Readiness Matrix Interpretation:</h4>
            <p><strong>Your Position:</strong> 
            {"High Collaboration + High Leadership = Ideal partnership leader" if collaboration_score >= 3.0 and leadership_score >= 3.0 else
             "High Collaboration + Developing Leadership = Strong team player, develop leadership" if collaboration_score >= 3.0 else
             "Developing Collaboration + High Leadership = Strong leader, enhance collaboration" if leadership_score >= 3.0 else
             "Focus on developing both collaboration and leadership skills"}
            </p>
        </div>
    </div>
    
    <script>
        var plotData = {fig.to_json()};
        Plotly.newPlot('partnership-dashboard', plotData.data, plotData.layout, {{responsive: true}});
    </script>
</body>
</html>"""
    
    # Save to HTML file
    with open('partnership_intelligence.html', 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print("✅ Partnership Intelligence analysis completed!")
    print(f"📊 Overall Partnership Score: {overall_score:.1f}/5.0 ({partnership_readiness})")
    print(f"💪 Top Strength: {max(trait_scores.keys(), key=trait_scores.get)} ({max(trait_scores.values()):.1f})")
    print(f"🎯 Development Priority: {min(trait_scores.keys(), key=trait_scores.get)} ({min(trait_scores.values()):.1f})")
    
    return df

if __name__ == "__main__":
    generate_partnership_intelligence() 