> Practice mode has been retired from the app. The dashboard uses real matchups only; demo submissions and simulated settlement are disabled. Existing practice records are retained in storage but are not displayed. Older demo integration scripts below describe the retired mode and should not be run against the current app.

# Courtside — NBA Paper Picks

A private, responsive NBA paper-prediction app with moneyline, spread, and total markets. No deposits, real-money wagering, or prizes.

## What works

- Real DraftKings lines read from the ESPN NBA odds page, with exact game dates, retrieval timestamps, and per-side prices. The server refreshes its cache after one minute. Source failures disable real-line picking rather than substituting invented odds.
- Server-side pick validation, immutable saved lines, one prediction per game/market, start-time lockouts, and atomic paper-bankroll limits.
- Parlays of 2–6 different games, mixing moneyline, spread, and total. One stake per ticket, combined odds, immutable leg snapshots, and per-leg results in history. Same-game parlays are excluded; selecting another market from a game replaces its leg.
- Parlay payouts multiply decimal odds and round once to cents. Any loss loses the ticket; pushes/voids remove legs, and an entirely pushed/void ticket refunds the stake. These are Courtside-calculated paper prices, not sportsbook parlay quotes. An identical combination can only be locked once per mode.
- 1,000 starting paper points. Separate real-line and practice balances and histories.
- Positive/negative American-odds payouts; wins, losses, pushes, and cancelled-game refunds.
- ESPN final-score settlement on dashboard refresh or “Check final results.” Practice has an explicit simulation button.
- Community sentiment uses single picks only; standings include single and parlay tickets. No seeded users or invented records.
- Sites authenticated identity; private owner-only deployment. Community participation requires deliberately expanding the Site audience later.
- Figma concept: https://www.figma.com/design/wCojbAlWHztMxETcPocU27

## Run locally

Node 22.13+ is required. The app uses React/Vinext and Cloudflare D1 for the hosted experience. Open this project in PyCharm or another IDE.

```sh
npm ci
npm run build
node --import ./scripts/sites-env.mjs ./node_modules/wrangler/bin/wrangler.js d1 execute DB --local --config dist/server/wrangler.json --persist-to .wrangler/state --file drizzle/0000_sharp_vargas.sql
node --import ./scripts/sites-env.mjs ./node_modules/wrangler/bin/wrangler.js d1 execute DB --local --config dist/server/wrangler.json --persist-to .wrangler/state --file drizzle/0001_cynical_jack_power.sql
npm run dev
```

Apply each migration only once to a new local database. The development sign-in uses a local preview identity and does not affect hosted user data. Production identity is provided by Sites. Never expose the development server publicly.

## Data boundaries

The ESPN page is a public-page integration, not a contracted sportsbook API. Its markup, availability, and delays can change. Retrieval time is not the sportsbook's last-update time. Quotes are checked against a server snapshot no more than 60 seconds old; clients cannot choose their own odds. A moved quote requires a fresh selection. Suspended/unavailable markets are omitted.

Results include overtime and require ESPN's final status. Cancelled games are voided; postponed or unconfirmed games remain pending. Settlement currently runs when an authenticated user opens or refreshes the dashboard, not as a background scheduler. Practice games are illustrative and never count as real-line results. Audit timestamps are app-recorded, not third-party certification.

WebMCP exposes `stage_paper_pick`, which only stages a selection and never submits it. Keyboard-accessible controls and a mobile navigation drawer are included.

## Validation

Run `npx tsc --noEmit` and `npm run build`. End-to-end API validation covered all three markets, odds tampering rejection, duplicate rejection, invalid stakes, concurrent balance protection, settlement idempotency, persistence, and separation between live and practice. See `tools/check_api.py` and `tools/check_parlay_api.py` (empty local practice database only). `node tools/check_domain.mjs` checks grading, parlay push/void adjustments, and payout rounding. Parlay integration also checks mixed markets, order-independent duplicates, and shared bankroll protection across concurrent single/parlay submissions.

### Player props

