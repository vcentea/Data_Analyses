#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Risk Assessment & Predictive Analysis - Phase 8
Predictive models for content risk scoring and flag escalation patterns
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, roc_curve
from sklearn.feature_selection import SelectKBest, f_classif
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_loader import load_and_merge_data, get_data_summary

def prepare_risk_features(df):
    """Prepare features for risk prediction models"""
    # Select personality traits and engagement metrics
    trait_cols = [col for col in df.columns if col.startswith(('big5_', 'partner_'))]
    engagement_cols = ['engagement_rate', 'comment_rate', 'like_rate']
    composite_cols = ['partnership_compatibility', 'thought_leadership', 'trait_volatility', 'brand_consistency']
    
    feature_cols = trait_cols + engagement_cols + composite_cols
    X = df[feature_cols].copy()
    
    # Handle any missing values
    X = X.fillna(X.mean())
    
    return X, feature_cols

def build_self_promotion_predictor(df):
    """Build logistic regression model to predict self_promotion flag"""
    X, feature_cols = prepare_risk_features(df)
    y = df['flag_self_promotion'].astype(int)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Feature selection
    selector = SelectKBest(f_classif, k=10)
    X_train_selected = selector.fit_transform(X_train_scaled, y_train)
    X_test_selected = selector.transform(X_test_scaled)
    
    # Train logistic regression
    lr_model = LogisticRegression(random_state=42, max_iter=1000)
    lr_model.fit(X_train_selected, y_train)
    
    # Predictions
    y_pred = lr_model.predict(X_test_selected)
    y_pred_proba = lr_model.predict_proba(X_test_selected)[:, 1]
    
    # Get selected features
    selected_features = [feature_cols[i] for i in selector.get_support(indices=True)]
    feature_importance = lr_model.coef_[0]
    
    # Cross-validation score
    cv_scores = cross_val_score(lr_model, X_train_selected, y_train, cv=5, scoring='roc_auc')
    
    return {
        'model': lr_model,
        'scaler': scaler,
        'selector': selector,
        'y_test': y_test,
        'y_pred': y_pred,
        'y_pred_proba': y_pred_proba,
        'selected_features': selected_features,
        'feature_importance': feature_importance,
        'cv_scores': cv_scores,
        'roc_auc': roc_auc_score(y_test, y_pred_proba)
    }

def calculate_content_risk_scores(df, self_promotion_model):
    """Calculate comprehensive content risk scores"""
    X, _ = prepare_risk_features(df)
    
    # Scale features
    X_scaled = self_promotion_model['scaler'].transform(X)
    X_selected = self_promotion_model['selector'].transform(X_scaled)
    
    # Get self-promotion probabilities
    self_promo_risk = self_promotion_model['model'].predict_proba(X_selected)[:, 1]
    
    # Calculate composite risk factors
    risk_factors = {
        'self_promotion_risk': self_promo_risk,
        'volatility_risk': df['trait_volatility'] / df['trait_volatility'].max(),
        'consistency_risk': 1 - (df['brand_consistency'] / df['brand_consistency'].max()),
        'authenticity_risk': 1 - (df['partnership_compatibility'] / df['partnership_compatibility'].max()),
        'engagement_risk': 1 - (df['engagement_rate'] / df['engagement_rate'].max())
    }
    
    # Weighted composite risk score
    weights = {
        'self_promotion_risk': 0.3,
        'volatility_risk': 0.2,
        'consistency_risk': 0.2,
        'authenticity_risk': 0.15,
        'engagement_risk': 0.15
    }
    
    composite_risk = np.zeros(len(df))
    for factor, weight in weights.items():
        composite_risk += risk_factors[factor] * weight
    
    # Normalize to 0-100 scale
    composite_risk = (composite_risk * 100).round(1)
    
    return composite_risk, risk_factors

def detect_flag_escalation_patterns(df):
    """Detect patterns in flag escalation over time"""
    # Create post sequence (REVERSE because data is newest to oldest)
    df['post_id_numeric'] = df['post_id'].astype(int)
    df_sorted = df.sort_values('post_id_numeric', ascending=False).copy()  # Reverse: oldest first
    
    # Calculate rolling flag frequencies
    window_size = 20  # 20-post rolling window
    
    flag_cols = [col for col in df.columns if col.startswith('flag_')]
    escalation_patterns = {}
    
    for flag_col in flag_cols:
        flag_name = flag_col.replace('flag_', '')
        rolling_freq = df_sorted[flag_col].rolling(window=window_size, min_periods=5).mean()
        
        # Detect escalation (increasing trend)
        escalation_score = 0
        if len(rolling_freq.dropna()) > 10:
            # Calculate trend slope
            x = np.arange(len(rolling_freq.dropna()))
            y = rolling_freq.dropna().values
            slope = np.polyfit(x, y, 1)[0]
            escalation_score = max(0, slope * 100)  # Convert to percentage
        
        escalation_patterns[flag_name] = {
            'rolling_frequency': rolling_freq,
            'escalation_score': escalation_score,
            'current_frequency': df_sorted[flag_col].tail(window_size).mean(),
            'peak_frequency': rolling_freq.max() if not rolling_freq.empty else 0
        }
    
    return escalation_patterns

