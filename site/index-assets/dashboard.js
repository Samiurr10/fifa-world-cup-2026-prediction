
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

function titleCase(value) {
  return String(value || '').toLowerCase().replace(/\b[\p{L}'][\p{L}']*/gu, (word) => word.charAt(0).toUpperCase() + word.slice(1));
}

function ratingValue(player) {
  return player.weighted_rating === undefined || player.weighted_rating === '' ? null : num(player.weighted_rating);
}

function ratingText(player) {
  const rating = ratingValue(player);
  return rating === null ? 'Pending' : rating.toFixed(2);
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
      status: 'awaiting match stats',
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
    goals: roster.reduce((total, player) => total + player.goals, 0),
    avgCaps: average(roster, (player) => player.caps),
    avgAge: average(roster, (player) => player.age),
    avgHeight: average(roster, (player) => player.height),
    rating: average(rated, (player) => ratingValue(player) || 0),
    roleCounts,
    topCaps: [...roster].sort((a, b) => b.caps - a.caps).slice(0, 5),
    topGoals: [...roster].sort((a, b) => b.goals - a.goals).slice(0, 5),
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
    goals: (a, b) => b.goals - a.goals,
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
  const value = mode === 'goals' ? player.goals : player.caps;
  const label = mode === 'goals' ? 'goals' : 'caps';
  return `<div class="leader-row"><div class="leader-info"><strong>${esc(player.player)}</strong><span class="muted">${esc(player.team)} · ${esc(player.club || 'club n/a')}</span></div><strong>${value} ${label}</strong></div>`;
}

function renderNotice() {
  const demo = state.players.some((player) => player.player.startsWith('Demo '));
  const hasRatings = state.players.some((player) => ratingValue(player) !== null);
  $('notice').className = `notice ${demo ? '' : 'verified'}`;
  if (demo) {
    $('notice').innerHTML = '<strong>Demo mode.</strong> This dashboard is using synthetic sample ratings. Do not interpret them as real World Cup data.';
  } else if (!hasRatings) {
    $('notice').innerHTML = '<strong>Official roster mode.</strong> The 48 squads and 1,248 players come from the FIFA squad list. Match ratings and prediction confidence will unlock after API-Football fixture player stats are imported with <code>API_FOOTBALL_KEY</code>.';
  } else {
    $('notice').innerHTML = '<strong>Rated data mode.</strong> Ratings are generated from imported player-match statistics. Interpret gaps according to data coverage.';
  }
  $('dataModeBadge').textContent = demo ? 'Demo data' : hasRatings ? 'Rated data' : 'Official rosters';
  $('coverageBadge').textContent = `${state.teams.length} teams · ${state.players.length} players`;
}

function renderKpis() {
  const hasRatings = state.players.filter((player) => ratingValue(player) !== null).length;
  const totalCaps = state.players.reduce((total, player) => total + player.caps, 0);
  const totalGoals = state.players.reduce((total, player) => total + player.goals, 0);
  const topScorer = [...state.players].sort((a, b) => b.goals - a.goals)[0] || {};
  const mostCapped = [...state.players].sort((a, b) => b.caps - a.caps)[0] || {};
  const cards = [
    ['Teams', state.teams.length, 'official squads loaded'],
    ['Players', state.players.length, 'searchable squad players'],
    ['Rated Players', hasRatings, 'from API/player stats'],
    ['Total Caps', totalCaps.toLocaleString(), 'international experience'],
    ['Squad Goals', totalGoals.toLocaleString(), 'international goals'],
    ['Most Capped', mostCapped.player || 'n/a', `${mostCapped.team || ''} · ${mostCapped.caps || 0} caps`],
    ['Top Scorer', topScorer.player || 'n/a', `${topScorer.team || ''} · ${topScorer.goals || 0} goals`],
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
    goals: (profile) => profile.goals,
    age: (profile) => profile.avgAge,
    height: (profile) => profile.avgHeight,
  };
  const labels = {
    caps: (value) => `${fmt(value)} avg`,
    goals: (value) => `${Math.round(value)} goals`,
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
  const rows = [...state.players].sort((a, b) => (b.goals * 4 + b.caps) - (a.goals * 4 + a.caps)).slice(0, 10);
  $('leaderList').innerHTML = rows.map((player) => playerLine(player, player.goals >= player.caps / 8 ? 'goals' : 'caps')).join('');
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
    <p class="team-meta">${profile.players} players · ${profile.caps.toLocaleString()} caps · ${profile.goals.toLocaleString()} goals</p>
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
      ${miniStat('Goals', player.goals)}
      ${miniStat('Matches', player.matches || 0)}
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
    <td>${player.goals}</td>
    <td><strong>${ratingText(player)}</strong></td>
    <td><span class="tag ${ratingValue(player) === null ? 'warn' : 'good'}">${esc(player.status || 'pending')}</span></td>
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
  $('playerCompare').innerHTML = `${playerCompareCard(a, 'Player A')}${playerCompareCard(b, 'Player B')}<article class="panel" style="grid-column:1 / -1"><p class="eyebrow">Head To Head</p><h2>Profile Comparison</h2><div class="comparison-bars">${compareMetric('Caps', a.caps, b.caps)}${compareMetric('International goals', a.goals, b.goals)}${compareMetric('Age', a.age, b.age)}${compareMetric('Height', a.height, b.height)}</div></article>`;
}

function renderPrediction() {
  const prediction = state.data.prediction || {};
  if (!prediction.home_team && !state.data.games.length) {
    $('predictionPanel').innerHTML = `<article class="panel"><p class="eyebrow">Prediction Lab</p><h2>Waiting For Match Stats</h2><div class="empty-state">Predictions need real team match stats and, for player-level confidence, API-Football fixture player stats. Set <code>API_FOOTBALL_KEY</code>, run <code>make api-football-ingest</code>, load the exported stats into the rating DB, and regenerate this dashboard.</div></article>`;
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
