"""
Defensive Secondary Rankings - Potential vs. Production
Streamlit Application for East-West Shrine Bowl Player Evaluation

5 Tabs:
1. Dashboard - Overview KPIs, scatter plot, category distribution
2. Player Profile - Individual player deep dive with radar chart
3. Compare - Side-by-side comparison (2-5 players)
4. Rankings Table - Full Great Tables implementation
5. Player Tracking - Movement visualization (placeholder data)

Data Source: secondary_ranks_new_prepared (Dataiku Dataset)
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from great_tables import GT, md, html, style, loc
import io

# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="Potential vs. Production - Secondary Prospects",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM CSS
# ============================================================================

st.markdown("""
<style>
    /* Metric styling */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
    }
    
    /* Category badge styling */
    .category-badge {
        padding: 4px 12px;
        border-radius: 15px;
        font-weight: bold;
        font-size: 14px;
        display: inline-block;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
    }
    
    /* Player card styling */
    .player-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
    }
    
    /* Score card styling */
    .score-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# CATEGORY COLORS
# ============================================================================

CATEGORY_COLORS = {
    'Elite': '#FFD700',         # Gold - The best of the best
    'Producer': '#28a745',      # Green - Gets it done
    'Prospect': '#6f42c1',      # Purple - High upside
    'Riser': '#17a2b8',         # Cyan - Improving (kept for future use)
    'Risk': '#dc3545',          # Red - Caution (kept for future use)
    'Developmental': '#6c757d'  # Gray - Depth/Average
}

# Order for display - categories that don't exist in data will be filtered out
CATEGORY_ORDER = [
    'Elite', 'Producer', 'Prospect', 'Riser', 'Risk', 'Developmental'
]

# ============================================================================
# DATA LOADING
# ============================================================================

@st.cache_data
def load_rankings_data():
    """Load the secondary rankings data from Dataiku dataset"""
    try:
        import dataiku
        dataset = dataiku.Dataset("secondary_ranks_new_prepared")
        df = dataset.get_dataframe()
    except:
        # Fallback for local development
        st.warning("⚠️ Could not connect to Dataiku. Using sample data.")
        df = pd.read_csv("secondary_ranks_new_prepared.csv")
    
    return df

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_category_color(category):
    """Get color for a category"""
    return CATEGORY_COLORS.get(category, '#6c757d')

def get_category_badge(category):
    """Generate HTML badge for category"""
    color = get_category_color(category)
    return f'<span class="category-badge" style="background-color: {color}; color: white;">{category}</span>'

def format_draft_pick(row):
    """Format draft pick as 'R1 #15' or 'UDFA'"""
    if pd.isna(row.get('draft_round')):
        return "UDFA"
    return f"R{int(row['draft_round'])} #{int(row['draft_overall_selection'])}"

