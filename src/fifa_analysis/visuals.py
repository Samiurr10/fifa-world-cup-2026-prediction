"""Dashboard app generation for World Cup roster, ratings, and prediction analysis."""

from __future__ import annotations

import csv
import html
import json
from pathlib import Path
from typing import Any


def read_csv(path: str | Path) -> list[dict[str, str]]:
    file_path = Path(path)
    if not file_path.exists():
        return []
    with file_path.open(encoding="utf-8", newline="") as csv_file:
        return list(csv.DictReader(csv_file))


def read_json(path: str | Path) -> dict[str, Any]:
    file_path = Path(path)
    if not file_path.exists():
        return {}
    with file_path.open(encoding="utf-8") as json_file:
        return json.load(json_file)


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def write_json(path: str | Path, data: object) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def dashboard_data(
    *,
    overall_rows: list[dict[str, str]],
    game_rows: list[dict[str, str]],
    advanced_rows: list[dict[str, str]],
    team_rows: list[dict[str, str]],
    prediction: dict[str, Any],
    validation: dict[str, Any],
    backtest: dict[str, Any],
    roster_rows: list[dict[str, str]] | None = None,
    tournament_stats_rows: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return {
        "overall": overall_rows,
        "games": game_rows,
        "advanced": advanced_rows,
        "roster": roster_rows or [],
        "tournamentStats": tournament_stats_rows or [],
        "teamStats": team_rows,
        "prediction": prediction,
        "validation": validation,
        "backtest": backtest,
    }


def render_dashboard(
    title: str = "FIFA World Cup 2026 Intelligence Dashboard",
    asset_dir_name: str = "index-assets",
) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <link rel="icon" href="data:,">
  <link rel="stylesheet" href="{esc(asset_dir_name)}/dashboard.css">
</head>
<body>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand-block">
        <span class="brand-mark">26</span>
        <div>
          <strong>WC26 Intelligence</strong>
          <small>official squads · ratings · prediction lab</small>
        </div>
      </div>
      <nav class="nav-list" aria-label="Dashboard sections">
        <button class="nav-item active" data-view="overview">Overview</button>
        <button class="nav-item" data-view="teams">Teams</button>
        <button class="nav-item" data-view="players">Players</button>
        <button class="nav-item" data-view="compare">Compare</button>
        <button class="nav-item" data-view="predictions">Predictions</button>
        <button class="nav-item" data-view="data">Data Quality</button>
      </nav>
      <div class="side-panel">
        <label>
          Search
          <input id="globalSearch" type="search" placeholder="Player, club, team">
        </label>
        <label>
          Team
          <select id="teamFilter"></select>
        </label>
        <label>
          Role
          <select id="roleFilter"></select>
        </label>
        <label>
          Sort Players
          <select id="sortMode">
            <option value="roster_index">Roster index</option>
            <option value="wc_goals">World Cup goals</option>
            <option value="wc_goal_assists">World Cup G+A</option>
            <option value="career_goals">Career int'l goals</option>
            <option value="caps">Caps</option>
            <option value="rating">Model rating</option>
            <option value="age">Age</option>
            <option value="height">Height</option>
          </select>
        </label>
      </div>
    </aside>

    <main class="workspace">
      <header class="topbar">
        <div>
          <p class="eyebrow">World Cup 2026 Analysis</p>
          <h1>{esc(title)}</h1>
        </div>
        <div class="status-stack">
          <span id="dataModeBadge" class="badge"></span>
          <span id="coverageBadge" class="badge muted"></span>
        </div>
      </header>

      <section id="notice" class="notice"></section>
      <section id="kpis" class="kpi-grid"></section>

      <section class="view active" id="view-overview">
        <div class="dashboard-grid">
          <article class="panel wide">
            <div class="panel-head">
              <div>
                <p class="eyebrow">Roster Strength</p>
                <h2>Team Experience Map</h2>
              </div>
              <select id="teamMetricMode">
                <option value="caps">Average caps</option>
                <option value="wc_goals">World Cup goals</option>
                <option value="career_goals">Career int'l goals</option>
                <option value="age">Average age</option>
                <option value="height">Average height</option>
              </select>
            </div>
            <div id="teamBars" class="bar-list"></div>
          </article>
          <article class="panel">
            <div class="panel-head">
              <div>
                <p class="eyebrow">Position Mix</p>
                <h2>Squad Shape</h2>
              </div>
            </div>
            <div id="roleDonut" class="donut-wrap"></div>
          </article>
          <article class="panel">
            <div class="panel-head">
              <div>
                <p class="eyebrow">Top Players</p>
                <h2>Experience Leaders</h2>
              </div>
            </div>
            <div id="leaderList" class="leader-list"></div>
          </article>
        </div>
      </section>

      <section class="view" id="view-teams">
        <div class="compare-toolbar">
          <label>Team A<select id="teamA"></select></label>
          <label>Team B<select id="teamB"></select></label>
        </div>
        <div id="teamCompare" class="team-compare-grid"></div>
      </section>

      <section class="view" id="view-players">
        <article class="panel">
          <div class="panel-head">
            <div>
              <p class="eyebrow">Player Search</p>
              <h2>All Players</h2>
            </div>
            <span id="playerCount" class="badge"></span>
          </div>
          <div id="playerCards" class="player-card-grid"></div>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Player</th><th>Team</th><th>Role</th><th>Club</th><th>Age</th>
                  <th>Caps</th><th>2026 Apps</th><th>2026 Min</th><th>WC G</th><th>WC A</th>
                  <th>xG</th><th>Shots</th><th>Carries</th><th>Prog Carries</th><th>Int</th><th>Tackles</th>
                  <th>Career G</th><th>Rating</th><th>Status</th>
                </tr>
              </thead>
              <tbody id="playerTable"></tbody>
            </table>
          </div>
        </article>
      </section>

      <section class="view" id="view-compare">
        <div class="compare-toolbar">
          <label>Player A<select id="playerA"></select></label>
          <label>Player B<select id="playerB"></select></label>
        </div>
        <div id="playerCompare" class="player-compare-grid"></div>
      </section>

      <section class="view" id="view-predictions">
        <div id="predictionPanel" class="prediction-layout"></div>
      </section>

      <section class="view" id="view-data">
        <div class="dashboard-grid">
          <article class="panel wide">
            <p class="eyebrow">Data Coverage</p>
            <h2>What Is Real Right Now</h2>
            <div id="coveragePanel" class="coverage-grid"></div>
          </article>
          <article class="panel">
            <p class="eyebrow">Validation</p>
            <h2>Model Checks</h2>
            <div id="validationPanel" class="metric-stack"></div>
          </article>
        </div>
      </section>
    </main>
  </div>
  <script src="{esc(asset_dir_name)}/dashboard.js"></script>
</body>
</html>
"""


def dashboard_css() -> str:
    return r"""
:root {
  --bg: #eef2ef;
  --panel: #ffffff;
  --panel-soft: #f7faf8;
  --ink: #14201b;
  --muted: #64746e;
  --line: #d7e0db;
  --green: #0a7c55;
  --blue: #255fa7;
  --gold: #a87512;
  --red: #a33b34;
  --purple: #6750a4;
  --shadow: 0 18px 44px rgba(20, 32, 27, .09);
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background:
    linear-gradient(135deg, rgba(10,124,85,.09), transparent 28%),
    linear-gradient(315deg, rgba(37,95,167,.08), transparent 26%),
    var(--bg);
  color: var(--ink);
  font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
button, input, select { font: inherit; }
.app-shell { display: grid; grid-template-columns: 306px minmax(0, 1fr); min-height: 100vh; }
.sidebar {
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
  padding: 22px 18px;
  background: #111f1a;
  color: #ecf6f0;
}
.brand-block { display: flex; gap: 12px; align-items: center; padding-bottom: 20px; border-bottom: 1px solid rgba(255,255,255,.14); }
.brand-mark {
  display: grid;
  place-items: center;
  width: 46px;
  height: 46px;
  border-radius: 8px;
  background: #e5fff1;
  color: #0a7c55;
  font-weight: 950;
  font-size: 20px;
}
.brand-block strong { display: block; font-size: 18px; }
.brand-block small { color: #b9cbc3; }
.nav-list { display: grid; gap: 8px; margin: 22px 0; }
.nav-item {
  width: 100%;
  border: 1px solid rgba(255,255,255,.13);
  background: transparent;
  color: #e8f5ee;
  border-radius: 8px;
  padding: 11px 12px;
  text-align: left;
  cursor: pointer;
  font-weight: 850;
}
.nav-item.active, .nav-item:hover { background: #e8f5ee; color: #0f261d; }
.side-panel {
  display: grid;
  gap: 14px;
  padding: 16px;
  border-radius: 8px;
  background: rgba(255,255,255,.06);
}
label { display: grid; gap: 6px; color: #cfe0d8; font-size: 12px; font-weight: 900; text-transform: uppercase; letter-spacing: .04em; }
input, select {
  min-height: 40px;
  width: 100%;
  border: 1px solid rgba(255,255,255,.18);
  border-radius: 8px;
  padding: 8px 10px;
  background: #21352c;
  color: #ffffff;
}
.workspace { padding: 26px clamp(18px, 3vw, 42px) 46px; max-width: 1760px; width: 100%; }
.topbar { display: flex; justify-content: space-between; align-items: flex-start; gap: 22px; margin-bottom: 16px; }
.eyebrow {
  margin: 0 0 7px;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: .08em;
  font-size: 12px;
  font-weight: 950;
}
h1, h2, h3, p { margin-top: 0; }
h1 { margin-bottom: 0; font-size: clamp(34px, 4.2vw, 62px); line-height: 1; letter-spacing: 0; }
h2 { margin-bottom: 12px; font-size: 22px; }
.status-stack { display: flex; flex-wrap: wrap; gap: 8px; justify-content: flex-end; }
.badge {
  display: inline-flex;
  align-items: center;
  min-height: 30px;
  border-radius: 8px;
  padding: 6px 10px;
  background: #e8f5ee;
  color: var(--green);
  font-weight: 950;
  font-size: 13px;
}
.badge.muted { color: var(--muted); background: #eef3f0; }
.notice, .panel, .kpi-card, .team-card, .player-card, .compare-card {
  background: rgba(255,255,255,.94);
  border: 1px solid var(--line);
  border-radius: 8px;
  box-shadow: var(--shadow);
}
.notice { padding: 14px 16px; color: #654600; background: #fff8e6; border-color: #edc775; line-height: 1.45; }
.notice.verified { color: #145d40; background: #eef9f3; border-color: #a9d9c2; }
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(150px, 1fr));
  gap: 14px;
  margin: 16px 0;
}
.kpi-card { padding: 16px; min-height: 112px; }
.kpi-card span { display: block; color: var(--muted); font-size: 12px; text-transform: uppercase; font-weight: 950; }
.kpi-card strong { display: block; font-size: 30px; margin: 8px 0 4px; }
.kpi-card small { color: var(--muted); }
.view { display: none; }
.view.active { display: block; }
.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(330px, .75fr);
  gap: 16px;
}
.panel { padding: clamp(18px, 2vw, 26px); min-width: 0; }
.panel.wide { min-height: 0; }
.panel-head, .compare-toolbar {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  align-items: flex-start;
  margin-bottom: 14px;
}
.panel-head select, .compare-toolbar select { background: #fff; color: var(--ink); border-color: var(--line); min-width: 220px; }
.bar-list { display: grid; gap: 10px; }
.metric-row { display: grid; grid-template-columns: minmax(160px, 1fr) minmax(200px, 3fr) 78px; gap: 12px; align-items: center; }
.track { height: 12px; background: #e7eee9; border-radius: 99px; overflow: hidden; }
.track i { display: block; height: 100%; background: linear-gradient(90deg, var(--green), var(--blue)); border-radius: inherit; }
.leader-list, .metric-stack { display: grid; gap: 10px; }
.leader-info { display: grid; gap: 2px; min-width: 0; }
.leader-row, .coverage-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
  padding: 12px 0;
  border-top: 1px solid var(--line);
}
.leader-row:first-child { border-top: 0; }
.muted { color: var(--muted); }
.team-compare-grid, .player-compare-grid, .prediction-layout {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}
.team-card, .player-card, .compare-card { padding: 18px; min-width: 0; }
.team-score, .rating-score { font-size: 44px; color: var(--green); font-weight: 950; line-height: 1; }
.team-meta { color: var(--muted); margin-bottom: 14px; }
.mini-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; margin: 14px 0; }
.mini-stat { background: var(--panel-soft); border: 1px solid var(--line); border-radius: 8px; padding: 10px; }
.mini-stat span { display: block; color: var(--muted); font-size: 11px; text-transform: uppercase; font-weight: 950; }
.mini-stat strong { display: block; font-size: 22px; margin-top: 4px; }
.role-stack { display: grid; gap: 8px; margin-top: 12px; }
.roster-list { display: grid; gap: 8px; max-height: 460px; overflow: auto; padding-right: 4px; }
.roster-row { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 10px; padding: 10px 0; border-top: 1px solid var(--line); }
.roster-row strong, .leader-row strong { overflow-wrap: anywhere; }
.player-card-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 14px; margin-bottom: 16px; }
.player-card { display: grid; gap: 14px; }
.player-head { display: flex; justify-content: space-between; gap: 12px; }
.player-head h3 { margin-bottom: 4px; overflow-wrap: anywhere; }
.player-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.tag { border-radius: 7px; padding: 5px 8px; background: #eef3f0; color: var(--muted); font-size: 12px; font-weight: 900; }
.tag.good { color: var(--green); background: #e8f5ee; }
.tag.warn { color: var(--gold); background: #fff4d8; }
.table-wrap { overflow: auto; border: 1px solid var(--line); border-radius: 8px; background: #fff; }
table { width: 100%; min-width: 1080px; border-collapse: collapse; }
th, td { padding: 12px 13px; border-bottom: 1px solid var(--line); text-align: left; vertical-align: top; }
th { position: sticky; top: 0; background: #f8fbf9; color: var(--muted); text-transform: uppercase; font-size: 12px; letter-spacing: .05em; z-index: 1; }
td span { display: block; color: var(--muted); font-size: 12px; margin-top: 3px; }
tbody tr:hover { background: #f8fbf9; }
.comparison-bars { display: grid; gap: 10px; margin-top: 14px; }
.compare-line { display: grid; grid-template-columns: 72px 1fr 72px; gap: 10px; align-items: center; }
.compare-line .track:first-of-type i { margin-left: auto; background: var(--blue); }
.coverage-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.coverage-card { border: 1px solid var(--line); border-radius: 8px; padding: 14px; background: var(--panel-soft); }
.empty-state {
  border: 1px dashed #bdcbc3;
  border-radius: 8px;
  padding: 22px;
  color: var(--muted);
  background: #f8fbf9;
  line-height: 1.5;
}
svg.responsive-svg { width: 100%; height: auto; display: block; }
@media (max-width: 1180px) {
  .app-shell { grid-template-columns: 1fr; }
  .sidebar { position: relative; height: auto; }
  .kpi-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .dashboard-grid, .team-compare-grid, .player-compare-grid, .prediction-layout { grid-template-columns: 1fr; }
}
@media (max-width: 720px) {
  .workspace { padding: 18px 12px 30px; }
  .topbar, .panel-head, .compare-toolbar { display: grid; }
  .kpi-grid, .mini-grid, .coverage-grid { grid-template-columns: 1fr 1fr; }
  h1 { font-size: 34px; }
}
"""


def dashboard_js() -> str:
    return r"""
const state = {
  data: null,
  players: [],
  teams: [],
  activeView: 'overview',
};

const $ = (id) => document.getElementById(id);
const num = (value) => Number.parseFloat(value || 0) || 0;
const fmt = (value, digits = 1) => num(value).toFixed(digits);
const esc = (value) => String(value ?? '').replace(/[&<>"']/g, (m) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]));
const average = (rows, getter) => rows.length ? rows.reduce((total, row) => total + getter(row), 0) / rows.length : 0;
const normalizeKey = (value) => String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '');
const normalizeTeamKey = (value) => {
  const key = normalizeKey(value);
  const aliases = {
    drcongo: 'congodr',
    drc: 'congodr',
    bosniaherzegovina: 'bosniaandherzegovina',
    bosniaandherzegovina: 'bosniaandherzegovina',
    bosnia: 'bosniaandherzegovina',
    bosniahz: 'bosniaandherzegovina',
    ivorycoast: 'cotedivoire',
    cotedivoire: 'cotedivoire',
    capeverde: 'caboverde',
    caboverde: 'caboverde',
    iran: 'iriran',
    unitedstates: 'usa',
    unitedstatesofamerica: 'usa',
  };
  return aliases[key] || key;
};

function parseDate(value) {
  if (!value) return null;
  const parts = String(value).split('/');
  if (parts.length !== 3) return null;
  return new Date(Number(parts[2]), Number(parts[1]) - 1, Number(parts[0]));
}

function ageFromDob(value) {
  const dob = parseDate(value);
  if (!dob) return 0;
  const ref = new Date(2026, 5, 11);
  let age = ref.getFullYear() - dob.getFullYear();
  const monthDiff = ref.getMonth() - dob.getMonth();
  if (monthDiff < 0 || (monthDiff === 0 && ref.getDate() < dob.getDate())) age -= 1;
  return age;
}

function roleFromPosition(position) {
  const text = String(position || '').toUpperCase();
  if (text === 'GK' || text === 'GOALKEEPER') return 'Goalkeeper';
  if (text === 'DF' || text === 'DEFENDER') return 'Defender';
  if (text === 'MF' || text === 'MIDFIELDER') return 'Midfielder';
  if (text === 'FW' || text === 'ATTACKER' || text === 'FORWARD') return 'Forward';
  return position || 'Unknown';
}

function displayName(row) {
  const shirt = titleCase(row.name_on_shirt || '');
  const first = titleCase(String(row.first_names || '').split(/[\s-]+/)[0] || '');
  if (shirt && first && !shirt.toLowerCase().startsWith(first.toLowerCase())) {
    return `${first} ${shirt}`.replace(/\s+/g, ' ').trim();
  }
  if (shirt) return shirt;
  if (row.first_names || row.last_names) {
    return titleCase(`${row.first_names || ''} ${row.last_names || ''}`.replace(/\s+/g, ' ').trim());
  }
  return row.player_name || row.player || '';
}

function reversedName(value) {
  const parts = String(value || '').trim().split(/\s+/);
  if (parts.length < 2) return '';
  return titleCase(`${parts.slice(1).join(' ')} ${parts[0]}`);
}

function matchNames(row, player) {
  const first = titleCase(String(row.first_names || '').split(/[\s-]+/)[0] || '');
  return [
    player,
    titleCase(row.player_name || ''),
    reversedName(row.player_name || ''),
    titleCase(`${row.first_names || ''} ${row.last_names || ''}`.replace(/\s+/g, ' ').trim()),
    titleCase(`${first} ${row.last_names || ''}`.replace(/\s+/g, ' ').trim()),
    titleCase(`${first} ${row.name_on_shirt || ''}`.replace(/\s+/g, ' ').trim()),
    titleCase(row.name_on_shirt || ''),
  ].filter(Boolean);
}

function titleCase(value) {
  return String(value || '').toLowerCase().replace(/\b[\p{L}'][\p{L}']*/gu, (word) => word.charAt(0).toUpperCase() + word.slice(1));
}

function playerNameMatches(wantedName, existing) {
  const wanted = normalizeKey(wantedName);
  const wantedTokens = String(wantedName || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().match(/[a-z0-9]+/g) || [];
  const candidates = existing.matchNames || [existing.player];
  return candidates.some((candidate) => {
    const candidateKey = normalizeKey(candidate);
    if (candidateKey === wanted) return true;
    const candidateTokens = String(candidate || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().match(/[a-z0-9]+/g) || [];
    if (wantedTokens.length === 1) return candidateTokens.includes(wantedTokens[0]);
    return wantedTokens.length > 1 && wantedTokens.every((token) => candidateTokens.includes(token));
  });
}

function ratingValue(player) {
  return player.weighted_rating === undefined || player.weighted_rating === '' ? null : num(player.weighted_rating);
}

function ratingText(player) {
  const rating = ratingValue(player);
  return rating === null ? 'Pending' : rating.toFixed(2);
}

function hasStat(player, key) {
  return player[key] !== undefined && player[key] !== '';
}

function statText(player, key, digits = null) {
  if (!hasStat(player, key)) return '—';
  const value = num(player[key]);
  return digits === null ? String(value) : value.toFixed(digits);
}

function buildModel(data) {
  const merged = new Map();
  data.roster.forEach((row) => {
    const player = displayName(row);
    const key = `${player}|||${row.team}`;
    merged.set(key, {
      player,
      team: row.team,
      teamCode: row.team_code || '',
      role: roleFromPosition(row.position || row.role_group),
      rawPosition: row.position || '',
      club: row.club || '',
      caps: num(row.caps),
      goals: num(row.international_goals),
      height: num(row.height_cm),
      age: ageFromDob(row.dob),
      dob: row.dob || '',
      squadNumber: row.squad_number || '',
      source: row.source || '',
      matchNames: matchNames(row, player),
      status: 'no 2026 minutes',
    });
  });
  data.overall.forEach((row) => {
    const key = `${row.player}|||${row.team}`;
    merged.set(key, {
      ...(merged.get(key) || {}),
      player: row.player,
      team: row.team,
      role: row.role_group || merged.get(key)?.role || 'Unknown',
      matches: num(row.matches),
      minutes: num(row.minutes),
      weighted_rating: row.weighted_rating,
      best_rating: row.best_rating,
      confidence: row.confidence || 'rated',
      status: row.confidence || 'rated',
    });
  });
  data.tournamentStats.forEach((row) => {
    const wantedTeam = normalizeTeamKey(row.team);
    let key = [...merged.keys()].find((candidate) => {
      const existing = merged.get(candidate);
      return playerNameMatches(row.player, existing) && normalizeTeamKey(existing.team) === wantedTeam;
    });
    if (!key) {
      return;
    }
    const existing = merged.get(key);
    const fields = [
      ['wcMatches', 'wc_matches'],
      ['wcMinutes', 'wc_minutes'],
      ['wcGoals', 'wc_goals'],
      ['wcAssists', 'wc_assists'],
      ['wcGoalAssists', 'wc_goal_assists'],
      ['wcXg', 'wc_xg'],
      ['wcXa', 'wc_xa'],
      ['wcShots', 'wc_shots'],
      ['wcShotsOnTarget', 'wc_shots_on_target'],
      ['wcChancesCreated', 'wc_chances_created'],
      ['wcPasses', 'wc_passes'],
      ['wcSuccessfulPasses', 'wc_successful_passes'],
      ['wcPassCompletion', 'wc_pass_completion'],
      ['wcCarries', 'wc_carries'],
      ['wcProgressiveCarries', 'wc_progressive_carries'],
      ['wcTackles', 'wc_tackles'],
      ['wcInterceptions', 'wc_interceptions'],
      ['wcRecoveries', 'wc_recoveries'],
      ['wcBlocks', 'wc_blocks'],
      ['wcClearances', 'wc_clearances'],
      ['wcAerialDuels', 'wc_aerial_duels'],
      ['wcAerialDuelsWon', 'wc_aerial_duels_won'],
      ['wcSaves', 'wc_saves'],
      ['wcSavePct', 'wc_save_pct'],
      ['wcGoalsPrevented', 'wc_goals_prevented'],
      ['wcGoalsConceded', 'wc_goals_conceded'],
      ['wcCleanSheets', 'wc_clean_sheets'],
      ['wcSavesPerGame', 'wc_saves_per_game'],
      ['wcGoalsConcededPerGame', 'wc_goals_conceded_per_game'],
    ];
    fields.forEach(([target, source]) => {
      const value = num(row[source]);
      if (value || existing[target] === undefined) existing[target] = Math.max(num(existing[target]), value);
    });
    existing.hasTournamentStats = true;
    existing.tournamentSource = row.source || 'tournament stats';
    existing.tournamentLastUpdated = row.last_updated || row.accessed_date || '';
    existing.status = '2026 stats loaded';
    if (row.position && (!existing.role || existing.role === 'Unknown')) existing.role = row.position;
  });
  state.players = [...merged.values()].filter((player) => player.player && player.team);
  state.teams = [...new Set(state.players.map((player) => player.team))].sort();
}

function teamProfile(team) {
  const roster = state.players.filter((player) => player.team === team);
  const rated = roster.filter((player) => ratingValue(player) !== null);
  const roleCounts = ['Goalkeeper', 'Defender', 'Midfielder', 'Forward'].map((role) => ({
    role,
    count: roster.filter((player) => player.role === role).length,
  }));
  return {
    team,
    roster,
    rated,
    players: roster.length,
    caps: roster.reduce((total, player) => total + player.caps, 0),
    careerGoals: roster.reduce((total, player) => total + player.goals, 0),
    wcGoals: roster.reduce((total, player) => total + num(player.wcGoals), 0),
    avgCaps: average(roster, (player) => player.caps),
    avgAge: average(roster, (player) => player.age),
    avgHeight: average(roster, (player) => player.height),
    rating: average(rated, (player) => ratingValue(player) || 0),
    roleCounts,
    topCaps: [...roster].sort((a, b) => b.caps - a.caps).slice(0, 5),
    topGoals: [...roster].sort((a, b) => num(b.wcGoals) - num(a.wcGoals)).slice(0, 5),
  };
}

function filteredPlayers() {
  const search = $('globalSearch').value.trim().toLowerCase();
  const team = $('teamFilter').value;
  const role = $('roleFilter').value;
  const sortMode = $('sortMode').value;
  const rows = state.players.filter((player) => {
    const haystack = `${player.player} ${player.team} ${player.club} ${player.role}`.toLowerCase();
    return (!search || haystack.includes(search))
      && (team === 'All teams' || player.team === team)
      && (role === 'All roles' || player.role === role);
  });
  const sorters = {
    roster_index: (a, b) => a.team.localeCompare(b.team) || num(a.squadNumber) - num(b.squadNumber),
    caps: (a, b) => b.caps - a.caps,
    wc_goals: (a, b) => num(b.wcGoals) - num(a.wcGoals),
    wc_goal_assists: (a, b) => num(b.wcGoalAssists) - num(a.wcGoalAssists),
    career_goals: (a, b) => b.goals - a.goals,
    rating: (a, b) => (ratingValue(b) ?? -1) - (ratingValue(a) ?? -1),
    age: (a, b) => b.age - a.age,
    height: (a, b) => b.height - a.height,
  };
  return rows.sort(sorters[sortMode] || sorters.roster_index);
}

function barRow(label, value, max, detail = '') {
  const width = max ? Math.max(2, Math.min(100, value / max * 100)) : 2;
  return `<div class="metric-row"><strong>${esc(label)}</strong><div class="track"><i style="width:${width}%"></i></div><span>${esc(detail || fmt(value))}</span></div>`;
}

function miniStat(label, value) {
  return `<div class="mini-stat"><span>${esc(label)}</span><strong>${esc(value)}</strong></div>`;
}

function playerLine(player, mode = 'caps') {
  const value = mode === 'wc_goals' ? num(player.wcGoals) : player.caps;
  const label = mode === 'wc_goals' ? 'WC goals' : 'caps';
  return `<div class="leader-row"><div class="leader-info"><strong>${esc(player.player)}</strong><span class="muted">${esc(player.team)} · ${esc(player.club || 'club n/a')}</span></div><strong>${value} ${label}</strong></div>`;
}

function renderNotice() {
  const demo = state.players.some((player) => player.player.startsWith('Demo '));
  const hasRatings = state.players.some((player) => ratingValue(player) !== null);
  $('notice').className = `notice ${demo ? '' : 'verified'}`;
  if (demo) {
    $('notice').innerHTML = '<strong>Demo mode.</strong> This dashboard is using synthetic sample ratings. Do not interpret them as real World Cup data.';
  } else if (!hasRatings) {
    const tournamentRows = state.players.filter((player) => player.hasTournamentStats).length;
    $('notice').innerHTML = `<strong>Official roster + 2026 stats mode.</strong> The 48 squads and 1,248 players come from the FIFA squad list. ${tournamentRows} players have current World Cup 2026 aggregate stats from The Analyst/Opta. API-Football is only needed later for fixture-level ratings, lineups, and per-game validation.`;
  } else {
    $('notice').innerHTML = '<strong>Rated data mode.</strong> Ratings are generated from imported player-match statistics. Interpret gaps according to data coverage.';
  }
  $('dataModeBadge').textContent = demo ? 'Demo data' : hasRatings ? 'Rated data' : 'Official + 2026 stats';
  $('coverageBadge').textContent = `${state.teams.length} teams · ${state.players.length} players`;
}

function renderKpis() {
  const hasRatings = state.players.filter((player) => ratingValue(player) !== null).length;
  const totalCaps = state.players.reduce((total, player) => total + player.caps, 0);
  const totalCareerGoals = state.players.reduce((total, player) => total + player.goals, 0);
  const totalWcGoals = state.players.reduce((total, player) => total + num(player.wcGoals), 0);
  const topScorer = [...state.players].sort((a, b) => num(b.wcGoals) - num(a.wcGoals) || num(b.wcGoalAssists) - num(a.wcGoalAssists))[0] || {};
  const mostCapped = [...state.players].sort((a, b) => b.caps - a.caps)[0] || {};
  const cards = [
    ['Teams', state.teams.length, 'official squads loaded'],
    ['Players', state.players.length, 'searchable squad players'],
    ['2026 Stat Rows', state.players.filter((player) => player.hasTournamentStats).length, 'The Analyst/Opta tournament players'],
    ['Total Caps', totalCaps.toLocaleString(), 'international experience'],
    ['WC Goals', totalWcGoals.toLocaleString(), 'tracked tournament goals'],
    ['Career Goals', totalCareerGoals.toLocaleString(), 'squad international goals'],
    ['Most Capped', mostCapped.player || 'n/a', `${mostCapped.team || ''} · ${mostCapped.caps || 0} caps`],
    ['Top WC Scorer', topScorer.player || 'n/a', `${topScorer.team || ''} · ${num(topScorer.wcGoals)} WC goals`],
  ];
  $('kpis').innerHTML = cards.map(([label, value, detail]) => `<article class="kpi-card"><span>${esc(label)}</span><strong>${esc(value)}</strong><small>${esc(detail)}</small></article>`).join('');
}

function renderControls() {
  const teamOptions = ['All teams', ...state.teams].map((team) => `<option>${esc(team)}</option>`).join('');
  $('teamFilter').innerHTML = teamOptions;
  $('teamA').innerHTML = state.teams.map((team) => `<option>${esc(team)}</option>`).join('');
  $('teamB').innerHTML = state.teams.map((team) => `<option>${esc(team)}</option>`).join('');
  if (state.teams[1]) $('teamB').value = state.teams[1];
  const roles = ['All roles', ...new Set(state.players.map((player) => player.role))].sort();
  $('roleFilter').innerHTML = roles.map((role) => `<option>${esc(role)}</option>`).join('');
  const playerOptions = state.players
    .slice()
    .sort((a, b) => b.caps - a.caps)
    .map((player) => `<option value="${esc(player.player)}|||${esc(player.team)}">${esc(player.player)} · ${esc(player.team)}</option>`)
    .join('');
  $('playerA').innerHTML = playerOptions;
  $('playerB').innerHTML = playerOptions;
  if (state.players[1]) $('playerB').selectedIndex = 1;
}

function renderTeamBars() {
  const mode = $('teamMetricMode').value;
  const profiles = state.teams.map(teamProfile);
  const getters = {
    caps: (profile) => profile.avgCaps,
    wc_goals: (profile) => profile.wcGoals,
    career_goals: (profile) => profile.careerGoals,
    age: (profile) => profile.avgAge,
    height: (profile) => profile.avgHeight,
  };
  const labels = {
    caps: (value) => `${fmt(value)} avg`,
    wc_goals: (value) => `${Math.round(value)} WC goals`,
    career_goals: (value) => `${Math.round(value)} career`,
    age: (value) => `${fmt(value)} yrs`,
    height: (value) => `${fmt(value)} cm`,
  };
  const rows = profiles
    .map((profile) => ({team: profile.team, value: getters[mode](profile)}))
    .sort((a, b) => b.value - a.value)
    .slice(0, 16);
  const max = Math.max(...rows.map((row) => row.value), 1);
  $('teamBars').innerHTML = rows.map((row) => barRow(row.team, row.value, max, labels[mode](row.value))).join('');
}

function renderRoleDonut() {
  const roles = ['Goalkeeper', 'Defender', 'Midfielder', 'Forward'];
  const counts = roles.map((role) => state.players.filter((player) => player.role === role).length);
  const total = counts.reduce((sum, value) => sum + value, 0) || 1;
  let offset = 25;
  const colors = ['#0a7c55', '#255fa7', '#a87512', '#6750a4'];
  const circles = counts.map((count, index) => {
    const length = count / total * 100;
    const circle = `<circle cx="70" cy="70" r="45" fill="none" stroke="${colors[index]}" stroke-width="18" stroke-dasharray="${length} ${100 - length}" stroke-dashoffset="${offset}" pathLength="100"></circle>`;
    offset -= length;
    return circle;
  }).join('');
  const legend = roles.map((role, index) => `<div class="leader-row"><span><i style="display:inline-block;width:10px;height:10px;background:${colors[index]};border-radius:2px;margin-right:7px"></i>${role}</span><strong>${counts[index]}</strong></div>`).join('');
  $('roleDonut').innerHTML = `<svg class="responsive-svg" viewBox="0 0 140 140" role="img" aria-label="Role distribution">${circles}<text x="70" y="68" text-anchor="middle" font-size="22" font-weight="900">${total}</text><text x="70" y="86" text-anchor="middle" font-size="11" fill="#64746e">players</text></svg>${legend}`;
}

function renderLeaders() {
  const rows = [...state.players].sort((a, b) => num(b.wcGoals) - num(a.wcGoals) || num(b.wcGoalAssists) - num(a.wcGoalAssists) || b.caps - a.caps).slice(0, 10);
  $('leaderList').innerHTML = rows.map((player) => playerLine(player, num(player.wcGoals) ? 'wc_goals' : 'caps')).join('');
}

function teamCard(profile, side) {
  const roleBars = profile.roleCounts.map(({role, count}) => barRow(role, count, 26, String(count))).join('');
  const roster = profile.roster
    .slice()
    .sort((a, b) => num(a.squadNumber) - num(b.squadNumber))
    .map((player) => `<div class="roster-row"><div><strong>${esc(player.squadNumber ? '#' + player.squadNumber + ' ' : '')}${esc(player.player)}</strong><span>${esc(player.role)} · ${esc(player.club || 'club n/a')}</span></div><strong>${ratingText(player)}</strong></div>`)
    .join('');
  return `<article class="team-card">
    <p class="eyebrow">${esc(side)}</p>
    <h2>${esc(profile.team)}</h2>
    <div class="team-score">${profile.rated.length ? fmt(profile.rating, 2) : 'Pending'}</div>
    <p class="team-meta">${profile.players} players · ${profile.caps.toLocaleString()} caps · ${profile.wcGoals.toLocaleString()} WC goals · ${profile.careerGoals.toLocaleString()} career int'l goals</p>
    <div class="mini-grid">
      ${miniStat('Avg Age', fmt(profile.avgAge))}
      ${miniStat('Avg Height', `${fmt(profile.avgHeight)} cm`)}
      ${miniStat('Avg Caps', fmt(profile.avgCaps))}
      ${miniStat('Rated', profile.rated.length)}
    </div>
    <h3>Squad shape</h3>
    <div class="role-stack">${roleBars}</div>
    <h3>Roster</h3>
    <div class="roster-list">${roster}</div>
  </article>`;
}

function renderTeamCompare() {
  const first = teamProfile($('teamA').value || state.teams[0]);
  const second = teamProfile($('teamB').value || state.teams[1] || state.teams[0]);
  $('teamCompare').innerHTML = teamCard(first, 'Team A') + teamCard(second, 'Team B');
}

function playerCard(player) {
  const rating = ratingValue(player);
  return `<article class="player-card">
    <div class="player-head">
      <div>
        <h3>${esc(player.player)}</h3>
        <div class="muted">${esc(player.team)} · ${esc(player.club || 'club n/a')}</div>
      </div>
      <strong class="rating-score">${rating === null ? 'Pending' : rating.toFixed(2)}</strong>
    </div>
    <div class="player-tags">
      <span class="tag good">${esc(player.role)}</span>
      <span class="tag">#${esc(player.squadNumber || 'n/a')}</span>
      <span class="tag">${esc(player.age || 'n/a')} yrs</span>
      <span class="tag">${esc(player.height || 'n/a')} cm</span>
    </div>
    <div class="mini-grid">
      ${miniStat('Caps', player.caps)}
      ${miniStat('2026 Apps', statText(player, 'wcMatches'))}
      ${miniStat('2026 Min', statText(player, 'wcMinutes'))}
      ${miniStat('WC Goals', statText(player, 'wcGoals'))}
      ${miniStat('WC Assists', statText(player, 'wcAssists'))}
      ${miniStat('xG', statText(player, 'wcXg', 2))}
      ${miniStat('Shots', statText(player, 'wcShots'))}
      ${miniStat('Carries', statText(player, 'wcCarries'))}
      ${miniStat('Prog Carries', statText(player, 'wcProgressiveCarries'))}
      ${miniStat('Interceptions', statText(player, 'wcInterceptions'))}
      ${miniStat('Tackles', statText(player, 'wcTackles'))}
      ${miniStat('Career G', player.goals)}
      ${miniStat('Status', player.status || 'pending')}
    </div>
  </article>`;
}

function renderPlayers() {
  const rows = filteredPlayers();
  $('playerCount').textContent = `${rows.length} shown`;
  $('playerCards').innerHTML = rows.slice(0, 12).map(playerCard).join('');
  $('playerTable').innerHTML = rows.map((player) => `<tr>
    <td><strong>${esc(player.player)}</strong><span>${esc(player.squadNumber ? '#' + player.squadNumber : '')}</span></td>
    <td>${esc(player.team)}</td>
    <td>${esc(player.role)}</td>
    <td>${esc(player.club || 'n/a')}</td>
    <td>${esc(player.age || 'n/a')}</td>
    <td>${player.caps}</td>
    <td>${statText(player, 'wcMatches')}</td>
    <td>${statText(player, 'wcMinutes')}</td>
    <td>${statText(player, 'wcGoals')}</td>
    <td>${statText(player, 'wcAssists')}</td>
    <td>${statText(player, 'wcXg', 2)}</td>
    <td>${statText(player, 'wcShots')}</td>
    <td>${statText(player, 'wcCarries')}</td>
    <td>${statText(player, 'wcProgressiveCarries')}</td>
    <td>${statText(player, 'wcInterceptions')}</td>
    <td>${statText(player, 'wcTackles')}</td>
    <td>${player.goals}</td>
    <td><strong>${ratingText(player)}</strong></td>
    <td><span class="tag ${player.hasTournamentStats ? 'good' : 'warn'}">${esc(player.status || 'pending')}</span></td>
  </tr>`).join('');
}

function selectedPlayer(id) {
  const [player, team] = ($(id).value || '').split('|||');
  return state.players.find((row) => row.player === player && row.team === team) || state.players[0] || {};
}

function compareMetric(label, a, b) {
  const max = Math.max(a, b, 1);
  return `<div class="compare-line"><strong>${fmt(a)}</strong><div class="track"><i style="width:${a / max * 100}%"></i></div><div class="track"><i style="width:${b / max * 100}%"></i></div><strong>${fmt(b)}</strong><span class="muted" style="grid-column:1 / -1;text-align:center">${esc(label)}</span></div>`;
}

function playerCompareCard(player, label) {
  return `<article class="compare-card">
    <p class="eyebrow">${esc(label)}</p>
    ${playerCard(player)}
  </article>`;
}

function renderPlayerCompare() {
  const a = selectedPlayer('playerA');
  const b = selectedPlayer('playerB');
  $('playerCompare').innerHTML = `${playerCompareCard(a, 'Player A')}${playerCompareCard(b, 'Player B')}<article class="panel" style="grid-column:1 / -1"><p class="eyebrow">Head To Head</p><h2>Profile Comparison</h2><div class="comparison-bars">${compareMetric('World Cup goals', num(a.wcGoals), num(b.wcGoals))}${compareMetric('World Cup assists', num(a.wcAssists), num(b.wcAssists))}${compareMetric('xG', num(a.wcXg), num(b.wcXg))}${compareMetric('Shots', num(a.wcShots), num(b.wcShots))}${compareMetric('Carries', num(a.wcCarries), num(b.wcCarries))}${compareMetric('Progressive carries', num(a.wcProgressiveCarries), num(b.wcProgressiveCarries))}${compareMetric('Interceptions', num(a.wcInterceptions), num(b.wcInterceptions))}${compareMetric('Tackles', num(a.wcTackles), num(b.wcTackles))}${compareMetric('Caps', a.caps, b.caps)}${compareMetric("Career int'l goals", a.goals, b.goals)}</div></article>`;
}

function renderPrediction() {
  const prediction = state.data.prediction || {};
  if (!prediction.home_team && !state.data.games.length) {
    $('predictionPanel').innerHTML = `<article class="panel"><p class="eyebrow">Prediction Lab</p><h2>Waiting For Fixture-Level Stats</h2><div class="empty-state">The dashboard now has aggregate World Cup 2026 player stats from The Analyst/Opta. Match predictions and per-game ratings still need fixture-level team/player rows. Run <code>make theanalyst-stats</code> to refresh aggregate stats, or use API-Football later when you want lineups and fixture-player ratings.</div></article>`;
    return;
  }
  const topScores = (prediction.top_scorelines || []).map((row) => barRow(row.score, num(row.probability), .2, `${fmt(num(row.probability) * 100)}%`)).join('');
  $('predictionPanel').innerHTML = `<article class="panel"><p class="eyebrow">Prediction Snapshot</p><h2>${esc(prediction.home_team || 'Team A')} vs ${esc(prediction.away_team || 'Team B')}</h2><div class="mini-grid">${miniStat('Home Win', `${fmt(num(prediction.home_win) * 100)}%`)}${miniStat('Draw', `${fmt(num(prediction.draw) * 100)}%`)}${miniStat('Away Win', `${fmt(num(prediction.away_win) * 100)}%`)}${miniStat('Confidence', prediction.confidence || 'unknown')}</div></article><article class="panel"><p class="eyebrow">Likely Scores</p><h2>Top Scorelines</h2>${topScores || '<div class="empty-state">No scoreline distribution available.</div>'}</article>`;
}

function renderCoverage() {
  const rated = state.players.filter((player) => ratingValue(player) !== null).length;
  const games = state.data.games.length;
  const advanced = state.data.advanced.length;
  const cards = [
    ['Official roster', `${state.players.length} players`, 'Loaded from FIFA squad list CSV'],
    ['World Cup 2026 player stats', `${state.data.tournamentStats.length} rows`, 'The Analyst/Opta aggregate player stats: goals, assists, xG, passing, carries, defending, goalkeeping'],
    ['Teams', `${state.teams.length} squads`, 'All selectable and searchable'],
    ['Player ratings', `${rated} players`, rated ? 'Imported stats are rated' : 'Pending API-Football fixture stats'],
    ['Player games', `${games} rows`, games ? 'Per-game stats available' : 'No real player-game rows imported yet'],
    ['Advanced metrics', `${advanced} rows`, advanced ? 'Role-fit metrics available' : 'Will unlock after stats import'],
    ['Predictions', state.data.prediction?.home_team ? 'Available' : 'Pending', 'Needs team match stats'],
  ];
  $('coveragePanel').innerHTML = cards.map(([label, value, detail]) => `<div class="coverage-card"><div><strong>${esc(label)}</strong><span class="muted">${esc(detail)}</span></div><strong>${esc(value)}</strong></div>`).join('');
  const validation = state.data.validation || {};
  const backtest = state.data.backtest || {};
  $('validationPanel').innerHTML = [
    ['Rating MAE', validation.mae ?? 'pending'],
    ['Correlation', validation.correlation ?? 'pending'],
    ['Within 0.5', validation.within_half_point_rate === undefined ? 'pending' : `${fmt(validation.within_half_point_rate * 100)}%`],
    ['Outcome Accuracy', backtest.outcome_accuracy === undefined ? 'pending' : `${fmt(backtest.outcome_accuracy * 100)}%`],
  ].map(([label, value]) => `<div class="leader-row"><span>${esc(label)}</span><strong>${esc(value)}</strong></div>`).join('');
}

function renderAll() {
  renderNotice();
  renderKpis();
  renderTeamBars();
  renderRoleDonut();
  renderLeaders();
  renderTeamCompare();
  renderPlayers();
  renderPlayerCompare();
  renderPrediction();
  renderCoverage();
}

function setView(view) {
  state.activeView = view;
  document.querySelectorAll('.view').forEach((node) => node.classList.toggle('active', node.id === `view-${view}`));
  document.querySelectorAll('.nav-item').forEach((node) => node.classList.toggle('active', node.dataset.view === view));
}

async function init() {
  const response = await fetch(new URL('app-data.json', document.currentScript.src));
  state.data = await response.json();
  buildModel(state.data);
  renderControls();
  renderAll();
  document.querySelectorAll('.nav-item').forEach((button) => button.addEventListener('click', () => setView(button.dataset.view)));
  ['globalSearch', 'teamFilter', 'roleFilter', 'sortMode'].forEach((id) => $(id).addEventListener('input', renderPlayers));
  $('teamMetricMode').addEventListener('change', renderTeamBars);
  ['teamA', 'teamB'].forEach((id) => $(id).addEventListener('change', renderTeamCompare));
  ['playerA', 'playerB'].forEach((id) => $(id).addEventListener('change', renderPlayerCompare));
}

init().catch((error) => {
  console.error(error);
  document.body.innerHTML = `<main class="workspace"><section class="notice"><strong>Dashboard failed to load.</strong><br>${esc(error.message)}</section></main>`;
});
"""


def generate_dashboard(
    *,
    overall_ratings_path: str | Path,
    game_ratings_path: str | Path,
    advanced_metrics_path: str | Path,
    roster_path: str | Path,
    tournament_stats_path: str | Path,
    team_stats_path: str | Path,
    prediction_path: str | Path,
    validation_path: str | Path,
    backtest_path: str | Path,
    output_path: str | Path,
    title: str = "FIFA World Cup 2026 Intelligence Dashboard",
) -> Path:
    output = Path(output_path)
    asset_dir_name = f"{output.stem}-assets"
    assets_dir = output.parent / asset_dir_name
    output.parent.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    data = dashboard_data(
        overall_rows=read_csv(overall_ratings_path),
        game_rows=read_csv(game_ratings_path),
        advanced_rows=read_csv(advanced_metrics_path),
        roster_rows=read_csv(roster_path),
        tournament_stats_rows=read_csv(tournament_stats_path),
        team_rows=read_csv(team_stats_path),
        prediction=read_json(prediction_path),
        validation=read_json(validation_path),
        backtest=read_json(backtest_path),
    )
    output.write_text(render_dashboard(title=title, asset_dir_name=asset_dir_name), encoding="utf-8")
    (assets_dir / "dashboard.css").write_text(dashboard_css(), encoding="utf-8")
    (assets_dir / "dashboard.js").write_text(dashboard_js(), encoding="utf-8")
    write_json(assets_dir / "app-data.json", data)
    return output
