#!/usr/bin/env python3
"""
Behavioral Flag Analysis - Phase 5
Analyzes behavioral flags patterns, correlations, and risk indicators
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import chi2_contingency
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_loader import load_and_merge_data, get_data_summary

def analyze_flag_correlations(df):
    """Analyze correlations between behavioral flags"""
    flag_cols = [col for col in df.columns if col.startswith('flag_')]
    
    # Create correlation matrix
    flag_data = df[flag_cols].astype(int)  # Convert boolean to int for correlation
    correlation_matrix = flag_data.corr()
    
    return correlation_matrix

def analyze_flag_topic_relationships(df):
    """Analyze relationships between flags and topics"""
    flag_cols = [col for col in df.columns if col.startswith('flag_')]
    
    # Expand topic_tags into individual columns
    all_topics = set()
    for topics in df['topic_tags']:
        if isinstance(topics, list):
            all_topics.update(topics)
        elif isinstance(topics, str):
            # Handle string representation of list
            topics_clean = topics.strip('[]').replace("'", "").replace('"', '')
            if topics_clean:
                topic_list = [t.strip() for t in topics_clean.split(',')]
                all_topics.update(topic_list)
    
    # Create topic-flag correlation matrix
    topic_flag_correlations = {}
    
    for topic in all_topics:
        if topic and topic != 'Other':
            # Create binary column for this topic
            df[f'topic_{topic}'] = df['topic_tags'].apply(
                lambda x: topic in (x if isinstance(x, list) else 
                                  [t.strip() for t in str(x).strip('[]').replace("'", "").replace('"', '').split(',') if t.strip()])
            )
            
            # Calculate correlations with flags
            for flag in flag_cols:
                correlation = df[f'topic_{topic}'].astype(int).corr(df[flag].astype(int))
                topic_flag_correlations[f"{topic}_{flag}"] = correlation
    
    return topic_flag_correlations

def analyze_flag_trends(df):
    """Analyze flag frequency trends over post sequence"""
    flag_cols = [col for col in df.columns if col.startswith('flag_')]
    
    # Sort by post_id to get chronological order (REVERSE because data is newest to oldest)
    df['post_id_numeric'] = df['post_id'].astype(int)
    df_sorted = df.sort_values('post_id_numeric', ascending=False)  # Reverse: oldest first
    
    # Calculate rolling averages for flag frequencies
    window_size = 20  # 20-post rolling window
    flag_trends = {}
    
    for flag in flag_cols:
        df_sorted[f'{flag}_rolling'] = df_sorted[flag].astype(int).rolling(window=window_size, min_periods=5).mean()
        flag_trends[flag] = {
            'rolling_mean': df_sorted[f'{flag}_rolling'].tolist(),
            'post_ids': df_sorted['post_id'].tolist(),
            'overall_frequency': df_sorted[flag].mean(),
            'trend_slope': stats.linregress(range(len(df_sorted)), df_sorted[flag].astype(int))[0]
        }
    
    return flag_trends

def analyze_flag_interval_trends(df, interval_size=50):
    """Analyze flag trends using fixed intervals for statistical significance"""
    flag_cols = [col for col in df.columns if col.startswith('flag_')]
    
    # Sort by post_id to get chronological order (REVERSE because data is newest to oldest)
    df['post_id_numeric'] = df['post_id'].astype(int)
    df_sorted = df.sort_values('post_id_numeric', ascending=False)  # Reverse: oldest first
    
    # Create intervals
    total_posts = len(df_sorted)
    num_intervals = total_posts // interval_size
    
    interval_trends = {}
    interval_data = []
    
    for flag in flag_cols:
        flag_name = flag.replace('flag_', '')
        intervals = []
        frequencies = []
        interval_labels = []
        
        for i in range(num_intervals):
            start_idx = i * interval_size
            end_idx = min((i + 1) * interval_size, total_posts)
            
            interval_df = df_sorted.iloc[start_idx:end_idx]
            frequency = interval_df[flag].mean()
            
            # Create interval label (showing post range)
            start_post = interval_df['post_id'].iloc[-1]  # Last post in interval (oldest)
            end_post = interval_df['post_id'].iloc[0]     # First post in interval (newest)
            interval_label = f"Posts {start_post}-{end_post}"
            
            intervals.append(i + 1)
            frequencies.append(frequency)
            interval_labels.append(interval_label)
        
        # Calculate trend statistics
        if len(frequencies) > 2:
            slope, intercept, r_value, p_value, std_err = stats.linregress(intervals, frequencies)
            trend_direction = "📈 Increasing" if slope > 0.01 else "📉 Decreasing" if slope < -0.01 else "📊 Stable"
            trend_strength = "Strong" if abs(r_value) > 0.7 else "Moderate" if abs(r_value) > 0.4 else "Weak"
        else:
            slope, r_value, p_value = 0, 0, 1
            trend_direction = "📊 Insufficient data"
            trend_strength = "N/A"
        
        interval_trends[flag] = {
            'intervals': intervals,
            'frequencies': frequencies,
            'interval_labels': interval_labels,
            'slope': slope,
            'r_squared': r_value ** 2,
            'p_value': p_value,
            'trend_direction': trend_direction,
            'trend_strength': trend_strength,
            'overall_frequency': df_sorted[flag].mean(),
            'frequency_change': frequencies[-1] - frequencies[0] if len(frequencies) > 1 else 0
        }
        
        # Store data for summary
        interval_data.append({
            'flag': flag_name,
            'slope': slope,
            'r_squared': r_value ** 2,
            'trend_direction': trend_direction,
            'trend_strength': trend_strength,
            'frequency_change': frequencies[-1] - frequencies[0] if len(frequencies) > 1 else 0
        })
    
    return interval_trends, interval_data, interval_size, num_intervals

def analyze_flag_drivers(df):
    """Analyze which trait combinations drive specific flags"""
    flag_cols = [col for col in df.columns if col.startswith('flag_')]
    trait_cols = [col for col in df.columns if col.startswith(('big5_', 'partner_'))]
    
    flag_drivers = {}
    
    for flag in flag_cols:
        flag_name = flag.replace('flag_', '')
        drivers = {}
        
        # Calculate correlation between each trait and the flag
        for trait in trait_cols:
            correlation = df[trait].corr(df[flag].astype(int))
            drivers[trait] = correlation
        
        # Sort by absolute correlation strength
        sorted_drivers = sorted(drivers.items(), key=lambda x: abs(x[1]), reverse=True)
        
        flag_drivers[flag_name] = {
            'correlations': drivers,
            'top_positive': [item for item in sorted_drivers if item[1] > 0][:3],
            'top_negative': [item for item in sorted_drivers if item[1] < 0][:3],
            'strongest_overall': sorted_drivers[:5]
        }
    
    return flag_drivers

def create_flag_correlation_heatmap(correlation_matrix):
    """Create heatmap of flag correlations"""
    # Clean up flag names for display
    clean_labels = [label.replace('flag_', '').replace('_', ' ').title() for label in correlation_matrix.columns]
    
    fig = go.Figure(data=go.Heatmap(
        z=correlation_matrix.values,
        x=clean_labels,
        y=clean_labels,
        colorscale='RdBu',
        zmid=0,
        text=np.round(correlation_matrix.values, 2),
        texttemplate="%{text}",
        textfont={"size": 12},
        hoverongaps=False,
        colorbar=dict(title="Correlation")
    ))
    
    fig.update_layout(
        title="🔗 Behavioral Flag Correlation Matrix",
        title_x=0.5,
        title_font_size=20,
        width=600,
        height=500,
        margin=dict(t=80, b=50, l=100, r=50)
    )
    
    return fig

def create_topic_flag_heatmap(topic_flag_correlations):
    """Create heatmap of topic-flag relationships"""
    # Parse the correlation data into matrix format
    topics = set()
    flags = set()
    
    for key in topic_flag_correlations.keys():
        if '_flag_' in key:
            topic, flag = key.split('_flag_')
            topics.add(topic)
            flags.add(f"flag_{flag}")
    
    topics = sorted(list(topics))
    flags = sorted(list(flags))
    
    # Create correlation matrix
    correlation_matrix = np.zeros((len(topics), len(flags)))
    
    for i, topic in enumerate(topics):
        for j, flag in enumerate(flags):
            key = f"{topic}_{flag}"
            if key in topic_flag_correlations:
                correlation_matrix[i, j] = topic_flag_correlations[key]
    
    # Clean up labels
    clean_topics = [topic.replace('_', ' ').title() for topic in topics]
    clean_flags = [flag.replace('flag_', '').replace('_', ' ').title() for flag in flags]
    
    fig = go.Figure(data=go.Heatmap(
        z=correlation_matrix,
        x=clean_flags,
        y=clean_topics,
        colorscale='RdYlBu',
        zmid=0,
        text=np.round(correlation_matrix, 2),
        texttemplate="%{text}",
        textfont={"size": 10},
        hoverongaps=False,
        colorbar=dict(title="Correlation")
    ))
    
    fig.update_layout(
        title="📊 Topic-Flag Relationship Heatmap",
        title_x=0.5,
        title_font_size=20,
        width=800,
        height=600,
        margin=dict(t=80, b=50, l=150, r=50)
    )
    
    return fig

def create_flag_trends_chart(flag_trends):
    """Create time series chart of flag trends"""
    fig = go.Figure()
    
    colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D']
    
    for i, (flag, data) in enumerate(flag_trends.items()):
        flag_name = flag.replace('flag_', '').replace('_', ' ').title()
        color = colors[i % len(colors)]
        
        # Add rolling average line
        fig.add_trace(go.Scatter(
            x=data['post_ids'],
            y=data['rolling_mean'],
            mode='lines',
            name=f"{flag_name} (Rolling Avg)",
            line=dict(color=color, width=3),
            hovertemplate=f'<b>{flag_name}</b><br>Post: %{{x}}<br>Frequency: %{{y:.2f}}<extra></extra>'
        ))
        
        # Add overall frequency line
        fig.add_hline(
            y=data['overall_frequency'],
            line_dash="dash",
            line_color=color,
            opacity=0.5,
            annotation_text=f"{flag_name} Avg: {data['overall_frequency']:.2f}",
            annotation_position="top left"
        )
    
    fig.update_layout(
        title="📈 Behavioral Flag Trends Over Time",
        title_x=0.5,
        title_font_size=20,
        xaxis_title="Time Progression (Oldest → Newest Posts)",
        yaxis_title="Flag Frequency (Rolling Average)",
        height=500,
        margin=dict(t=80, b=50, l=50, r=50),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig

def create_flag_interval_trends_chart(interval_trends, interval_size, num_intervals):
    """Create chart showing flag trends across fixed intervals"""
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[f"{flag.replace('flag_', '').replace('_', ' ').title()}" for flag in list(interval_trends.keys())],
        specs=[[{"secondary_y": True}, {"secondary_y": True}],
               [{"secondary_y": True}, {"secondary_y": True}]],
        vertical_spacing=0.12
    )
    
    flag_names = list(interval_trends.keys())
    positions = [(1, 1), (1, 2), (2, 1), (2, 2)]
    colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D']
    
    for i, (flag, data) in enumerate(interval_trends.items()):
        if i >= 4:  # Limit to 4 flags for layout
            break
            
        row, col = positions[i]
        color = colors[i]
        
        # Bar chart for frequencies
        fig.add_trace(go.Bar(
            x=data['intervals'],
            y=data['frequencies'],
            name=f"{flag.replace('flag_', '').title()} Frequency",
            marker_color=color,
            opacity=0.7,
            text=[f"{freq:.1%}" for freq in data['frequencies']],
            textposition='outside',
            showlegend=False
        ), row=row, col=col)
        
        # Trend line
        if len(data['frequencies']) > 2:
            trend_line = [data['slope'] * x + data['frequencies'][0] for x in range(len(data['intervals']))]
            fig.add_trace(go.Scatter(
                x=data['intervals'],
                y=trend_line,
                mode='lines',
                name=f"Trend (R²={data['r_squared']:.3f})",
                line=dict(color='red', width=3, dash='dash'),
                showlegend=False
            ), row=row, col=col, secondary_y=True)
        
        # Add trend annotation
        trend_text = f"{data['trend_direction']}<br>{data['trend_strength']} (R²={data['r_squared']:.3f})"
        if data['frequency_change'] != 0:
            change_pct = data['frequency_change'] * 100
            trend_text += f"<br>Change: {change_pct:+.1f}pp"
        
        fig.add_annotation(
            text=trend_text,
            xref=f"x{i+1}", yref=f"y{i+1}",
            x=max(data['intervals']) * 0.7,
            y=max(data['frequencies']) * 0.9,
            showarrow=False,
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor=color,
            borderwidth=1,
            font=dict(size=10),
            row=row, col=col
        )
        
        # Update axes
        fig.update_xaxes(title_text=f"Interval ({interval_size} posts each)", row=row, col=col)
        fig.update_yaxes(title_text="Flag Frequency", row=row, col=col)
    
    fig.update_layout(
        title=f"📊 Behavioral Flag Trends Across {num_intervals} Intervals ({interval_size} posts each)",
        title_x=0.5,
        title_font_size=18,
        height=800,
        margin=dict(t=100, b=50, l=50, r=50)
    )
    
    return fig

def create_flag_drivers_chart(flag_drivers):
    """Create chart showing trait drivers for each flag"""
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[flag.replace('_', ' ').title() for flag in flag_drivers.keys()],
        specs=[[{"type": "bar"}, {"type": "bar"}],
               [{"type": "bar"}, {"type": "bar"}]]
    )
    
    flag_names = list(flag_drivers.keys())
    positions = [(1, 1), (1, 2), (2, 1), (2, 2)]
    
    for i, (flag_name, data) in enumerate(flag_drivers.items()):
        if i >= 4:  # Limit to 4 flags for layout
            break
            
        row, col = positions[i]
        
        # Get top 5 strongest correlations (positive and negative)
        strongest = data['strongest_overall'][:5]
        traits = [item[0].replace('big5_', 'B5: ').replace('partner_', 'P: ').replace('_', ' ').title() for item in strongest]
        correlations = [item[1] for item in strongest]
        
        colors = ['#2E86AB' if corr > 0 else '#C73E1D' for corr in correlations]
        
        fig.add_trace(go.Bar(
            x=correlations,
            y=traits,
            orientation='h',
            marker_color=colors,
            text=[f"{corr:.2f}" for corr in correlations],
            textposition='outside',
            name=flag_name,
            showlegend=False
        ), row=row, col=col)
        
        fig.update_xaxes(title_text="Correlation", row=row, col=col)
    
    fig.update_layout(
        title="🎯 Trait Drivers for Behavioral Flags",
        title_x=0.5,
        title_font_size=20,
        height=800,
        margin=dict(t=100, b=50, l=200, r=50)
    )
    
    return fig

def generate_behavioral_flags():
    """Generate complete behavioral flags analysis"""
    print("🔄 Loading data for behavioral flags analysis...")
    df = load_and_merge_data()
    
    print("🔗 Analyzing flag correlations...")
    correlation_matrix = analyze_flag_correlations(df)
    
    print("📊 Analyzing topic-flag relationships...")
    topic_flag_correlations = analyze_flag_topic_relationships(df)
    
    print("📈 Analyzing flag trends...")
    flag_trends = analyze_flag_trends(df)
    
    print("📊 Analyzing flag interval trends...")
    interval_trends, interval_data, interval_size, num_intervals = analyze_flag_interval_trends(df, interval_size=50)
    
    print("🎯 Analyzing flag drivers...")
    flag_drivers = analyze_flag_drivers(df)
    
    print("📈 Creating visualizations...")
    correlation_fig = create_flag_correlation_heatmap(correlation_matrix)
    topic_flag_fig = create_topic_flag_heatmap(topic_flag_correlations)
    trends_fig = create_flag_trends_chart(flag_trends)
    interval_trends_fig = create_flag_interval_trends_chart(interval_trends, interval_size, num_intervals)
    drivers_fig = create_flag_drivers_chart(flag_drivers)
    
    # Calculate key insights
    flag_cols = [col for col in df.columns if col.startswith('flag_')]
    flag_frequencies = {flag: df[flag].mean() for flag in flag_cols}
    most_common_flag = max(flag_frequencies, key=flag_frequencies.get)
    least_common_flag = min(flag_frequencies, key=flag_frequencies.get)
    
    # Find strongest correlations
    strongest_correlation = 0
    strongest_pair = ""
    for i, flag1 in enumerate(flag_cols):
        for j, flag2 in enumerate(flag_cols):
            if i < j:
                corr = abs(correlation_matrix.loc[flag1, flag2])
                if corr > strongest_correlation:
                    strongest_correlation = corr
                    strongest_pair = f"{flag1.replace('flag_', '')} & {flag2.replace('flag_', '')}"
    
    # Find most significant interval trends
    significant_trends = [item for item in interval_data if abs(item['slope']) > 0.01 and item['r_squared'] > 0.3]
    most_trending_flag = max(interval_data, key=lambda x: abs(x['slope']))['flag'] if interval_data else "None"
    
    # Count high-risk flags (controversial + aggressive)
    high_risk_flags = sum([df['flag_controversial'].sum(), df['flag_aggressive_language'].sum()])
    
    # Create HTML template
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Content-Personality Analysis: Behavioral Flags Analysis</title>
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
                background: linear-gradient(135deg, #C73E1D, #A23B72);
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
                border-left: 5px solid #C73E1D;
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
                color: #C73E1D;
            }}
            .grid-2 {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
            }}
            .warning {{
                background: #fff3cd;
                border: 1px solid #ffeaa7;
                color: #856404;
                padding: 15px;
                border-radius: 8px;
                margin: 10px 0;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚨 Behavioral Flags Analysis</h1>
            <h2>Risk Patterns & Behavioral Indicators</h2>
            <p>Analysis of behavioral flags across {len(df)} posts</p>
        </div>
        
        <div class="insights">
            <h3>🎯 Key Flag Insights</h3>
            <div class="metric">
                <div class="score">{most_common_flag.replace('flag_', '').replace('_', ' ').title()}</div>
                <div>Most Common Flag</div>
                <small>{flag_frequencies[most_common_flag]:.1%} frequency</small>
            </div>
            <div class="metric">
                <div class="score">{strongest_pair.replace('_', ' ').title()}</div>
                <div>Strongest Correlation</div>
                <small>r = {strongest_correlation:.2f}</small>
            </div>
            <div class="metric">
                <div class="score">{high_risk_flags}</div>
                <div>High-Risk Flags</div>
                <small>Controversial + Aggressive</small>
            </div>
            <div class="metric">
                <div class="score">{len(significant_trends)}</div>
                <div>Significant Trends</div>
                <small>Across {num_intervals} intervals</small>
            </div>
        </div>
        
        <div class="warning">
            <strong>📊 Interval Trend Analysis:</strong> 
            Analyzed {len(df)} posts across {num_intervals} intervals of {interval_size} posts each. 
            Most trending flag: <strong>{most_trending_flag.replace('_', ' ').title()}</strong>. 
            {len(significant_trends)} flags show statistically significant trends (R² > 0.3).
        </div>
        
        <div class="grid-2">
            <div class="chart-container">
                <div id="correlation-chart"></div>
            </div>
            <div class="chart-container">
                <div id="trends-chart"></div>
            </div>
        </div>
        
        <div class="chart-container">
            <div id="interval-trends-chart"></div>
        </div>
        
        <div class="chart-container">
            <div id="topic-flag-chart"></div>
        </div>
        
        <div class="chart-container">
            <div id="drivers-chart"></div>
        </div>
        
        <script>
            Plotly.newPlot('correlation-chart', {correlation_fig.to_json()});
            Plotly.newPlot('trends-chart', {trends_fig.to_json()});
            Plotly.newPlot('interval-trends-chart', {interval_trends_fig.to_json()});
            Plotly.newPlot('topic-flag-chart', {topic_flag_fig.to_json()});
            Plotly.newPlot('drivers-chart', {drivers_fig.to_json()});
        </script>
    </body>
    </html>
    """
    
    # Save to HTML file
    with open('behavioral_flags_analysis.html', 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print("✅ Behavioral flags analysis saved to 'behavioral_flags_analysis.html'")
    print(f"🚨 Most Common Flag: {most_common_flag.replace('flag_', '')} ({flag_frequencies[most_common_flag]:.1%})")
    print(f"🔗 Strongest Correlation: {strongest_pair} (r={strongest_correlation:.2f})")
    print(f"⚠️ High-Risk Flags: {len([f for f in flag_frequencies.values() if f > 0.1])}")
    
    return df, flag_frequencies, correlation_matrix, flag_drivers

if __name__ == "__main__":
    generate_behavioral_flags() 