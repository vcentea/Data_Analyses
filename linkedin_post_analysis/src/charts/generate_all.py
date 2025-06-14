#!/usr/bin/env python3
"""
Master Generator for Content-Personality Analysis
Runs all analysis scripts and creates an index page
"""

import os
import sys
import traceback
from datetime import datetime

def run_analysis(module_name, description):
    """Run an analysis module and handle errors"""
    try:
        print(f"\n🔄 Running {description}...")
        
        # Handle nested module imports
        if '.' in module_name:
            # For nested modules like core_analyses.consistency_analysis
            parts = module_name.split('.')
            module = __import__(module_name, fromlist=[parts[-1]])
            func_name = f'generate_{parts[-1]}'
        else:
            # For top-level modules
            module = __import__(module_name)
            func_name = f'generate_{module_name}'
        
        if hasattr(module, func_name):
            getattr(module, func_name)()
        else:
            print(f"⚠️  Warning: No {func_name} function found")
        
        print(f"✅ {description} completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error in {description}: {str(e)}")
        print(f"📝 Details: {traceback.format_exc()}")
        return False

def create_index_page():
    """Create main index page linking all analyses"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Check which HTML files exist
    analyses = [
        ("landscape_overview.html", "📊 Landscape Overview", "KPI dashboard and content distribution"),
        ("personality_profile.html", "🧠 Personality Profile", "Big Five and partner traits analysis"),
        ("consistency_analysis.html", "📊 Consistency Analysis", "Trait stability and volatility assessment"),
        ("behavioral_flags_analysis.html", "🚩 Behavioral Flags", "Risk patterns and flag analysis"),
        ("content_trait_nexus.html", "🎯 Content-Trait Nexus", "Topic authority and skill complementarity"),
        ("content_archetypes.html", "🎭 Content Archetypes", "Clustering and persona discovery"),
        ("risk_assessment.html", "⚠️ Risk Assessment", "Predictive models and content risk scoring"),
        ("partnership_intelligence.html", "🤝 Partnership Intelligence", "Strategic compatibility and alignment analysis"),
        ("evolution_tracking.html", "📈 Evolution Tracking", "Time-series analysis and maturation indicators"),
        ("topic_analysis.html", "🔍 Topic Analysis", "Content relationships and heatmaps"),
        ("engagement_analysis.html", "📈 Engagement Analysis", "Performance vs personality correlation"),
        ("trend_analysis.html", "📊 Trend Analysis", "Evolution over time")
    ]
    
    available_analyses = []
    for filename, title, description in analyses:
        if os.path.exists(filename):
            available_analyses.append((filename, title, description))
    
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Content-Personality Analysis Dashboard</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }}
            
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }}
            
            .header {{
                text-align: center;
                color: white;
                margin-bottom: 40px;
                padding: 40px 20px;
            }}
            
            .header h1 {{
                font-size: 3em;
                margin-bottom: 10px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }}
            
            .header p {{
                font-size: 1.2em;
                opacity: 0.9;
            }}
            
            .dashboard-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                gap: 25px;
                margin-bottom: 40px;
            }}
            
            .analysis-card {{
                background: white;
                border-radius: 15px;
                padding: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                transform: translateY(0);
                transition: all 0.3s ease;
                cursor: pointer;
                text-decoration: none;
                color: inherit;
            }}
            
            .analysis-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 15px 40px rgba(0,0,0,0.3);
                text-decoration: none;
                color: inherit;
            }}
            
            .card-icon {{
                font-size: 3em;
                margin-bottom: 15px;
                display: block;
            }}
            
            .card-title {{
                font-size: 1.5em;
                font-weight: bold;
                margin-bottom: 10px;
                color: #2E86AB;
            }}
            
            .card-description {{
                color: #666;
                font-size: 1em;
                margin-bottom: 20px;
            }}
            
            .card-button {{
                background: linear-gradient(135deg, #2E86AB, #A23B72);
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 25px;
                font-weight: bold;
                text-transform: uppercase;
                letter-spacing: 1px;
                font-size: 0.9em;
                transition: all 0.3s ease;
            }}
            
            .card-button:hover {{
                background: linear-gradient(135deg, #A23B72, #2E86AB);
                transform: scale(1.05);
            }}
            
            .unavailable {{
                opacity: 0.5;
                cursor: not-allowed;
            }}
            
            .unavailable:hover {{
                transform: none;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }}
            
            .unavailable .card-button {{
                background: #ccc;
                cursor: not-allowed;
            }}
            
            .footer {{
                text-align: center;
                color: white;
                margin-top: 40px;
                padding: 20px;
                opacity: 0.8;
            }}
            
            .stats-bar {{
                display: flex;
                justify-content: center;
                gap: 40px;
                margin: 30px 0;
                flex-wrap: wrap;
            }}
            
            .stat-item {{
                text-align: center;
                color: white;
            }}
            
            .stat-number {{
                font-size: 2.5em;
                font-weight: bold;
                display: block;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }}
            
            .stat-label {{
                font-size: 1em;
                opacity: 0.9;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            
            @media (max-width: 768px) {{
                .dashboard-grid {{
                    grid-template-columns: 1fr;
                }}
                
                .header h1 {{
                    font-size: 2em;
                }}
                
                .stats-bar {{
                    gap: 20px;
                }}
                
                .stat-number {{
                    font-size: 2em;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎯 Content-Personality Analysis</h1>
                <p>Comprehensive analysis of LinkedIn content through the lens of psychology</p>
                
                <div class="stats-bar">
                    <div class="stat-item">
                        <span class="stat-number">{len(available_analyses)}</span>
                        <span class="stat-label">Analyses Available</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">500+</span>
                        <span class="stat-label">Posts Analyzed</span>
                    </div>
                    <div class="stat-item">
                        <span class="stat-number">12</span>
                        <span class="stat-label">Personality Traits</span>
                    </div>
                </div>
            </div>
            
            <div class="dashboard-grid">
    """
    
    # Add cards for available analyses
    for filename, title, description in analyses:
        is_available = filename in [a[0] for a in available_analyses]
        card_class = "analysis-card" if is_available else "analysis-card unavailable"
        
        # Extract emoji from title
        emoji = title.split()[0] if title.split() else "📊"
        title_text = " ".join(title.split()[1:]) if len(title.split()) > 1 else title
        
        if is_available:
            html_template += f"""
                <a href="{filename}" class="{card_class}">
                    <div class="card-icon">{emoji}</div>
                    <div class="card-title">{title_text}</div>
                    <div class="card-description">{description}</div>
                    <div class="card-button">View Analysis</div>
                </a>
            """
        else:
            html_template += f"""
                <div class="{card_class}">
                    <div class="card-icon">{emoji}</div>
                    <div class="card-title">{title_text}</div>
                    <div class="card-description">{description}</div>
                    <div class="card-button">Coming Soon</div>
                </div>
            """
    
    html_template += f"""
            </div>
            
            <div class="footer">
                <p>📅 Generated on {current_time}</p>
                <p>🔬 Powered by advanced psychometric analysis and machine learning</p>
                <p>💡 Each analysis provides unique insights into content strategy and personality</p>
            </div>
        </div>
        
        <script>
            // Add some interactivity
            document.querySelectorAll('.analysis-card:not(.unavailable)').forEach(card => {{
                card.addEventListener('click', function(e) {{
                    // Add a subtle animation on click
                    this.style.transform = 'scale(0.98)';
                    setTimeout(() => {{
                        this.style.transform = '';
                    }}, 150);
                }});
            }});
            
            // Welcome message
            console.log('🎯 Content-Personality Analysis Dashboard Loaded');
            console.log('📊 Available analyses: {len(available_analyses)}');
        </script>
    </body>
    </html>
    """
    
    # Save index page
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print(f"✅ Index page created with {len(available_analyses)} available analyses")

