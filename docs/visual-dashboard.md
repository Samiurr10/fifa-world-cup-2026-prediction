# Visual Dashboard

The project includes a generated static dashboard app for team comparison, player search, player ratings, predictions, and validation.

Default output:

```text
site/index.html
```

Serve the repository root and open this file in a browser. The dashboard loads JSON from its generated asset folder, so an HTTP server is recommended.

## Generate The Dashboard

```bash
make official-dashboard
```

Or run the CLI directly:

```bash
PYTHONPATH=src python3 -m fifa_analysis.cli dashboard \
  --roster data/official/fifa_squads_2026.csv \
  --output site/index.html
```

The official dashboard writes:

- `site/index.html`
- `site/index-assets/dashboard.css`
- `site/index-assets/dashboard.js`
- `site/index-assets/app-data.json`

The sample dashboard is separate:

```bash
make sample-dashboard
```

It writes `site/sample.html` and `site/sample-assets/*`.

## Dashboard Sections

The dashboard includes:

- Team A and Team B selectors for comparing any teams loaded in the dataset.
- Team profile cards with roster size, caps, international goals, age, height, role mix, and rating status.
- Full roster tables for both selected teams.
- Searchable player database across every loaded player and team.
- Role filters for narrowing ratings by tactical profile.
- Player A and Player B selectors for side-by-side player comparison.
- KPI cards for loaded players, teams, caps, goals, rated players, top scorers, and most capped players.
- Match prediction panel with pending-state guidance until real team/player stats are imported.
- Advanced player metrics table for attack, progression, security, disruption, two-way value, usage, and xG efficiency.
- Rating validation cards with MAE, correlation, and within-half-point rate.
- Backtest cards with exact-score top-3 rate, outcome accuracy, log loss, and calibration buckets.
- Experience and scoring leaderboards.
- Data coverage cards explaining what is official, imported, pending, or unavailable.

## Design Rules

- The dashboard is generated from real CSV/JSON outputs.
- It does not invent missing player stats.
- The default dashboard uses official FIFA squad data and marks match ratings as pending until API-Football player stats are imported.
- The synthetic sample dashboard is isolated at `site/sample.html`.
- It escapes dynamic values before rendering.
- It is responsive for desktop and mobile widths.
- It uses generated CSS, vanilla JavaScript, and JSON assets, so it works without a frontend build step.
