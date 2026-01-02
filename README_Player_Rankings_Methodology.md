# Defensive Secondary Rankings: Potential vs. Production

## NFL Rookie Evaluation System for East-West Shrine Bowl Prospects

---

## Executive Summary

This ranking system evaluates defensive secondary players (Cornerbacks and Safeties) who participated in the East-West Shrine Bowl over the past 5 years. The system uses a **three-pillar approach** to assess players, but ultimately categorizes them based on **proven NFL production** as the primary indicator of success.

**Key Insight:** Once a player reaches the NFL, their college stats and combine measurables become secondary to actual on-field performance. Elite status is earned through production, not potential.

---

## Table of Contents

1. [Datasets](#datasets)
2. [The Three Pillars](#the-three-pillars)
3. [Score Calculations](#score-calculations)
4. [Player Categories](#player-categories)
5. [Category Decision Logic](#category-decision-logic)
6. [Output Columns](#output-columns)
7. [Streamlit Application](#streamlit-application)
8. [Usage Guide](#usage-guide)

---

## Datasets

### Input Dataset

**Name:** `players_def_secondary_RAS`

| Column Group | Key Columns | Description |
|--------------|-------------|-------------|
| **Player Info** | `player_display_name`, `position`, `gsis_player_id` | Player identification |
| **Draft Info** | `draft_season`, `draft_round`, `draft_overall_selection`, `draft_club_name` | NFL draft details |
| **College Info** | `team_name`, `college_season_distinct` | College team and seasons played |
| **RAS** | `RAS` | Relative Athletic Score (1-10 scale) |
| **College Stats** | `college_defense_interceptions_sum`, `college_defense_pass_breakups_sum`, `college_defense_total_tackles_sum`, `college_defense_tackles_for_loss_sum` | Cumulative college statistics |
| **NFL Stats** | `total_snaps`, `defense_interceptions`, `defense_pass_breakups`, `run_defense_tackles`, `primary_in_coverage_yards_allowed`, `primary_in_coverage_total` | NFL rookie season statistics |
| **Media** | `headshot_url` | Player photo URL |

### Output Dataset

**Name:** `secondary_ranks_new_prepared`

Contains all input columns plus calculated scores, rankings, and player categories.

---

## The Three Pillars

The evaluation system is built on three pillars, each measuring a different aspect of player quality.

### Pillar 1: Athletic Potential (RAS)

**Source:** Relative Athletic Score (RAS)

**What it measures:** Raw athletic ability based on NFL Combine and Pro Day measurables

**Scale:** 1-10 (already position-normalized)

**Why it matters:** Athletic traits like speed, agility, and explosiveness are foundational for defensive backs. RAS provides a standardized way to compare athleticism across players.

| RAS Score | Interpretation |
|-----------|----------------|
| 9.0 - 10.0 | Elite athlete |
| 7.0 - 8.9 | Above average |
| 5.0 - 6.9 | Average |
| 3.0 - 4.9 | Below average |
| 1.0 - 2.9 | Poor athlete |

---

### Pillar 2: College Production

**Source:** College defensive statistics normalized by seasons played

**What it measures:** On-field production and playmaking ability during college career

**Components:**

| Metric | Calculation | Weight | Rationale |
|--------|-------------|--------|-----------|
| Playmaking | (INTs + PBUs) / seasons | 40% | Ball skills are critical for DBs |
| Tackling | Total tackles / seasons | 35% | Shows willingness to support run game |
| Disruption | TFL / seasons | 25% | Indicates aggression and versatility |

**Why per-season rates:** Normalizes for players with different college tenures (3 vs 4+ years).

---

### Pillar 3: NFL Rookie Production

**Source:** NFL rookie season statistics

**What it measures:** Actual performance at the NFL level in year one

**Components:**

| Metric | Calculation | Weight | Direction |
|--------|-------------|--------|-----------|
| Coverage | Yards allowed / coverage snaps | 45% | Lower is better |
| Playmaking | (INTs + PBUs) / snaps × 100 | 35% | Higher is better |
| Tackling | Tackles / snaps × 100 | 20% | Higher is better |

**Why this matters most:** NFL production is the ultimate measure of a player's ability. College stats and athleticism are predictive; NFL stats are definitive.

**Minimum Sample:** Players must have 100+ NFL snaps to be evaluated on NFL production.

---

## Score Calculations

### Step 1: Calculate Rate Statistics

**College Rates:**
```
college_playmaking_per_season = (INTs + PBUs) / seasons_played
college_tackles_per_season = total_tackles / seasons_played
college_tfl_per_season = tackles_for_loss / seasons_played
```

**NFL Rates:**
```
yards_allowed_per_coverage_snap = coverage_yards_allowed / coverage_snaps
playmaking_per_100_snaps = (INTs + PBUs) / total_snaps × 100
tackles_per_100_snaps = tackles / total_snaps × 100
```

### Step 2: Convert to Percentiles

Each rate statistic is converted to a percentile (0-100) **within position group** (CB or SAF separately).

```
Higher is better: percentile = rank(pct=True) × 100
Lower is better:  percentile = (1 - rank(pct=True)) × 100
```

### Step 3: Calculate Pillar Scores

**Athletic Potential Score:**
```
athletic_potential_score = RAS percentile within position (0-100)
```

**College Production Score:**
```
college_production_score = (
    playmaking_percentile × 0.40 +
    tackling_percentile × 0.35 +
    tfl_percentile × 0.25
) / total_available_weights
```

**NFL Production Score:**
```
nfl_production_score = (
    coverage_percentile × 0.45 +
    playmaking_percentile × 0.35 +
    tackling_percentile × 0.20
) / total_available_weights
```

### Step 4: Calculate Composite Score

```
composite_score = mean(athletic_potential_score, college_production_score, nfl_production_score)
```

**Note:** Only available pillars are averaged. Missing data is handled gracefully.

---

## Player Categories

Players are classified into **4 categories** based on their performance across the three pillars.

### Category Definitions

| Category | Emoji | Color | Criteria | Description |
|----------|-------|-------|----------|-------------|
| **Elite** | 🌟 | Gold (#FFD700) | NFL Production ≥ 85 (top 15%) + 100+ snaps | Proven NFL performers. The best rookie producers regardless of athleticism or college stats. |
| **Producer** | ✅ | Green (#28a745) | High NFL (66-85%) OR High College + Medium NFL | Solid contributors who get the job done on the field. |
| **Prospect** | 🎯 | Purple (#6f42c1) | High RAS or High College, but <100 NFL snaps | High-upside players who haven't had NFL opportunity yet. |
| **Developmental** | 🔨 | Gray (#6c757d) | Everything else | Average profiles, incomplete data, or depth players. |

### Threshold Definitions

| Level | Percentile | Description |
|-------|------------|-------------|
| **Elite NFL** | ≥ 85 | Top 15% of NFL production |
| **High** | ≥ 66.67 | Top 33% |
| **Medium** | 33.33 - 66.66 | Middle 33% |
| **Low** | < 33.33 | Bottom 33% |

### Minimum Sample Requirements

| Requirement | Threshold | Purpose |
|-------------|-----------|---------|
| NFL Snaps | ≥ 100 | Ensures meaningful NFL sample size |

---

## Category Decision Logic

```
┌─────────────────────────────────────────────────────────────────┐
│                         START                                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │  NFL Production ≥ 85%         │
              │  AND 100+ snaps?              │
              └───────────────────────────────┘
                     │              │
                    YES             NO
                     │              │
                     ▼              ▼
              ┌──────────┐  ┌───────────────────────────┐
              │  ELITE   │  │  NFL High (66-85%)        │
              │    🌟    │  │  AND 100+ snaps?          │
              └──────────┘  └───────────────────────────┘
                                   │              │
                                  YES             NO
                                   │              │
                                   ▼              ▼
                            ┌──────────┐  ┌───────────────────────────┐
                            │ PRODUCER │  │  College High + NFL Med   │
                            │    ✅    │  │  AND 100+ snaps?          │
                            └──────────┘  └───────────────────────────┘
                                                 │              │
                                                YES             NO
                                                 │              │
                                                 ▼              ▼
                                          ┌──────────┐  ┌───────────────────────────┐
                                          │ PRODUCER │  │  <100 NFL snaps           │
                                          │    ✅    │  │  AND (RAS High OR         │
                                          └──────────┘  │  College High)?           │
                                                        └───────────────────────────┘
                                                               │              │
                                                              YES             NO
                                                               │              │
                                                               ▼              ▼
                                                        ┌──────────┐  ┌──────────────┐
                                                        │ PROSPECT │  │ DEVELOPMENTAL│
                                                        │    🎯    │  │      🔨      │
                                                        └──────────┘  └──────────────┘
```

### Category Logic in Plain English

1. **Elite:** Did you produce at an elite level (top 15%) in the NFL with a meaningful sample? You're Elite. Period. College stats and athleticism don't matter once you've proven it at the highest level.

2. **Producer:** Did you produce well (top 33%) in the NFL, or did you have strong college production with decent NFL translation? You're a Producer.

3. **Prospect:** Do you have high athletic potential or strong college production, but haven't gotten enough NFL snaps to prove yourself? You're a Prospect with upside.

4. **Developmental:** Everyone else. Average across the board, missing data, or limited opportunity.

---

## Output Columns

### Calculated Scores (0-100 scale)

| Column | Description |
|--------|-------------|
| `athletic_potential_score` | RAS percentile within position |
| `college_production_score` | Weighted college production percentile |
| `nfl_production_score` | Weighted NFL production percentile |
| `composite_score` | Average of available pillars |

### Rankings (1 = Best, within position)

| Column | Description |
|--------|-------------|
| `athletic_potential_rank` | Rank by RAS within position |
| `college_production_rank` | Rank by college production within position |
| `nfl_production_rank` | Rank by NFL production within position |
| `composite_rank` | Overall rank within position |

### Calculated Rate Statistics

| Column | Description |
|--------|-------------|
| `college_playmaking_per_season` | (INTs + PBUs) / seasons played |
| `college_defense_total_tackles_per_season` | Tackles / seasons played |
| `college_defense_tackles_for_loss_per_season` | TFL / seasons played |
| `yards_allowed_per_coverage_snap` | Coverage yards allowed / coverage snaps |
| `playmaking_per_100_snaps` | (INTs + PBUs) / snaps × 100 |
| `tackles_per_100_snaps` | Tackles / snaps × 100 |

### Percentile Columns

| Column | Description |
|--------|-------------|
| `ras_percentile` | RAS percentile within position |
| `college_playmaking_per_season_percentile` | College playmaking percentile |
| `yards_allowed_per_coverage_snap_percentile` | Coverage efficiency percentile (reversed) |
| `playmaking_per_100_snaps_percentile` | NFL playmaking percentile |
| `tackles_per_100_snaps_percentile` | NFL tackling percentile |

### Category and Flags

| Column | Description |
|--------|-------------|
| `player_category` | Elite, Producer, Prospect, or Developmental |
| `ras_available` | True if RAS data exists |
| `college_stats_complete` | True if 2+ college stats available |
| `nfl_sample_sufficient` | True if 100+ NFL snaps |

---

## Streamlit Application

### Overview

The Streamlit application (`secondary_rankings_app.py`) provides an interactive dashboard for exploring player rankings and categories.

### Tab Structure

| Tab | Purpose | Key Features |
|-----|---------|--------------|
| **📊 Dashboard** | High-level overview | KPI cards, scatter plot (RAS vs NFL), category distribution chart, top players by category |
| **👤 Player Profile** | Individual deep dive | Player photo, category badge, radar chart (3 pillars), scores table, detailed stats |
| **⚖️ Compare** | Side-by-side comparison | Multi-select (2-5 players), headshots, comparison table with conditional formatting, overlay radar chart |
| **📋 Rankings Table** | Full data table | Great Tables implementation, grouped by category, sortable, filterable, CSV/PDF export |
| **📍 Player Tracking** | Movement visualization | Placeholder for tracking data integration |

### Sidebar Filters

| Filter | Type | Options |
|--------|------|---------|
| Position | Radio | All, CB, SAF |
| Categories | Multi-select | Elite, Producer, Prospect, Developmental |
| Draft Year | Range slider | Dynamic based on data |
| RAS Range | Range slider | 0.0 - 10.0 |

### Visual Components

**Scatter Plot (Dashboard):**
- X-axis: RAS (1-10)
- Y-axis: NFL Production Score (0-100)
- Color: Category or Position
- Size: Composite Score
- Quadrant lines at 66.67 threshold

**Radar Chart (Player Profile):**
- 3 axes: Athletic Potential, College Production, NFL Production
- Player values filled with category color
- Position average overlay for comparison

**Comparison Table:**
- Conditional formatting: Dark green = best, Light green = above average
- Metrics: RAS, all pillar scores, ranks, category

**Great Table (Rankings):**
- Grouped by category
- Player headshots
- Draft info, teams, RAS, all ranks
- Column spanners for organization

---

## Usage Guide

### Running the Analysis Script

```python
# Cell 1: Load the dataset
import dataiku
players_def_secondary_RAS = dataiku.Dataset("players_def_secondary_RAS")
players_df = players_def_secondary_RAS.get_dataframe()

# Cell 2: Import and run analysis
from defensive_secondary_rankings_RAS import analyze
results_df = analyze(players_df)

# Cell 3: Export to Dataiku dataset
output_dataset = dataiku.Dataset("secondary_ranks_new_prepared")
output_dataset.write_with_schema(results_df)
```

### Common Queries

```python
# Get Elite players
elite = results_df[results_df['player_category'] == 'Elite']
print(elite[['player_display_name', 'position', 'nfl_production_score']])

# Get top 10 NFL producers
top_nfl = results_df.nlargest(10, 'nfl_production_score')
print(top_nfl[['player_display_name', 'nfl_production_score', 'player_category']])

# Compare CBs vs SAFs
cb_avg = results_df[results_df['position'] == 'CB']['nfl_production_score'].mean()
saf_avg = results_df[results_df['position'] == 'SAF']['nfl_production_score'].mean()
print(f"CB Avg: {cb_avg:.1f}, SAF Avg: {saf_avg:.1f}")

# Find high-RAS underperformers (potential buy-low candidates)
underperformers = results_df[
    (results_df['athletic_potential_score'] >= 66.67) &
    (results_df['nfl_production_score'] < 50)
]

# Find overachievers (low RAS, high production)
overachievers = results_df[
    (results_df['athletic_potential_score'] < 50) &
    (results_df['nfl_production_score'] >= 66.67)
]
```

### Running the Streamlit App

```bash
streamlit run secondary_rankings_app.py
```

---

## Key Insights for Scouts

### What This System Reveals

1. **Elite is Exclusive:** Only the top 15% of NFL producers earn Elite status. This represents truly exceptional rookie performance.

2. **Production > Potential:** High RAS doesn't guarantee NFL success. Look for players who produce regardless of athleticism.

3. **Prospects Have Upside:** Players with high potential (RAS or College) but limited NFL snaps deserve monitoring.

4. **Category Mobility:** A "Prospect" this year could become "Elite" next year with more opportunity.

### Actionable Recommendations

| Category | Scout Action |
|----------|--------------|
| **Elite** | Study what makes them successful. Model for future evaluations. |
| **Producer** | Reliable contributors. Target in free agency or trades. |
| **Prospect** | Monitor closely. High upside if they get playing time. |
| **Developmental** | Depth options. May need specific scheme fit to succeed. |

### Questions This System Answers

1. **Who are the best rookie DBs from recent Shrine Bowls?** → Filter by Elite category
2. **Which players outperformed their athleticism?** → Low RAS + High NFL Production
3. **Who has untapped potential?** → Prospect category with high RAS
4. **Are combine numbers predictive?** → Compare RAS vs NFL Production correlation

---

## Technical Notes

### Position Handling

- Positions are standardized: DC → CB, DS → SAF
- All percentiles calculated within position group
- Rankings are position-specific (CB ranked against CB, SAF against SAF)

### Missing Data Handling

- Missing pillars are excluded from composite score calculation
- Players with <100 NFL snaps cannot be Elite or Producer (NFL-based categories)
- `skipna=True` used for all aggregations

### Threshold Rationale

| Threshold | Value | Rationale |
|-----------|-------|-----------|
| Elite NFL | 85% | Top 15% ensures exclusivity (~9 players of 61) |
| High | 66.67% | Top third is a reasonable "above average" bar |
| Low | 33.33% | Bottom third indicates weakness |
| Min Snaps | 100 | Ensures meaningful NFL sample |

---

## File Reference

| File | Purpose |
|------|---------|
| `defensive_secondary_rankings_RAS.py` | Main analysis script with scoring and categorization |
| `secondary_rankings_app.py` | Streamlit dashboard application |
| `player_category_great_table.py` | Great Tables visualization for rankings |
| `README_Player_Rankings_Methodology.md` | This documentation |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025 | Initial 3-pillar system with 12 categories |
| 2.0 | 2025 | Simplified to 6 categories, added RAS as primary athletic metric |
| 3.0 | 2025 | Reduced to 4 categories, Elite based solely on NFL production |
| 3.1 | 2025 | Fixed score calculation bug (removed extra ×100), set Elite threshold to 85% |

---

## Contact

For questions about this ranking methodology or the Streamlit application:

**Kyle Berry**  
Twitter/X: [@kb_analytix](https://twitter.com/kb_analytix)

---

*This system was designed to provide NFL scouts with an objective, data-driven framework for evaluating defensive secondary prospects from the East-West Shrine Bowl. The emphasis on proven NFL production over potential reflects the reality that performance at the highest level is the ultimate measure of player quality.*
