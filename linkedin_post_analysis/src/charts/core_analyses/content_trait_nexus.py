#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Content-Trait Nexus Analysis - Phase 6
Analyzes the intersection between content topics and personality traits
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

def analyze_topic_trait_relationships(df):
    """Analyze relationships between topics and personality traits"""
    trait_cols = [col for col in df.columns if col.startswith(('big5_', 'partner_'))]
    
    # Expand topic_tags into individual columns
    all_topics = set()
    for topics in df['topic_tags']:
        if isinstance(topics, list):
            all_topics.update(topics)
        elif isinstance(topics, str):
            topics_clean = topics.strip('[]').replace("'", "").replace('"', '')
            if topics_clean:
                topic_list = [t.strip() for t in topics_clean.split(',')]
                all_topics.update(topic_list)
    
    # Remove empty topics and 'Other'
    all_topics = {topic for topic in all_topics if topic and topic.strip() and topic != 'Other'}
    
    # Create topic-trait correlation matrix
    topic_trait_correlations = {}
    topic_trait_averages = {}
    
    for topic in all_topics:
        # Create binary column for this topic
        df[f'topic_{topic}'] = df['topic_tags'].apply(
            lambda x: topic in (x if isinstance(x, list) else 
                              [t.strip() for t in str(x).strip('[]').replace("'", "").replace('"', '').split(',') if t.strip()])
        )
        
        # Calculate average trait scores for posts with this topic
        topic_posts = df[df[f'topic_{topic}'] == True]
        if len(topic_posts) > 0:
            topic_trait_averages[topic] = {}
            for trait in trait_cols:
                avg_score = topic_posts[trait].mean()
                topic_trait_averages[topic][trait] = avg_score
                
                # Calculate correlation between topic presence and trait
                correlation = df[f'topic_{topic}'].astype(int).corr(df[trait])
                topic_trait_correlations[f"{topic}_{trait}"] = correlation
    
    return topic_trait_correlations, topic_trait_averages, all_topics

def calculate_topic_authority_scores(df, topic_trait_averages):
    """Calculate topic authority based on strategic thinking and reliability"""
    topic_authority = {}
    
    for topic, traits in topic_trait_averages.items():
        # Authority = weighted combination of strategic thinking and reliability
        strategic_score = traits.get('partner_strategic_thinking', 0)
        reliability_score = traits.get('partner_reliability', 0)
        integrity_score = traits.get('partner_integrity_trust', 0)
        
        # Weighted authority score (strategic thinking 40%, reliability 35%, integrity 25%)
        authority_score = (strategic_score * 0.4 + reliability_score * 0.35 + integrity_score * 0.25)
        
        # Get post count for this topic
        topic_posts = df[df['topic_tags'].apply(
            lambda x: topic in (x if isinstance(x, list) else 
                              [t.strip() for t in str(x).strip('[]').replace("'", "").replace('"', '').split(',') if t.strip()])
        )]
        post_count = len(topic_posts)
        
        topic_authority[topic] = {
            'authority_score': authority_score,
            'post_count': post_count,
            'strategic_thinking': strategic_score,
            'reliability': reliability_score,
            'integrity_trust': integrity_score,
            'avg_engagement': topic_posts['engagement_rate'].mean() if len(topic_posts) > 0 else 0
        }
    
    return topic_authority

def analyze_skill_complementarity(topic_trait_averages):
    """Analyze skill complementarity between different topics"""
    topics = list(topic_trait_averages.keys())
    complementarity_matrix = np.zeros((len(topics), len(topics)))
    
    for i, topic1 in enumerate(topics):
        for j, topic2 in enumerate(topics):
            if i != j:
                # Calculate complementarity as inverse of similarity
                traits1 = np.array(list(topic_trait_averages[topic1].values()))
                traits2 = np.array(list(topic_trait_averages[topic2].values()))
                
                # Cosine similarity
                similarity = np.dot(traits1, traits2) / (np.linalg.norm(traits1) * np.linalg.norm(traits2))
                complementarity = 1 - similarity  # Higher complementarity = lower similarity
                complementarity_matrix[i, j] = complementarity
    
    return complementarity_matrix, topics

