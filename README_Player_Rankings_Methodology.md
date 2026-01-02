# Defensive Secondary Rankings: Potential vs. Production

## East-West Shrine Bowl Player Evaluation System

---

## Overview

This ranking system evaluates defensive secondary players (Cornerbacks and Safeties) using a **three-pillar approach** that balances athletic potential against actual production at both the college and NFL levels.

The goal is to create an objective, data-driven framework that can:
1. Identify elite prospects for future drafts
2. Find undervalued players (overachievers)
3. Flag potential bust risks
4. Validate whether athletic measurables predict NFL success

---

## Data Sources

| Dataset | Description |
|---------|-------------|
| `players_def_secondary_RAS` | Input dataset containing player info, measurables, college stats, and NFL rookie stats |
| `secondary_ranks_new` | Output dataset with calculated scores, ranks, and categories |

### Key Input Columns

| Column | Description |
|--------|-------------|
| `RAS` | Relative Athletic Score (1-10 scale, position-relative) |
| `position` | DC (renamed to CB) or DS (renamed to SAF) |
| `college_defense_*` | College defensive statistics |
| `total_snaps` | NFL rookie season snap count |
| `primary_in_coverage_*` | NFL coverage statistics |
| `defense_interceptions` | NFL interceptions |
| `defense_pass_breakups` | NFL pass breakups |

---

## The Three Pillars

### Pillar 1: Athletic Potential (RAS)

**Source:** Relative Athletic Score (RAS)

**What it measures:** Raw athletic ability based on combine/pro day measurables

**Scale:** 1-10 (already position-normalized)

**Scoring:**
```
Athletic Potential Score = RAS percentile within position group (0-100)
```

**Example:**
- Player has RAS of 8.5
- Ranks 5th out of 35 CBs
- Percentile = (35 - 5) / 35 × 100 = 85.7
- Athletic Potential Score = 85.7

---

### Pillar 2: College Production

**Source:** College defensive statistics normalized by seasons played

**What it measures:** Production and playmaking ability in college

**Components:**

| Metric | Weight | Higher is Better |
|--------|--------|------------------|
| Playmaking per season (INT + PBU) | 40% | ✓ |
| Total tackles per season | 35% | ✓ |
| Tackles for loss per season | 25% | ✓ |

**Calculation:**
```
1. Calculate per-season rates:
   - college_playmaking_per_season = (INTs + PBUs) / seasons_played
   - college_tackles_per_season = total_tackles / seasons_played
   - college_tfl_per_season = tackles_for_loss / seasons_played

2. Convert each to percentile within position (0-100)

3. Weighted average:
   College Production Score = (Playmaking × 0.40) + (Tackles × 0.35) + (TFL × 0.25)
```

---

### Pillar 3: NFL Rookie Production

**Source:** NFL rookie season statistics

**What it measures:** Actual NFL performance in year one

**Components:**

| Metric | Weight | Direction |
|--------|--------|-----------|
| Yards allowed per coverage snap | 45% | Lower is better |
| Playmaking per 100 snaps (INT + PBU) | 35% | Higher is better |
| Tackles per 100 snaps | 20% | Higher is better |

**Calculation:**
```
1. Calculate rate stats:
   - yards_allowed_per_coverage_snap = yards_allowed / coverage_snaps
   - playmaking_per_100_snaps = (INTs + PBUs) / total_snaps × 100
   - tackles_per_100_snaps = tackles / total_snaps × 100

2. Convert each to percentile within position (0-100)
   - For yards allowed: REVERSE percentile (lower = better = higher score)

3. Weighted average:
   NFL Production Score = (Coverage × 0.45) + (Playmaking × 0.35) + (Tackling × 0.20)
```

---

## Composite Score

The overall player score combines all three pillars with **equal weighting**:

```
Composite Score = (Athletic Potential + College Production + NFL Production) / 3
```

**Note:** If a pillar is missing (e.g., no NFL data), the composite averages only the available pillars.

---

## Ranking Methodology

Rankings are calculated **within each position group** (CB and SAF separately):

| Rank Column | Based On |
|-------------|----------|
| `athletic_potential_rank` | Athletic Potential Score (RAS percentile) |
| `college_production_rank` | College Production Score |
| `nfl_production_rank` | NFL Production Score |
| `composite_rank` | Composite Score |

**Rank 1 = Best** in each category.

---

## Player Categories

Players are classified into categories based on their performance across all three pillars.

### Threshold Definitions

| Level | Percentile Range |
|-------|------------------|
| **High** | ≥ 66.67 (Top 33%) |
| **Medium** | 33.33 - 66.66 (Middle 33%) |
| **Low** | < 33.33 (Bottom 33%) |
| **Unknown** | Missing data |

---

### Category Definitions

#### 🌟 Elite Tier

| Category | RAS | College | NFL | Description |
|----------|-----|---------|-----|-------------|
| **Superstar** | High | High | High | Elite in ALL three pillars. The complete package. Franchise cornerstone. |
| **Star** | High OR Med | High OR Med | High | High in 2 of 3 pillars including NFL. Proven starters. |
| **Proven Producer** | Any | High | High | Produces at every level regardless of athleticism. Safe bet. |

#### 🚀 Overachieving Tier

| Category | RAS | College | NFL | Description |
|----------|-----|---------|-----|-------------|
| **Overachiever** | Low/Med | High | High/Med | Exceeds athletic limitations through production. Draft value. |
| **Late Bloomer** | Any | Low/Med | High | Struggled in college but figured it out in NFL. Development win. |

#### 🎯 Potential Tier (Limited NFL Data)