Click a game card (or focus it and press Enter) to open Points, Assists, and Rebounds over/under markets. Player picks are singles (not parlay legs), share the mode's bankroll, and appear in My predictions. One pick per player/stat/game is allowed, including alternate lines. Exact ties refund the stake. Confirmed zero participation voids a pick; unavailable or unconfirmed statistics remain pending. Practice uses fictional position-based players and deterministic simulated results.

Live player odds use DraftKings through BALLDONTLIE, independently of the ESPN team-market feed. Copy `.dev.vars.example` to `.dev.vars`, set `BALLDONTLIE_API_KEY` privately with an account that has player-props and stats access, and restart `npm run dev`. Cloudflare loads this as a server-only binding. For deployed environments configure the same name as a Worker secret. Never use a `VITE_` or `NEXT_PUBLIC_` prefix for this key. The Python research script still reads `.env.local`; that file does not configure this Worker binding.

Apply the new database migration after building:

```sh
node --import ./scripts/sites-env.mjs ./node_modules/wrangler/bin/wrangler.js d1 execute DB --local --config dist/server/wrangler.json --persist-to .wrangler/state --file drizzle/0002_tense_skrulls.sql
```

Live odds are re-fetched on submission; changed lines are rejected. Games are matched by scheduled date and both team abbreviations because ESPN and BALLDONTLIE IDs differ. Player stats settle only after the provider reports a final game. Live provider behavior requires verification with an entitled API key; missing credentials never substitute practice odds.

Checks: `node tools/check_domain.mjs`, `npx tsc --noEmit`, `npm run build`. `python3 tools/check_player_props.py` additionally tests a running local preview with an empty practice record and writes `/private/tmp/courtside-prop-cleanup.sql` to remove only its generated test picks afterward.

### CSV model predictions (no API key)

Real game cards now default to **Model predictions**, with **PTS**, **PR** (points + rebounds), and **PRA** (points + rebounds + assists). The panel displays projection, model-generated line, and over/under probability from `ml/data/processed/nba_prop_predictions.csv`. Users can select Over or Under on any generated PTS/PR/PRA line. Both sides use fixed **-110 Courtside paper odds**, separate from the displayed model probabilities. Existing sportsbook-backed picks remain under **Paper markets**.

`/api/model-props?gameId=<ESPN event ID>` matches CSV rows by Eastern game date, home/away orientation, and both teams' BALLDONTLIE IDs. It never assumes ESPN event IDs equal BALLDONTLIE IDs or reuses an old game's predictions. Invalid rows are excluded; unavailable matches have an empty state. Team/roster data is displayed as supplied by the CSV, without independently validating active rosters or model calibration.

Vite bundles the CSV into the server through a raw import, so no API key or runtime filesystem is needed to read model predictions. Replace the CSV and rebuild/redeploy to publish updated predictions. In development Vite reloads the imported data. The existing game board still uses ESPN to supply matchups. The model integration does not rerun or alter the Python training pipeline.

Model picks share the live-mode paper bankroll and appear in history and the Social feed. The server verifies the current CSV line and pregame status, reserves stakes atomically, and prevents repeat picks for the same player/model market/game. Snapshots preserve the original line and model probabilities. Final ESPN box scores settle PTS, PTS+REB, and PTS+REB+AST, including overtime. Exact ties push, cancelled games and explicitly confirmed DNPs void, and missing/ambiguous players or stats remain pending. Player matching requires a unique normalized full name within the recorded home/away team; provider IDs are not treated as ESPN athlete IDs. No BALLDONTLIE key is needed for model pick submission or ESPN settlement.

### Shared single/parlay slip

There is one slip for all game lines, generated model props, and available sportsbook player props. One selection submits a single through its existing endpoint; 2–6 selections submit a parlay. Selecting the same side again removes it; selecting the opposite side replaces it. The API independently rejects duplicate or opposite sides for the same game/player/stat, including PTS versus sportsbook points. Same-game combinations are allowed with explicitly labeled multiplied paper odds; correlations are not priced. Model legs retain -110 odds and immutable prediction snapshots, and settle against ESPN player statistics. Pushes/voids remove a leg and recalculate the return.