def create_radar_chart(player_data, position_avg=None):
    """Create radar chart for player's 3 pillars"""
    
    categories = ['Athletic<br>Potential', 'College<br>Production', 'NFL<br>Production']
    
    # Player values
    values = [
        player_data.get('athletic_potential_score', 0) or 0,
        player_data.get('college_production_score', 0) or 0,
        player_data.get('nfl_production_score', 0) or 0
    ]
    values.append(values[0])  # Close the polygon
    
    fig = go.Figure()
    
    # Player trace
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories + [categories[0]],
        fill='toself',
        name=player_data.get('player_display_name', 'Player'),
        line_color=get_category_color(player_data.get('player_category', 'Developmental')),
        fillcolor=get_category_color(player_data.get('player_category', 'Developmental')),
        opacity=0.6
    ))
    
    # Position average trace (if provided)
    if position_avg is not None:
        avg_values = [
            position_avg.get('athletic_potential_score', 50),
            position_avg.get('college_production_score', 50),
            position_avg.get('nfl_production_score', 50)
        ]
        avg_values.append(avg_values[0])
        
        fig.add_trace(go.Scatterpolar(
            r=avg_values,
            theta=categories + [categories[0]],
            fill='toself',
            name=f"Position Avg",
            line_color='gray',
            fillcolor='gray',
            opacity=0.2
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=True,
        height=350,
        margin=dict(l=60, r=60, t=40, b=40)
    )
    
    return fig

def create_scatter_plot(df, color_by='player_category'):
    """Create scatter plot of RAS vs NFL Production"""
    
    # Filter out rows with missing data
    plot_df = df.dropna(subset=['RAS', 'nfl_production_score']).copy()
    
    if len(plot_df) == 0:
        return None
    
    # Create hover text
    plot_df['hover_text'] = plot_df.apply(
        lambda row: f"<b>{row['player_display_name']}</b><br>" +
                    f"Position: {row['position']}<br>" +
                    f"Category: {row['player_category']}<br>" +
                    f"RAS: {row['RAS']:.2f}<br>" +
                    f"NFL Score: {row['nfl_production_score']:.1f}<br>" +
                    f"Composite: {row['composite_score']:.1f}",
        axis=1
    )
    
    if color_by == 'player_category':
        color_map = CATEGORY_COLORS
        fig = px.scatter(
            plot_df,
            x='RAS',
            y='nfl_production_score',
            color='player_category',
            size='composite_score',
            hover_name='player_display_name',
            hover_data={
                'position': True,
                'RAS': ':.2f',
                'nfl_production_score': ':.1f',
                'composite_score': ':.1f',
                'player_category': True
            },
            color_discrete_map=color_map,
            category_orders={'player_category': CATEGORY_ORDER}
        )
    else:  # color by position
        fig = px.scatter(
            plot_df,
            x='RAS',
            y='nfl_production_score',
            color='position',
            size='composite_score',
            hover_name='player_display_name',
            hover_data={
                'position': True,
                'RAS': ':.2f',
                'nfl_production_score': ':.1f',
                'composite_score': ':.1f',
                'player_category': True
            },
            color_discrete_map={'CB': '#1f77b4', 'SAF': '#d62728'}
        )
    
    # Add quadrant lines
    fig.add_hline(y=66.67, line_dash="dot", line_color="gray", opacity=0.5)
    fig.add_vline(x=6.67, line_dash="dot", line_color="gray", opacity=0.5)  # 66.67% of 10
    
    # Add quadrant labels
    fig.add_annotation(x=8.5, y=85, text="Stars/Superstars", showarrow=False, font=dict(size=10, color="gray"))
    fig.add_annotation(x=4, y=85, text="Overachievers", showarrow=False, font=dict(size=10, color="gray"))
    fig.add_annotation(x=8.5, y=25, text="Underperformers", showarrow=False, font=dict(size=10, color="gray"))
    fig.add_annotation(x=4, y=25, text="Developmental", showarrow=False, font=dict(size=10, color="gray"))
    
    fig.update_layout(
        xaxis_title="RAS (Relative Athletic Score)",
        yaxis_title="NFL Production Score",
        xaxis=dict(range=[0, 10.5]),
        yaxis=dict(range=[0, 105]),
        height=500,
        legend_title="Category" if color_by == 'player_category' else "Position"
    )
    
    return fig

def create_category_bar_chart(df):
    """Create horizontal bar chart of category distribution"""
    
    category_counts = df['player_category'].value_counts().reindex(CATEGORY_ORDER).fillna(0)
    
    fig = go.Figure(go.Bar(
        x=category_counts.values,
        y=category_counts.index,
        orientation='h',
        marker_color=[CATEGORY_COLORS.get(cat, '#6c757d') for cat in category_counts.index]
    ))
    
    fig.update_layout(
        xaxis_title="Number of Players",
        yaxis_title="",
        height=400,
        margin=dict(l=150, r=20, t=20, b=40),
        yaxis=dict(autorange="reversed")
    )
    
    return fig

def create_great_table(df):
    """Create Great Tables visualization"""
    
    # Prepare display dataframe
    display_cols = [
        'headshot_url', 'player_display_name', 'draft_season', 'draft_round',
        'draft_overall_selection', 'position', 'draft_club_name', 'team_name',
        'RAS', 'athletic_potential_rank', 'college_production_rank',
        'nfl_production_rank', 'composite_rank', 'player_category'
    ]
    
    available_cols = [c for c in display_cols if c in df.columns]
    table_df = df[available_cols].copy()
    
    # Rename columns
    column_rename = {
        'headshot_url': 'Photo',
        'player_display_name': 'Player',
        'draft_season': 'Year',
        'draft_round': 'Round',
        'draft_overall_selection': 'Pick',
        'position': 'Pos',
        'draft_club_name': 'NFL Team',
        'team_name': 'College',
        'RAS': 'RAS',
        'athletic_potential_rank': 'Ath Rank',
        'college_production_rank': 'Col Rank',
        'nfl_production_rank': 'NFL Rank',
        'composite_rank': 'Overall',
        'player_category': 'Category'
    }
    
    table_df = table_df.rename(columns={k: v for k, v in column_rename.items() if k in table_df.columns})
    
    # Sort by category order then composite rank
    table_df['Category_Order'] = table_df['Category'].apply(
        lambda x: CATEGORY_ORDER.index(x) if x in CATEGORY_ORDER else 99
    )
    table_df = table_df.sort_values(['Category_Order', 'Overall'], ascending=[True, True])
    table_df = table_df.drop(columns=['Category_Order'])
    
    # Format columns
    if 'Year' in table_df.columns:
        table_df['Year'] = table_df['Year'].apply(lambda x: f"{int(x)}" if pd.notna(x) else "—")
    
    if 'Round' in table_df.columns:
        table_df['Round'] = table_df['Round'].apply(lambda x: f"R{int(x)}" if pd.notna(x) else "UDFA")
    
    if 'Pick' in table_df.columns:
        table_df['Pick'] = table_df['Pick'].apply(lambda x: f"#{int(x)}" if pd.notna(x) else "—")
    
    if 'RAS' in table_df.columns:
        table_df['RAS'] = table_df['RAS'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "—")
    
    rank_cols = ['Ath Rank', 'Col Rank', 'NFL Rank', 'Overall']
    for col in rank_cols:
        if col in table_df.columns:
            table_df[col] = table_df[col].apply(lambda x: f"{int(x)}" if pd.notna(x) else "—")
    
    if 'NFL Team' in table_df.columns:
        table_df['NFL Team'] = table_df['NFL Team'].apply(
            lambda x: x[:15] + "..." if pd.notna(x) and len(str(x)) > 18 else (x if pd.notna(x) else "—")
        )
    
    if 'College' in table_df.columns:
        table_df['College'] = table_df['College'].apply(
            lambda x: x[:15] + "..." if pd.notna(x) and len(str(x)) > 18 else (x if pd.notna(x) else "—")
        )
    
    if 'Photo' in table_df.columns:
        table_df['Photo'] = table_df['Photo'].apply(
            lambda x: f'<img src="{x}" style="height:40px; width:40px; object-fit:cover; border-radius:50%;">' 
            if pd.notna(x) and x != '' else '👤'
        )
    
    # Create Great Table
    table = (
        GT(table_df, groupname_col='Category')
        .tab_header(
            title=md("**Defensive Secondary Rankings**"),
            subtitle=md("*Potential vs. Production — East-West Shrine Bowl*")
        )
        .tab_spanner(label="Draft Info", columns=['Year', 'Round', 'Pick'])
        .tab_spanner(label="Team", columns=['Pos', 'NFL Team', 'College'])
        .tab_spanner(label="Rankings", columns=['RAS', 'Ath Rank', 'Col Rank', 'NFL Rank', 'Overall'])
        .fmt_markdown(columns=['Photo'])
        .cols_align(align='center', columns=['Photo', 'Year', 'Round', 'Pick', 'Pos', 'RAS', 'Ath Rank', 'Col Rank', 'NFL Rank', 'Overall'])
        .cols_align(align='left', columns=['Player', 'NFL Team', 'College'])
        .cols_width({
            'Photo': '55px',
            'Player': '140px',
            'Year': '50px',
            'Round': '50px',
            'Pick': '50px',
            'Pos': '45px',
            'NFL Team': '110px',
            'College': '110px',
            'RAS': '50px',
            'Ath Rank': '55px',
            'Col Rank': '55px',
            'NFL Rank': '55px',
            'Overall': '55px'
        })
        .tab_style(
            style=style.fill(color="#f0f9e8"),
            locations=loc.row_groups()
        )
        .tab_style(
            style=style.text(weight="bold"),
            locations=loc.row_groups()
        )
        .tab_options(
            table_font_size="11px",
            heading_title_font_size="16px",
            heading_subtitle_font_size="12px",
            column_labels_font_size="10px",
            row_group_font_size="12px",
            data_row_padding="5px"
        )
        .tab_source_note(
            source_note=md("*Rankings within position. RAS = Relative Athletic Score (1-10).*")
        )
    )
    
    return table

def style_comparison_table(df, metrics_config):
    """Apply conditional formatting to comparison dataframe"""
    
    def highlight_cells(row):
        styles = [''] * len(row)
        
        metric = row.iloc[0]  # First column is the metric name
        if metric not in metrics_config:
            return styles
        
        higher_better = metrics_config[metric]
        
        # Get numeric values
        values = []
        indices = []
        for idx in range(1, len(row)):
            try:
                val = row.iloc[idx]
                if pd.notna(val) and str(val) not in ['N/A', '—', '']:
                    clean_val = str(val).replace('%', '').replace('#', '').strip()
                    values.append(float(clean_val))
                    indices.append(idx)
            except:
                pass
        
        if len(values) < 2:
            return styles
        
        best_val = max(values) if higher_better else min(values)
        
        for idx, val in zip(indices, values):
            if val == best_val:
                styles[idx] = 'background-color: #28a745; color: white; font-weight: bold'
            elif higher_better and best_val != min(values):
                ratio = (val - min(values)) / (best_val - min(values))
                if ratio > 0.7:
                    styles[idx] = 'background-color: #d4edda; color: #155724'
            elif not higher_better and best_val != max(values):
                ratio = (max(values) - val) / (max(values) - best_val)
                if ratio > 0.7:
                    styles[idx] = 'background-color: #d4edda; color: #155724'
        
        return styles
    
    return df.style.apply(highlight_cells, axis=1)

def export_to_pdf(df, filename="rankings_export.pdf"):
    """Export dataframe to PDF (returns bytes)"""
    # Create a simple HTML table and convert to PDF-like format
    # Note: Full PDF export requires additional libraries like weasyprint
    html_content = df.to_html(index=False)
    return html_content.encode()

# ============================================================================
# LOAD DATA
# ============================================================================

with st.spinner("Loading player data..."):
    rankings_df = load_rankings_data()

if rankings_df.empty:
    st.error("❌ No data loaded. Please check the data source.")
    st.stop()

# ============================================================================
# SIDEBAR - GLOBAL FILTERS
# ============================================================================

st.sidebar.image("https://upload.wikimedia.org/wikipedia/en/thumb/a/a2/National_Football_League_logo.svg/1200px-National_Football_League_logo.svg.png", width=100)
st.sidebar.title("🏈 Secondary Rankings")
st.sidebar.markdown("**Potential vs. Production**")
st.sidebar.markdown("---")

# Position filter
position_filter = st.sidebar.radio(
    "Position",
    ["All", "CB", "SAF"],
    index=0,
    horizontal=True
)

# Apply position filter
if position_filter != "All":
    filtered_df = rankings_df[rankings_df['position'] == position_filter].copy()
else:
    filtered_df = rankings_df.copy()

# Category filter - only show categories that exist in the data
all_categories_in_data = rankings_df['player_category'].unique().tolist()
available_categories = [c for c in CATEGORY_ORDER if c in all_categories_in_data]

# If no categories match the order, just use what's in the data
if not available_categories:
    available_categories = all_categories_in_data

selected_categories = st.sidebar.multiselect(
    "Categories",
    options=available_categories,
    default=available_categories
)

# Apply category filter
if selected_categories:
    filtered_df = filtered_df[filtered_df['player_category'].isin(selected_categories)]
else:
    # If nothing selected, show all (avoid empty dataframe)
    selected_categories = available_categories

# Draft year filter
if 'draft_season' in filtered_df.columns:
    years = sorted(filtered_df['draft_season'].dropna().unique())
    if len(years) > 1:
        year_range = st.sidebar.slider(
            "Draft Year",
            min_value=int(min(years)),
            max_value=int(max(years)),
            value=(int(min(years)), int(max(years)))
        )
        filtered_df = filtered_df[
            (filtered_df['draft_season'] >= year_range[0]) & 
            (filtered_df['draft_season'] <= year_range[1])
        ]

# RAS filter
if 'RAS' in filtered_df.columns:
    ras_range = st.sidebar.slider(
        "RAS Range",
        min_value=0.0,
        max_value=10.0,
        value=(0.0, 10.0),
        step=0.5
    )
    filtered_df = filtered_df[
        (filtered_df['RAS'] >= ras_range[0]) & 
        (filtered_df['RAS'] <= ras_range[1]) |
        filtered_df['RAS'].isna()
    ]

st.sidebar.markdown("---")
st.sidebar.metric("Players Shown", len(filtered_df))

# ============================================================================
# MAIN CONTENT - TABS
# ============================================================================

st.title("🏈 Potential vs. Production")
st.markdown("### Evaluating Secondary Prospects in East-West Shrine Bowl")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Dashboard", 
    "👤 Player Profile", 
    "⚖️ Compare", 
    "📋 Rankings Table",
    "📍 Player Tracking"
])

