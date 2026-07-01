"""Interactive static dashboard generation for player/team analysis."""

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


def safe_json(data: object) -> str:
    return (
        json.dumps(data, ensure_ascii=False)
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("</", "<\\/")
    )


def render_dashboard(
    *,
    overall_rows: list[dict[str, str]],
    game_rows: list[dict[str, str]],
    advanced_rows: list[dict[str, str]],
    team_rows: list[dict[str, str]],
    prediction: dict[str, Any],
    validation: dict[str, Any],
    backtest: dict[str, Any],
    title: str = "FIFA World Cup 2026 Performance Dashboard",
) -> str:
    data = {
        "overall": overall_rows,
        "games": game_rows,
        "advanced": advanced_rows,
        "teamStats": team_rows,
        "prediction": prediction,
        "validation": validation,
        "backtest": backtest,
    }
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <style>{css()}</style>
</head>
<body>
  <aside class="sidebar">
    <div class="brand">
      <strong>WC26 Intelligence</strong>
      <span>ratings · teams · predictions</span>
    </div>
    <label>Search players<input id="playerSearch" type="search" placeholder="Name, team, role"></label>
    <label>Team A<select id="teamA"></select></label>
    <label>Team B<select id="teamB"></select></label>
    <label>Role<select id="roleFilter"></select></label>
    <label>Player A<select id="playerA"></select></label>
    <label>Player B<select id="playerB"></select></label>
    <nav>
      <a href="#overview">Overview</a>
      <a href="#compare">Team Compare</a>
      <a href="#players">Players</a>
      <a href="#playerCompare">Player Compare</a>
      <a href="#validation">Validation</a>
    </nav>
  </aside>
  <main>
    <section class="hero" id="overview">
      <div>
        <p class="eyebrow">Interactive dashboard</p>
        <h1>{esc(title)}</h1>
        <p>Search every loaded player, compare any two loaded teams, inspect complete team rosters, compare two players, and review prediction/validation quality from generated data.</p>
      </div>
      <div id="dataBanner" class="data-banner"></div>
    </section>
    <section id="kpis" class="kpi-grid"></section>
    <section id="predictionPanel" class="panel"></section>
    <section id="compare" class="comparison-grid"></section>
    <section id="players" class="panel">
      <div class="panel-head">
        <div>
          <p class="eyebrow">Player database</p>
          <h2>Searchable player ratings</h2>
        </div>
        <span id="playerCount" class="pill"></span>
      </div>
      <div id="playerCards" class="player-grid"></div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Player</th><th>Team</th><th>Role</th><th>Matches</th><th>Minutes</th><th>Rating</th><th>Role fit</th><th>Usage</th><th>Confidence</th></tr></thead>
          <tbody id="playerTable"></tbody>
        </table>
      </div>
    </section>
    <section id="playerCompare" class="comparison-grid"></section>
    <section id="advanced" class="panel">
      <div class="panel-head">
        <div>
          <p class="eyebrow">Advanced metrics</p>
          <h2>Role-fit leaderboard</h2>
        </div>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Player</th><th>Team</th><th>Role</th><th>Role Fit</th><th>Attack</th><th>Progression</th><th>Security</th><th>Disruption</th><th>Two-way</th><th>Usage</th></tr></thead>
          <tbody id="advancedTable"></tbody>
        </table>
      </div>
    </section>
    <section id="validation" class="metric-grid"></section>
  </main>
  <script id="app-data" type="application/json">{safe_json(data)}</script>
  <script>{javascript()}</script>