| Category | RAS | College | NFL | Description |
|----------|-----|---------|-----|-------------|
| **Elite Prospect** | High | High | Unknown | Perfect profile, just needs NFL opportunity. Highest upside. |
| **Raw Athlete** | High | Low/Med/Unk | Unknown | Pure athlete, unproven football ability. High risk/reward. |
| **Sleeper** | Any | High | Unknown | College producer without NFL chance yet. Depth value. |

#### ⚠️ Risk Tier (Red Flags)

| Category | RAS | College | NFL | Description |
|----------|-----|---------|-----|-------------|
| **Underperformer** | High | High | Low/Med | Had everything but flopped. Major concerns. |
| **College Bust** | Any | High | Low | College stats didn't translate. Competition level issue? |
| **Athletic Bust** | High | Low | Low | Great measurables, can't play football. Avoid pure athletes. |

#### 🔨 Default

| Category | Criteria | Description |
|----------|----------|-------------|
| **Developmental** | Everything else | Average across board, incomplete data, or role players. |

---

### Category Decision Logic

```
START
  │
  ├─► All 3 High? ──────────────────────────► SUPERSTAR
  │
  ├─► NFL High + (RAS High OR College High)? ► STAR
  │
  ├─► College High + NFL High? ─────────────► PROVEN PRODUCER
  │
  ├─► RAS Low/Med + Production High? ───────► OVERACHIEVER
  │
  ├─► College High + NFL Low? ──────────────► COLLEGE BUST
  │
  ├─► RAS High + College Low + NFL Low? ────► ATHLETIC BUST
  │
  ├─► RAS High + College High + NFL Low/Med? ► UNDERPERFORMER
  │
  ├─► RAS High + College High + NFL Unknown? ► ELITE PROSPECT
  │
  ├─► RAS High + College Low + NFL Unknown? ─► RAW ATHLETE
  │
  ├─► College High + NFL Unknown? ──────────► SLEEPER
  │
  ├─► College Low/Med + NFL High? ──────────► LATE BLOOMER
  │
  └─► Else ─────────────────────────────────► DEVELOPMENTAL
```

---

## Output Columns

### Calculated Scores (0-100 scale)

| Column | Description |
|--------|-------------|
| `athletic_potential_score` | RAS percentile within position |
| `college_production_score` | Weighted college production percentile |
| `nfl_production_score` | Weighted NFL production percentile |
| `composite_score` | Average of available pillars |

### Rankings (1 = Best)

| Column | Description |
|--------|-------------|
| `athletic_potential_rank` | Rank by RAS within position |
| `college_production_rank` | Rank by college production within position |
| `nfl_production_rank` | Rank by NFL production within position |
| `composite_rank` | Overall rank within position |

### Calculated Rate Stats

| Column | Description |
|--------|-------------|
| `college_playmaking_per_season` | (INTs + PBUs) / seasons played |
| `college_defense_total_tackles_per_season` | Tackles / seasons played |
| `yards_allowed_per_coverage_snap` | Coverage yards allowed / coverage snaps |
| `playmaking_per_100_snaps` | (INTs + PBUs) / snaps × 100 |
| `tackles_per_100_snaps` | Tackles / snaps × 100 |

### Flags

| Column | Description |
|--------|-------------|
| `ras_available` | True if RAS data exists |
| `college_stats_complete` | True if 2+ college stats available |
| `nfl_sample_sufficient` | True if 100+ NFL snaps |
| `player_category` | Assigned category label |

---

## Interpretation Guide

### For 2026 Draft Scouting

| Category | Action |
|----------|--------|
| **Superstar / Star** | Target in early rounds |
| **Proven Producer** | Safe pick, reliable starter |
| **Elite Prospect** | High ceiling if they get opportunity |
| **Overachiever** | Value pick, often overdrafted |
| **Late Bloomer** | Development success, look for similar traits |
| **Underperformer** | Investigate why (injury? scheme? effort?) |
| **College Bust** | Check competition level, conference strength |
| **Athletic Bust** | Avoid reaching for combine warriors |

### Key Questions This Framework Answers

1. **Does RAS predict NFL success?**
   - Compare Overachievers (low RAS, high production) vs Athletic Busts (high RAS, low production)

2. **Does college production translate?**
   - Compare Proven Producers vs College Busts

3. **What's the minimum RAS for success?**
   - Analyze RAS distribution of high NFL producers

4. **Are there market inefficiencies?**
   - Overachievers are often drafted later than their production suggests

---

## Usage Example

```python
# Load data
import dataiku
players_df = dataiku.Dataset("players_def_secondary_RAS").get_dataframe()

# Run analysis
results_df = analyze(players_df)

# Find elite prospects for 2026
elite = results_df[results_df['player_category'].isin(['Superstar', 'Star', 'Elite Prospect'])]

# Find value picks (overachievers)
value = results_df[results_df['player_category'] == 'Overachiever']

# Avoid bust risks
avoid = results_df[results_df['player_category'].isin(['Athletic Bust', 'College Bust'])]

# Export
output = dataiku.Dataset("secondary_ranks_new")
output.write_with_schema(results_df)
```

---

## Limitations & Considerations

1. **Sample Size:** NFL rookie stats may be limited for players with few snaps
2. **Scheme Fit:** Production can be affected by defensive scheme
3. **Injury:** Does not account for injuries affecting stats
4. **Competition Level:** College stats don't account for conference strength
5. **Role:** Some players may have limited stats due to depth chart position, not ability

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025 | Initial release with 3-pillar system |
| 1.1 | 2025 | Added RAS as primary athletic metric |
| 1.2 | 2025 | Expanded player categories to include college production |

---

## Contact

For questions about this ranking methodology, contact the Analytics team.
