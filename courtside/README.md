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

## Historical NBA data / Python

The Kaggle dataset is for historical analysis, not current sportsbook odds. It has not been bulk-downloaded or inserted into the live app. The included streaming utility can download its archive and inspect all SQLite tables without loading the dataset into memory:

```sh
python3 tools/kaggle_history.py --download work/history --report work/history/inventory.json
# Or inspect an already downloaded database:
python3 tools/kaggle_history.py --database /path/to/nba.sqlite --report work/history/inventory.json
```

If Kaggle requires authentication, download through your Kaggle account and use `--database`. No credentials belong in source control.

Attribution: [Wyatt Walsh, NBA Database](https://www.kaggle.com/datasets/wyattowalsh/basketball), CC BY-SA 4.0. Preserve attribution and applicable share-alike requirements when distributing derived data. The app includes no redistributed historical records.

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
