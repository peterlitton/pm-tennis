(() => {
  "use strict";

  const rowsEl = document.getElementById("rows");
  const liveCountEl = document.getElementById("live-count");
  const upcomingCountEl = document.getElementById("upcoming-count");
  const clockEl = document.getElementById("clock");
  const apiTennisAgeEl = document.getElementById("api-tennis-age");
  const apiTennisDotEl = document.getElementById("api-tennis-dot");
  const polymarketAgeEl = document.getElementById("polymarket-age");
  const polymarketDotEl = document.getElementById("polymarket-dot");
  const uptimeValueEl = document.getElementById("uptime-value");

  // Liveness color thresholds (Design Notes §8). Initial guesses; TBD
  // after first session of use.
  const API_TENNIS_YELLOW_MS = 30 * 1000;
  const API_TENNIS_RED_MS = 90 * 1000;
  // Polymarket REST-direct mode polls every 15s (Step 3.2-fix). Earlier
  // 10s/30s thresholds were calibrated for the WS-based plan where
  // updates arrived sub-second. With 15s polling, the counter sits in
  // [0, 15s] on a healthy connection — green threshold needs a one-poll
  // miss before yellow, two extra missed polls before red.
  const POLYMARKET_YELLOW_MS = 20 * 1000;
  const POLYMARKET_RED_MS = 45 * 1000;

  // Latest source timestamps from the most recent WS/REST snapshot.
  // These are what the liveness counters tick against, NOT the
  // backend-to-frontend snapshot cadence.
  let sourceTimestamps = {api_tennis: null, polymarket: null};

  // v0.6.11: process start time (epoch ms). Updated on every snapshot
  // from snapshot.process_started_ms. Used to render the uptime badge.
  // A drop in uptime indicates the backend process restarted — either
  // a deploy (expected) or the WS watchdog auto-restart (investigate).
  let processStartedMs = null;

  // ---------- clock ----------
  function tickClock() {
    const d = new Date();
    let h = d.getHours();
    const m = String(d.getMinutes()).padStart(2, "0");
    const s = String(d.getSeconds()).padStart(2, "0");
    const ampm = h >= 12 ? "pm" : "am";
    h = h % 12 || 12;
    clockEl.textContent = `${h}:${m}:${s} ${ampm}`;
  }
  tickClock();
  setInterval(tickClock, 1000);

  // ---------- liveness counters ----------
  function formatAge(ms) {
    if (ms == null) return "—";
    const sec = Math.max(0, Math.round(ms / 1000));
    if (sec < 60) return `${sec}s`;
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m}:${String(s).padStart(2, "0")}`;
  }

  function dotClassFor(ms, yellowMs, redMs) {
    if (ms == null) return "dot-unknown";
    if (ms >= redMs) return "dot-red";
    if (ms >= yellowMs) return "dot-yellow";
    return "dot-ok";
  }

  function tickLiveness() {
    const now = Date.now();

    const apiAge = sourceTimestamps.api_tennis == null
      ? null
      : now - sourceTimestamps.api_tennis;
    apiTennisAgeEl.textContent = formatAge(apiAge);
    apiTennisDotEl.className = "dot " + dotClassFor(apiAge, API_TENNIS_YELLOW_MS, API_TENNIS_RED_MS);

    const pmAge = sourceTimestamps.polymarket == null
      ? null
      : now - sourceTimestamps.polymarket;
    polymarketAgeEl.textContent = formatAge(pmAge);
    polymarketDotEl.className = "dot " + dotClassFor(pmAge, POLYMARKET_YELLOW_MS, POLYMARKET_RED_MS);

    // v0.6.11 uptime badge.
    if (uptimeValueEl) {
      uptimeValueEl.textContent = formatUptime(processStartedMs, now);
    }
  }
  setInterval(tickLiveness, 500);

  // v0.6.11: format uptime. Compact, glanceable units.
  //   < 60s     → "Ns"
  //   < 60m     → "Nm"
  //   < 24h     → "Nh Mm"
  //   else      → "Nd Mh"
  // Returns "—" when start time is unknown (snapshot not yet received).
  function formatUptime(startedMs, nowMs) {
    if (startedMs == null) return "—";
    const sec = Math.max(0, Math.floor((nowMs - startedMs) / 1000));
    if (sec < 60) return `${sec}s`;
    const min = Math.floor(sec / 60);
    if (min < 60) return `${min}m`;
    const hr = Math.floor(min / 60);
    const remMin = min % 60;
    if (hr < 24) return `${hr}h ${remMin}m`;
    const day = Math.floor(hr / 24);
    const remHr = hr % 24;
    return `${day}d ${remHr}h`;
  }

  // ---------- rendering ----------
  // ISO-3 → ISO-2 lookup. 108 codes covering all ATP/WTA player
  // countries observed in player_metadata.csv. SVG flag assets live
  // at /static/flags/{ISO2}.svg. See Player-DB-Build-Plan-2026-05-02-v3.md.
  const ISO3_TO_ISO2 = {
    AGO: "AO", AND: "AD", ARG: "AR", ARM: "AM", AUS: "AU", AUT: "AT",
    BDI: "BI", BEL: "BE", BEN: "BJ", BFA: "BF", BGR: "BG", BIH: "BA",
    BMU: "BM", BOL: "BO", BRA: "BR", BRB: "BB", CAN: "CA", CHE: "CH",
    CHL: "CL", CHN: "CN", CIV: "CI", CMR: "CM", COL: "CO", CRI: "CR",
    CYP: "CY", CZE: "CZ", DEU: "DE", DNK: "DK", DOM: "DO", DZA: "DZ",
    ECU: "EC", EGY: "EG", ESP: "ES", EST: "EE", FIN: "FI", FJI: "FJ",
    FRA: "FR", GBR: "GB", GEO: "GE", GHA: "GH", GLP: "GP", GRC: "GR",
    GTM: "GT", HKG: "HK", HRV: "HR", HUN: "HU", IDN: "ID", IND: "IN",
    IRL: "IE", IRN: "IR", ISR: "IL", ITA: "IT", JAM: "JM", JOR: "JO",
    JPN: "JP", KAZ: "KZ", KEN: "KE", KOR: "KR", KWT: "KW", LBN: "LB",
    LIE: "LI", LTU: "LT", LUX: "LU", LVA: "LV", MAR: "MA", MCO: "MC",
    MDA: "MD", MEX: "MX", MKD: "MK", MLT: "MT", MNE: "ME", MNP: "MP",
    MYS: "MY", NCL: "NC", NIC: "NI", NLD: "NL", NOR: "NO", NZL: "NZ",
    PAK: "PK", PER: "PE", PHL: "PH", POL: "PL", PRI: "PR", PRT: "PT",
    PRY: "PY", ROU: "RO", SAU: "SA", SEN: "SN", SGP: "SG", SLV: "SV",
    SRB: "RS", SVK: "SK", SVN: "SI", SWE: "SE", SYR: "SY", THA: "TH",
    TUN: "TN", TUR: "TR", TWN: "TW", UKR: "UA", URY: "UY", USA: "US",
    UZB: "UZ", VEN: "VE", VNM: "VN", XKX: "XK", ZAF: "ZA", ZWE: "ZW",
  };

  function flagSvg(iso3) {
    // Render a flat SVG flag from a bundled asset. ISO-3 → ISO-2,
    // emit <img> pointing to /static/flags/{ISO2}.svg. Browser caches
    // them after first hit on each flag, so subsequent rows are free.
    //
    // Falls back to placeholder span when:
    //   - iso3 is null/empty (Russian/Belarusian "World" players, brand-new
    //     players not yet in player_metadata.csv)
    //   - iso3 isn't in the ISO3_TO_ISO2 lookup (unknown code)
    if (!iso3) {
      return `<span class="flag flag-placeholder" aria-label="flag"></span>`;
    }
    const iso2 = ISO3_TO_ISO2[iso3];
    if (!iso2) {
      return `<span class="flag flag-placeholder" aria-label="${iso3}"></span>`;
    }
    return `<img src="/static/flags/${iso2}.svg" class="flag" alt="${iso3}" />`;
  }

  const TENNIS_BALL = `
    <svg class="ball" viewBox="0 0 48 48" aria-label="serving">
      <circle cx="24" cy="24" r="22" fill="url(#tennisBallGradient)"/>
      <path d="M 4 10 C 16 22, 32 22, 44 10" stroke="#FFFFFF" stroke-width="1.8" fill="none" opacity="0.9"/>
      <path d="M 4 38 C 16 26, 32 26, 44 38" stroke="#FFFFFF" stroke-width="1.8" fill="none" opacity="0.9"/>
    </svg>`;

  // 2026-05-01: render p1 and p2 set scores with no separator between sets
  // (was " - " hyphen, operator found confusing). Bold the winning side's
  // score per completed set. A set is complete when the higher score is
  // ≥6 with 2-game lead, OR 7-5, OR 7-6 with a tiebreak. Mid-set scores
  // (e.g., 5-4) get no bold — neither side has won the set yet.
  function isSetComplete(a, b) {
    if (a == null || b == null) return false;
    const hi = Math.max(a, b);
    const lo = Math.min(a, b);
    if (hi >= 6 && hi - lo >= 2) return true;  // 6-0..6-4, 7-5, 8-6, etc.
    if (hi === 7 && lo === 6) return true;     // 7-6 tiebreak set
    return false;
  }

  function setCellHtml(score, isWinner) {
    if (score == null || score.games == null) return "";
    const cls = isWinner ? "set-winner" : "";
    if (score.tiebreak != null) {
      return `<span class="${cls}">${score.games}<sup class="tb">${score.tiebreak}</sup></span>`;
    }
    return `<span class="${cls}">${score.games}</span>`;
  }

  function setsRowHtml(mySets, otherSets) {
    if (!mySets || mySets.length === 0) return "—";
    const parts = [];
    for (let i = 0; i < mySets.length; i++) {
      const me = mySets[i];
      const other = otherSets ? otherSets[i] : null;
      const complete = other != null && isSetComplete(me?.games, other?.games);
      const isWinner = complete && me.games > other.games;
      parts.push(setCellHtml(me, isWinner));
    }
    return parts.join(" ");
  }

  function startTimeHtml(iso) {
    if (!iso) return "—";
    const d = new Date(iso);
    let h = d.getHours();
    const m = String(d.getMinutes()).padStart(2, "0");
    const ampm = h >= 12 ? "pm" : "am";
    h = h % 12 || 12;
    return `${h}:${m} ${ampm}`;
  }

  function priceHtml(cents) {
    return cents == null ? "—" : `${cents}¢`;
  }

  // Step 4.2: momentum delta-display rendering. v2.0.0 spec:
  //   none      — no display (no data, or both below noise floor)
  //   contested — small grey "=" marker on each side, no pill
  //               (preserves the "computed-but-balanced" signal vs
  //                "no data at all" — they look different on the dashboard)
  //   leader    — single pill on leader's side: arrow + delta magnitude
  //               (e.g., "↗ +5"). Trailing player has nothing.
  // Thresholds rescaled to match v2.0.0's time-decay-adjusted score range
  // (decay roughly halves the unweighted maximum, so previous 4/3 thresholds
  //  would fire less often. 2/2 preserves comparable behavior).
  //
  // Step 4.2 v2 (v2.1.0) addition: trend arrow direction reflects how the
  // leader's lead is changing over the most recent 6 points.
  //   "extending" → ↗  the lead is growing
  //   "holding"   → →  the lead is stable (or insufficient history yet)
  //   "closing"   → ↘  the lead is shrinking
  // Backend computes via momentum.compute_trend() and sets it on
  // match.momentum_trend. Frontend renders the corresponding glyph.
  const MOMENTUM_NOISE_FLOOR = 2;
  const MOMENTUM_DIFF_THRESHOLD = 2;

  function momentumState(p1, p2) {
    if (p1 == null || p2 == null) return "none";
    if (Math.max(p1, p2) < MOMENTUM_NOISE_FLOOR) return "none";
    if (Math.abs(p1 - p2) < MOMENTUM_DIFF_THRESHOLD) return "contested";
    return "leader";
  }

  // v2.1.0: three arrow glyphs by trend direction. Each is a 12×12 SVG
  // sized to fit the existing .momentum-arrow CSS (11px square, currentColor
  // stroke). Same style as the v2.0.0 arrow — pill background and font
  // identical, only the arrow direction (or absence) varies.
  //
  // 2026-05-03 update: HOLDING renders no arrow. Bare "+N" pill. Operator
  // economy — only "active" trends (extending / closing) get visual weight.
  // Implied direction = stable.
  const MOMENTUM_ARROW_EXTENDING = `<svg class="momentum-arrow" viewBox="0 0 12 12" aria-hidden="true">
      <path d="M 2 9 L 8 3" stroke-width="2" fill="none" stroke-linecap="round"/>
      <path d="M 6 3 L 8 3 L 8 5" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>`;

  const MOMENTUM_ARROW_CLOSING = `<svg class="momentum-arrow" viewBox="0 0 12 12" aria-hidden="true">
      <path d="M 2 3 L 8 9" stroke-width="2" fill="none" stroke-linecap="round"/>
      <path d="M 6 9 L 8 9 L 8 7" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>`;

  // Backwards-compat alias. Default = extending (matches v2.0.0's
  // always-up-arrow rendering for any older code path that references
  // the old name).
  const MOMENTUM_ARROW = MOMENTUM_ARROW_EXTENDING;

  function momentumArrowFor(trend) {
    if (trend === "extending") return MOMENTUM_ARROW_EXTENDING;
    if (trend === "closing") return MOMENTUM_ARROW_CLOSING;
    // "holding", null, undefined, or any unknown value → no arrow.
    // The pill renders bare "+N"; stable lead is implied.
    return "";
  }

  // v2.0.0: single-leader pill shows DELTA magnitude (lead size), not
  // each player's raw score. The lead is what's actionable on the
  // dashboard; absolute scores are still computed for state determination
  // but aren't displayed.
  // v2.1.0: arrow direction reflects momentum_trend.
  // v2.1.0 update (2026-05-03): holding renders without an arrow.
  function momentumLeaderPillHtml(delta, trend) {
    const arrow = momentumArrowFor(trend);
    return `<span class="momentum-pill leader">${arrow}<span class="momentum-value">+${delta}</span></span>`;
  }

  // Contested marker: small grey "=" sign, no pill background.
  // Distinguishes "computed, no leader" from "no data."
  function momentumContestedMarkerHtml() {
    return `<span class="momentum-marker-contested">=</span>`;
  }

  function momentumPills(m) {
    const state = momentumState(m.p1_momentum, m.p2_momentum);
    if (state === "none") {
      return { p1: "", p2: "" };
    }
    if (state === "contested") {
      return {
        p1: momentumContestedMarkerHtml(),
        p2: momentumContestedMarkerHtml(),
      };
    }
    // state === "leader" — single pill on leader's side, magnitude + trend arrow
    const delta = Math.abs(m.p1_momentum - m.p2_momentum);
    const p1Leads = m.p1_momentum > m.p2_momentum;
    const trend = m.momentum_trend;  // "extending" | "holding" | "closing" | null
    return {
      p1: p1Leads ? momentumLeaderPillHtml(delta, trend) : "",
      p2: p1Leads ? "" : momentumLeaderPillHtml(delta, trend),
    };
  }

  // Step 5: pre-match edge badge.
  // Fair value (Sackmann pre_pct) vs current Polymarket price (cents).
  // Edge = pre_pct - price_cents. Positive edge = the dashboard thinks
  // this player is underpriced; we'd back them. Negative edge = overpriced;
  // the market already accounts for what Sackmann would say.
  // Show the badge on the row of the player with positive edge above the
  // small threshold. Three color tiers by magnitude. None below threshold.
  const EDGE_THRESHOLD_SMALL = 3;
  const EDGE_THRESHOLD_MEDIUM = 7;
  const EDGE_THRESHOLD_LARGE = 15;

  function edgeBadgeHtml(m, side) {
    // side is 1 or 2. We compute the edge for that side and render only
    // if it's the side with positive edge above threshold.
    const prePct = side === 1 ? m.p1_pre_pct : m.p2_pre_pct;
    const priceCents = side === 1 ? m.p1_price_cents : m.p2_price_cents;
    if (prePct == null || priceCents == null) return "";

    const edge = prePct - priceCents;
    if (edge < EDGE_THRESHOLD_SMALL) return "";

    let tier = "small";
    if (edge >= EDGE_THRESHOLD_LARGE) tier = "large";
    else if (edge >= EDGE_THRESHOLD_MEDIUM) tier = "medium";

    // Pre-match prefix per mockup: "PRE" before the value
    return `<span class="edge-badge edge-${tier}"><span class="edge-pre">PRE</span><span class="edge-value">${edge}</span></span>`;
  }

  // Renders only on upcoming matches per Step 5 scope. Live edge badge
  // is Step 6 (parked).
  function preMatchEdgeBadges(m) {
    if (m.status !== "upcoming") return { p1: "", p2: "" };
    return {
      p1: edgeBadgeHtml(m, 1),
      p2: edgeBadgeHtml(m, 2),
    };
  }

  // Ranking display next to player names. Small grey number before flag.
  // Renders whenever rank data is present (live OR upcoming).
  // Step 5.1: ALWAYS renders the slot for layout stability — uses "—" as
  // placeholder when no rank data, matching the existing placeholder
  // convention from .score-cell. Without this, flex layout shifts
  // horizontally between rows where one player has rank and the other
  // doesn't, and between rows with both/neither/one ranked.
  function rankHtml(rank) {
    if (rank == null) return `<span class="player-rank player-rank-empty">—</span>`;
    return `<span class="player-rank">${rank}</span>`;
  }

  // Step 9-A C2 (2026-05-02): position sub-row. When the operator has an
  // open position on either side of a match, render a second row beneath
  // the match showing position state.
  //
  // Data: m.p1_position / m.p2_position from C1 v2 (server-side join via
  // player-name overlap). Each is null if no position on that side, else
  // {net_shares, cost_cents, cash_value_cents, realized_cents, update_time}.
  //
  // Computed client-side from the position fields and current match data:
  //   entry_price_cents = round(cost_cents / net_shares)
  //   pnl_cents = cash_value_cents - cost_cents
  //   pnl_pct = pnl_cents / cost_cents * 100
  //
  // Held-time derived from update_time (rough — Polymarket's update_time
  // reflects last position change, not original entry, so this is a
  // conservative "minimum time held" estimate). If update_time absent,
  // omit the held-time element.
  function pricePillHtml(cents) {
    if (cents == null) return `<span class="price-pill">—</span>`;
    const txt = cents >= 100 ? `$${(cents / 100).toFixed(2)}` : `${cents}¢`;
    return `<span class="price-pill">${txt}</span>`;
  }

  function pnlDollarHtml(cents) {
    const sign = cents >= 0 ? "+" : "−";
    const abs = Math.abs(cents) / 100;
    return `${sign}$${abs.toFixed(2)}`;
  }

  function pnlPctHtml(pct) {
    if (!isFinite(pct)) return "";
    const sign = pct >= 0 ? "+" : "−";
    const abs = Math.abs(pct);
    return `${sign}${abs.toFixed(1)}%`;
  }

  function heldTimeHtml(updateTimeIso) {
    if (!updateTimeIso) return "";
    try {
      const updated = new Date(updateTimeIso);
      const now = new Date();
      const elapsedMs = now - updated;
      if (elapsedMs < 0) return "";
      const minutes = Math.floor(elapsedMs / 60000);
      if (minutes < 1) return "<1m";
      if (minutes < 60) return `${minutes}m`;
      const hours = Math.floor(minutes / 60);
      const remMin = minutes % 60;
      return remMin > 0 ? `${hours}h ${remMin}m` : `${hours}h`;
    } catch (e) {
      return "";
    }
  }

  // Render a single position sub-row given the position object, the side
  // (1 or 2 for diagnostic clarity), the player name, and the current
  // price for that side (used for entry → now display).
  //
  // 2026-05-02 abs(net_shares) fix: Polymarket's API returns net_shares
  // as negative when the order-book routed the buy through the NO side
  // (SHORT-routing). From the operator's perspective there is no SHORT —
  // they clicked "Buy [Player]" and got a LONG position. The cost_cents
  // already reflects what the operator paid (e.g. 7691¢ = $76.91 for
  // 100 shares at 76.91¢ per share). Same convention as the v0.5
  // trade-data-semantics fix on the trading page parser.
  // v0.7.0 (PM-D.4 unfilled-orders feature): rewrite for v5 vocabulary.
  //
  // v0.8.2 (PM-D5): derive the "now" price for an OPEN row from the
  // OPPOSING player's displayed market price.
  //
  //   now_for_held_player = 100 - opposing_displayed_cents
  //
  // This matches the price the operator would realize on exit:
  // exiting a long position on Player A means selling at whatever the
  // market is paying on Player B's token. Operator-locked rule,
  // validated against the iPhone Polymarket app. See
  // PM-D5-Now-Price-From-Opposing-Side.md.
  //
  // Null-safe: when the opposing side has no displayed price (rare,
  // transient — one token's book hasn't populated), return null so
  // pricePillHtml renders "—" rather than 100¢.
  function deriveNowCents(opposingCents) {
    if (opposingCents == null) return null;
    return 100 - opposingCents;
  }

  // OPEN row format: NUM sh @ ENTRY → now CURRENT  $INVEST  PNL  PCT  AGE
  //
  // The player name is NO LONGER on this row. The match row above
  // carries the bold player name (.player-name.invested), which is
  // sufficient to anchor "this position belongs to that player." Same
  // logic as for COND rows when an OPEN sits above on the same side.
  //
  // Other v5 vocabulary changes from production:
  //   - "entry" word dropped
  //   - bullet separators (·) dropped between tokens
  //   - "at" replaced by "@" symbol
  //   - "ago" dropped from age (now bare duration)
  //
  // 2026-05-02 abs(net_shares) fix preserved: Polymarket's API returns
  // net_shares as negative when the order-book routed the buy through
  // the NO side (SHORT-routing). From the operator's perspective there
  // is no SHORT — they clicked "Buy [Player]" and got a LONG position.
  function positionSubRow(position, sideName, currentPriceCents) {
    if (!position) return "";
    const rawShares = position.net_shares;
    const cost = position.cost_cents;
    const cashValue = position.cash_value_cents;
    if (rawShares == null || rawShares === 0 || cost == null || cashValue == null) return "";

    const shares = Math.abs(rawShares);
    const entryCents = Math.round(cost / shares);
    const pnlCents = cashValue - cost;
    const pnlPct = (pnlCents / cost) * 100;
    const isProfit = pnlCents >= 0;
    const pnlClass = isProfit ? "position-pnl" : "position-pnl loss";

    const heldStr = heldTimeHtml(position.update_time);
    const heldHtml = heldStr ? `<span class="position-time">${heldStr}</span>` : "";

    // v0.8.1: investment field, no label, between current price and pnl.
    // cost is in cents (cost_cents), display in whole dollars (operator
    // only places investments in round dollar amounts so .00 is noise).
    const investDollars = Math.round(cost / 100);

    return `
      <div class="position-row ${isProfit ? "profit" : "loss"}">
        <span class="position-label">OPEN</span>
        <span class="position-detail">${shares} sh <span class="at">@</span> ${pricePillHtml(entryCents)} <span class="arrow">→</span> <span class="now">now</span> ${pricePillHtml(currentPriceCents)}</span>
        <span class="position-investment">$${investDollars}</span>
        <span class="${pnlClass}">${pnlDollarHtml(pnlCents)}</span>
        <span class="position-pct ${isProfit ? "" : "loss"}">${pnlPctHtml(pnlPct)}</span>
        ${heldHtml}
      </div>`;
  }

  // v0.7.3: B/S badge dropped. Per docs/trade-data-semantics.md, the
  // operator never places SELL orders — the iPhone app only offers
  // "Buy [Player]" for retail users. Every COND row is therefore
  // unambiguously a buy from the operator's perspective. The B-only
  // badge was informationally redundant (every row was identical), so
  // we remove it. The COND label + player name + shares + price reads
  // cleanly as a buy order without it.
  //
  // Each resting limit order on a given side becomes one .order-row.
  // Multiple orders on the same side stack as siblings. Caller passes
  // hasOpenAbove=true when an OPEN row sits above this COND row on the
  // same side; that suppresses the player name (the OPEN row already
  // anchors which player). When hasOpenAbove=false (COND-only on a
  // player with no current position), the player name renders on the
  // first row and on every row in a stack.
  //
  // Ordering: caller passes orders pre-sorted closest-to-fill first
  // (resolver does this server-side via _sort_orders_closest_to_fill).
  //
  // Partial fills: when cum_quantity > 0 the leading "NUM sh" is
  // replaced by a progress display "FILLED [bar] of TOTAL". Otherwise
  // the original quantity reads as "NUM sh".
  function orderRowHtml(order, sideName, hasOpenAbove) {
    const priceCents = order.price_cents;
    const total = order.quantity;
    const filled = order.cum_quantity || 0;
    const isPartialFill = filled > 0;

    let qtyBlock;
    if (isPartialFill) {
      const pct = total > 0 ? Math.max(0, Math.min(100, (filled / total) * 100)) : 0;
      qtyBlock = `<span class="order-progress"><span class="filled">${filled}</span><span class="order-fill-bar"><span style="width:${pct.toFixed(0)}%"></span></span><span class="total">of ${total}</span></span>`;
    } else {
      qtyBlock = `${total} sh`;
    }

    const nameBlock = hasOpenAbove ? "" : `<strong>${sideName}</strong>`;
    const ageStr = orderAgeHtml(order.insert_time);
    const ageHtml = ageStr ? `<span class="order-time">${ageStr}</span>` : "";

    // B/S badge — derived from order.intent.
    // B = buy-to-open (acquiring shares). S = sell-to-close (exiting
    // shares the operator already holds). The LONG/SHORT routing
    // distinction in intent is invisible to the operator (per
    // docs/trade-data-semantics.md): both BUY_LONG and BUY_SHORT are
    // operationally a buy. Likewise SELL_LONG and SELL_SHORT are both
    // sells. The badge surfaces the operator-perspective direction.
    const intent = String(order.intent || "");
    const sideBadge = intent.includes("SELL") ? "S" : "B";
    const sideHtml = `<span class="order-side">${sideBadge}</span>`;

    return `
      <div class="order-row">
        <span class="order-label">COND</span>
        ${sideHtml}
        <span class="order-detail">${nameBlock}${qtyBlock} <span class="at">@</span> ${pricePillHtml(priceCents)}</span>
        ${ageHtml}
      </div>`;
  }

  function orderSubRows(orders, sideName, hasOpenAbove) {
    if (!orders || orders.length === 0) return "";
    return orders.map(o => orderRowHtml(o, sideName, hasOpenAbove)).join("");
  }

  // Render order-age as a bare duration (no "ago" suffix per v5).
  // Same time math as heldTimeHtml but uses insert_time and emits
  // without the "ago" qualifier.
  function orderAgeHtml(insertTimeIso) {
    if (!insertTimeIso) return "";
    try {
      const insertedMs = Date.parse(insertTimeIso);
      if (!isFinite(insertedMs)) return "";
      const ageMs = Date.now() - insertedMs;
      if (ageMs < 0) return "";
      const ageMin = Math.floor(ageMs / 60000);
      if (ageMin < 1) return "<1m";
      if (ageMin < 60) return `${ageMin}m`;
      const ageHr = Math.floor(ageMin / 60);
      if (ageHr < 24) return `${ageHr}h`;
      const ageDay = Math.floor(ageHr / 24);
      return `${ageDay}d`;
    } catch (_) {
      return "";
    }
  }

  function renderRow(m) {
    const isLive = m.status === "live";
    const p1Serves = m.server === 1;
    const p2Serves = m.server === 2;
    const pills = isLive ? momentumPills(m) : { p1: "", p2: "" };
    const edges = preMatchEdgeBadges(m);

    // v0.7.0 v5: bold the player name when that player has an OPEN
    // position OR a COND order on this match. The .invested class is
    // styled in dashboard.css. Default state is regular weight.
    const p1Orders = m.p1_orders || [];
    const p2Orders = m.p2_orders || [];
    const p1Invested = !!m.p1_position || p1Orders.length > 0;
    const p2Invested = !!m.p2_position || p2Orders.length > 0;
    const p1NameClass = p1Invested ? "player-name invested" : "player-name";
    const p2NameClass = p2Invested ? "player-name invested" : "player-name";

    const statusBlock = isLive
      ? `<div class="status-live-line"><span class="dot"></span><span class="status-text">${m.set_label || ""}</span></div>
         <div class="status-meta">${m.venue} · ${m.tour} · ${m.round}</div>`
      : `<div class="status-text">${startTimeHtml(m.start_time)}</div>
         <div class="status-meta">${m.venue} · ${m.tour} · ${m.round}</div>`;

    const matchBlock = `
      <div class="player">
        ${rankHtml(m.p1_rank)}
        ${flagSvg(m.p1.country_iso3)}
        <span class="${p1NameClass}">${m.p1.name}</span>
        ${pills.p1}
        ${p1Serves ? TENNIS_BALL : ""}
      </div>
      <div class="player">
        ${rankHtml(m.p2_rank)}
        ${flagSvg(m.p2.country_iso3)}
        <span class="${p2NameClass}">${m.p2.name}</span>
        ${pills.p2}
        ${p2Serves ? TENNIS_BALL : ""}
      </div>`;

    const setsBlock = isLive
      ? `<div>${setsRowHtml(m.p1_sets, m.p2_sets)}</div><div>${setsRowHtml(m.p2_sets, m.p1_sets)}</div>`
      : `<div class="placeholder">—</div><div class="placeholder">—</div>`;

    const gameBlock = isLive
      ? `<div class="${p1Serves ? "serving" : ""}">${m.p1_game ?? ""}</div>
         <div class="${p2Serves ? "serving" : ""}">${m.p2_game ?? ""}</div>`
      : `<div class="placeholder">—</div><div class="placeholder">—</div>`;

    const priceBlock = `<div>${edges.p1}${priceHtml(m.p1_price_cents)}</div><div>${edges.p2}${priceHtml(m.p2_price_cents)}</div>`;

    // v0.7.0 v5 sub-row rendering. Order:
    //   1. Match row (above)
    //   2. P1 OPEN (if position exists)
    //   3. P1 COND rows (if any orders) — name suppressed if P1 OPEN above
    //   4. P2 OPEN (if position exists)
    //   5. P2 COND rows (if any orders) — name suppressed if P2 OPEN above
    //
    // All wrapped in a .match-group div so the heavier between-match
    // separator can be applied via CSS without per-row computation.
    //
    // v0.8.2 (PM-D5): the "now" price on the OPEN row is derived from
    // the OPPOSING player's displayed market price:
    //   now_for_held_player = 100 - opposing_displayed_cents
    // This matches the price the operator would realize on exit, since
    // exiting a long position on Player A means selling at whatever the
    // market is paying on Player B's token. Operator-locked rule,
    // validated against iPhone Polymarket app. See
    // PM-D5-Now-Price-From-Opposing-Side.md. The match-row per-side
    // prices remain source-side (m.p{1,2}_price_cents) — only the OPEN
    // row's "now" uses the opposing-side derivation. Null-safe: when
    // the opposing side has no displayed price, derive returns null
    // and pricePillHtml downstream renders "—".
    const p1NowCents = deriveNowCents(m.p2_price_cents);
    const p2NowCents = deriveNowCents(m.p1_price_cents);
    const p1Pos = positionSubRow(m.p1_position, m.p1.name, p1NowCents);
    const p2Pos = positionSubRow(m.p2_position, m.p2.name, p2NowCents);
    const p1OrdersHtml = orderSubRows(p1Orders, m.p1.name, !!m.p1_position);
    const p2OrdersHtml = orderSubRows(p2Orders, m.p2.name, !!m.p2_position);
    const hasSubRows = !!(p1Pos || p2Pos || p1OrdersHtml || p2OrdersHtml);

    return `
      <div class="match-group">
        <div class="row ${isLive ? "" : "upcoming"} ${hasSubRows ? "has-position" : ""}">
          <div>${statusBlock}</div>
          <div>${matchBlock}</div>
          <div class="score-cell">${setsBlock}</div>
          <div class="score-cell">${gameBlock}</div>
          <div class="price-cell">${priceBlock}</div>
        </div>${p1Pos}${p1OrdersHtml}${p2Pos}${p2OrdersHtml}
      </div>`;
  }

  // v0.6.10: indicator legend.
  //
  // Renders an operator-facing reference of the conditions / parameters
  // driving each indicator on the dashboard. Source of truth for "what
  // does +5 momentum mean today" — and the place to read parameter names
  // (window_points, noise_floor, diff_threshold, trend_lookback,
  // trend_threshold, weight_*) when directing tuning.
  //
  // Content is BACKEND-DRIVEN via the snapshot's momentum_indicator block.
  // When MI_VERSION or any parameter changes in src/momentum.py, the legend
  // updates on next snapshot push without a frontend redeploy.
  //
  // Other indicators (edge badge, ranking, surface) are stable and don't
  // yet have parameter-set versioning. Their lines are static text.
  // Add MI-style versioning to a given indicator when operator wants to
  // start tuning its parameters.
  const legendBodyEl = document.getElementById("legend-body");

  function renderLegend(momentumIndicator) {
    if (!legendBodyEl) return;

    let momentumBlock = "";
    if (momentumIndicator && momentumIndicator.parameters) {
      const p = momentumIndicator.parameters;
      const v = momentumIndicator.version || "MI.?";
      // Param rows. Parameter names match the constants in src/momentum.py
      // — operator can reference any of them by name when directing tuning.
      const params = [
        ["window_points",   p.window_points,   "rolling window of points scored over"],
        ["weight_serve",    p.weight_serve,    "weight for points won on own serve"],
        ["weight_return",   p.weight_return,   "weight for points won on opponent's serve"],
        ["weight_hold",     p.weight_hold,     "weight for winning the entire game on serve"],
        ["weight_break",    p.weight_break,    "weight for breaking opponent's serve"],
        ["noise_floor",     p.noise_floor,     "min max(p1,p2) score before any signal renders"],
        ["diff_threshold",  p.diff_threshold,  "min |p1−p2| to render a leader pill (else contested)"],
        ["trend_lookback",  p.trend_lookback,  "points-back to compare current delta against"],
        ["trend_threshold", p.trend_threshold, "min |delta change| to render extending/closing"],
        ["decay",           p.decay,           "decay function applied to point weights over the window"],
      ];
      const rows = params.map(([name, value, desc]) =>
        `<tr><td class="legend-param">${name}</td><td class="legend-value">${value}</td><td class="legend-desc">${desc}</td></tr>`
      ).join("");
      momentumBlock = `
        <div class="legend-section">
          <h4 class="legend-title">Momentum indicator <span class="legend-mi-version">${v}</span></h4>
          <p class="legend-explainer">
            Pill on the leader's side: <span class="legend-inline-arrow">↗</span> <strong>+N</strong> = lead extending,
            <strong>+N</strong> alone = lead holding, <span class="legend-inline-arrow">↘</span> <strong>+N</strong> = lead closing.
            "<strong>=</strong>" on both sides = contested. No display = below noise floor or no data.
          </p>
          <table class="legend-table">
            <thead><tr><th>Parameter</th><th>Value</th><th>Meaning</th></tr></thead>
            <tbody>${rows}</tbody>
          </table>
          ${p.notes ? `<p class="legend-notes">${p.notes}</p>` : ""}
        </div>
      `;
    }

    // Static content for indicators that don't yet have parameter versioning.
    const staticBlock = `
      <div class="legend-section">
        <h4 class="legend-title">Other indicators</h4>
        <table class="legend-table">
          <thead><tr><th>Indicator</th><th>What it shows</th></tr></thead>
          <tbody>
            <tr><td class="legend-param">Edge badge</td><td class="legend-desc">Pre-match: green/red badge when |Sackmann pre_pct − Polymarket price| crosses the operator-threshold tiers (small/medium/large).</td></tr>
            <tr><td class="legend-param">Rank</td><td class="legend-desc">Player's current ATP/WTA ranking (left of name).</td></tr>
            <tr><td class="legend-param">Country flag</td><td class="legend-desc">Player's country (right of name; hidden on mobile).</td></tr>
            <tr><td class="legend-param">Player name (bold)</td><td class="legend-desc">Bold when you have an open position OR resting limit order on that player; regular weight otherwise.</td></tr>
            <tr><td class="legend-param">OPEN row</td><td class="legend-desc">Your open position on this match. Shows shares held @ entry price → current "now" price (derived as 100 − opposing player's match-row price; this is your effective exit value), total invested ($), $ P&amp;L, % P&amp;L, and time since position opened. Green left border = profit; red = loss.</td></tr>
            <tr><td class="legend-param">COND row</td><td class="legend-desc">Resting limit buy order(s) on Polymarket. Shows shares @ target price, and time since order placed. Operator-perspective price (matches the iPhone receipt's odds %). Multiple orders stack closest-to-fill first; orders disappear when fully filled or cancelled (within ~30s).</td></tr>
            <tr><td class="legend-param">Progress bar</td><td class="legend-desc">On COND rows when an order is partially filled: shows <code>FILLED · bar · of TOTAL</code>. Plain <code>NUM sh</code> when nothing has filled yet.</td></tr>
            <tr><td class="legend-param">Time on OPEN</td><td class="legend-desc">Time since position opened (first fill).</td></tr>
            <tr><td class="legend-param">Time on COND</td><td class="legend-desc">Time since limit order placed on Polymarket.</td></tr>
            <tr><td class="legend-param">Open position</td><td class="legend-desc">Cents-amount pill on the side the operator has shares on; updates as price moves.</td></tr>
            <tr><td class="legend-param">Liveness dots</td><td class="legend-desc">Header: green = fresh frame, red = stale. API-Tennis &lt;5s = green; Polymarket &lt;5s = green.</td></tr>
            <tr><td class="legend-param">Uptime</td><td class="legend-desc">Time since the worker process last started. A drop you didn't expect signals a watchdog auto-restart — check logs.</td></tr>
          </tbody>
        </table>
      </div>
    `;

    legendBodyEl.innerHTML = momentumBlock + staticBlock;
  }

  function applySnapshot(snapshot) {
    const matches = snapshot.matches || [];
    sourceTimestamps = snapshot.source_timestamps || sourceTimestamps;
    // v0.6.11: capture process start time for the uptime badge. Stable
    // across a single process; changes only when the backend restarts.
    if (typeof snapshot.process_started_ms === "number") {
      processStartedMs = snapshot.process_started_ms;
    }

    // v0.6.10: render the operator-facing indicator legend from the
    // snapshot's momentum_indicator block. Re-rendering on every snapshot
    // is overkill but cheap (the block changes only when MI version bumps,
    // which is rare). Single-source-of-truth from backend.
    renderLegend(snapshot.momentum_indicator);

    // Step 3.6: filter out matches with no Polymarket price coverage.
    // A live match with API-Tennis scores but no prices has no decision
    // value for the operator — they can't trade it. State.matches stays
    // complete on the server (preserves diagnostic data, leaves the
    // door open for a "show all matches" toggle later); the renderer
    // applies the visibility filter.
    //
    // Pass: a match must have at least one of p1_price_cents or
    // p2_price_cents non-null. This handles:
    //   - Live mapped matches: prices set (mostly both sides)
    //   - Pre-match Polymarket-listed: prices set, status upcoming
    //   - Live API-Tennis-only (e.g., ITF Charlotte, niche Challengers
    //     Polymarket doesn't cover): both null → filtered out
    const tradeable = matches.filter(
      m => m.p1_price_cents !== null || m.p2_price_cents !== null
    );

    const live = tradeable.filter(m => m.status === "live").length;
    const upcoming = tradeable.filter(m => m.status === "upcoming").length;
    // Step 9-A C2: count open positions across all matches (matches may
    // have positions on either or both sides — count each position).
    const positions = tradeable.reduce(
      (n, m) => n + (m.p1_position ? 1 : 0) + (m.p2_position ? 1 : 0),
      0
    );
    liveCountEl.textContent = `${live} live`;
    const counterParts = [];
    if (upcoming > 0) counterParts.push(`+ ${upcoming} upcoming`);
    if (positions > 0) counterParts.push(`${positions} open position${positions === 1 ? "" : "s"}`);
    upcomingCountEl.textContent = counterParts.join(" · ");
    rowsEl.innerHTML = tradeable.map(renderRow).join("");

    // Recompute liveness immediately so the counter doesn't lag a half-second.
    tickLiveness();
  }

  // ---------- websocket ----------
  let ws;
  let reconnectDelayMs = 1000;

  function connect() {
    const proto = location.protocol === "https:" ? "wss:" : "ws:";
    ws = new WebSocket(`${proto}//${location.host}/ws/matches`);

    ws.addEventListener("message", evt => {
      try {
        const snapshot = JSON.parse(evt.data);
        applySnapshot(snapshot);
        reconnectDelayMs = 1000;
      } catch (e) {
        console.error("bad ws frame", e);
      }
    });

    ws.addEventListener("close", () => {
      setTimeout(connect, reconnectDelayMs);
      reconnectDelayMs = Math.min(reconnectDelayMs * 2, 15000);
    });

    ws.addEventListener("error", () => {
      try { ws.close(); } catch (_) { /* ignore */ }
    });
  }

  // Hydrate once via REST so the page has data before the first WS frame.
  fetch("/api/matches")
    .then(r => r.json())
    .then(applySnapshot)
    .catch(e => console.error("initial fetch failed", e))
    .finally(connect);
})();