def create_content_trait_bubble_chart(df, topic_authority):
    """Create bubble chart showing post count vs strategic thinking vs integrity trust"""
    topics = []
    post_counts = []
    strategic_scores = []
    integrity_scores = []
    authority_scores = []
    
    for topic, data in topic_authority.items():
        if data['post_count'] > 2:  # Only include topics with sufficient posts
            topics.append(topic.replace('_', ' ').title())
            post_counts.append(data['post_count'])
            strategic_scores.append(data['strategic_thinking'])
            integrity_scores.append(data['integrity_trust'])
            authority_scores.append(data['authority_score'])
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=strategic_scores,
        y=integrity_scores,
        mode='markers+text',
        marker=dict(
            size=[count * 3 for count in post_counts],
            color=authority_scores,
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="Authority Score"),
            line=dict(width=2, color='white'),
            opacity=0.8
        ),
        text=topics,
        textposition='middle center',
        textfont=dict(size=10, color='white'),
        hovertemplate='<b>%{text}</b><br>' +
                     'Strategic Thinking: %{x:.2f}<br>' +
                     'Integrity Trust: %{y:.2f}<br>' +
                     'Posts: %{marker.size}<br>' +
                     'Authority Score: %{marker.color:.2f}<br>' +
                     '<extra></extra>',
        name='Topics'
    ))
    
    fig.update_layout(
        title="Content-Trait Nexus: Topic Authority Landscape",
        title_x=0.5,
        title_font_size=20,
        xaxis_title="Strategic Thinking Score",
        yaxis_title="Integrity Trust Score",
        width=800,
        height=600,
        margin=dict(t=80, b=50, l=50, r=50),
        plot_bgcolor='rgba(240,240,240,0.8)'
    )
    
    return fig

def create_topic_trait_heatmap(topic_trait_averages):
    """Create heatmap showing average trait scores by topic"""
    if not topic_trait_averages:
        return go.Figure()
    
    topics = list(topic_trait_averages.keys())
    traits = list(next(iter(topic_trait_averages.values())).keys())
    
    # Create matrix
    matrix = np.zeros((len(topics), len(traits)))
    for i, topic in enumerate(topics):
        for j, trait in enumerate(traits):
            matrix[i, j] = topic_trait_averages[topic][trait]
    
    # Clean up labels
    clean_topics = [topic.replace('_', ' ').title() for topic in topics]
    clean_traits = [trait.replace('big5_', 'B5: ').replace('partner_', 'P: ').replace('_', ' ').title() for trait in traits]
    
    fig = go.Figure(data=go.Heatmap(
        z=matrix,
        x=clean_traits,
        y=clean_topics,
        colorscale='RdYlBu_r',
        text=np.round(matrix, 2),
        texttemplate="%{text}",
        textfont={"size": 10},
        hoverongaps=False,
        colorbar=dict(title="Average Score")
    ))
    
    fig.update_layout(
        title="Topic-Trait Intensity Heatmap",
        title_x=0.5,
        title_font_size=20,
        width=1000,
        height=600,
        margin=dict(t=80, b=100, l=200, r=50)
    )
    
    return fig

def create_topic_authority_ranking(topic_authority):
    """Create ranking chart of topic authority scores"""
    # Sort topics by authority score
    sorted_topics = sorted(topic_authority.items(), key=lambda x: x[1]['authority_score'], reverse=True)
    
    topics = [item[0].replace('_', ' ').title() for item in sorted_topics]
    authority_scores = [item[1]['authority_score'] for item in sorted_topics]
    
    # Take top 10 topics
    topics = topics[:10]
    authority_scores = authority_scores[:10]
    
    fig = go.Figure()
    
    # Add authority score bars
    fig.add_trace(go.Bar(
        y=topics,
        x=authority_scores,
        orientation='h',
        name='Authority Score',
        marker_color='#2E86AB',
        text=[f"{score:.2f}" for score in authority_scores],
        textposition='outside'
    ))
    
    fig.update_layout(
        title="Topic Authority Ranking",
        title_x=0.5,
        title_font_size=20,
        xaxis_title="Authority Score (Strategic + Reliability + Integrity)",
        yaxis_title="Content Topics",
        width=800,
        height=600,
        margin=dict(t=80, b=50, l=200, r=100)
    )
    
    return fig

def create_skill_complementarity_matrix(complementarity_matrix, topics):
    """Create heatmap showing skill complementarity between topics"""
    clean_topics = [topic.replace('_', ' ').title() for topic in topics]
    
    fig = go.Figure(data=go.Heatmap(
        z=complementarity_matrix,
        x=clean_topics,
        y=clean_topics,
        colorscale='Viridis',
        text=np.round(complementarity_matrix, 2),
        texttemplate="%{text}",
        textfont={"size": 10},
        hoverongaps=False,
        colorbar=dict(title="Complementarity Score")
    ))
    
    fig.update_layout(
        title="Skill Complementarity Matrix",
        title_x=0.5,
        title_font_size=20,
        width=800,
        height=700,
        margin=dict(t=80, b=100, l=150, r=50)
    )
    
    return fig