def main():
    """Main execution function"""
    print("🚀 Starting Content-Personality Analysis Suite")
    print("=" * 60)
    
    # List of analyses to run
    analyses_to_run = [
        ("data_loader", "Data Loading & Preparation"),
        ("landscape_overview", "Landscape Overview Dashboard"),
        ("personality_profile", "Personality Profile Analysis"),
        ("core_analyses.consistency_analysis", "Consistency Analysis"),
        ("core_analyses.behavioral_flags", "Behavioral Flags Analysis"),
        ("core_analyses.content_trait_nexus", "Content-Trait Nexus Analysis"),
        ("advanced_analytics.content_archetypes", "Content Archetype Discovery"),
        ("advanced_analytics.risk_assessment", "Risk Assessment & Predictive Analysis"),
        ("advanced_analytics.partnership_intelligence", "Partnership Intelligence Analysis"),
        ("advanced_analytics.evolution_tracking", "Evolution Tracking Analysis"),
        # Add more as they're implemented
        # ("topic_analysis", "Topic Relationship Analysis"),
        # ("engagement_analysis", "Engagement Performance Analysis"),
        # ("trend_analysis", "Trend Evolution Analysis"),
    ]
    
    successful_runs = 0
    total_runs = len(analyses_to_run)
    
    # Run each analysis
    for module_name, description in analyses_to_run:
        if run_analysis(module_name, description):
            successful_runs += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Analysis Summary: {successful_runs}/{total_runs} completed successfully")
    
    # Create index page
    print("\n🔄 Creating master dashboard...")
    create_index_page()
    
    # Final summary
    print("\n🎉 Content-Personality Analysis Suite Complete!")
    print(f"📂 Open 'index.html' to view the dashboard")
    print(f"⏱️  Analysis completed at {datetime.now().strftime('%H:%M:%S')}")
    
    if successful_runs == total_runs:
        print("✅ All analyses completed successfully!")
    else:
        failed_runs = total_runs - successful_runs
        print(f"⚠️  {failed_runs} analysis(es) had errors - check logs above")

if __name__ == "__main__":
    main() 