# ============================================================================
# TAB 1: DASHBOARD
# ============================================================================

with tab1:
    st.markdown("## Overview")
    
    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Players", len(filtered_df))
    
    with col2:
        avg_ras = filtered_df['RAS'].mean()
        st.metric("Avg RAS", f"{avg_ras:.2f}" if pd.notna(avg_ras) else "N/A")
    
    with col3:
        top_category = filtered_df['player_category'].value_counts().idxmax() if len(filtered_df) > 0 else "N/A"
        st.metric("Top Category", top_category)
    
    with col4:
        elite_count = len(filtered_df[filtered_df['player_category'].isin(['Elite', 'Producer'])])
        st.metric("Elite/Producers", elite_count)
    
    st.markdown("---")
    
    # Scatter Plot
    col_scatter, col_dist = st.columns([3, 2])
    
    with col_scatter:
        st.markdown("### RAS vs NFL Production")
        color_option = st.radio("Color by:", ["Category", "Position"], horizontal=True, key="scatter_color")
        
        color_by = 'player_category' if color_option == "Category" else 'position'
        scatter_fig = create_scatter_plot(filtered_df, color_by=color_by)
        
        if scatter_fig:
            st.plotly_chart(scatter_fig, use_container_width=True)
        else:
            st.info("Not enough data to display scatter plot")
    
    with col_dist:
        st.markdown("### Category Distribution")
        bar_fig = create_category_bar_chart(filtered_df)
        st.plotly_chart(bar_fig, use_container_width=True)
    
    st.markdown("---")
    
    # Top Players by Category
    st.markdown("### Top Players by Category")
    
    # Only show categories that exist in the filtered data
    categories_to_show = [c for c in ['Elite', 'Producer', 'Prospect', 'Riser', 'Risk'] 
                          if c in filtered_df['player_category'].values]
    
    for category in categories_to_show:
        cat_players = filtered_df[filtered_df['player_category'] == category].nlargest(3, 'composite_score')
        if len(cat_players) > 0:
            with st.expander(f"{category} ({len(filtered_df[filtered_df['player_category'] == category])})"):
                for _, player in cat_players.iterrows():
                    col_img, col_info = st.columns([1, 5])
                    with col_img:
                        if pd.notna(player.get('headshot_url')):
                            st.image(player['headshot_url'], width=60)
                        else:
                            st.write("👤")
                    with col_info:
                        draft_info = format_draft_pick(player)
                        st.markdown(f"**{player['player_display_name']}** ({player['position']}) - {draft_info}")
                        st.caption(f"RAS: {player['RAS']:.2f} | Composite: {player['composite_score']:.1f}")

# ============================================================================
# TAB 2: PLAYER PROFILE
# ============================================================================

