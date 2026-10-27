# Courtside — NBA Paper Picks

Courtside is a social NBA prediction dashboard. Fans make risk-free paper picks against game lines and model-generated player props, build a lifetime record, and compete on a weekly leaderboard. There are no deposits, real-money wagers, or prizes.

## Features

### Game markets

- Moneyline, spread, and total odds from DraftKings via the ESPN NBA odds page.
- Game dates, start times, team logos, and odds retrieval timestamps.
- Picks lock when the game starts. Changed or unavailable lines are rejected on submission.

### Player props

Click a game card to view generated player predictions:

| Market | Statistic | CSV fields |
| --- | --- | --- |
| PTS | Points | `pts_projection`, `pts_line`, `pts_over_prob`, `pts_under_prob` |
| PR | Points + rebounds | `pr_projection`, `pr_line`, `pr_over_prob`, `pr_under_prob` |
| PRA | Points + rebounds + assists | `pra_projection`, `pra_line`, `pra_over_prob`, `pra_under_prob` |

- Predictions are read from `ml/data/processed/nba_prop_predictions.csv`.
- Users select Over or Under on the generated line. Both sides use **-110 paper odds**; displayed probabilities are model estimates, not payout odds.
- Players are sorted by highest projection for the selected statistic.
- Player headshots and team logos appear beside names. Missing headshots fall back to initials.
- Displaying and submitting generated props does not require a BALLDONTLIE API key.
- The unused Paper markets tab and practice mode have been removed.

### Shared pick slip

- One selection creates a single; 2–6 selections create a parlay.
- Game lines and generated player props can be combined.
- The slip displays **Single**, **SGP** for multiple selections from one game, or **SGPx** for selections across games.
- Selecting the opposite side of the same prop replaces the previous selection. Both sides cannot appear in one ticket.
- Selecting a team's moneyline and spread keeps only its spread.
- Stake buttons add **+1, +2, +5, or +10** points to the current amount. The stake starts empty; pressing +10 twice sets it to 20.
- Stakes must be at least 1 point, with up to two decimal places, and cannot exceed the available balance. There is no separate per-ticket stake cap.
- Saved tickets retain their original lines and timestamps and cannot be edited.

Parlay payouts multiply decimal odds and round to cents. These are app-calculated paper payouts, including same-game combinations; they do not account for correlation or represent sportsbook parlay quotes.

### Weekly competition and lifetime records

- Every account gets **100 points each Monday at midnight Eastern** (`America/New_York`). Daylight-saving changes are handled automatically.
- The balance resets to 100 even when the previous week's balance was higher. Unused points do not carry over.
- Each ticket belongs to the week it was placed. Late results update that week's results and lifetime stats, not the next week's balance.
- The weekly leaderboard ranks net profit: winning profit minus losing stakes.
- **One settled win or loss** qualifies a player. Pushes and voids do not qualify; a parlay counts as one ticket.
- Equal profits share a rank. The leaderboard displays up to 20 qualified accounts.
- Lifetime history, wins, losses, profit, and ROI remain available after weekly resets.

### Community

Community sentiment includes game-market selections from both singles and parlays. Each fan counts once per game, market, and side, even if the same selection appears on multiple tickets. Player props do not contribute to moneyline, spread, or total sentiment. These are this app's user selections, not sportsbook betting volume.

The Social feed shows recent submitted tickets. Other users appear under anonymous fan tags.

## Technology

- **Frontend:** React, TypeScript, Tailwind CSS, and shadcn UI components.
- **App framework:** Vinext with Vite and Next-style routes.
- **Backend:** TypeScript API routes on Cloudflare Workers.
- **Database:** Cloudflare D1 / SQLite with Drizzle schema and migrations.
- **Model pipeline:** Python scripts in `ml/` producing a CSV consumed by the app.

## Run locally

Requires Node.js **22.13 or newer** and npm. Run these commands from the repository root:

```sh
cd courtside
npm ci
npm run build
```

For a new local database, apply all three migrations in order:

```sh
node --import ./scripts/sites-env.mjs ./node_modules/wrangler/bin/wrangler.js d1 execute DB --local --config dist/server/wrangler.json --persist-to .wrangler/state --file drizzle/0000_sharp_vargas.sql
node --import ./scripts/sites-env.mjs ./node_modules/wrangler/bin/wrangler.js d1 execute DB --local --config dist/server/wrangler.json --persist-to .wrangler/state --file drizzle/0001_cynical_jack_power.sql
node --import ./scripts/sites-env.mjs ./node_modules/wrangler/bin/wrangler.js d1 execute DB --local --config dist/server/wrangler.json --persist-to .wrangler/state --file drizzle/0002_tense_skrulls.sql
```

