#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Content Archetype Discovery - Phase 7
Discovers distinct content personas through clustering analysis
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_loader import load_and_merge_data, get_data_summary

def prepare_clustering_data(df):
    """Prepare data for clustering analysis"""
    # Select personality traits for clustering
    trait_cols = [col for col in df.columns if col.startswith(('big5_', 'partner_'))]
    
    # Create feature matrix
    X = df[trait_cols].values
    
    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    return X_scaled, trait_cols, scaler

def find_optimal_clusters(X, max_clusters=8):
    """Find optimal number of clusters using silhouette score"""
    silhouette_scores = []
    inertias = []
    K_range = range(2, max_clusters + 1)
    
    for k in K_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(X)
        silhouette_avg = silhouette_score(X, cluster_labels)
        silhouette_scores.append(silhouette_avg)
        inertias.append(kmeans.inertia_)
    
    # Find optimal k (highest silhouette score)
    optimal_k = K_range[np.argmax(silhouette_scores)]
    
    return optimal_k, silhouette_scores, inertias, K_range

def perform_clustering(X, n_clusters):
    """Perform K-means clustering"""
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(X)
    cluster_centers = kmeans.cluster_centers_
    
    return cluster_labels, cluster_centers, kmeans

def perform_dimensionality_reduction(X):
    """Perform PCA and t-SNE for visualization"""
    # PCA
    pca = PCA(n_components=2, random_state=42)
    X_pca = pca.fit_transform(X)
    
    # t-SNE
    tsne = TSNE(n_components=2, random_state=42, perplexity=30, n_iter=1000)
    X_tsne = tsne.fit_transform(X)
    
    return X_pca, X_tsne, pca

def label_archetypes(cluster_centers, trait_cols, scaler):
    """Generate descriptive labels for each archetype"""
    # Inverse transform to get original scale
    centers_original = scaler.inverse_transform(cluster_centers)
    
    archetype_labels = []
    archetype_descriptions = []
    
    for i, center in enumerate(centers_original):
        # Create trait profile
        trait_profile = dict(zip(trait_cols, center))
        
        # Determine dominant traits (above average)
        high_traits = []
        low_traits = []
        
        for trait, value in trait_profile.items():
            if value >= 4.0:  # High trait
                clean_trait = trait.replace('big5_', '').replace('partner_', '').replace('_', ' ').title()
                high_traits.append(clean_trait)
            elif value <= 2.5:  # Low trait
                clean_trait = trait.replace('big5_', '').replace('partner_', '').replace('_', ' ').title()
                low_traits.append(clean_trait)
        
        # Generate archetype name based on dominant traits
        if 'Strategic Thinking' in high_traits and 'Leadership' in high_traits:
            label = "Strategic Leader"
            description = "High strategic thinking and leadership, drives vision and direction"
        elif 'Collaboration' in high_traits and 'Agreeableness' in high_traits:
            label = "Team Builder"
            description = "Collaborative and agreeable, focuses on team harmony and cooperation"
        elif 'Openness' in high_traits and 'Risk Tolerance' in high_traits:
            label = "Innovation Pioneer"
            description = "Open to new ideas with high risk tolerance, drives innovation"
        elif 'Conscientiousness' in high_traits and 'Reliability' in high_traits:
            label = "Reliable Executor"
            description = "Highly conscientious and reliable, ensures consistent delivery"
        elif 'Extraversion' in high_traits and 'Leadership' in high_traits:
            label = "Charismatic Influencer"
            description = "Extraverted leader, influences through charisma and presence"
        elif 'Integrity Trust' in high_traits and 'Reliability' in high_traits:
            label = "Trusted Advisor"
            description = "High integrity and reliability, serves as trusted counsel"
        elif 'Adaptability' in high_traits and 'Openness' in high_traits:
            label = "Adaptive Innovator"
            description = "Highly adaptable and open, thrives in changing environments"
        else:
            # Fallback naming based on highest trait
            if high_traits:
                primary_trait = high_traits[0]
                label = f"{primary_trait} Focused"
                description = f"Characterized by high {primary_trait.lower()}"
            else:
                label = f"Archetype {i+1}"
                description = "Balanced personality profile"
        
        archetype_labels.append(label)
        archetype_descriptions.append(description)
    
    return archetype_labels, archetype_descriptions

