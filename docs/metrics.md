# Metrics

This project uses role-aware football metrics. The same raw event can mean different things depending on the player's job, so player impact is scored against role expectations rather than one global formula.

## Event Metrics

### Passing

- `passes`: all pass events by a player.
- `completed_passes`: passes without an unsuccessful outcome.
- `pass_completion_pct`: completed passes divided by total passes.
- `progressive_passes`: passes that move the ball at least 10 units toward goal.
- `key_passes`: passes marked as shot assists.
- `assists`: passes marked as goal assists.

### Carrying

- `carries`: all carry events.
- `carry_distance`: total distance from carry start to carry end.
- `progressive_carries`: carries that move the ball at least 10 units toward goal.

### Dribbling

- `dribbles`: all dribble events.
- `successful_dribbles`: dribbles with a complete outcome.

### Defending

- `interceptions`: interception events.
- `tackles`: duel events where the duel type is tackle.
- `clearances`: clearance events.
- `aerials_won`: successful duel/aerial-style outcomes when present.
- `pressures`: pressure events.
- `ball_recoveries`: ball recovery events.
- `defensive_actions`: interceptions, tackles, clearances, pressures, and recoveries combined.

### Attacking

- `shots`: shot events.
- `xg`: summed StatsBomb expected goals value from shots.
- `goals`: shots with goal outcome.
- `goal_contributions`: goals plus assists.
- `chance_creation`: shot assists plus related creative pass actions.
- `saves`: goalkeeper save actions when present.
- `claims`: goalkeeper claim/collection/punch actions when present.

## Role-Aware Contribution Score

The score is calculated in three steps:

1. Compute raw player metrics.
2. Normalize each metric against the best player in the analyzed file.
3. Apply position-specific weights and convert the result to a 0-100 score.

Example role priorities:

- Center backs: interceptions, defensive actions, pass completion, progressive passes.
- Fullbacks: defensive actions, progressive carries, progressive passes, chance creation.
- Defensive midfielders: interceptions, recoveries, progressive passes, pass completion.
- Central midfielders: progressive passing, pass completion, ball carrying, chance creation.
- Attacking midfielders: chance creation, progressive passes, progressive carries, shots.
- Wingers: progressive carries, dribbles, chance creation, goal contributions.
- Forwards: xG, shots, goals, assists, pressing.

## Accuracy Improvements

The current metric engine is a transparent baseline. Strong improvements would be:

- per-90 normalization once minutes are added
- possession-adjusted defensive metrics
- expected threat or possession value
- pressure regains
- carry value by pitch zone
- shot quality beyond xG
- opponent strength adjustment
- knockout-stage pressure adjustment
