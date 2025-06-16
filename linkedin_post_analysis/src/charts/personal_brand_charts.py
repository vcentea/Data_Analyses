#!/usr/bin/env python3
"""
Personal Brand Charts Generator
Creates HTML dashboard with 12 interactive charts for personal brand analysis
"""

import json
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class PersonalBrandChartsGenerator:
    """
    Generates HTML dashboard with Chart.js visualizations
    """
    
    def __init__(self, analysis_results):
        """
        Initialize with analysis results
        
        Args:
            analysis_results: Complete analysis data from PersonalBrandAnalyzer
        """
        self.results = analysis_results
        self.chart_data = analysis_results.get('chart_data', {})
        
    def generate_html_dashboard(self, output_file: str = 'personal_brand_analysis.html') -> str:
        """
        Generate complete HTML dashboard
        
        Args:
            output_file: Output filename
            
        Returns:
            str: Path to generated HTML file
        """
        html_content = self._create_html_template()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Personal brand dashboard generated: {output_file}")
        return output_file
    
    def _create_html_template(self) -> str:
        """Create the complete HTML template with all charts"""
        
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Personal Brand Analysis Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-date-fns/dist/chartjs-adapter-date-fns.bundle.min.js"></script>
    <style>
        {self._get_css_styles()}
    </style>
</head>
<body>
    <div class="dashboard-container">
        {self._create_header()}
        {self._create_kpi_cards()}
        {self._create_trend_cards()}
        {self._create_charts_grid()}
        {self._create_insights_section()}
        {self._create_recommendations_section()}
        {self._create_footer()}
    </div>
    
    <script>
        {self._generate_chart_scripts()}
    </script>