</body>
</html>
"""


def css() -> str:
    return """
    :root {
      --bg: #f3f6f2;
      --panel: #ffffff;
      --ink: #16211d;
      --muted: #63716c;
      --line: #dbe3dd;
      --accent: #0f7a52;
      --blue: #2557a8;
      --amber: #a36b00;
      --red: #a13b36;
      --shadow: 0 18px 45px rgba(22, 33, 29, .08);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      display: grid;
      grid-template-columns: 292px minmax(0, 1fr);
      min-height: 100vh;
    }
    .sidebar {
      position: sticky;
      top: 0;
      height: 100vh;
      padding: 22px 18px;
      background: #11201a;
      color: #eef8f1;
      overflow-y: auto;
    }
    .brand { padding-bottom: 18px; border-bottom: 1px solid rgba(255,255,255,.14); margin-bottom: 18px; }
    .brand strong { display: block; font-size: 20px; }
    .brand span { color: #b9cbc2; font-size: 13px; }
    label { display: block; margin: 14px 0; color: #cfe0d8; font-size: 13px; font-weight: 800; }
    input, select {
      width: 100%;
      margin-top: 6px;
      min-height: 38px;
      padding: 8px 10px;
      border-radius: 6px;
      border: 1px solid rgba(255,255,255,.18);
      background: #20332b;
      color: #fff;
      font: inherit;
    }
    nav { display: grid; gap: 8px; margin-top: 22px; }
    nav a {
      color: #e7f5ed;
      text-decoration: none;
      padding: 9px 10px;
      border: 1px solid rgba(255,255,255,.12);
      border-radius: 6px;
    }
    main { padding: 24px clamp(16px, 3vw, 40px) 42px; max-width: 1640px; width: 100%; }
    .hero, .panel, .team-card, .player-card, .metric-card, .kpi {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
    }
    .hero {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(280px, 430px);
      gap: 18px;
      padding: clamp(20px, 3vw, 34px);
      align-items: center;
    }
    h1, h2, h3, p { margin-top: 0; }
    h1 { font-size: clamp(34px, 5vw, 60px); line-height: 1.02; letter-spacing: 0; margin-bottom: 12px; }
    h2 { margin-bottom: 12px; }
    .hero p { color: var(--muted); line-height: 1.55; max-width: 850px; }
    .eyebrow {
      color: var(--muted);
      text-transform: uppercase;
      font-size: 12px;
      letter-spacing: .08em;
      font-weight: 900;
      margin-bottom: 6px;
    }
    .data-banner {
      padding: 14px 16px;
      border-radius: 8px;
      background: #fff7e5;
      border: 1px solid #f0c36d;
      color: #654600;
      line-height: 1.45;
    }
    .data-banner.verified { background: #eef9f3; border-color: #a9d9c2; color: #145d40; }
    .kpi-grid, .metric-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
      gap: 14px;
      margin-top: 16px;
    }
    .kpi, .metric-card { padding: 17px; min-height: 112px; }
    .kpi span, .metric-card span { color: var(--muted); font-size: 12px; text-transform: uppercase; font-weight: 900; letter-spacing: .06em; }
    .kpi strong, .metric-card strong { display: block; font-size: 32px; margin: 8px 0 4px; }
    .kpi small, .metric-card small { color: var(--muted); }
    .panel { padding: clamp(17px, 2.2vw, 26px); margin-top: 16px; }
    .panel-head { display: flex; justify-content: space-between; gap: 16px; align-items: start; margin-bottom: 12px; }
    .comparison-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
      margin-top: 16px;
    }
    .team-card, .player-card { padding: 18px; }
    .team-card h2, .player-card h3 { margin-bottom: 4px; }
    .subtle { color: var(--muted); font-size: 13px; }
    .score { font-size: 42px; color: var(--accent); font-weight: 900; }
    .bar-row { display: grid; grid-template-columns: 120px 1fr 58px; gap: 10px; align-items: center; margin: 10px 0; color: var(--muted); font-size: 13px; }
    .bar-track { height: 12px; border-radius: 999px; overflow: hidden; background: #e8efeb; }
    .bar-track i { display: block; height: 100%; border-radius: inherit; background: linear-gradient(90deg, var(--accent), var(--blue)); }
    .player-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 14px;
      margin: 14px 0;
    }
    .player-card-head { display: flex; justify-content: space-between; gap: 12px; align-items: start; }
    .player-card-head strong { font-size: 34px; color: var(--accent); }
    .sparkline { width: 100%; height: 58px; margin-top: 10px; color: var(--blue); border: 1px solid var(--line); border-radius: 8px; background: #f8faf8; }
    .radar { width: 120px; height: 120px; }
    .radar circle, .radar line { fill: none; stroke: #d6dfd9; stroke-width: 1.5; }
    .radar polygon { fill: rgba(15,122,82,.18); stroke: var(--accent); stroke-width: 2; }
    .pill, .tag {
      display: inline-flex;
      align-items: center;
      min-height: 28px;
      padding: 5px 9px;
      border-radius: 6px;
      background: #edf4f0;
      color: var(--accent);
      font-size: 13px;
      font-weight: 900;
    }
    .warn { color: var(--amber); background: #fff4d8; }
    .risk { color: var(--red); background: #ffe8e5; }
    .table-wrap { overflow-x: auto; border: 1px solid var(--line); border-radius: 8px; background: #fff; }
    table { width: 100%; min-width: 920px; border-collapse: collapse; }
    th, td { padding: 12px 13px; text-align: left; border-bottom: 1px solid var(--line); vertical-align: top; }
    th { background: #f8faf8; color: var(--muted); text-transform: uppercase; font-size: 12px; letter-spacing: .05em; }
    td span { display: block; color: var(--muted); font-size: 12px; margin-top: 3px; }
    tbody tr:hover { background: #f8fbf9; }
    .roster-list { display: grid; gap: 8px; margin-top: 12px; }
    .roster-row { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 10px; padding: 9px 0; border-top: 1px solid var(--line); }
    @media (max-width: 980px) {
      body { grid-template-columns: 1fr; }
      .sidebar { position: relative; height: auto; }
      .hero, .comparison-grid { grid-template-columns: 1fr; }
    }
    """


def javascript() -> str:
    return r"""
    const app = JSON.parse(document.getElementById('app-data').textContent);
    const $ = (id) => document.getElementById(id);
    const num = (v) => Number.parseFloat(v || 0) || 0;
    const fmt = (v, d = 2) => num(v).toFixed(d);
    const pct = (v) => `${(num(v) * 100).toFixed(1)}%`;
    const esc = (v) => String(v ?? '').replace(/[&<>"']/g, (m) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]));

    function teams() {
      return [...new Set([
        ...app.overall.map(r => r.team),
        ...app.games.map(r => r.team),
        ...app.teamStats.map(r => r.team)
      ].filter(Boolean))].sort();
    }
    function roles() {
      return ['All roles', ...new Set(app.overall.map(r => r.role_group).filter(Boolean))].sort();
    }
    function players() {
      return app.overall.slice().sort((a,b) => num(b.weighted_rating)-num(a.weighted_rating));
    }
    function advFor(player, team) {
      const rows = app.advanced.filter(r => r.player === player && r.team === team);
      if (!rows.length) return {};
      const avg = (field) => rows.reduce((s,r) => s + num(r[field]), 0) / rows.length;
      return {
        role_fit_score: avg('role_fit_score'),
        attacking_involvement: avg('attacking_involvement'),
        progression_value: avg('progression_value'),
        ball_security: avg('ball_security'),
        defensive_disruption: avg('defensive_disruption'),
        two_way_value: avg('two_way_value'),
        usage_rate: avg('usage_rate'),
        xg_efficiency: avg('xg_efficiency')
      };
    }
    function teamProfile(team) {
      const overall = app.overall.filter(r => r.team === team);
      const games = app.games.filter(r => r.team === team);
      const advanced = app.advanced.filter(r => r.team === team);
      const teamStats = app.teamStats.filter(r => r.team === team);
      const avg = (rows, field) => rows.length ? rows.reduce((s,r) => s + num(r[field]), 0) / rows.length : 0;
      return {
        team,
        players: overall.length,
        playerGames: games.length,
        avgRating: avg(overall, 'weighted_rating'),
        best: overall.slice().sort((a,b) => num(b.weighted_rating)-num(a.weighted_rating))[0],
        attack: avg(advanced, 'attacking_involvement'),
        progression: avg(advanced, 'progression_value'),
        security: avg(advanced, 'ball_security'),
        defense: avg(advanced, 'defensive_disruption'),
        usage: avg(advanced, 'usage_rate'),
        xgFor: avg(teamStats, 'xg_for'),
        xgAgainst: avg(teamStats, 'xg_against'),
        shotsFor: avg(teamStats, 'shots_for'),
        shotsAgainst: avg(teamStats, 'shots_against'),
        roster: overall
      };
    }
    function confidenceClass(v) {
      const text = String(v || '').toLowerCase();
      if (text === 'high') return '';
      if (text === 'medium') return 'warn';
      return 'risk';
    }
    function bar(label, value, max = 10) {
      const width = Math.max(0, Math.min(100, max ? value / max * 100 : 0));
      return `<div class="bar-row"><span>${esc(label)}</span><div class="bar-track"><i style="width:${width}%"></i></div><strong>${fmt(value)}</strong></div>`;
    }
    function sparkline(values) {
      if (!values.length) return '<svg class="sparkline"></svg>';
      const w = 220, h = 58, min = Math.min(...values), max = Math.max(...values), span = Math.max(max-min, .01);
      const points = values.map((v,i) => `${values.length === 1 ? w/2 : i*(w/(values.length-1))},${h - ((v-min)/span*(h-12)) - 6}`).join(' ');
      return `<svg class="sparkline" viewBox="0 0 ${w} ${h}"><polyline points="${points}" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"></polyline></svg>`;
    }
    function radar(values) {
      const labels = ['attacking_involvement','progression_value','defensive_disruption','ball_security'];
      const size=120, c=60, r=42;
      const axes = labels.map((_,i) => {
        const a = -Math.PI/2 + i * Math.PI/2;
        return `<line x1="${c}" y1="${c}" x2="${c+r*Math.cos(a)}" y2="${c+r*Math.sin(a)}"></line>`;
      }).join('');
      const points = labels.map((key,i) => {
        const a = -Math.PI/2 + i * Math.PI/2;
        const v = Math.max(0, Math.min(1, num(values[key])/10));
        return `${c+r*v*Math.cos(a)},${c+r*v*Math.sin(a)}`;
      }).join(' ');
      return `<svg class="radar" viewBox="0 0 ${size} ${size}"><circle cx="${c}" cy="${c}" r="${r}"></circle>${axes}<polygon points="${points}"></polygon></svg>`;
    }
    function playerTrend(player, team) {
      return app.games
        .filter(r => r.player === player && r.team === team)
        .sort((a,b) => String(a.match_id).localeCompare(String(b.match_id)))
        .map(r => num(r.rating));
    }
    function populateControls() {
      const teamOptions = teams().map(t => `<option value="${esc(t)}">${esc(t)}</option>`).join('');
      $('teamA').innerHTML = teamOptions;
      $('teamB').innerHTML = teamOptions;
      if (teams()[1]) $('teamB').value = teams()[1];
      $('roleFilter').innerHTML = roles().map(r => `<option value="${esc(r)}">${esc(r)}</option>`).join('');
      const playerOptions = players().map(p => `<option value="${esc(p.player)}|||${esc(p.team)}">${esc(p.player)} · ${esc(p.team)}</option>`).join('');
      $('playerA').innerHTML = playerOptions;
      $('playerB').innerHTML = playerOptions;
      if (players()[1]) $('playerB').selectedIndex = 1;
    }
    function renderBanner() {
      const demo = [...app.overall, ...app.games].some(r => String(r.player || '').startsWith('Demo '));
      $('dataBanner').className = `data-banner ${demo ? '' : 'verified'}`;
      $('dataBanner').innerHTML = demo
        ? '<strong>Demo data view</strong><br>This page is using synthetic sample players. Import verified roster, lineup, event, and rating data before treating analysis as real.'
        : '<strong>Imported data view</strong><br>Data appears imported. Interpret results according to source coverage and validation quality.';
    }
    function renderKpis() {
      const top = players()[0] || {};
      const bestGame = app.games.slice().sort((a,b) => num(b.rating)-num(a.rating))[0] || {};
      $('kpis').innerHTML = [
        ['Teams', teams().length, 'loaded teams'],
        ['Players', app.overall.length, 'searchable players'],
        ['Player Games', app.games.length, 'rated match rows'],
        ['Advanced Rows', app.advanced.length, 'role-fit profiles'],
        ['Top Rating', fmt(top.weighted_rating), `${top.player || 'n/a'} · ${top.team || ''}`],
        ['Best Game', fmt(bestGame.rating), `${bestGame.player || 'n/a'} vs ${bestGame.opponent || ''}`],
      ].map(([label,value,detail]) => `<section class="kpi"><span>${label}</span><strong>${value}</strong><small>${esc(detail)}</small></section>`).join('');
    }
    function renderPrediction() {
      const p = app.prediction || {};
      const topScores = (p.top_scorelines || []).map(s => bar(s.score, num(s.probability), Math.max(...(p.top_scorelines || []).map(x => num(x.probability)), .01))).join('');
      $('predictionPanel').innerHTML = `
        <div class="panel-head"><div><p class="eyebrow">Prediction snapshot</p><h2>${esc(p.home_team || 'Team A')} vs ${esc(p.away_team || 'Team B')}</h2></div><span class="pill">${esc(p.confidence || 'unknown')} confidence</span></div>
        <div class="comparison-grid">
          <div>${bar('Home win', num(p.home_win), 1)}${bar('Draw', num(p.draw), 1)}${bar('Away win', num(p.away_win), 1)}</div>
          <div>${topScores}</div>
        </div>`;
    }
    function teamCard(profile, side) {
      const roster = profile.roster
        .slice().sort((a,b) => num(b.weighted_rating)-num(a.weighted_rating))
        .map(p => `<div class="roster-row"><div><strong>${esc(p.player)}</strong><span>${esc(p.role_group)} · ${fmt(p.minutes,0)} min</span></div><strong>${fmt(p.weighted_rating)}</strong></div>`)
        .join('');
      return `<article class="team-card">
        <p class="eyebrow">${side}</p>
        <h2>${esc(profile.team)}</h2>
        <div class="score">${fmt(profile.avgRating)}</div>
        <p class="subtle">${profile.players} players · ${profile.playerGames} player-games · top player ${esc(profile.best?.player || 'n/a')}</p>
        ${bar('Attack', profile.attack)}${bar('Progression', profile.progression)}${bar('Security', profile.security)}${bar('Defense', profile.defense)}${bar('Usage', profile.usage)}
        <h3>Roster</h3><div class="roster-list">${roster || '<p class="subtle">No players loaded for this team.</p>'}</div>
      </article>`;
    }
    function renderTeamCompare() {
      const a = teamProfile($('teamA').value);
      const b = teamProfile($('teamB').value);
      $('compare').innerHTML = teamCard(a, 'Team A') + teamCard(b, 'Team B');
    }
    function filteredPlayers() {
      const term = $('playerSearch').value.toLowerCase().trim();
      const role = $('roleFilter').value;
      return players().filter(p => {
        const haystack = `${p.player} ${p.team} ${p.role_group}`.toLowerCase();
        const roleMatch = role === 'All roles' || p.role_group === role;
        return roleMatch && (!term || haystack.includes(term));
      });
    }
    function playerCard(p) {
      const advanced = advFor(p.player, p.team);
      return `<article class="player-card">
        <div class="player-card-head"><div><h3>${esc(p.player)}</h3><span>${esc(p.team)} · ${esc(p.role_group)}</span></div><strong>${fmt(p.weighted_rating)}</strong></div>
        ${sparkline(playerTrend(p.player, p.team))}
        <div style="display:grid;grid-template-columns:130px 1fr;gap:10px;align-items:center;margin-top:10px">${radar(advanced)}<div>${bar('Role fit', num(advanced.role_fit_score))}${bar('Usage', num(advanced.usage_rate))}${bar('Two-way', num(advanced.two_way_value))}</div></div>
      </article>`;
    }
    function renderPlayers() {
      const rows = filteredPlayers();
      $('playerCount').textContent = `${rows.length} players`;
      $('playerCards').innerHTML = rows.slice(0, 8).map(playerCard).join('');
      $('playerTable').innerHTML = rows.map(p => {
        const advanced = advFor(p.player, p.team);
        return `<tr><td><strong>${esc(p.player)}</strong></td><td>${esc(p.team)}</td><td>${esc(p.role_group)}</td><td>${esc(p.matches)}</td><td>${fmt(p.minutes,0)}</td><td><strong>${fmt(p.weighted_rating)}</strong></td><td>${fmt(advanced.role_fit_score)}</td><td>${fmt(advanced.usage_rate)}</td><td><span class="tag ${confidenceClass(p.confidence)}">${esc(p.confidence)}</span></td></tr>`;
      }).join('');
    }
    function playerBySelect(id) {
      const [player, team] = $(id).value.split('|||');
      return app.overall.find(p => p.player === player && p.team === team) || {};
    }
    function playerCompareCard(p, label) {
      const advanced = advFor(p.player, p.team);
      return `<article class="player-card"><p class="eyebrow">${label}</p><div class="player-card-head"><div><h3>${esc(p.player || 'n/a')}</h3><span>${esc(p.team || '')} · ${esc(p.role_group || '')}</span></div><strong>${fmt(p.weighted_rating)}</strong></div>${sparkline(playerTrend(p.player, p.team))}${bar('Role fit', num(advanced.role_fit_score))}${bar('Attack', num(advanced.attacking_involvement))}${bar('Progression', num(advanced.progression_value))}${bar('Defense', num(advanced.defensive_disruption))}${bar('Security', num(advanced.ball_security))}${bar('Usage', num(advanced.usage_rate))}</article>`;
    }
    function renderPlayerCompare() {
      $('playerCompare').innerHTML = playerCompareCard(playerBySelect('playerA'), 'Player A') + playerCompareCard(playerBySelect('playerB'), 'Player B');
    }
    function renderAdvanced() {
      $('advancedTable').innerHTML = app.advanced
        .slice().sort((a,b) => num(b.role_fit_score)-num(a.role_fit_score))
        .map(r => `<tr><td><strong>${esc(r.player)}</strong></td><td>${esc(r.team)}</td><td>${esc(r.role_group)}</td><td><strong>${fmt(r.role_fit_score)}</strong></td><td>${fmt(r.attacking_involvement)}</td><td>${fmt(r.progression_value)}</td><td>${fmt(r.ball_security)}</td><td>${fmt(r.defensive_disruption)}</td><td>${fmt(r.two_way_value)}</td><td>${fmt(r.usage_rate)}</td></tr>`)
        .join('');
    }
    function renderValidation() {
      const v = app.validation || {}, b = app.backtest || {};
      const cards = [
        ['Rating MAE', v.mae ?? 'n/a', 'lower is better'],
        ['Correlation', v.correlation ?? 'n/a', 'external rating alignment'],
        ['Within 0.5', pct(v.within_half_point_rate), 'close rating share'],
        ['Top-3 Score', pct(b.exact_score_top3_rate), 'exact score backtest'],
        ['Outcome Accuracy', pct(b.outcome_accuracy), 'W/D/L backtest'],
        ['Log Loss', b.log_loss ?? 'n/a', 'probability penalty'],
      ];
      $('validation').innerHTML = cards.map(([label,value,detail]) => `<section class="metric-card"><span>${label}</span><strong>${value}</strong><small>${detail}</small></section>`).join('');
    }
    function renderAll() {
      renderBanner(); renderKpis(); renderPrediction(); renderTeamCompare(); renderPlayers(); renderPlayerCompare(); renderAdvanced(); renderValidation();
    }
    populateControls();
    ['teamA','teamB'].forEach(id => $(id).addEventListener('change', renderTeamCompare));
    ['playerA','playerB'].forEach(id => $(id).addEventListener('change', renderPlayerCompare));
    $('playerSearch').addEventListener('input', renderPlayers);
    $('roleFilter').addEventListener('change', renderPlayers);
    renderAll();
    """


def generate_dashboard(
    *,
    overall_ratings_path: str | Path,
    game_ratings_path: str | Path,
    advanced_metrics_path: str | Path,
    team_stats_path: str | Path,
    prediction_path: str | Path,
    validation_path: str | Path,
    backtest_path: str | Path,
    output_path: str | Path,
    title: str = "FIFA World Cup 2026 Performance Dashboard",
) -> Path:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        render_dashboard(
            overall_rows=read_csv(overall_ratings_path),
            game_rows=read_csv(game_ratings_path),
            advanced_rows=read_csv(advanced_metrics_path),
            team_rows=read_csv(team_stats_path),
            prediction=read_json(prediction_path),
            validation=read_json(validation_path),
            backtest=read_json(backtest_path),
            title=title,
        ),
        encoding="utf-8",
    )
    return output
