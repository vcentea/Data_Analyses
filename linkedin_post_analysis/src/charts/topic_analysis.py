#!/usr/bin/env python3
"""
Topic Analysis Module
Analyzes content relationships, topic heatmaps, and authority patterns
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.figure_factory as ff
from collections import Counter, defaultdict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import LatentDirichletAllocation
import networkx as nx
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

from data_loader import load_and_merge_data

def analyze_topic_relationships(df):
    """Analyze relationships between different topics"""
    # Extract topics from topic_tags
    all_topics = []
    topic_cooccurrence = defaultdict(lambda: defaultdict(int))
    
    for topics in df['topic_tags']:
        if isinstance(topics, list):
            topic_list = topics
        else:
            # Handle string representation of list
            topic_list = str(topics).split(', ')
        
        all_topics.extend(topic_list)
        
        # Count co-occurrences
        for i, topic1 in enumerate(topic_list):
            for topic2 in topic_list[i+1:]:
                topic_cooccurrence[topic1][topic2] += 1
                topic_cooccurrence[topic2][topic1] += 1
    
    # Get most common topics
    topic_counts = Counter(all_topics)
    top_topics = dict(topic_counts.most_common(15))
    
    return top_topics, topic_cooccurrence

def create_topic_network(topic_cooccurrence, min_connections=2):
    """Create network graph of topic relationships"""
    G = nx.Graph()
    
    # Add edges based on co-occurrence
    for topic1, connections in topic_cooccurrence.items():
        for topic2, weight in connections.items():
            if weight >= min_connections:
                G.add_edge(topic1, topic2, weight=weight)
    
    # Calculate centrality metrics
    try:
        centrality = nx.degree_centrality(G)
        betweenness = nx.betweenness_centrality(G)
        closeness = nx.closeness_centrality(G)
    except:
        centrality = {}
        betweenness = {}
        closeness = {}
    
    return G, centrality, betweenness, closeness

def analyze_topic_authority(df):
    """Analyze topic authority based on engagement and personality traits"""
    topic_authority = {}
    
    for _, row in df.iterrows():
        if isinstance(row['topic_tags'], list):
            topics = row['topic_tags']
        else:
            topics = str(row['topic_tags']).split(', ')
        
        # Calculate authority score based on engagement and traits
        engagement_score = row.get('combined', 0)
        expertise_score = row.get('big5_openness', 3) + row.get('partner_strategic_thinking', 3)
        consistency_score = row.get('big5_conscientiousness', 3)
        
        authority_score = (engagement_score * 0.4 + expertise_score * 0.4 + consistency_score * 0.2)
        
        for topic in topics:
            if topic not in topic_authority:
                topic_authority[topic] = {'scores': [], 'posts': 0, 'total_engagement': 0}
            
            topic_authority[topic]['scores'].append(authority_score)
            topic_authority[topic]['posts'] += 1
            topic_authority[topic]['total_engagement'] += engagement_score
    
    # Calculate final authority metrics
    for topic in topic_authority:
        scores = topic_authority[topic]['scores']
        topic_authority[topic]['avg_authority'] = np.mean(scores)
        topic_authority[topic]['consistency'] = 1 / (np.std(scores) + 1)  # Higher consistency = lower std
        topic_authority[topic]['avg_engagement'] = topic_authority[topic]['total_engagement'] / topic_authority[topic]['posts']
    
    return topic_authority

def create_topic_heatmap(df):
    """Create heatmap of topics vs personality traits"""
    # Get topics and traits
    all_topics = []
    for topics in df['topic_tags']:
        if isinstance(topics, list):
            all_topics.extend(topics)
        else:
            all_topics.extend(str(topics).split(', '))
    
    top_topics = [topic for topic, _ in Counter(all_topics).most_common(10)]
    
    # Personality traits to analyze
    traits = ['big5_openness', 'big5_conscientiousness', 'big5_extraversion', 
              'big5_agreeableness', 'partner_strategic_thinking', 'partner_leadership']
    
    # Create matrix
    heatmap_data = []
    for topic in top_topics:
        topic_rows = df[df['topic_tags'].apply(lambda x: topic in (x if isinstance(x, list) else str(x).split(', ')))]
        if len(topic_rows) > 0:
            topic_scores = []
            for trait in traits:
                if trait in topic_rows.columns:
                    score = topic_rows[trait].mean()
                    topic_scores.append(score)
                else:
                    topic_scores.append(3.0)  # Default neutral score
            heatmap_data.append(topic_scores)
        else:
            heatmap_data.append([3.0] * len(traits))
    
    return np.array(heatmap_data), top_topics, traits

def create_topic_evolution_timeline(df):
    """Create timeline showing topic evolution"""
    # Simulate time periods based on post order
    df_sorted = df.copy().reset_index(drop=True)
    n_periods = 5
    period_size = len(df_sorted) // n_periods
    
    timeline_data = {}
    
    for period in range(n_periods):
        start_idx = period * period_size
        end_idx = start_idx + period_size if period < n_periods - 1 else len(df_sorted)
        period_df = df_sorted.iloc[start_idx:end_idx]
        
        # Count topics in this period
        period_topics = []
        for topics in period_df['topic_tags']:
            if isinstance(topics, list):
                period_topics.extend(topics)
            else:
                period_topics.extend(str(topics).split(', '))
        
        topic_counts = Counter(period_topics)
        timeline_data[f'Period {period + 1}'] = dict(topic_counts.most_common(8))
    
    return timeline_data

def generate_topic_insights(top_topics, topic_authority, centrality_metrics):
    """Generate actionable insights about topics"""
    insights = []
    
    # Most popular topic
    most_popular = max(top_topics.items(), key=lambda x: x[1])
    insights.append(f"🏆 Most Popular Topic: '{most_popular[0]}' appears in {most_popular[1]} posts")
    
    # Highest authority topic
    if topic_authority:
        highest_authority = max(topic_authority.items(), key=lambda x: x[1]['avg_authority'])
        insights.append(f"👑 Highest Authority Topic: '{highest_authority[0]}' with authority score {highest_authority[1]['avg_authority']:.2f}")
    
    # Most connected topic (if network analysis worked)
    if centrality_metrics:
        most_central = max(centrality_metrics.items(), key=lambda x: x[1])
        insights.append(f"🌐 Most Connected Topic: '{most_central[0]}' connects to many other topics")
    
    # Engagement insights
    if topic_authority:
        best_engagement = max(topic_authority.items(), key=lambda x: x[1]['avg_engagement'])
        insights.append(f"📈 Best Engagement Topic: '{best_engagement[0]}' with {best_engagement[1]['avg_engagement']:.1f} avg engagement")
    
    return insights

def create_topic_visualizations(df, top_topics, topic_authority, heatmap_data, top_heatmap_topics, traits, timeline_data):
    """Create comprehensive topic analysis visualizations"""
    
    # Create subplot layout
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=[
            "Topic Popularity Distribution",
            "Topic Authority vs Engagement",
            "Topic-Personality Trait Heatmap",
            "Topic Evolution Timeline",
            "Topic Authority Scores",
            "Topic Consistency Analysis"
        ],
        specs=[
            [{"type": "bar"}, {"type": "scatter"}],
            [{"type": "heatmap"}, {"type": "scatter"}],
            [{"type": "bar"}, {"type": "bar"}]
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.1
    )
    
    # 1. Topic Popularity
    topics_list = list(top_topics.keys())[:10]
    counts_list = list(top_topics.values())[:10]
    
    fig.add_trace(
        go.Bar(
            x=counts_list,
            y=topics_list,
            orientation='h',
            marker_color='lightblue',
            name="Topic Count"
        ),
        row=1, col=1
    )
    
    # 2. Topic Authority vs Engagement
    if topic_authority:
        auth_topics = []
        auth_scores = []
        engagement_scores = []
        
        for topic, data in topic_authority.items():
            if topic in topics_list[:8]:  # Top topics only
                auth_topics.append(topic)
                auth_scores.append(data['avg_authority'])
                engagement_scores.append(data['avg_engagement'])
        
        fig.add_trace(
            go.Scatter(
                x=engagement_scores,
                y=auth_scores,
                mode='markers+text',
                text=auth_topics,
                textposition='top center',
                marker=dict(size=10, color='orange'),
                name="Authority vs Engagement"
            ),
            row=1, col=2
        )
    
    # 3. Topic-Personality Heatmap
    fig.add_trace(
        go.Heatmap(
            z=heatmap_data,
            x=[trait.replace('big5_', '').replace('partner_', '').title() for trait in traits],
            y=top_heatmap_topics,
            colorscale='RdYlBu_r',
            name="Topic-Trait Correlation"
        ),
        row=2, col=1
    )
    
    # 4. Topic Evolution Timeline
    if timeline_data:
        periods = list(timeline_data.keys())
        # Get top 3 topics across all periods
        all_timeline_topics = set()
        for period_data in timeline_data.values():
            all_timeline_topics.update(list(period_data.keys())[:3])
        
        for topic in list(all_timeline_topics)[:5]:  # Limit to 5 topics
            topic_evolution = []
            for period in periods:
                topic_evolution.append(timeline_data[period].get(topic, 0))
            
            fig.add_trace(
                go.Scatter(
                    x=periods,
                    y=topic_evolution,
                    mode='lines+markers',
                    name=topic[:20],  # Truncate long topic names
                    line=dict(width=2)
                ),
                row=2, col=2
            )
    
    # 5. Topic Authority Scores
    if topic_authority:
        auth_topics_sorted = sorted(
            [(k, v['avg_authority']) for k, v in topic_authority.items()],
            key=lambda x: x[1],
            reverse=True
        )[:8]
        
        fig.add_trace(
            go.Bar(
                x=[t[0] for t in auth_topics_sorted],
                y=[t[1] for t in auth_topics_sorted],
                marker_color='green',
                name="Authority Score"
            ),
            row=3, col=1
        )
    
    # 6. Topic Consistency Analysis
    if topic_authority:
        consistency_data = sorted(
            [(k, v['consistency']) for k, v in topic_authority.items()],
            key=lambda x: x[1],
            reverse=True
        )[:8]
        
        fig.add_trace(
            go.Bar(
                x=[t[0] for t in consistency_data],
                y=[t[1] for t in consistency_data],
                marker_color='purple',
                name="Consistency Score"
            ),
            row=3, col=2
        )
    
    # Update layout
    fig.update_layout(
        height=1200,
        title_text="📊 Comprehensive Topic Relationship Analysis",
        title_x=0.5,
        showlegend=False,
        template="plotly_white"
    )
    
    # Update x-axis labels for better readability
    fig.update_xaxes(tickangle=45, row=3, col=1)
    fig.update_xaxes(tickangle=45, row=3, col=2)
    
    return fig

def generate_topic_analysis(data_file: str = None):
    """Generate complete topic analysis"""
    print("Loading data for topic analysis...")
    df = load_and_merge_data(data_file)
    
    print("Analyzing topic relationships...")
    top_topics, topic_cooccurrence = analyze_topic_relationships(df)
    
    print("Creating topic network...")
    network_graph, centrality, betweenness, closeness = create_topic_network(topic_cooccurrence)
    
    print("Analyzing topic authority...")
    topic_authority = analyze_topic_authority(df)
    
    print("Creating topic heatmap...")
    heatmap_data, top_heatmap_topics, traits = create_topic_heatmap(df)
    
    print("Analyzing topic evolution...")
    timeline_data = create_topic_evolution_timeline(df)
    
    print("Generating insights...")
    insights = generate_topic_insights(top_topics, topic_authority, centrality)
    
    print("Creating visualizations...")
    fig = create_topic_visualizations(
        df, top_topics, topic_authority, heatmap_data, 
        top_heatmap_topics, traits, timeline_data
    )
    
    # Create comprehensive HTML report
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Topic Relationship Analysis</title>
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
                <h1>🔍 Topic Relationship Analysis</h1>
                <p>Content relationships, topic authority, and thematic evolution patterns</p>
            </div>
            
            <div class="metrics">
                <div class="metric-card">
                    <div class="metric-value">{len(top_topics)}</div>
                    <div class="metric-label">Unique Topics</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{max(top_topics.values()) if top_topics else 0}</div>
                    <div class="metric-label">Max Topic Frequency</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{len([t for t in topic_authority.values() if t['avg_authority'] > 10]) if topic_authority else 0}</div>
                    <div class="metric-label">High Authority Topics</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{len(network_graph.nodes()) if network_graph else 0}</div>
                    <div class="metric-label">Connected Topics</div>
                </div>
            </div>
            
            <div id="plotly-div"></div>
            
            <div class="insights">
                <h3>🎯 Key Topic Insights</h3>
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
    with open('topic_analysis.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("✅ Topic analysis saved to 'topic_analysis.html'")
    print(f"📊 Analyzed {len(top_topics)} unique topics")
    print(f"🔗 Found {len(network_graph.nodes()) if network_graph else 0} connected topics")
    print(f"👑 Top authority topic: {max(topic_authority.items(), key=lambda x: x[1]['avg_authority'])[0] if topic_authority else 'N/A'}")

if __name__ == "__main__":
    import sys
    data_file = sys.argv[1] if len(sys.argv) > 1 else None
    generate_topic_analysis(data_file) 