def validate_authenticity_scores(df):
    """Validate authenticity by comparing scores with evidence"""
    authenticity_validation = {}
    
    partner_traits = [col for col in df.columns if col.startswith('partner_')]
    
    for trait in partner_traits:
        trait_name = trait.replace('partner_', '')
        evidence_col = f'evidence_{trait_name}'
        
        if evidence_col in df.columns:
            # Calculate correlation between score and evidence quality
            # Evidence quality proxy: length of evidence text
            evidence_lengths = df[evidence_col].astype(str).str.len()
            score_evidence_corr = df[trait].corr(evidence_lengths)
            
            # Identify potential authenticity issues (high scores with low evidence)
            high_score_low_evidence = ((df[trait] >= 4.0) & (evidence_lengths < 50)).sum()
            
            authenticity_validation[trait_name] = {
                'score_evidence_correlation': score_evidence_corr,
                'high_score_low_evidence_count': high_score_low_evidence,
                'authenticity_risk': high_score_low_evidence / len(df) * 100
            }
    
    return authenticity_validation

def create_risk_prediction_chart(self_promotion_model):
    """Create ROC curve and feature importance charts"""
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('ROC Curve - Self Promotion Prediction', 'Feature Importance'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # ROC Curve
    fpr, tpr, _ = roc_curve(self_promotion_model['y_test'], self_promotion_model['y_pred_proba'])
    auc_score = self_promotion_model['roc_auc']
    
    fig.add_trace(
        go.Scatter(
            x=fpr,
            y=tpr,
            mode='lines',
            name=f'ROC Curve (AUC = {auc_score:.3f})',
            line=dict(color='#2E86AB', width=3)
        ),
        row=1, col=1
    )
    
    # Diagonal line
    fig.add_trace(
        go.Scatter(
            x=[0, 1],
            y=[0, 1],
            mode='lines',
            name='Random Classifier',
            line=dict(color='gray', dash='dash'),
            showlegend=False
        ),
        row=1, col=1
    )
    
    # Feature Importance
    features = [f.replace('big5_', 'B5: ').replace('partner_', 'P: ').replace('_', ' ').title() 
                for f in self_promotion_model['selected_features']]
    importance = self_promotion_model['feature_importance']
    
    # Sort by absolute importance
    sorted_idx = np.argsort(np.abs(importance))[::-1]
    
    fig.add_trace(
        go.Bar(
            x=np.abs(importance[sorted_idx]),
            y=[features[i] for i in sorted_idx],
            orientation='h',
            name='Feature Importance',
            marker_color='#A23B72'
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        title="Risk Prediction Model Performance",
        title_x=0.5,
        title_font_size=20,
        height=500,
        showlegend=True
    )
    
    fig.update_xaxes(title_text="False Positive Rate", row=1, col=1)
    fig.update_yaxes(title_text="True Positive Rate", row=1, col=1)
    fig.update_xaxes(title_text="Coefficient Magnitude", row=1, col=2)
    fig.update_yaxes(title_text="Features", row=1, col=2)
    
    return fig

def create_risk_distribution_chart(composite_risk):
    """Create enhanced risk score distribution chart with clear explanations"""
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Risk Score Distribution', 'Risk Level Breakdown'),
        specs=[[{"secondary_y": False}], [{"secondary_y": False}]],
        vertical_spacing=0.15,
        row_heights=[0.6, 0.4]
    )
    
    # Histogram with color-coded risk zones
    low_risk = composite_risk[composite_risk < 40]
    medium_risk = composite_risk[(composite_risk >= 40) & (composite_risk < 70)]
    high_risk = composite_risk[composite_risk >= 70]
    
    fig.add_trace(go.Histogram(
        x=low_risk,
        nbinsx=15,
        name='Low Risk (0-39)',
        marker_color='#28a745',
        opacity=0.8
    ), row=1, col=1)
    
    fig.add_trace(go.Histogram(
        x=medium_risk,
        nbinsx=15,
        name='Medium Risk (40-69)',
        marker_color='#ffc107',
        opacity=0.8
    ), row=1, col=1)
    
    fig.add_trace(go.Histogram(
        x=high_risk,
        nbinsx=15,
        name='High Risk (70-100)',
        marker_color='#dc3545',
        opacity=0.8
    ), row=1, col=1)
    
    # Risk level breakdown bar chart
    risk_counts = [len(low_risk), len(medium_risk), len(high_risk)]
    risk_labels = ['Low Risk\n(0-39)', 'Medium Risk\n(40-69)', 'High Risk\n(70-100)']
    risk_colors = ['#28a745', '#ffc107', '#dc3545']
    
    fig.add_trace(go.Bar(
        x=risk_labels,
        y=risk_counts,
        marker_color=risk_colors,
        text=[f'{count} posts<br>({count/len(composite_risk)*100:.1f}%)' for count in risk_counts],
        textposition='auto',
        name='Risk Breakdown'
    ), row=2, col=1)
    
    # Add threshold lines to histogram
    fig.add_vline(x=40, line_dash="dash", line_color="orange", line_width=2,
                  annotation_text="Medium Risk Starts", row=1, col=1)
    fig.add_vline(x=70, line_dash="dash", line_color="red", line_width=2,
                  annotation_text="High Risk Starts", row=1, col=1)
    
    fig.update_layout(
        title="Content Risk Analysis with Clear Risk Zones",
        title_x=0.5,
        title_font_size=20,
        height=700,
        showlegend=True
    )
    
    fig.update_xaxes(title_text="Risk Score (0-100)", row=1, col=1)
    fig.update_yaxes(title_text="Number of Posts", row=1, col=1)
    fig.update_xaxes(title_text="Risk Categories", row=2, col=1)
    fig.update_yaxes(title_text="Number of Posts", row=2, col=1)
    
    return fig

def create_escalation_patterns_chart(escalation_patterns):
    """Create flag escalation patterns chart"""
    fig = go.Figure()
    
    flags = list(escalation_patterns.keys())
    escalation_scores = [escalation_patterns[flag]['escalation_score'] for flag in flags]
    current_frequencies = [escalation_patterns[flag]['current_frequency'] * 100 for flag in flags]
    
    fig.add_trace(go.Bar(
        x=flags,
        y=escalation_scores,
        name='Escalation Score',
        marker_color='#A23B72',
        yaxis='y'
    ))
    
    fig.add_trace(go.Scatter(
        x=flags,
        y=current_frequencies,
        mode='markers+lines',
        name='Current Frequency (%)',
        marker=dict(size=10, color='#2E86AB'),
        yaxis='y2'
    ))
    
    fig.update_layout(
        title="Flag Escalation Pattern Analysis",
        title_x=0.5,
        title_font_size=20,
        xaxis_title="Behavioral Flags",
        yaxis=dict(title="Escalation Score", side="left"),
        yaxis2=dict(title="Current Frequency (%)", side="right", overlaying="y"),
        width=800,
        height=500
    )
    
    return fig

def create_authenticity_validation_chart(authenticity_validation):
    """Create authenticity validation chart"""
    traits = list(authenticity_validation.keys())
    correlations = [authenticity_validation[trait]['score_evidence_correlation'] for trait in traits]
    risk_scores = [authenticity_validation[trait]['authenticity_risk'] for trait in traits]
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Score-Evidence Correlation', 'Authenticity Risk'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # Correlation chart
    fig.add_trace(
        go.Bar(
            x=traits,
            y=correlations,
            name='Correlation',
            marker_color='#2E86AB'
        ),
        row=1, col=1
    )
    
    # Risk chart
    fig.add_trace(
        go.Bar(
            x=traits,
            y=risk_scores,
            name='Risk %',
            marker_color='#A23B72'
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        title="Authenticity Validation Analysis",
        title_x=0.5,
        title_font_size=20,
        height=500,
        showlegend=False
    )
    
    fig.update_xaxes(title_text="Personality Traits", row=1, col=1)
    fig.update_xaxes(title_text="Personality Traits", row=1, col=2)
    fig.update_yaxes(title_text="Correlation Coefficient", row=1, col=1)
    fig.update_yaxes(title_text="Authenticity Risk (%)", row=1, col=2)
    
    return fig

def generate_risk_assessment():
    """Generate complete risk assessment and predictive analysis"""
    print("Loading data for risk assessment...")
    df = load_and_merge_data()
    
    print("Building self-promotion prediction model...")
    self_promotion_model = build_self_promotion_predictor(df)
    
    print("Calculating content risk scores...")
    composite_risk, risk_factors = calculate_content_risk_scores(df, self_promotion_model)
    
    print("Detecting flag escalation patterns...")
    escalation_patterns = detect_flag_escalation_patterns(df)
    
    print("Validating authenticity scores...")
    authenticity_validation = validate_authenticity_scores(df)
    
    print("Creating visualizations...")
    prediction_fig = create_risk_prediction_chart(self_promotion_model)
    distribution_fig = create_risk_distribution_chart(composite_risk)
    escalation_fig = create_escalation_patterns_chart(escalation_patterns)
    authenticity_fig = create_authenticity_validation_chart(authenticity_validation)
    
    # Calculate key insights with updated thresholds
    high_risk_posts = (composite_risk >= 70).sum()
    medium_risk_posts = ((composite_risk >= 40) & (composite_risk < 70)).sum()
    low_risk_posts = (composite_risk < 40).sum()
    avg_risk_score = composite_risk.mean()
    
    # Calculate risk percentages
    total_posts = len(composite_risk)
    high_risk_pct = (high_risk_posts / total_posts) * 100
    medium_risk_pct = (medium_risk_posts / total_posts) * 100
    low_risk_pct = (low_risk_posts / total_posts) * 100
    
    most_escalating_flag = max(escalation_patterns.keys(), 
                              key=lambda x: escalation_patterns[x]['escalation_score'])
    
    highest_auth_risk = max(authenticity_validation.keys(),
                           key=lambda x: authenticity_validation[x]['authenticity_risk'])
    
    # Create HTML template
    html_template = f"""<!DOCTYPE html>
<html>
<head>
    <title>Content-Personality Analysis: Risk Assessment</title>
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
        .risk-explanation {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }}
        .risk-level {{
            display: flex;
            align-items: center;
            margin: 15px 0;
            padding: 15px;
            border-radius: 8px;
            border-left: 5px solid;
        }}
        .risk-low {{
            background: #d4edda;
            border-left-color: #28a745;
        }}
        .risk-medium {{
            background: #fff3cd;
            border-left-color: #ffc107;
        }}
        .risk-high {{
            background: #f8d7da;
            border-left-color: #dc3545;
        }}
        .risk-icon {{
            font-size: 24px;
            margin-right: 15px;
        }}
        .risk-content h4 {{
            margin: 0 0 10px 0;
            font-size: 1.2em;
        }}
        .risk-content p {{
            margin: 5px 0;
            color: #495057;
        }}
        .interpretation-box {{
            background: #e3f2fd;
            border: 1px solid #2196f3;
            border-radius: 8px;
            padding: 15px;
            margin: 15px 0;
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
        .risk-high {{ color: #dc3545; }}
        .risk-medium {{ color: #fd7e14; }}
        .risk-low {{ color: #28a745; }}
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
        .warning {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            color: #856404;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Risk Assessment & Predictive Analysis</h1>
        <h2>Content Risk Scoring & Flag Prediction</h2>
        <p>Machine learning models for predicting and assessing content risks</p>
    </div>
    
    <div class="insights">
        <h3>Risk Assessment Summary</h3>
        <div class="metric">
            <div class="score risk-high">{high_risk_posts}</div>
            <div>High Risk Posts</div>
            <small>Score ≥ 70 ({high_risk_pct:.1f}%)</small>
        </div>
        <div class="metric">
            <div class="score risk-medium">{medium_risk_posts}</div>
            <div>Medium Risk Posts</div>
            <small>Score 40-69 ({medium_risk_pct:.1f}%)</small>
        </div>
        <div class="metric">
            <div class="score risk-low">{low_risk_posts}</div>
            <div>Low Risk Posts</div>
            <small>Score 0-39 ({low_risk_pct:.1f}%)</small>
        </div>
        <div class="metric">
            <div class="score">{avg_risk_score:.1f}</div>
            <div>Average Risk Score</div>
            <small>Overall risk level</small>
        </div>
    </div>
    
    <div class="risk-explanation">
        <h3>📊 Understanding Risk Levels - What They Actually Mean</h3>
        <p><strong>Risk scores are calculated based on 5 key factors:</strong> Self-promotion likelihood (30%), Content volatility (20%), Brand consistency (20%), Authenticity (15%), and Engagement patterns (15%).</p>
        
        <div class="risk-level risk-low">
            <div class="risk-icon">✅</div>
            <div class="risk-content">
                <h4>Low Risk (0-39 points) - {low_risk_posts} posts ({low_risk_pct:.1f}%)</h4>
                <p><strong>What it means:</strong> Professional, authentic content with consistent messaging</p>
                <p><strong>Characteristics:</strong> Balanced self-promotion, stable personality traits, high brand consistency</p>
                <p><strong>Action needed:</strong> Continue current approach - these posts represent your best content</p>
            </div>
        </div>
        
        <div class="risk-level risk-medium">
            <div class="risk-icon">⚠️</div>
            <div class="risk-content">
                <h4>Medium Risk (40-69 points) - {medium_risk_posts} posts ({medium_risk_pct:.1f}%)</h4>
                <p><strong>What it means:</strong> Content that may benefit from refinement but isn't problematic</p>
                <p><strong>Characteristics:</strong> Moderate self-promotion, some trait volatility, or engagement inconsistencies</p>
                <p><strong>Action needed:</strong> Review for optimization opportunities - consider adjusting tone, messaging, or timing</p>
                <p><strong>Examples:</strong> Posts with heavy self-promotion but good engagement, or authentic content with inconsistent branding</p>
            </div>
        </div>
        
        <div class="risk-level risk-high">
            <div class="risk-icon">🚨</div>
            <div class="risk-content">
                <h4>High Risk (70-100 points) - {high_risk_posts} posts ({high_risk_pct:.1f}%)</h4>
                <p><strong>What it means:</strong> Content that could damage professional reputation or brand consistency</p>
                <p><strong>Characteristics:</strong> Excessive self-promotion, high trait volatility, poor authenticity, or very low engagement</p>
                <p><strong>Action needed:</strong> Immediate review recommended - consider editing, deleting, or learning from these patterns</p>
                <p><strong>Examples:</strong> Overly promotional posts with no value, inconsistent personality presentation, or content that seems inauthentic</p>
            </div>
        </div>
    </div>
    
    <div class="interpretation-box">
        <h4>🎯 How to Use This Analysis</h4>
        <p><strong>For Content Strategy:</strong> Focus on replicating patterns from low-risk posts while addressing issues in medium/high-risk content.</p>
        <p><strong>For Professional Growth:</strong> Medium-risk posts often represent growth opportunities - they're not "bad" but can be improved.</p>
        <p><strong>For Brand Building:</strong> Consistency across risk levels indicates strong personal branding. High variation suggests need for clearer content guidelines.</p>
    </div>
    
    <div class="highlight">
        <strong>Predictive Insight:</strong> 
        Self-promotion prediction model achieved {self_promotion_model['roc_auc']:.3f} ROC AUC score. 
        {high_risk_posts} posts identified as high-risk requiring attention.
    </div>
    
    <div class="warning">
        <strong>⚠️ Escalation Alert:</strong> 
        "{most_escalating_flag.replace('_', ' ').title()}" flag shows highest escalation pattern 
        ({escalation_patterns[most_escalating_flag]['escalation_score']:.2f} escalation score).
        Authenticity risk highest for "{highest_auth_risk.replace('_', ' ').title()}" trait 
        ({authenticity_validation[highest_auth_risk]['authenticity_risk']:.1f}% risk).
    </div>
    
    <div class="chart-container">
        <div id="prediction-chart"></div>
    </div>
    
    <div class="grid-2">
        <div class="chart-container">
            <div id="distribution-chart"></div>
        </div>
        <div class="chart-container">
            <div id="escalation-chart"></div>
        </div>
    </div>
    
    <div class="chart-container">
        <div id="authenticity-chart"></div>
    </div>
    
    <script>
        Plotly.newPlot('prediction-chart', {prediction_fig.to_json()});
        Plotly.newPlot('distribution-chart', {distribution_fig.to_json()});
        Plotly.newPlot('escalation-chart', {escalation_fig.to_json()});
        Plotly.newPlot('authenticity-chart', {authenticity_fig.to_json()});
    </script>
</body>
</html>"""
    
    # Save to HTML file
    with open('risk_assessment.html', 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print("Risk assessment analysis saved to 'risk_assessment.html'")
    print(f"High-risk posts: {high_risk_posts}")
    print(f"Average risk score: {avg_risk_score:.1f}")
    print(f"Prediction accuracy (ROC AUC): {self_promotion_model['roc_auc']:.3f}")
    print(f"Most escalating flag: {most_escalating_flag}")
    
    return df, composite_risk, self_promotion_model, escalation_patterns

if __name__ == "__main__":
    generate_risk_assessment() 