Apply each migration only once. Existing checkouts need only migrations they have not already applied. Do not delete `.wrangler/state` unless you intend to erase local records.

```sh
npm run dev
```

Open the URL printed in the terminal, normally `http://localhost:5173`. The dashboard is at `/dashboard`. If local preview authentication is required, visit `/signin-with-chatgpt?return_to=/dashboard` on the same local server.

Local development uses a preview identity rather than independent production user accounts. The existing authentication integration relies on Sites-provided identity in its hosted environment. Publishing under a separate hosting account requires configuring production authentication and database bindings; the development server is not a public deployment.

## Prediction data and photos

The frontend uses the generated CSV; it does not run the Python training pipeline. Linear models produce projections and logistic models produce over/under probabilities. To update predictions, replace `ml/data/processed/nba_prop_predictions.csv` with the pipeline output, then rebuild and redeploy. Vite reloads the imported CSV during development.

Rows are matched to games using Eastern game date, home/away orientation, and team identities. ESPN event IDs and BALLDONTLIE game IDs are not interchangeable. Invalid rows are excluded, and missing matchups show an empty state. Roster labels and model estimates are supplied by the CSV and are not independently verified by the frontend.

`lib/player-headshots.json` maps CSV player IDs and names to NBA IDs. Its initial mapping covers 689 of 712 CSV players. New or unmatched players show initials until the mapping is updated. Photos load from the NBA CDN; both ID and name are checked before selecting a photo.

Identifier source: [nba_api player directory](https://github.com/swar/nba_api/blob/master/src/nba_api/stats/library/data.py), retrieved October 27, 2026.

Legacy sportsbook-prop backend support remains for compatibility with existing records. Its BALLDONTLIE credentials are separate from the generated CSV workflow. If needed, configure `BALLDONTLIE_API_KEY` privately using `.dev.vars.example` as a template. Never commit credentials or put them in client-visible environment variables.

## Settlement

- Game picks use ESPN final scores; generated props use ESPN final player box scores. Overtime counts.
- Wins earn the stored profit; losses consume the stake.
- Exact ties push, and cancelled games are voided. Confirmed player non-participation voids the corresponding prop.
- Missing or ambiguous player results remain pending.
- Any losing parlay leg loses the ticket. Pushes and voids remove legs and recalculate the return; an entirely pushed/void ticket refunds its stake.
- Settlement runs during authenticated dashboard refreshes and manual result checks, not through a background scheduler.

The ESPN integration reads a public odds page and can be affected by source changes or delays. Odds are cached for one minute; live submissions reject snapshots older than two minutes. Retrieval timestamps are not sportsbook update timestamps. Prediction records are app-maintained, not third-party certification.

## Checks

From `courtside/`:

```sh
npx tsc --noEmit
node tools/check_domain.mjs
python3 tools/check_weekly_sql.py
python3 tools/check_sentiment.py
npm run build
```

These cover grading, payout rounding, CSV matching, selection conflicts, Eastern weekly boundaries and DST, balance guards, leaderboard qualification, and sentiment deduplication. SQLite checks run against isolated in-memory databases.

`tools/check_model_picks.py` and `tools/check_mixed_parlays.py` exercise a running local app and create test tickets. Use a disposable local database and follow their cleanup instructions. Older demo-based API scripts target retired practice behavior and are not current acceptance checks.

## Project layout

```text
courtside/
├── app/                 Dashboard, player props, shared slip, API routes
├── components/ui/       Used UI components
├── lib/                 Odds, grading, settlement, weekly rules, headshot mapping
├── db/                  Database schema and connection
├── drizzle/             SQL migrations and migration metadata
├── ml/                  Python model pipeline and generated predictions CSV
├── tools/               Validation scripts
├── public/              Static assets
├── scripts/             Development and build helpers
├── build/               Required Sites Vite integration
└── .openai/hosting.json  Hosting configuration used by the build
```

Keep `build/`, `scripts/`, and `.openai/hosting.json`: the current configuration imports them. Dependencies, build output, local database state, and private environment files are excluded from Git. The unused Kaggle utility and starter examples have been removed.