def find_representative_posts(df, cluster_labels, cluster_centers, X_scaled):
    """Find most representative posts for each archetype"""
    representative_posts = {}
    
    for cluster_id in range(len(cluster_centers)):
        # Find posts in this cluster
        cluster_mask = cluster_labels == cluster_id
        cluster_posts = df[cluster_mask].copy()
        cluster_features = X_scaled[cluster_mask]
        
        if len(cluster_posts) == 0:
            continue
        
        # Find post closest to cluster center
        center = cluster_centers[cluster_id]
        distances = np.linalg.norm(cluster_features - center, axis=1)
        closest_idx = np.argmin(distances)
        
        representative_post = cluster_posts.iloc[closest_idx]
        
        representative_posts[cluster_id] = {
            'post_id': representative_post['post_id'],
            'post_text': representative_post['post_text'][:200] + "..." if len(str(representative_post['post_text'])) > 200 else str(representative_post['post_text']),
            'topic_tags': representative_post['topic_tags'],
            'engagement_rate': representative_post['engagement_rate'],
            'distance_to_center': distances[closest_idx]
        }
    
    return representative_posts

def create_cluster_optimization_chart(silhouette_scores, inertias, K_range):
    """Create chart showing optimal cluster selection"""
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Silhouette Score', 'Elbow Method (Inertia)'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # Silhouette scores
    fig.add_trace(
        go.Scatter(
            x=list(K_range),
            y=silhouette_scores,
            mode='lines+markers',
            name='Silhouette Score',
            line=dict(color='#2E86AB', width=3),
            marker=dict(size=8)
        ),
        row=1, col=1
    )
    
    # Inertia (Elbow method)
    fig.add_trace(
        go.Scatter(
            x=list(K_range),
            y=inertias,
            mode='lines+markers',
            name='Inertia',
            line=dict(color='#A23B72', width=3),
            marker=dict(size=8)
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        title="Cluster Optimization Analysis",
        title_x=0.5,
        title_font_size=20,
        height=400,
        showlegend=False
    )
    
    fig.update_xaxes(title_text="Number of Clusters", row=1, col=1)
    fig.update_xaxes(title_text="Number of Clusters", row=1, col=2)
    fig.update_yaxes(title_text="Silhouette Score", row=1, col=1)
    fig.update_yaxes(title_text="Inertia", row=1, col=2)
    
    return fig

def create_tsne_cluster_plot(X_tsne, cluster_labels, archetype_labels):
    """Create t-SNE visualization of clusters"""
    df_plot = pd.DataFrame({
        'x': X_tsne[:, 0],
        'y': X_tsne[:, 1],
        'cluster': cluster_labels,
        'archetype': [archetype_labels[label] for label in cluster_labels]
    })
    
    fig = px.scatter(
        df_plot,
        x='x', y='y',
        color='archetype',
        title="Content Archetypes (t-SNE Visualization)",
        labels={'x': 't-SNE Component 1', 'y': 't-SNE Component 2'},
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_layout(
        title_x=0.5,
        title_font_size=20,
        width=800,
        height=600,
        legend_title="Content Archetypes"
    )
    
    fig.update_traces(marker=dict(size=8, opacity=0.7))
    
    return fig

def create_pca_cluster_plot(X_pca, cluster_labels, archetype_labels, pca):
    """Create PCA visualization of clusters"""
    df_plot = pd.DataFrame({
        'x': X_pca[:, 0],
        'y': X_pca[:, 1],
        'cluster': cluster_labels,
        'archetype': [archetype_labels[label] for label in cluster_labels]
    })
    
    fig = px.scatter(
        df_plot,
        x='x', y='y',
        color='archetype',
        title="Content Archetypes (PCA Visualization)",
        labels={
            'x': f'PC1 ({pca.explained_variance_ratio_[0]:.1%} variance)',
            'y': f'PC2 ({pca.explained_variance_ratio_[1]:.1%} variance)'
        },
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    fig.update_layout(
        title_x=0.5,
        title_font_size=20,
        width=800,
        height=600,
        legend_title="Content Archetypes"
    )
    
    fig.update_traces(marker=dict(size=8, opacity=0.7))
    
    return fig

def create_archetype_profiles_chart(cluster_centers, trait_cols, scaler, archetype_labels):
    """Create radar charts showing archetype profiles"""
    # Inverse transform to original scale
    centers_original = scaler.inverse_transform(cluster_centers)
    
    # Clean trait names
    clean_traits = [trait.replace('big5_', 'B5: ').replace('partner_', 'P: ').replace('_', ' ').title() for trait in trait_cols]
    
    fig = go.Figure()
    
    colors = px.colors.qualitative.Set3[:len(archetype_labels)]
    
    for i, (center, label, color) in enumerate(zip(centers_original, archetype_labels, colors)):
        fig.add_trace(go.Scatterpolar(
            r=center,
            theta=clean_traits,
            fill='toself',
            name=label,
            line_color=color,
            opacity=0.7
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[1, 5]
            )
        ),
        title="Content Archetype Personality Profiles",
        title_x=0.5,
        title_font_size=20,
        width=800,
        height=600
    )
    
    return fig

def create_archetype_distribution_chart(cluster_labels, archetype_labels):
    """Create distribution chart of archetypes"""
    # Count posts per archetype
    unique_labels, counts = np.unique(cluster_labels, return_counts=True)
    archetype_names = [archetype_labels[i] for i in unique_labels]
    
    fig = go.Figure(data=[
        go.Bar(
            x=archetype_names,
            y=counts,
            marker_color=px.colors.qualitative.Set3[:len(archetype_names)],
            text=counts,
            textposition='outside'
        )
    ])
    
    fig.update_layout(
        title="Content Archetype Distribution",
        title_x=0.5,
        title_font_size=20,
        xaxis_title="Content Archetypes",
        yaxis_title="Number of Posts",
        width=800,
        height=500
    )
    
    return fig

def generate_content_archetypes():
    """Generate complete content archetype discovery analysis"""
    print("Loading data for content archetype discovery...")
    df = load_and_merge_data()
    
    print("Preparing clustering data...")
    X_scaled, trait_cols, scaler = prepare_clustering_data(df)
    
    print("Finding optimal number of clusters...")
    optimal_k, silhouette_scores, inertias, K_range = find_optimal_clusters(X_scaled)
    
    print(f"Performing clustering with {optimal_k} clusters...")
    cluster_labels, cluster_centers, kmeans = perform_clustering(X_scaled, optimal_k)
    
    print("Performing dimensionality reduction...")
    X_pca, X_tsne, pca = perform_dimensionality_reduction(X_scaled)
    
    print("Labeling archetypes...")
    archetype_labels, archetype_descriptions = label_archetypes(cluster_centers, trait_cols, scaler)
    
    print("Finding representative posts...")
    representative_posts = find_representative_posts(df, cluster_labels, cluster_centers, X_scaled)
    
    print("Creating visualizations...")
    optimization_fig = create_cluster_optimization_chart(silhouette_scores, inertias, K_range)
    tsne_fig = create_tsne_cluster_plot(X_tsne, cluster_labels, archetype_labels)
    pca_fig = create_pca_cluster_plot(X_pca, cluster_labels, archetype_labels, pca)
    profiles_fig = create_archetype_profiles_chart(cluster_centers, trait_cols, scaler, archetype_labels)
    distribution_fig = create_archetype_distribution_chart(cluster_labels, archetype_labels)
    
    # Calculate insights
    silhouette_avg = silhouette_score(X_scaled, cluster_labels)
    most_common_archetype = archetype_labels[np.argmax(np.bincount(cluster_labels))]
    total_variance_explained = sum(pca.explained_variance_ratio_)
    
    # Create HTML template
    html_template = f"""<!DOCTYPE html>
<html>
<head>
    <title>Content-Personality Analysis: Content Archetypes</title>
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
        .archetype-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            margin: 10px 0;
        }}
        .archetype-title {{
            font-size: 18px;
            font-weight: bold;
            color: #2E86AB;
            margin-bottom: 10px;
        }}
        .archetype-description {{
            color: #666;
            margin-bottom: 15px;
        }}
        .representative-post {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border-left: 3px solid #2E86AB;
            font-style: italic;
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
        <h1>Content Archetype Discovery</h1>
        <h2>Personality-Based Content Personas</h2>
        <p>Machine learning analysis revealing distinct content archetypes based on personality traits</p>
    </div>
    
    <div class="insights">
        <h3>Archetype Discovery Insights</h3>
        <div class="metric">
            <div class="score">{optimal_k}</div>
            <div>Distinct Archetypes</div>
            <small>Optimal clusters found</small>
        </div>
        <div class="metric">
            <div class="score">{silhouette_avg:.3f}</div>
            <div>Silhouette Score</div>
            <small>Clustering quality</small>
        </div>
        <div class="metric">
            <div class="score">{most_common_archetype}</div>
            <div>Most Common Archetype</div>
            <small>Dominant persona</small>
        </div>
        <div class="metric">
            <div class="score">{total_variance_explained:.1%}</div>
            <div>Variance Explained</div>
            <small>PCA components</small>
        </div>
    </div>
    
    <div class="highlight">
        <strong>Discovery Insight:</strong> 
        Analysis identified {optimal_k} distinct content archetypes with a silhouette score of {silhouette_avg:.3f}, 
        indicating well-separated personality-based content personas. The "{most_common_archetype}" archetype is most prevalent.
    </div>
    
    <div class="chart-container">
        <div id="optimization-chart"></div>
    </div>
    
    <div class="grid-2">
        <div class="chart-container">
            <div id="tsne-chart"></div>
        </div>
        <div class="chart-container">
            <div id="pca-chart"></div>
        </div>
    </div>
    
    <div class="chart-container">
        <div id="profiles-chart"></div>
    </div>
    
    <div class="chart-container">
        <div id="distribution-chart"></div>
    </div>
    
    <div class="insights">
        <h3>Content Archetype Profiles</h3>"""
    
    # Add archetype cards
    for i, (label, description) in enumerate(zip(archetype_labels, archetype_descriptions)):
        if i in representative_posts:
            rep_post = representative_posts[i]
            html_template += f"""
        <div class="archetype-card">
            <div class="archetype-title">{label}</div>
            <div class="archetype-description">{description}</div>
            <div class="representative-post">
                <strong>Representative Post:</strong><br>
                "{rep_post['post_text']}"<br>
                <small>Topics: {rep_post['topic_tags']} | Engagement: {rep_post['engagement_rate']:.1%}</small>
            </div>
        </div>"""
    
    html_template += f"""
    </div>
    
    <script>
        Plotly.newPlot('optimization-chart', {optimization_fig.to_json()});
        Plotly.newPlot('tsne-chart', {tsne_fig.to_json()});
        Plotly.newPlot('pca-chart', {pca_fig.to_json()});
        Plotly.newPlot('profiles-chart', {profiles_fig.to_json()});
        Plotly.newPlot('distribution-chart', {distribution_fig.to_json()});
    </script>
</body>
</html>"""
    
    # Save to HTML file
    with open('content_archetypes.html', 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print("Content archetype discovery saved to 'content_archetypes.html'")
    print(f"Discovered {optimal_k} archetypes with silhouette score: {silhouette_avg:.3f}")
    print(f"Most common archetype: {most_common_archetype}")
    print(f"PCA variance explained: {total_variance_explained:.1%}")
    
    return df, cluster_labels, archetype_labels, representative_posts

if __name__ == "__main__":
    generate_content_archetypes() 