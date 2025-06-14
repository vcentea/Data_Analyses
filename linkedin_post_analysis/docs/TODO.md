# Content-Personality Analysis - TODO

## 📁 Project Structure
```
charts/
├── data_loader.py          # Load and clean data
├── landscape_overview.py   # KPIs and content distribution  
├── personality_profile.py  # Big Five + Partner traits radar charts
├── topic_analysis.py       # Topic relationships and heatmaps
├── engagement_analysis.py  # Performance vs personality correlation
├── behavioral_flags.py     # Flag patterns and risk analysis
├── content_archetypes.py   # Clustering and archetype discovery
├── trend_analysis.py       # Evolution over time
└── generate_all.py         # Run all analyses and create index
```

## ✅ Implementation Tasks

### Phase 1: Setup & Data Loading
- [ ] Create `charts/` folder
- [ ] Implement `data_loader.py` 
  - Load results.jsonl (personality data)
  - Load engagement CSV data  
  - Merge datasets on post_id
  - Clean and validate data

### Phase 2: Core Analysis Charts  
- [ ] **Landscape Overview** (`landscape_overview.py`)
  - KPI cards (total posts, topics, flags %)
  - Topic distribution bar chart
  - Content diversity metrics

- [ ] **Personality Profile** (`personality_profile.py`) 
  - Big Five radar chart
  - Partner traits radar chart
  - Trait comparison bars

- [ ] **Topic Analysis** (`topic_analysis.py`)
  - Topic co-occurrence network
  - Topic-trait heatmap
  - Topic performance ranking

- [ ] **Engagement Analysis** (`engagement_analysis.py`)
  - Engagement vs traits scatter plot
  - Performance by topic bubble chart
  - Viral content DNA analysis

- [ ] **Behavioral Flags** (`behavioral_flags.py`)
  - Flag frequency by topic heatmap
  - Flag correlation matrix
  - Risk scoring distribution

### Phase 3: Advanced Analytics
- [ ] **Content Archetypes** (`content_archetypes.py`)
  - t-SNE clustering visualization
  - Archetype radar charts
  - Representative post examples

- [ ] **Trend Analysis** (`trend_analysis.py`)
  - Trait evolution over time
  - Topic mastery curves  
  - Engagement trends

### Phase 4: Integration
- [ ] **Master Generator** (`generate_all.py`)
  - Run all analysis scripts
  - Create HTML index page
  - Link all charts together

## 🛠 Technical Stack
- **Python**: pandas, numpy, scikit-learn
- **Visualization**: plotly (interactive HTML/JS charts)
- **HTML**: Simple templates with navigation
- **Output**: Self-contained HTML files

## 📊 Output Files
Each analysis will generate:
- `[analysis_name].html` - Interactive chart page
- `index.html` - Main dashboard linking all charts

## 🎯 Success Criteria
- [ ] All charts load as interactive HTML
- [ ] Clean, professional styling
- [ ] Fast loading (<3 seconds per chart)
- [ ] Mobile-responsive design
- [ ] Clear insights and interpretations 