</body>
</html>
        """
        
        return html_template
    
    def _get_css_styles(self) -> str:
        """Get CSS styles for the dashboard"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        
        .dashboard-container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 40px;
            padding: 40px 20px;
        }
        
        .header h1 {
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .brand-score {
            background: rgba(255,255,255,0.1);
            padding: 20px;
            border-radius: 15px;
            margin: 20px 0;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
        }
        
        .score-number {
            font-size: 4em;
            font-weight: bold;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .kpi-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        
        .kpi-card {
            background: rgba(255,255,255,0.95);
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.3);
            transition: transform 0.3s ease;
        }
        
        .kpi-card:hover {
            transform: translateY(-5px);
        }
        
        .kpi-value {
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        
        .kpi-label {
            font-size: 0.9em;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .trend-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin-bottom: 40px;
        }
        
        .trend-card {
            background: rgba(255,255,255,0.95);
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
            backdrop-filter: blur(10px);
        }
        
        .trend-value {
            font-size: 1.8em;
            font-weight: bold;
            margin-bottom: 8px;
        }
        
        .trend-positive { color: #28a745; }
        .trend-negative { color: #dc3545; }
        .trend-neutral { color: #6c757d; }
        
        .trend-arrow {
            font-size: 1.2em;
            margin-left: 5px;
        }
        
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 30px;
            margin-bottom: 40px;
        }
        
        .chart-container {
            background: rgba(255,255,255,0.95);
            padding: 30px;
            border-radius: 20px;
            box-shadow: 0 15px 40px rgba(0,0,0,0.2);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.3);
        }
        
        .chart-title {
            font-size: 1.4em;
            font-weight: bold;
            margin-bottom: 20px;
            color: #2E86AB;
            text-align: center;
        }
        
        .chart-canvas {
            position: relative;
            height: 400px;
            width: 100%;
        }
        
        .insights-section {
            background: rgba(255,255,255,0.95);
            padding: 40px;
            border-radius: 20px;
            margin-bottom: 30px;
            box-shadow: 0 15px 40px rgba(0,0,0,0.2);
            backdrop-filter: blur(10px);
        }
        
        .insights-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
        }
        
        .insight-card {
            background: #f8f9fa;
            padding: 25px;
            border-radius: 15px;
            border-left: 5px solid #2E86AB;
        }
        
        .insight-title {
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 15px;
            color: #2E86AB;
        }
        
        .insight-list {
            list-style: none;
        }
        
        .insight-list li {
            margin-bottom: 10px;
            padding-left: 20px;
            position: relative;
        }
        
        .insight-list li:before {
            content: "•";
            color: #2E86AB;
            font-weight: bold;
            position: absolute;
            left: 0;
        }
        
        .recommendations-section {
            background: rgba(255,255,255,0.95);
            padding: 40px;
            border-radius: 20px;
            margin-bottom: 30px;
            box-shadow: 0 15px 40px rgba(0,0,0,0.2);
            backdrop-filter: blur(10px);
        }
        
        .footer {
            text-align: center;
            color: white;
            padding: 20px;
            opacity: 0.8;
        }
        
        @media (max-width: 768px) {
            .charts-grid {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .kpi-grid {
                grid-template-columns: repeat(2, 1fr);
            }
            
            .trend-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        """
    
    def _create_header(self) -> str:
        """Create dashboard header"""
        brand_score = self.results.get('brand_growth_score', {}).get('overall_score', 0)
        total_posts = self.results.get('total_posts', 0)
        
        return f"""
        <div class="header">
            <h1>🎯 Personal Brand Analysis Dashboard</h1>
            <p>Comprehensive analysis of content performance and brand growth potential</p>
            
            <div class="brand-score">
                <div class="score-number">{brand_score}/100</div>
                <div style="font-size: 1.2em; margin-top: 10px;">Brand Growth Potential Score</div>
                <div style="font-size: 1em; opacity: 0.8; margin-top: 5px;">Based on {total_posts} posts analyzed</div>
            </div>
        </div>
        """
    
    def _create_kpi_cards(self) -> str:
        """Create KPI summary cards"""
        kpi_scores = self.results.get('kpi_scores', {})
        
        kpi_cards = []
        kpi_config = [
            ('brand_authenticity_score', 'Brand Authenticity', '🎭'),
            ('growth_execution_rate', 'Growth Execution', '📈'),
            ('content_authority_level', 'Content Authority', '🎓'),
            ('customer_acquisition_readiness', 'Acquisition Readiness', '🎯'),
            ('audience_engagement_quality', 'Engagement Quality', '💬'),
            ('brand_risk_score', 'Brand Risk', '⚠️')
        ]
        
        for key, label, emoji in kpi_config:
            value = kpi_scores.get(key, 0)
            color_class = 'trend-negative' if 'risk' in key else ('trend-positive' if value > 75 else 'trend-neutral')
            
            kpi_cards.append(f"""
            <div class="kpi-card">
                <div class="kpi-value {color_class}">{emoji} {value:.1f}%</div>
                <div class="kpi-label">{label}</div>
            </div>
            """)
        
        return f"""
        <div class="kpi-grid">
            {''.join(kpi_cards)}
        </div>
        """
    
    def _create_trend_cards(self) -> str:
        """Create trend evolution cards"""
        trend_changes = self.results.get('trend_changes', {})
        
        trend_cards = []
        trend_config = [
            ('thought_leadership', 'Thought Leadership', '🧠'),
            ('authenticity_gaps', 'Authenticity Gaps', '🎭'),
            ('conversion_intent', 'Conversion Intent', '🎯'),
            ('over_promotion', 'Over-Promotion', '📢'),
            ('audience_engagement', 'Audience Engagement', '💬'),
            ('viral_potential', 'Viral Potential', '🚀')
        ]
        
        for key, label, emoji in trend_config:
            change = trend_changes.get(key, 0)
            
            if change > 0:
                color_class = 'trend-positive'
                arrow = '↗'
                sign = '+'
            elif change < 0:
                color_class = 'trend-negative'
                arrow = '↘'
                sign = ''
            else:
                color_class = 'trend-neutral'
                arrow = '→'
                sign = ''
            
            trend_cards.append(f"""
            <div class="trend-card">
                <div class="trend-value {color_class}">
                    {emoji} {sign}{change}%
                    <span class="trend-arrow">{arrow}</span>
                </div>
                <div class="kpi-label">{label}</div>
            </div>
            """)
        
        return f"""
        <div class="trend-grid">
            {''.join(trend_cards)}
        </div>
        """
    
    def _create_charts_grid(self) -> str:
        """Create the grid of 12 charts"""
        charts = [
            ('growthTrendChart', 'Growth Metrics Trend Analysis', 'growth_metrics_trend'),
            ('correlationChart', 'Brand & Growth Correlation Matrix', 'correlation_matrix'),
            ('acquisitionRadarChart', 'Customer Acquisition Traits', 'acquisition_radar'),
            ('evolutionTimelineChart', 'Brand Growth Evolution Timeline', 'evolution_timeline'),
            ('personalityProfileChart', 'Personal Brand Personality Profile', 'personality_profile'),
            ('riskGrowthScatterChart', 'Growth vs Brand Risk Analysis', 'risk_vs_growth'),
            ('contentDistributionChart', 'Content Strategy Distribution', 'content_distribution'),
            ('brandEvolutionChart', 'Brand Evolution Over Time', 'brand_evolution'),
            ('riskIndicatorsChart', 'Brand Risk Indicators', 'risk_indicators'),
            ('engagementEvolutionChart', 'Audience Engagement Evolution', 'engagement_evolution'),
            ('benchmarkRadarChart', 'Growth KPIs vs Industry Benchmarks', 'kpi_benchmarks'),
            ('acquisitionReadinessChart', 'Customer Acquisition Readiness', 'acquisition_readiness')
        ]
        
        chart_containers = []
        for chart_id, title, data_key in charts:
            chart_containers.append(f"""
            <div class="chart-container">
                <div class="chart-title">{title}</div>
                <div class="chart-canvas">
                    <canvas id="{chart_id}"></canvas>
                </div>
            </div>
            """)
        
        return f"""
        <div class="charts-grid">
            {''.join(chart_containers)}
        </div>
        """
    
    def _create_insights_section(self) -> str:
        """Create insights section"""
        insights = self.results.get('insights', {})
        
        insight_cards = []
        insight_config = [
            ('strong_correlations', 'Strong Brand Correlations', '🔗'),
            ('acquisition_strengths', 'Customer Acquisition Strengths', '💪'),
            ('growth_opportunities', 'Growth Acceleration Opportunities', '🚀'),
            ('risk_mitigation', 'Brand Risk Mitigation', '🛡️')
        ]
        
        for key, title, emoji in insight_config:
            insight_items = insights.get(key, [])
            if not insight_items:
                insight_items = [f"No specific {title.lower()} identified in current data"]
            
            items_html = ''.join([f'<li>{item}</li>' for item in insight_items])
            
            insight_cards.append(f"""
            <div class="insight-card">
                <div class="insight-title">{emoji} {title}</div>
                <ul class="insight-list">
                    {items_html}
                </ul>
            </div>
            """)
        
        return f"""
        <div class="insights-section">
            <h2 style="text-align: center; margin-bottom: 30px; color: #2E86AB;">📊 Key Insights</h2>
            <div class="insights-grid">
                {''.join(insight_cards)}
            </div>
        </div>
        """
    
    def _create_recommendations_section(self) -> str:
        """Create recommendations section"""
        recommendations = self.results.get('recommendations', {})
        
        rec_cards = []
        rec_config = [
            ('content_strategy', 'Content Strategy Optimization', '📝'),
            ('brand_strengthening', 'Personal Brand Strengthening', '💎'),
            ('acquisition_improvement', 'Customer Acquisition Improvement', '🎯'),
            ('risk_mitigation', 'Risk Mitigation Approaches', '🛡️')
        ]
        
        for key, title, emoji in rec_config:
            rec_items = recommendations.get(key, [])
            if not rec_items:
                rec_items = [f"Continue current {title.lower()} practices"]
            
            items_html = ''.join([f'<li>{item}</li>' for item in rec_items])
            
            rec_cards.append(f"""
            <div class="insight-card">
                <div class="insight-title">{emoji} {title}</div>
                <ul class="insight-list">
                    {items_html}
                </ul>
            </div>
            """)
        
        return f"""
        <div class="recommendations-section">
            <h2 style="text-align: center; margin-bottom: 30px; color: #2E86AB;">💡 Strategic Recommendations</h2>
            <div class="insights-grid">
                {''.join(rec_cards)}
            </div>
        </div>
        """
    
    def _create_footer(self) -> str:
        """Create dashboard footer"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return f"""
        <div class="footer">
            <p>📅 Generated on {current_time}</p>
            <p>🎯 Personal Brand Analysis Dashboard - Powered by advanced analytics</p>
        </div>
        """
    
    def _generate_chart_scripts(self) -> str:
        """Generate JavaScript for all charts"""
        
        # Convert chart data to JSON
        chart_data_json = json.dumps(self.chart_data, indent=2)
        
        return f"""
        // Chart data
        const chartData = {chart_data_json};
        
        // Chart configurations and initialization
        {self._get_chart_1_script()}
        {self._get_chart_2_script()}
        {self._get_chart_3_script()}
        {self._get_chart_4_script()}
        {self._get_chart_5_script()}
        {self._get_chart_6_script()}
        {self._get_chart_7_script()}
        {self._get_chart_8_script()}
        {self._get_chart_9_script()}
        {self._get_chart_10_script()}
        {self._get_chart_11_script()}
        {self._get_chart_12_script()}
        """
    
    def _get_chart_1_script(self) -> str:
        """Growth Metrics Trend Analysis - Bar Chart"""
        return """
        // Chart 1: Growth Metrics Trend Analysis
        if (chartData.growth_metrics_trend && chartData.growth_metrics_trend.labels) {
            const ctx1 = document.getElementById('growthTrendChart').getContext('2d');
            new Chart(ctx1, {
                type: 'bar',
                data: {
                    labels: chartData.growth_metrics_trend.labels,
                    datasets: [
                        {
                            label: 'Historical',
                            data: chartData.growth_metrics_trend.historical,
                            backgroundColor: 'rgba(54, 162, 235, 0.6)',
                            borderColor: 'rgba(54, 162, 235, 1)',
                            borderWidth: 2
                        },
                        {
                            label: 'Recent',
                            data: chartData.growth_metrics_trend.recent,
                            backgroundColor: 'rgba(75, 192, 192, 0.6)',
                            borderColor: 'rgba(75, 192, 192, 1)',
                            borderWidth: 2
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Historical vs Recent Performance'
                        },
                        tooltip: {
                            callbacks: {
                                afterLabel: function(context) {
                                    const index = context.dataIndex;
                                    const change = chartData.growth_metrics_trend.changes[index];
                                    return `Change: ${change > 0 ? '+' : ''}${change}%`;
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            title: {
                                display: true,
                                text: 'Score (0-100)'
                            }
                        }
                    }
                }
            });
        }
        """
    
    def _get_chart_2_script(self) -> str:
        """Brand & Growth Correlation Matrix - Heatmap"""
        return """
        // Chart 2: Brand & Growth Correlation Matrix
        if (chartData.correlation_matrix && chartData.correlation_matrix.labels) {
            const ctx2 = document.getElementById('correlationChart').getContext('2d');
            
            // Transform correlation data for heatmap
            const heatmapData = [];
            chartData.correlation_matrix.data.forEach((row, i) => {
                row.forEach((value, j) => {
                    heatmapData.push({
                        x: chartData.correlation_matrix.labels[j],
                        y: chartData.correlation_matrix.labels[i],
                        v: value
                    });
                });
            });
            
            new Chart(ctx2, {
                type: 'scatter',
                data: {
                    datasets: [{
                        label: 'Correlation',
                        data: heatmapData,
                        backgroundColor: function(context) {
                            const value = context.parsed.v;
                            const alpha = Math.abs(value);
                            return value > 0 ? `rgba(75, 192, 192, ${alpha})` : `rgba(255, 99, 132, ${alpha})`;
                        },
                        pointRadius: 15
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        tooltip: {
                            callbacks: {
                                title: function(context) {
                                    return `${context[0].parsed.y} vs ${context[0].parsed.x}`;
                                },
                                label: function(context) {
                                    return `Correlation: ${context.parsed.v.toFixed(3)}`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            type: 'category',
                            labels: chartData.correlation_matrix.labels,
                            title: { display: true, text: 'Metrics' }
                        },
                        y: {
                            type: 'category',
                            labels: chartData.correlation_matrix.labels,
                            title: { display: true, text: 'Metrics' }
                        }
                    }
                }
            });
        }
        """
    
    def _get_chart_3_script(self) -> str:
        """Customer Acquisition Traits Radar"""
        return """
        // Chart 3: Customer Acquisition Traits Radar
        if (chartData.acquisition_radar && chartData.acquisition_radar.labels) {
            const ctx3 = document.getElementById('acquisitionRadarChart').getContext('2d');
            new Chart(ctx3, {
                type: 'radar',
                data: {
                    labels: chartData.acquisition_radar.labels,
                    datasets: [
                        {
                            label: 'Current Performance',
                            data: chartData.acquisition_radar.data,
                            backgroundColor: 'rgba(54, 162, 235, 0.2)',
                            borderColor: 'rgba(54, 162, 235, 1)',
                            borderWidth: 2,
                            pointBackgroundColor: 'rgba(54, 162, 235, 1)'
                        },
                        {
                            label: 'Optimal Range',
                            data: chartData.acquisition_radar.benchmarks,
                            backgroundColor: 'rgba(255, 206, 86, 0.1)',
                            borderColor: 'rgba(255, 206, 86, 1)',
                            borderWidth: 2,
                            borderDash: [5, 5],
                            pointBackgroundColor: 'rgba(255, 206, 86, 1)'
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        r: {
                            beginAtZero: true,
                            max: 100,
                            ticks: {
                                stepSize: 20
                            }
                        }
                    }
                }
            });
        }
        """
    
    def _get_chart_4_script(self) -> str:
        """Brand Growth Evolution Timeline"""
        return """
        // Chart 4: Brand Growth Evolution Timeline
        if (chartData.evolution_timeline && chartData.evolution_timeline.labels) {
            const ctx4 = document.getElementById('evolutionTimelineChart').getContext('2d');
            new Chart(ctx4, {
                type: 'line',
                data: {
                    labels: chartData.evolution_timeline.labels,
                    datasets: chartData.evolution_timeline.datasets.map((dataset, index) => ({
                        label: dataset.label,
                        data: dataset.data,
                        borderColor: ['rgba(255, 99, 132, 1)', 'rgba(54, 162, 235, 1)', 'rgba(75, 192, 192, 1)'][index],
                        backgroundColor: ['rgba(255, 99, 132, 0.1)', 'rgba(54, 162, 235, 0.1)', 'rgba(75, 192, 192, 0.1)'][index],
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4
                    }))
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Evolution Over Time Periods'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            title: {
                                display: true,
                                text: 'Score (0-100)'
                            }
                        }
                    }
                }
            });
        }
        """
    
    def _get_chart_5_script(self) -> str:
        """Personal Brand Personality Profile"""
        return """
        // Chart 5: Personal Brand Personality Profile
        if (chartData.personality_profile && chartData.personality_profile.labels) {
            const ctx5 = document.getElementById('personalityProfileChart').getContext('2d');
            new Chart(ctx5, {
                type: 'polarArea',
                data: {
                    labels: chartData.personality_profile.labels,
                    datasets: [{
                        data: chartData.personality_profile.data,
                        backgroundColor: [
                            'rgba(255, 99, 132, 0.6)',
                            'rgba(54, 162, 235, 0.6)',
                            'rgba(255, 206, 86, 0.6)',
                            'rgba(75, 192, 192, 0.6)',
                            'rgba(153, 102, 255, 0.6)'
                        ],
                        borderColor: [
                            'rgba(255, 99, 132, 1)',
                            'rgba(54, 162, 235, 1)',
                            'rgba(255, 206, 86, 1)',
                            'rgba(75, 192, 192, 1)',
                            'rgba(153, 102, 255, 1)'
                        ],
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        r: {
                            beginAtZero: true,
                            max: 100,
                            ticks: {
                                stepSize: 20
                            }
                        }
                    }
                }
            });
        }
        """
    
    def _get_chart_6_script(self) -> str:
        """Growth vs Brand Risk Analysis"""
        return """
        // Chart 6: Growth vs Brand Risk Analysis
        if (chartData.risk_vs_growth && chartData.risk_vs_growth.data) {
            const ctx6 = document.getElementById('riskGrowthScatterChart').getContext('2d');
            new Chart(ctx6, {
                type: 'scatter',
                data: {
                    datasets: [{
                        label: 'Content Posts',
                        data: chartData.risk_vs_growth.data,
                        backgroundColor: function(context) {
                            const point = context.parsed;
                            if (point.x < 30 && point.y > 70) return 'rgba(75, 192, 192, 0.6)'; // Low risk, high growth
                            if (point.x > 70 && point.y < 30) return 'rgba(255, 99, 132, 0.6)'; // High risk, low growth
                            return 'rgba(255, 206, 86, 0.6)'; // Medium
                        },
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 2,
                        pointRadius: 6
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Risk vs Growth Opportunity Matrix'
                        }
                    },
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: 'Brand Risk Score'
                            },
                            min: 0,
                            max: 100
                        },
                        y: {
                            title: {
                                display: true,
                                text: 'Growth Opportunity Score'
                            },
                            min: 0,
                            max: 100
                        }
                    }
                }
            });
        }
        """
    
    def _get_chart_7_script(self) -> str:
        """Content Strategy Distribution"""
        return """
        // Chart 7: Content Strategy Distribution
        if (chartData.content_distribution && chartData.content_distribution.labels) {
            const ctx7 = document.getElementById('contentDistributionChart').getContext('2d');
            new Chart(ctx7, {
                type: 'doughnut',
                data: {
                    labels: chartData.content_distribution.labels,
                    datasets: [{
                        data: chartData.content_distribution.data,
                        backgroundColor: [
                            'rgba(255, 99, 132, 0.8)',
                            'rgba(54, 162, 235, 0.8)',
                            'rgba(255, 206, 86, 0.8)',
                            'rgba(75, 192, 192, 0.8)',
                            'rgba(153, 102, 255, 0.8)',
                            'rgba(255, 159, 64, 0.8)',
                            'rgba(199, 199, 199, 0.8)',
                            'rgba(83, 102, 255, 0.8)'
                        ],
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    const percentage = chartData.content_distribution.percentages[context.dataIndex];
                                    return `${context.label}: ${context.parsed} posts (${percentage}%)`;
                                }
                            }
                        }
                    }
                }
            });
        }
        """
    
    def _get_chart_8_script(self) -> str:
        """Brand Evolution Over Time"""
        return """
        // Chart 8: Brand Evolution Over Time
        if (chartData.brand_evolution && chartData.brand_evolution.labels) {
            const ctx8 = document.getElementById('brandEvolutionChart').getContext('2d');
            new Chart(ctx8, {
                type: 'line',
                data: {
                    labels: chartData.brand_evolution.labels,
                    datasets: chartData.brand_evolution.datasets.map((dataset, index) => ({
                        label: dataset.label,
                        data: dataset.data,
                        borderColor: ['rgba(255, 99, 132, 1)', 'rgba(54, 162, 235, 1)', 'rgba(75, 192, 192, 1)', 'rgba(153, 102, 255, 1)'][index],
                        backgroundColor: ['rgba(255, 99, 132, 0.1)', 'rgba(54, 162, 235, 0.1)', 'rgba(75, 192, 192, 0.1)', 'rgba(153, 102, 255, 0.1)'][index],
                        borderWidth: 2,
                        fill: false,
                        tension: 0.4
                    }))
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Content Category Evolution'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            title: {
                                display: true,
                                text: 'Percentage (%)'
                            }
                        }
                    }
                }
            });
        }
        """
    
    def _get_chart_9_script(self) -> str:
        """Brand Risk Indicators"""
        return """
        // Chart 9: Brand Risk Indicators
        if (chartData.risk_indicators && chartData.risk_indicators.labels) {
            const ctx9 = document.getElementById('riskIndicatorsChart').getContext('2d');
            new Chart(ctx9, {
                type: 'bar',
                data: {
                    labels: chartData.risk_indicators.labels,
                    datasets: [{
                        label: 'Risk Percentage',
                        data: chartData.risk_indicators.data,
                        backgroundColor: chartData.risk_indicators.colors,
                        borderColor: chartData.risk_indicators.colors.map(color => color.replace('0.6', '1')),
                        borderWidth: 2
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Behavioral Risk Assessment'
                        }
                    },
                    scales: {
                        x: {
                            beginAtZero: true,
                            max: 100,
                            title: {
                                display: true,
                                text: 'Risk Percentage (%)'
                            }
                        }
                    }
                }
            });
        }
        """
    
    def _get_chart_10_script(self) -> str:
        """Audience Engagement Evolution"""
        return """
        // Chart 10: Audience Engagement Evolution
        if (chartData.engagement_evolution && chartData.engagement_evolution.datasets) {
            const ctx10 = document.getElementById('engagementEvolutionChart').getContext('2d');
            new Chart(ctx10, {
                type: 'bubble',
                data: {
                    datasets: chartData.engagement_evolution.datasets.map((dataset, index) => ({
                        label: dataset.label,
                        data: dataset.data,
                        backgroundColor: index === 0 ? 'rgba(255, 99, 132, 0.6)' : 'rgba(54, 162, 235, 0.6)',
                        borderColor: index === 0 ? 'rgba(255, 99, 132, 1)' : 'rgba(54, 162, 235, 1)',
                        borderWidth: 2
                    }))
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Engagement vs Conversion Evolution'
                        }
                    },
                    scales: {
                        x: {
                            title: {
                                display: true,
                                text: 'Audience Engagement Score'
                            },
                            min: 0,
                            max: 100
                        },
                        y: {
                            title: {
                                display: true,
                                text: 'Conversion Intent Score'
                            },
                            min: 0,
                            max: 100
                        }
                    }
                }
            });
        }
        """
    
    def _get_chart_11_script(self) -> str:
        """Growth KPIs vs Industry Benchmarks"""
        return """
        // Chart 11: Growth KPIs vs Industry Benchmarks
        if (chartData.kpi_benchmarks && chartData.kpi_benchmarks.labels) {
            const ctx11 = document.getElementById('benchmarkRadarChart').getContext('2d');
            new Chart(ctx11, {
                type: 'radar',
                data: {
                    labels: chartData.kpi_benchmarks.labels,
                    datasets: [
                        {
                            label: 'Your Performance',
                            data: chartData.kpi_benchmarks.actual,
                            backgroundColor: 'rgba(54, 162, 235, 0.2)',
                            borderColor: 'rgba(54, 162, 235, 1)',
                            borderWidth: 3,
                            pointBackgroundColor: 'rgba(54, 162, 235, 1)',
                            pointRadius: 6
                        },
                        {
                            label: 'Industry Benchmark',
                            data: chartData.kpi_benchmarks.benchmarks,
                            backgroundColor: 'rgba(255, 206, 86, 0.1)',
                            borderColor: 'rgba(255, 206, 86, 1)',
                            borderWidth: 2,
                            borderDash: [5, 5],
                            pointBackgroundColor: 'rgba(255, 206, 86, 1)',
                            pointRadius: 4
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        r: {
                            beginAtZero: true,
                            max: 100,
                            ticks: {
                                stepSize: 20
                            }
                        }
                    }
                }
            });
        }
        """
    
    def _get_chart_12_script(self) -> str:
        """Customer Acquisition Readiness Breakdown"""
        return """
        // Chart 12: Customer Acquisition Readiness Breakdown
        if (chartData.acquisition_readiness && chartData.acquisition_readiness.labels) {
            const ctx12 = document.getElementById('acquisitionReadinessChart').getContext('2d');
            new Chart(ctx12, {
                type: 'doughnut',
                data: {
                    labels: chartData.acquisition_readiness.labels,
                    datasets: [{
                        data: chartData.acquisition_readiness.data,
                        backgroundColor: [
                            'rgba(75, 192, 192, 0.8)',
                            'rgba(54, 162, 235, 0.8)',
                            'rgba(255, 206, 86, 0.8)',
                            'rgba(153, 102, 255, 0.8)',
                            'rgba(255, 99, 132, 0.8)'
                        ],
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        title: {
                            display: true,
                            text: 'Readiness Component Breakdown'
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return `${context.label}: ${context.parsed}% ready`;
                                }
                            }
                        }
                    }
                }
            });
        }
        """

def generate_personal_brand_charts(analysis_results: dict, output_file: str = 'personal_brand_analysis.html') -> str:
    """
    Generate personal brand analysis dashboard
    
    Args:
        analysis_results: Complete analysis results
        output_file: Output HTML filename
        
    Returns:
        str: Path to generated HTML file
    """
    generator = PersonalBrandChartsGenerator(analysis_results)
    return generator.generate_html_dashboard(output_file) 