with tab2:
    st.markdown("## Player Profile")
    
    # Player selection
    player_options = ['-- Select a Player --'] + [
        f"{row['position']} - {row['player_display_name']}" 
        for _, row in filtered_df.sort_values(['position', 'player_display_name']).iterrows()
    ]
    
    selected_player_display = st.selectbox("Select Player", player_options, key="profile_select")
    
    if selected_player_display == '-- Select a Player --':
        st.info("👆 Select a player from the dropdown to view their profile")
    else:
        # Parse selection
        player_name = selected_player_display.split(" - ", 1)[1]
        player_data = filtered_df[filtered_df['player_display_name'] == player_name].iloc[0]
        
        # Header with photo and basic info
        col_photo, col_info, col_category = st.columns([1, 3, 2])
        
        with col_photo:
            if pd.notna(player_data.get('headshot_url')):
                st.image(player_data['headshot_url'], width=150)
            else:
                st.markdown("### 👤")
        
        with col_info:
            st.markdown(f"## {player_data['player_display_name']}")
            draft_info = format_draft_pick(player_data)
            team = player_data.get('draft_club_name', 'N/A')
            college = player_data.get('team_name', 'N/A')
            st.markdown(f"**{player_data['position']}** | {team} | {college}")
            st.markdown(f"**Draft:** {player_data.get('draft_season', 'N/A')} {draft_info}")
        
        with col_category:
            category = player_data['player_category']
            color = get_category_color(category)
            st.markdown(f"""
                <div style="background-color: {color}; color: white; padding: 15px; 
                            border-radius: 10px; text-align: center; margin-top: 20px;">
                    <h3 style="margin: 0;">{category}</h3>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Radar chart and scores
        col_radar, col_scores = st.columns([1, 1])
        
        with col_radar:
            st.markdown("### Performance Profile")
            
            # Calculate position average
            pos_avg = filtered_df[filtered_df['position'] == player_data['position']][
                ['athletic_potential_score', 'college_production_score', 'nfl_production_score']
            ].mean().to_dict()
            
            radar_fig = create_radar_chart(player_data.to_dict(), pos_avg)
            st.plotly_chart(radar_fig, use_container_width=True)
        
        with col_scores:
            st.markdown("### Scores & Rankings")
            
            scores_data = [
                ("RAS", f"{player_data.get('RAS', 'N/A'):.2f}" if pd.notna(player_data.get('RAS')) else "N/A", "—"),
                ("Athletic Potential", f"{player_data.get('athletic_potential_score', 'N/A'):.1f}" if pd.notna(player_data.get('athletic_potential_score')) else "N/A", 
                 f"#{int(player_data.get('athletic_potential_rank', 0))}" if pd.notna(player_data.get('athletic_potential_rank')) else "—"),
                ("College Production", f"{player_data.get('college_production_score', 'N/A'):.1f}" if pd.notna(player_data.get('college_production_score')) else "N/A",
                 f"#{int(player_data.get('college_production_rank', 0))}" if pd.notna(player_data.get('college_production_rank')) else "—"),
                ("NFL Production", f"{player_data.get('nfl_production_score', 'N/A'):.1f}" if pd.notna(player_data.get('nfl_production_score')) else "N/A",
                 f"#{int(player_data.get('nfl_production_rank', 0))}" if pd.notna(player_data.get('nfl_production_rank')) else "—"),
                ("Composite", f"{player_data.get('composite_score', 'N/A'):.1f}" if pd.notna(player_data.get('composite_score')) else "N/A",
                 f"#{int(player_data.get('composite_rank', 0))}" if pd.notna(player_data.get('composite_rank')) else "—"),
            ]
            
            for metric, score, rank in scores_data:
                col_m, col_s, col_r = st.columns([2, 1, 1])
                with col_m:
                    st.markdown(f"**{metric}**")
                with col_s:
                    st.markdown(f"{score}")
                with col_r:
                    st.markdown(f"{rank}")

# ============================================================================
# TAB 3: COMPARE
# ============================================================================

with tab3:
    st.markdown("## Player Comparison")
    st.markdown("Compare 2-5 players side-by-side")
    
    # Multi-select players
    compare_options = [
        f"{row['position']} - {row['player_display_name']}" 
        for _, row in filtered_df.sort_values(['position', 'player_display_name']).iterrows()
    ]
    
    selected_players = st.multiselect(
        "Select Players to Compare",
        compare_options,
        max_selections=5,
        key="compare_select"
    )
    
    if len(selected_players) < 2:
        st.info("👆 Select at least 2 players to compare")
    else:
        # Get selected player data
        selected_names = [s.split(" - ", 1)[1] for s in selected_players]
        compare_df = filtered_df[filtered_df['player_display_name'].isin(selected_names)].copy()
        
        # Headshots row
        st.markdown("### Selected Players")
        cols = st.columns(len(compare_df))
        
        for idx, (_, player) in enumerate(compare_df.iterrows()):
            with cols[idx]:
                if pd.notna(player.get('headshot_url')):
                    st.image(player['headshot_url'], width=100)
                else:
                    st.markdown("### 👤")
                st.markdown(f"**{player['player_display_name']}**")
                st.caption(f"{player['position']} | {player.get('draft_club_name', 'N/A')}")
        
        st.markdown("---")
        
        # Comparison table
        st.markdown("### Comparison Table")
        st.caption("🟢 Green = Best value")
        
        # Build comparison data
        metrics = [
            ('RAS', 'RAS', True),
            ('Athletic Score', 'athletic_potential_score', True),
            ('Athletic Rank', 'athletic_potential_rank', False),
            ('College Score', 'college_production_score', True),
            ('College Rank', 'college_production_rank', False),
            ('NFL Score', 'nfl_production_score', True),
            ('NFL Rank', 'nfl_production_rank', False),
            ('Composite Score', 'composite_score', True),
            ('Composite Rank', 'composite_rank', False),
            ('Category', 'player_category', None),
        ]
        
        comparison_data = []
        metrics_config = {}
        
        for metric_name, col_name, higher_better in metrics:
            row = {'Metric': metric_name}
            for _, player in compare_df.iterrows():
                val = player.get(col_name)
                if pd.isna(val):
                    row[player['player_display_name']] = 'N/A'
                elif isinstance(val, float):
                    if 'Rank' in metric_name:
                        row[player['player_display_name']] = f"#{int(val)}"
                    else:
                        row[player['player_display_name']] = f"{val:.1f}"
                else:
                    row[player['player_display_name']] = str(val)
            
            comparison_data.append(row)
            if higher_better is not None:
                metrics_config[metric_name] = higher_better
        
        comparison_df = pd.DataFrame(comparison_data)
        styled_df = style_comparison_table(comparison_df, metrics_config)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        # Overlay radar chart
        st.markdown("---")
        st.markdown("### Performance Overlay")
        
        overlay_fig = go.Figure()
        
        categories = ['Athletic<br>Potential', 'College<br>Production', 'NFL<br>Production']
        
        for _, player in compare_df.iterrows():
            values = [
                player.get('athletic_potential_score', 0) or 0,
                player.get('college_production_score', 0) or 0,
                player.get('nfl_production_score', 0) or 0
            ]
            values.append(values[0])
            
            overlay_fig.add_trace(go.Scatterpolar(
                r=values,
                theta=categories + [categories[0]],
                fill='toself',
                name=player['player_display_name'],
                opacity=0.5
            ))
        
        overlay_fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=True,
            height=400
        )
        
        st.plotly_chart(overlay_fig, use_container_width=True)

# ============================================================================
# TAB 4: RANKINGS TABLE
# ============================================================================

with tab4:
    st.markdown("## Full Rankings Table")
    
    # Additional filters for this tab
    col_sort, col_export = st.columns([2, 1])
    
    with col_sort:
        sort_by = st.selectbox(
            "Sort By",
            ["Composite Rank", "RAS", "Athletic Rank", "College Rank", "NFL Rank"],
            key="table_sort"
        )
    
    with col_export:
        st.markdown("<br>", unsafe_allow_html=True)
        export_format = st.selectbox("Export Format", ["CSV", "PDF"], key="export_format")
    
    # Sort the dataframe
    sort_map = {
        "Composite Rank": ("composite_rank", True),
        "RAS": ("RAS", False),
        "Athletic Rank": ("athletic_potential_rank", True),
        "College Rank": ("college_production_rank", True),
        "NFL Rank": ("nfl_production_rank", True)
    }
    sort_col, ascending = sort_map[sort_by]
    
    sorted_df = filtered_df.sort_values(sort_col, ascending=ascending)
    
    # Export button
    if export_format == "CSV":
        csv = sorted_df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name="secondary_rankings.csv",
            mime="text/csv"
        )
    else:
        # PDF export (simplified HTML)
        html_table = sorted_df.to_html(index=False)
        st.download_button(
            label="📥 Download PDF (HTML)",
            data=html_table,
            file_name="secondary_rankings.html",
            mime="text/html"
        )
    
    st.markdown("---")
    
    # Display Great Table
    try:
        great_table = create_great_table(sorted_df)
        st.markdown(great_table.as_raw_html(), unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"Great Tables rendering issue: {e}")
        st.markdown("### Fallback Table")
        display_cols = ['player_display_name', 'position', 'draft_season', 'RAS', 
                       'composite_score', 'composite_rank', 'player_category']
        display_cols = [c for c in display_cols if c in sorted_df.columns]
        st.dataframe(sorted_df[display_cols], use_container_width=True, hide_index=True)

# ============================================================================
# TAB 5: PLAYER TRACKING
# ============================================================================

with tab5:
    st.markdown("## Player Tracking")
    st.markdown("Visualize player movement and performance metrics")
    
    # -------------------------------------------------------------------------
    # LAZY LOADING FUNCTION - Load tracking data for single player on demand
    # -------------------------------------------------------------------------
    @st.cache_data(ttl=600)  # Cache for 10 minutes
    def load_player_tracking(gsis_id):
        """Load tracking data for a single player (lazy loading)"""
        try:
            import dataiku
            dataset = dataiku.Dataset("game_data_24_secondary_all")
            
            # Load full dataset and filter (Dataiku handles optimization)
            # For very large datasets, consider using dataset.iter_dataframes()
            df = dataset.get_dataframe()
            df = df[df['gsis_id'] == gsis_id].copy()
            
            if 'ts' in df.columns:
                df['ts'] = pd.to_datetime(df['ts'])
                df = df.sort_values('ts')
            
            return df
        except Exception as e:
            st.error(f"Error loading tracking data: {e}")
            return pd.DataFrame()
    
    # -------------------------------------------------------------------------
    # HELPER FUNCTIONS
    # -------------------------------------------------------------------------
    def calculate_tracking_stats(player_tracking_df):
        """Calculate summary statistics from tracking data"""
        if player_tracking_df.empty:
            return {}
        
        stats = {}
        
        # Speed stats (convert yards/sec to MPH: multiply by 2.045)
        if 's' in player_tracking_df.columns:
            speeds = player_tracking_df['s'].dropna()
            if len(speeds) > 0:
                stats['max_speed_mph'] = speeds.max() * 2.045
                stats['avg_speed_mph'] = speeds.mean() * 2.045
                stats['min_speed_mph'] = speeds.min() * 2.045
        
        # Acceleration stats
        if 'a' in player_tracking_df.columns:
            accels = player_tracking_df['a'].dropna()
            if len(accels) > 0:
                stats['max_acceleration'] = accels.max()
                stats['avg_acceleration'] = accels.mean()
        
        # Distance stats
        if 'dis' in player_tracking_df.columns:
            distances = player_tracking_df['dis'].dropna()
            if len(distances) > 0:
                stats['total_distance'] = distances.sum()
                stats['avg_distance_per_frame'] = distances.mean()
        
        # Frame/time stats
        stats['total_frames'] = len(player_tracking_df)
        
        if 'ts' in player_tracking_df.columns:
            ts = player_tracking_df['ts'].dropna()
            if len(ts) > 1:
                time_range = (ts.max() - ts.min()).total_seconds()
                stats['total_time_seconds'] = time_range
        
        # Play count (unique play identifiers if available)
        if 'play_id' in player_tracking_df.columns:
            stats['play_count'] = player_tracking_df['play_id'].nunique()
        elif 'playId' in player_tracking_df.columns:
            stats['play_count'] = player_tracking_df['playId'].nunique()
        
        # Direction changes (significant changes > 45 degrees)
        if 'dir' in player_tracking_df.columns:
            dirs = player_tracking_df['dir'].dropna()
            if len(dirs) > 1:
                dir_changes = dirs.diff().abs()
                # Account for 360-degree wraparound
                dir_changes = dir_changes.apply(lambda x: min(x, 360 - x) if pd.notna(x) else 0)
                significant_changes = (dir_changes > 45).sum()
                stats['direction_changes'] = significant_changes
        
        return stats
    
    def create_field_figure():
        """Create base football field figure"""
        fig = go.Figure()
        
        # Field background
        fig.add_shape(
            type="rect", x0=0, y0=0, x1=120, y1=53.3,
            fillcolor="#2e7d32", line=dict(color="white", width=2)
        )
        
        # End zones
        fig.add_shape(
            type="rect", x0=0, y0=0, x1=10, y1=53.3,
            fillcolor="#1b5e20", line=dict(color="white", width=1)
        )
        fig.add_shape(
            type="rect", x0=110, y0=0, x1=120, y1=53.3,
            fillcolor="#1b5e20", line=dict(color="white", width=1)
        )
        
        # Yard lines (every 10 yards)
        for yard in range(10, 111, 10):
            fig.add_shape(
                type="line", x0=yard, y0=0, x1=yard, y1=53.3,
                line=dict(color="white", width=1)
            )
        
        # Yard line labels
        for yard in range(10, 51, 10):
            # Left side numbers
            fig.add_annotation(
                x=yard + 10, y=5, text=str(yard),
                showarrow=False, font=dict(color="white", size=12)
            )
            fig.add_annotation(
                x=yard + 10, y=48.3, text=str(yard),
                showarrow=False, font=dict(color="white", size=12)
            )
            # Right side numbers (mirrored)
            if yard < 50:
                fig.add_annotation(
                    x=110 - yard, y=5, text=str(yard),
                    showarrow=False, font=dict(color="white", size=12)
                )
                fig.add_annotation(
                    x=110 - yard, y=48.3, text=str(yard),
                    showarrow=False, font=dict(color="white", size=12)
                )
        
        # Hash marks (simplified)
        for yard in range(10, 111, 1):
            # Top hash
            fig.add_shape(
                type="line", x0=yard, y0=23.6, x1=yard, y1=24.6,
                line=dict(color="white", width=0.5)
            )
            # Bottom hash
            fig.add_shape(
                type="line", x0=yard, y0=28.7, x1=yard, y1=29.7,
                line=dict(color="white", width=0.5)
            )
        
        fig.update_layout(
            xaxis=dict(
                range=[-5, 125], showgrid=False, zeroline=False,
                showticklabels=False, fixedrange=True
            ),
            yaxis=dict(
                range=[-5, 58.3], showgrid=False, zeroline=False,
                showticklabels=False, fixedrange=True,
                scaleanchor="x", scaleratio=1
            ),
            height=500,
            margin=dict(l=20, r=20, t=40, b=20),
            plot_bgcolor='#2e7d32'
        )
        
        return fig
    
    def add_player_path_to_field(fig, tracking_df, color_by_speed=True):
        """Add player movement path to field figure"""
        if tracking_df.empty or 'x' not in tracking_df.columns or 'y' not in tracking_df.columns:
            return fig
        
        # Sort by timestamp if available
        if 'ts' in tracking_df.columns:
            tracking_df = tracking_df.sort_values('ts')
        
        x_coords = tracking_df['x'].values
        y_coords = tracking_df['y'].values
        
        if color_by_speed and 's' in tracking_df.columns:
            speeds = tracking_df['s'].values
            
            # Create color scale based on speed
            fig.add_trace(go.Scatter(
                x=x_coords,
                y=y_coords,
                mode='lines+markers',
                line=dict(width=3, color='rgba(255,255,255,0.3)'),
                marker=dict(
                    size=6,
                    color=speeds,
                    colorscale='YlOrRd',  # Yellow to Red (slow to fast)
                    colorbar=dict(
                        title="Speed<br>(yds/s)",
                        x=1.02,
                        len=0.5
                    ),
                    showscale=True
                ),
                hovertemplate=(
                    '<b>Position</b><br>'
                    'X: %{x:.1f} yds<br>'
                    'Y: %{y:.1f} yds<br>'
                    'Speed: %{marker.color:.1f} yds/s<br>'
                    '<extra></extra>'
                ),
                name='Movement Path'
            ))
        else:
            # Simple path without speed coloring
            fig.add_trace(go.Scatter(
                x=x_coords,
                y=y_coords,
                mode='lines+markers',
                line=dict(width=3, color='yellow'),
                marker=dict(size=6, color='yellow'),
                name='Movement Path'
            ))
        
        # Add start and end markers
        if len(x_coords) > 0:
            # Start point (green)
            fig.add_trace(go.Scatter(
                x=[x_coords[0]], y=[y_coords[0]],
                mode='markers',
                marker=dict(size=15, color='lime', symbol='circle',
                           line=dict(color='white', width=2)),
                name='Start',
                hovertemplate='<b>START</b><br>X: %{x:.1f}<br>Y: %{y:.1f}<extra></extra>'
            ))
            
            # End point (red)
            fig.add_trace(go.Scatter(
                x=[x_coords[-1]], y=[y_coords[-1]],
                mode='markers',
                marker=dict(size=15, color='red', symbol='square',
                           line=dict(color='white', width=2)),
                name='End',
                hovertemplate='<b>END</b><br>X: %{x:.1f}<br>Y: %{y:.1f}<extra></extra>'
            ))
        
        return fig
    
    # -------------------------------------------------------------------------
    # MAIN TRACKING TAB UI
    # -------------------------------------------------------------------------
    
    # Get players from the rankings data that might have tracking
    tracking_player_options = [
        f"{row['position']} - {row['player_display_name']}"
        for _, row in filtered_df.sort_values(['position', 'player_display_name']).iterrows()
        if pd.notna(row.get('gsis_player_id'))
    ]
    
    if not tracking_player_options:
        st.warning("No players available for tracking visualization")
    else:
        # Player selection
        selected_tracking_player = st.selectbox(
            "Select Player for Tracking",
            ['-- Select a Player --'] + tracking_player_options,
            key="tracking_player_select"
        )
        
        if selected_tracking_player == '-- Select a Player --':
            st.info("👆 Select a player to view their movement tracking data")
            
            # Show empty field as preview
            st.markdown("### Field Preview")
            preview_fig = create_field_figure()
            preview_fig.update_layout(title="Select a player to view tracking data")
            st.plotly_chart(preview_fig, use_container_width=True)
            
        else:
            # Get player info
            player_name = selected_tracking_player.split(" - ", 1)[1]
            player_info = filtered_df[filtered_df['player_display_name'] == player_name].iloc[0]
            gsis_id = player_info.get('gsis_player_id')
            
            if pd.isna(gsis_id):
                st.error("Player ID not found. Cannot load tracking data.")
            else:
                # Load tracking data for this player (lazy loading)
                with st.spinner(f"Loading tracking data for {player_name}..."):
                    player_tracking = load_player_tracking(gsis_id)
                
                if player_tracking.empty:
                    st.warning(f"No tracking data found for {player_name}")
                    
                    # Show empty field
                    empty_fig = create_field_figure()
                    empty_fig.update_layout(title=f"No tracking data available for {player_name}")
                    st.plotly_chart(empty_fig, use_container_width=True)
                else:
                    # Calculate stats
                    stats = calculate_tracking_stats(player_tracking)
                    
                    # ---------------------------------------------------------
                    # TOP KPI CARDS
                    # ---------------------------------------------------------
                    st.markdown("### Performance Metrics")
                    
                    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
                    
                    with kpi_col1:
                        max_speed = stats.get('max_speed_mph', 0)
                        st.metric("🚀 Max Speed", f"{max_speed:.1f} MPH")
                    
                    with kpi_col2:
                        avg_speed = stats.get('avg_speed_mph', 0)
                        st.metric("⚡ Avg Speed", f"{avg_speed:.1f} MPH")
                    
                    with kpi_col3:
                        max_accel = stats.get('max_acceleration', 0)
                        st.metric("📈 Max Acceleration", f"{max_accel:.2f} yds/s²")
                    
                    with kpi_col4:
                        total_dist = stats.get('total_distance', 0)
                        st.metric("📏 Total Distance", f"{total_dist:.1f} yds")
                    
                    st.markdown("---")
                    
                    # ---------------------------------------------------------
                    # PLAY SELECTION (if multiple plays available)
                    # ---------------------------------------------------------
                    play_col = None
                    if 'play_id' in player_tracking.columns:
                        play_col = 'play_id'
                    elif 'playId' in player_tracking.columns:
                        play_col = 'playId'
                    
                    if play_col and player_tracking[play_col].nunique() > 1:
                        unique_plays = player_tracking[play_col].unique()
                        
                        st.markdown("### Select Play")
                        
                        play_option = st.radio(
                            "View:",
                            ["All Plays Combined", "Individual Play"],
                            horizontal=True,
                            key="play_view_option"
                        )
                        
                        if play_option == "Individual Play":
                            selected_play = st.selectbox(
                                "Select Play",
                                unique_plays,
                                key="play_select"
                            )
                            display_tracking = player_tracking[player_tracking[play_col] == selected_play]
                        else:
                            display_tracking = player_tracking
                    else:
                        display_tracking = player_tracking
                    
                    # ---------------------------------------------------------
                    # FIELD VISUALIZATION WITH VIEW MODES
                    # ---------------------------------------------------------
                    st.markdown("### Movement Visualization")
                    
                    # View mode toggle
                    view_mode = st.radio(
                        "View Mode:",
                        ["📍 Path View", "🔥 Heat Map", "🎬 Frame-by-Frame"],
                        horizontal=True,
                        key="view_mode_select"
                    )
                    
                    # Sort tracking data by timestamp
                    if 'ts' in display_tracking.columns:
                        display_tracking = display_tracking.sort_values('ts').reset_index(drop=True)
                    
                    # =============================================================
                    # PATH VIEW (Original)
                    # =============================================================
                    if view_mode == "📍 Path View":
                        st.caption("🟢 Start | 🔴 End | Color intensity = Speed")
                        
                        # Create field with player path
                        field_fig = create_field_figure()
                        field_fig = add_player_path_to_field(field_fig, display_tracking, color_by_speed=True)
                        field_fig.update_layout(
                            title=f"{player_name} - Movement Path",
                            showlegend=True,
                            legend=dict(
                                yanchor="top", y=0.99,
                                xanchor="left", x=0.01,
                                bgcolor="rgba(0,0,0,0.5)",
                                font=dict(color="white")
                            )
                        )
                        
                        st.plotly_chart(field_fig, use_container_width=True)
                    
                    # =============================================================
                    # HEAT MAP VIEW
                    # =============================================================
                    elif view_mode == "🔥 Heat Map":
                        st.caption("Color intensity = Time spent in zone | Useful for coverage analysis")
                        
                        if 'x' in display_tracking.columns and 'y' in display_tracking.columns:
                            heat_fig = create_field_figure()
                            
                            x_coords = display_tracking['x'].dropna().values
                            y_coords = display_tracking['y'].dropna().values
                            
                            if len(x_coords) > 0:
                                # Add 2D histogram (heat map)
                                heat_fig.add_trace(go.Histogram2d(
                                    x=x_coords,
                                    y=y_coords,
                                    colorscale=[
                                        [0, 'rgba(0,0,0,0)'],        # Transparent for empty
                                        [0.1, 'rgba(0,0,255,0.3)'],  # Blue - low density
                                        [0.3, 'rgba(0,255,255,0.5)'],# Cyan
                                        [0.5, 'rgba(0,255,0,0.6)'],  # Green
                                        [0.7, 'rgba(255,255,0,0.7)'],# Yellow
                                        [0.9, 'rgba(255,128,0,0.8)'],# Orange
                                        [1.0, 'rgba(255,0,0,0.9)']   # Red - high density
                                    ],
                                    nbinsx=40,
                                    nbinsy=20,
                                    colorbar=dict(
                                        title="Time<br>Density",
                                        x=1.02
                                    ),
                                    hovertemplate=(
                                        'X: %{x:.0f} yds<br>'
                                        'Y: %{y:.0f} yds<br>'
                                        'Frames: %{z}<br>'
                                        '<extra></extra>'
                                    )
                                ))
                                
                                # Add contour overlay for cleaner visualization
                                heat_fig.add_trace(go.Histogram2dContour(
                                    x=x_coords,
                                    y=y_coords,
                                    colorscale='Hot',
                                    showscale=False,
                                    contours=dict(
                                        showlabels=False,
                                        coloring='none'
                                    ),
                                    line=dict(width=1, color='white'),
                                    ncontours=8,
                                    opacity=0.5
                                ))
                            
                            heat_fig.update_layout(
                                title=f"{player_name} - Coverage Heat Map",
                                showlegend=False
                            )
                            
                            st.plotly_chart(heat_fig, use_container_width=True)
                            
                            # Heat map insights
                            st.markdown("#### 🔍 Zone Analysis")
                            
                            # Calculate zone stats
                            zone_col1, zone_col2, zone_col3 = st.columns(3)
                            
                            with zone_col1:
                                # Left/Right distribution
                                left_side = (x_coords < 60).sum()
                                right_side = (x_coords >= 60).sum()
                                total = len(x_coords)
                                st.metric("Left Side", f"{left_side/total*100:.1f}%")
                            
                            with zone_col2:
                                # Deep/Short distribution
                                deep = ((x_coords < 30) | (x_coords > 90)).sum()
                                st.metric("End Zone Area", f"{deep/total*100:.1f}%")
                            
                            with zone_col3:
                                # Middle of field
                                middle = ((y_coords > 20) & (y_coords < 33.3)).sum()
                                st.metric("Middle of Field", f"{middle/total*100:.1f}%")
                        else:
                            st.warning("Position data (x, y) not available for heat map")
                    
                    # =============================================================
                    # FRAME-BY-FRAME VIEW
                    # =============================================================
                    elif view_mode == "🎬 Frame-by-Frame":
                        st.caption("Scrub through individual frames to analyze positioning")
                        
                        if len(display_tracking) > 0:
                            total_frames = len(display_tracking)
                            
                            # Frame slider
                            frame_col1, frame_col2 = st.columns([4, 1])
                            
                            with frame_col1:
                                current_frame = st.slider(
                                    "Frame",
                                    min_value=0,
                                    max_value=total_frames - 1,
                                    value=0,
                                    key="frame_slider",
                                    help="Drag to scrub through frames"
                                )
                            
                            with frame_col2:
                                st.markdown(f"**{current_frame + 1}** / {total_frames}")
                            
                            # Get current frame data
                            current_data = display_tracking.iloc[current_frame]
                            
                            # Frame metrics
                            frame_metrics = st.columns(5)
                            
                            with frame_metrics[0]:
                                if 'ts' in display_tracking.columns and pd.notna(current_data.get('ts')):
                                    ts_val = pd.to_datetime(current_data['ts'])
                                    st.metric("⏱️ Time", ts_val.strftime("%H:%M:%S.%f")[:-3])
                                else:
                                    st.metric("⏱️ Frame", f"#{current_frame + 1}")
                            
                            with frame_metrics[1]:
                                x_val = current_data.get('x', 0)
                                st.metric("📍 X Position", f"{x_val:.1f} yds" if pd.notna(x_val) else "N/A")
                            
                            with frame_metrics[2]:
                                y_val = current_data.get('y', 0)
                                st.metric("📍 Y Position", f"{y_val:.1f} yds" if pd.notna(y_val) else "N/A")
                            
                            with frame_metrics[3]:
                                speed_val = current_data.get('s', 0)
                                speed_mph = speed_val * 2.045 if pd.notna(speed_val) else 0
                                st.metric("🚀 Speed", f"{speed_mph:.1f} MPH")
                            
                            with frame_metrics[4]:
                                accel_val = current_data.get('a', 0)
                                st.metric("📈 Accel", f"{accel_val:.2f}" if pd.notna(accel_val) else "N/A")
                            
                            # Create field with frame position
                            frame_fig = create_field_figure()
                            
                            # Add path up to current frame (faded)
                            if current_frame > 0:
                                path_df = display_tracking.iloc[:current_frame + 1]
                                if 'x' in path_df.columns and 'y' in path_df.columns:
                                    frame_fig.add_trace(go.Scatter(
                                        x=path_df['x'].values,
                                        y=path_df['y'].values,
                                        mode='lines',
                                        line=dict(width=2, color='rgba(255,255,0,0.4)'),
                                        name='Path History',
                                        hoverinfo='skip'
                                    ))
                            
                            # Add future path (very faded)
                            if current_frame < total_frames - 1:
                                future_df = display_tracking.iloc[current_frame:]
                                if 'x' in future_df.columns and 'y' in future_df.columns:
                                    frame_fig.add_trace(go.Scatter(
                                        x=future_df['x'].values,
                                        y=future_df['y'].values,
                                        mode='lines',
                                        line=dict(width=1, color='rgba(255,255,255,0.2)', dash='dot'),
                                        name='Future Path',
                                        hoverinfo='skip'
                                    ))
                            
                            # Add current position (large marker)
                            if pd.notna(current_data.get('x')) and pd.notna(current_data.get('y')):
                                # Direction arrow if available
                                if pd.notna(current_data.get('dir')):
                                    dir_rad = np.radians(current_data['dir'])
                                    arrow_len = 3
                                    dx = arrow_len * np.sin(dir_rad)
                                    dy = arrow_len * np.cos(dir_rad)
                                    
                                    frame_fig.add_annotation(
                                        x=current_data['x'],
                                        y=current_data['y'],
                                        ax=current_data['x'] + dx,
                                        ay=current_data['y'] + dy,
                                        xref="x", yref="y",
                                        axref="x", ayref="y",
                                        showarrow=True,
                                        arrowhead=2,
                                        arrowsize=1.5,
                                        arrowwidth=3,
                                        arrowcolor="cyan"
                                    )
                                
                                # Player marker
                                speed_color = 'red' if speed_mph > 15 else 'yellow' if speed_mph > 10 else 'lime'
                                frame_fig.add_trace(go.Scatter(
                                    x=[current_data['x']],
                                    y=[current_data['y']],
                                    mode='markers',
                                    marker=dict(
                                        size=20,
                                        color=speed_color,
                                        symbol='circle',
                                        line=dict(color='white', width=3)
                                    ),
                                    name=f'Current Position',
                                    hovertemplate=(
                                        f'<b>{player_name}</b><br>'
                                        f'X: {current_data["x"]:.1f}<br>'
                                        f'Y: {current_data["y"]:.1f}<br>'
                                        f'Speed: {speed_mph:.1f} MPH<br>'
                                        '<extra></extra>'
                                    )
                                ))
                            
                            # Start marker
                            first_frame = display_tracking.iloc[0]
                            if pd.notna(first_frame.get('x')) and pd.notna(first_frame.get('y')):
                                frame_fig.add_trace(go.Scatter(
                                    x=[first_frame['x']],
                                    y=[first_frame['y']],
                                    mode='markers',
                                    marker=dict(size=12, color='lime', symbol='circle',
                                               line=dict(color='white', width=2)),
                                    name='Start',
                                    hoverinfo='skip'
                                ))
                            
                            frame_fig.update_layout(
                                title=f"{player_name} - Frame {current_frame + 1} of {total_frames}",
                                showlegend=True,
                                legend=dict(
                                    yanchor="top", y=0.99,
                                    xanchor="left", x=0.01,
                                    bgcolor="rgba(0,0,0,0.5)",
                                    font=dict(color="white")
                                )
                            )
                            
                            st.plotly_chart(frame_fig, use_container_width=True)
                            
                            # Additional frame details
                            with st.expander("📊 Frame Details"):
                                detail_cols = ['ts', 'x', 'y', 's', 'a', 'dis', 'dir', 'o']
                                available_detail_cols = [c for c in detail_cols if c in display_tracking.columns]
                                
                                frame_details = {}
                                for col in available_detail_cols:
                                    val = current_data.get(col)
                                    if col == 's' and pd.notna(val):
                                        frame_details['Speed (yds/s)'] = f"{val:.2f}"
                                        frame_details['Speed (MPH)'] = f"{val * 2.045:.2f}"
                                    elif col == 'a' and pd.notna(val):
                                        frame_details['Acceleration'] = f"{val:.3f}"
                                    elif col == 'dis' and pd.notna(val):
                                        frame_details['Distance'] = f"{val:.3f}"
                                    elif col == 'dir' and pd.notna(val):
                                        frame_details['Direction (°)'] = f"{val:.1f}"
                                    elif col == 'o' and pd.notna(val):
                                        frame_details['Orientation (°)'] = f"{val:.1f}"
                                    elif col == 'x' and pd.notna(val):
                                        frame_details['X Position'] = f"{val:.2f}"
                                    elif col == 'y' and pd.notna(val):
                                        frame_details['Y Position'] = f"{val:.2f}"
                                    elif col == 'ts' and pd.notna(val):
                                        frame_details['Timestamp'] = str(val)
                                
                                for k, v in frame_details.items():
                                    st.markdown(f"**{k}:** {v}")
                        else:
                            st.warning("No frames available for this play")
                    
                    # ---------------------------------------------------------
                    # DETAILED SUMMARY STATS TABLE
                    # ---------------------------------------------------------
                    st.markdown("---")
                    st.markdown("### Detailed Statistics")
                    
                    # Create two-column layout for stats
                    stat_col1, stat_col2 = st.columns(2)
                    
                    with stat_col1:
                        st.markdown("#### Speed & Acceleration")
                        speed_stats = {
                            "Max Speed (MPH)": f"{stats.get('max_speed_mph', 0):.2f}",
                            "Avg Speed (MPH)": f"{stats.get('avg_speed_mph', 0):.2f}",
                            "Min Speed (MPH)": f"{stats.get('min_speed_mph', 0):.2f}",
                            "Max Acceleration (yds/s²)": f"{stats.get('max_acceleration', 0):.2f}",
                            "Avg Acceleration (yds/s²)": f"{stats.get('avg_acceleration', 0):.2f}",
                        }
                        for stat_name, stat_value in speed_stats.items():
                            st.markdown(f"**{stat_name}:** {stat_value}")
                    
                    with stat_col2:
                        st.markdown("#### Distance & Activity")
                        activity_stats = {
                            "Total Distance (yds)": f"{stats.get('total_distance', 0):.1f}",
                            "Total Frames": f"{stats.get('total_frames', 0):,}",
                            "Direction Changes (>45°)": f"{stats.get('direction_changes', 0):,}",
                        }
                        if 'play_count' in stats:
                            activity_stats["Plays Tracked"] = f"{stats.get('play_count', 0)}"
                        if 'total_time_seconds' in stats:
                            activity_stats["Total Time (sec)"] = f"{stats.get('total_time_seconds', 0):.1f}"
                        
                        for stat_name, stat_value in activity_stats.items():
                            st.markdown(f"**{stat_name}:** {stat_value}")
                    
                    # ---------------------------------------------------------
                    # SPEED DISTRIBUTION CHART
                    # ---------------------------------------------------------
                    if 's' in display_tracking.columns:
                        st.markdown("---")
                        st.markdown("### Speed Distribution")
                        
                        speed_fig = go.Figure()
                        
                        speeds_mph = display_tracking['s'].dropna() * 2.045
                        
                        speed_fig.add_trace(go.Histogram(
                            x=speeds_mph,
                            nbinsx=30,
                            marker_color='#1f77b4',
                            opacity=0.75,
                            name='Speed Distribution'
                        ))
                        
                        # Add vertical lines for avg and max
                        avg_speed = speeds_mph.mean()
                        max_speed = speeds_mph.max()
                        
                        speed_fig.add_vline(
                            x=avg_speed, line_dash="dash", line_color="yellow",
                            annotation_text=f"Avg: {avg_speed:.1f}",
                            annotation_position="top"
                        )
                        speed_fig.add_vline(
                            x=max_speed, line_dash="dash", line_color="red",
                            annotation_text=f"Max: {max_speed:.1f}",
                            annotation_position="top"
                        )
                        
                        speed_fig.update_layout(
                            xaxis_title="Speed (MPH)",
                            yaxis_title="Frame Count",
                            height=300,
                            margin=dict(l=40, r=40, t=40, b=40),
                            showlegend=False
                        )
                        
                        st.plotly_chart(speed_fig, use_container_width=True)
                    
                    # ---------------------------------------------------------
                    # RAW DATA EXPANDER (Optional)
                    # ---------------------------------------------------------
                    with st.expander("📊 View Raw Tracking Data"):
                        display_cols = ['ts', 'x', 'y', 's', 'a', 'dis', 'dir', 'o']
                        available_cols = [c for c in display_cols if c in display_tracking.columns]
                        
                        if play_col and play_col in display_tracking.columns:
                            available_cols = [play_col] + available_cols
                        
                        st.dataframe(
                            display_tracking[available_cols].head(500),
                            use_container_width=True,
                            hide_index=True
                        )
                        st.caption(f"Showing first 500 of {len(display_tracking):,} frames")

# ============================================================================
# FOOTER
# ============================================================================

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: gray; font-size: 12px;">
    <p>Defensive Secondary Rankings | Potential vs. Production | East-West Shrine Bowl</p>
    <p>Data: Combine Measurables (RAS), College Stats, NFL Rookie Production</p>
</div>
""", unsafe_allow_html=True)