def generate_content_trait_nexus():
    """Generate complete content-trait nexus analysis"""
    print("Loading data for content-trait nexus analysis...")
    df = load_and_merge_data()
    
    print("Analyzing topic-trait relationships...")
    topic_trait_correlations, topic_trait_averages, all_topics = analyze_topic_trait_relationships(df)
    
    print("Calculating topic authority scores...")
    topic_authority = calculate_topic_authority_scores(df, topic_trait_averages)
    
    print("Analyzing skill complementarity...")
    complementarity_matrix, topics = analyze_skill_complementarity(topic_trait_averages)
    
    print("Creating visualizations...")
    bubble_fig = create_content_trait_bubble_chart(df, topic_authority)
    heatmap_fig = create_topic_trait_heatmap(topic_trait_averages)
    authority_fig = create_topic_authority_ranking(topic_authority)
    complementarity_fig = create_skill_complementarity_matrix(complementarity_matrix, topics)
    
    # Calculate key insights
    if topic_authority:
        top_authority_topic = max(topic_authority.items(), key=lambda x: x[1]['authority_score'])
        most_posts_topic = max(topic_authority.items(), key=lambda x: x[1]['post_count'])
        highest_engagement_topic = max(topic_authority.items(), key=lambda x: x[1]['avg_engagement'])
        
        # Find most complementary topic pair
        max_complementarity = 0
        most_complementary_pair = ""
        for i, topic1 in enumerate(topics):
            for j, topic2 in enumerate(topics):
                if i < j and complementarity_matrix[i, j] > max_complementarity:
                    max_complementarity = complementarity_matrix[i, j]
                    most_complementary_pair = f"{topic1} & {topic2}"
    else:
        top_authority_topic = ("No Data", {"authority_score": 0})
        most_posts_topic = ("No Data", {"post_count": 0})
        highest_engagement_topic = ("No Data", {"avg_engagement": 0})
        most_complementary_pair = "No Data"
        max_complementarity = 0
    
    # Create HTML template
    html_template = f"""<!DOCTYPE html>
<html>
<head>
    <title>Content-Personality Analysis: Content-Trait Nexus</title>
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
        .highlight {{
            background: #e3f2fd;
            border: 1px solid #2196f3;
            color: #1565c0;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Content-Trait Nexus Analysis</h1>
        <h2>The Intersection of Content & Personality</h2>
        <p>Analysis of how personality traits manifest across different content topics</p>
    </div>
    
    <div class="insights">
        <h3>Key Nexus Insights</h3>
        <div class="metric">
            <div class="score">{top_authority_topic[0].replace('_', ' ').title()}</div>
            <div>Highest Authority Topic</div>
            <small>Score: {top_authority_topic[1]['authority_score']:.2f}/5</small>
        </div>
        <div class="metric">
            <div class="score">{most_posts_topic[0].replace('_', ' ').title()}</div>
            <div>Most Frequent Topic</div>
            <small>{most_posts_topic[1]['post_count']} posts</small>
        </div>
        <div class="metric">
            <div class="score">{highest_engagement_topic[0].replace('_', ' ').title()}</div>
            <div>Highest Engagement Topic</div>
            <small>{highest_engagement_topic[1]['avg_engagement']:.1%} rate</small>
        </div>
        <div class="metric">
            <div class="score">{most_complementary_pair.replace('_', ' ').title()}</div>
            <div>Most Complementary Pair</div>
            <small>Complementarity: {max_complementarity:.2f}</small>
        </div>
    </div>
    
    <div class="highlight">
        <strong>Strategic Insight:</strong> 
        The topic "{top_authority_topic[0].replace('_', ' ').title()}" shows the highest authority score ({top_authority_topic[1]['authority_score']:.2f}), 
        indicating strong strategic thinking, reliability, and integrity in this content area.
    </div>
    
    <div class="chart-container">
        <div id="bubble-chart"></div>
    </div>
    
    <div class="grid-2">
        <div class="chart-container">
            <div id="authority-chart"></div>
        </div>
        <div class="chart-container">
            <div id="complementarity-chart"></div>
        </div>
    </div>
    
    <div class="chart-container">
        <div id="heatmap-chart"></div>
    </div>
    
    <script>
        Plotly.newPlot('bubble-chart', {bubble_fig.to_json()});
        Plotly.newPlot('authority-chart', {authority_fig.to_json()});
        Plotly.newPlot('complementarity-chart', {complementarity_fig.to_json()});
        Plotly.newPlot('heatmap-chart', {heatmap_fig.to_json()});
    </script>
</body>
</html>"""
    
    # Save to HTML file
    with open('content_trait_nexus.html', 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print("Content-trait nexus analysis saved to 'content_trait_nexus.html'")
    print(f"Top Authority Topic: {top_authority_topic[0]} (Score: {top_authority_topic[1]['authority_score']:.2f})")
    print(f"Most Posts: {most_posts_topic[0]} ({most_posts_topic[1]['post_count']} posts)")
    print(f"Highest Engagement: {highest_engagement_topic[0]} ({highest_engagement_topic[1]['avg_engagement']:.1%})")
    print(f"Most Complementary: {most_complementary_pair} ({max_complementarity:.2f})")
    
    return df, topic_authority, complementarity_matrix

if __name__ == "__main__":
    generate_content_trait_nexus() 