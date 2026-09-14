/*
 * Backfill animation for "The Queue Is Not a Line".
 *
 * Plays two invented days on four of Aqua's H100 nodes in gpu_batch_exec:
 * one scheduling cycle per simulated minute, backfill_depth 5, scores from the
 * live job_sort_formula. Builds itself inside the element with id
 * "backfill-animation" and hooks into Material for MkDocs' document$ stream,
 * the same way javascripts/queue-score-explorer.js does.
 */
(function () {
  "use strict";

  window.BACKFILL_CONFIG = window.BACKFILL_CONFIG || { nodes: 4, arrivalsPerHour: 1.25, initialQueue: 8 };

// Backfill illustration engine for gpu_batch_exec on Aqua's 13 H100 nodes.
// One scheduling cycle per simulated minute (scheduler_iteration = 60 s), backfill_depth 5,
// scores from the live job_sort_formula. Workload is generated from a fixed seed. Pure logic, no DOM.
(function (root) {
  "use strict";

  // Optional page-level settings; the defaults describe all 13 H100 nodes.
  var cfg = root.BACKFILL_CONFIG || {};
  var DEPTH = 5;
  var CYCLE_MIN = 1;
  var RUN_MIN = 48 * 60;
  var ARRIVALS_PER_HOUR = cfg.arrivalsPerHour || 3.2;
  var INITIAL_QUEUE = cfg.initialQueue || 20;
  var NODES = [];
  for (var n = 0; n < (cfg.nodes || 13); n++) {
    var lanes = [];
    for (var g = 0; g < 4; g++) lanes.push(n * 4 + g);
    NODES.push({ name: "gpu1n0" + String(n + 2).padStart(2, "0"), lanes: lanes });
  }

  function mulberry32(a) {
    return function () {
      a |= 0; a = (a + 0x6d2b79f5) | 0;
      var t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function pick(rand, weighted) {
    var total = weighted.reduce(function (s, w) { return s + w[1]; }, 0), x = rand() * total;
    for (var i = 0; i < weighted.length; i++) { x -= weighted[i][1]; if (x <= 0) return weighted[i][0]; }
    return weighted[weighted.length - 1][0];
  }

  // Request shapes from the site's recipes, all gpu_id=H100, one chunk.
  var SHAPES = [
    [{ ncpus: 12, ngpus: 1, mem: 64 }, 42],
    [{ ncpus: 8, ngpus: 1, mem: 32 }, 12],
    [{ ncpus: 24, ngpus: 2, mem: 128 }, 26],
    [{ ncpus: 16, ngpus: 4, mem: 240 }, 12],
    [{ ncpus: 48, ngpus: 4, mem: 480 }, 8]
  ];
  var WALLTIMES = [[1, 5], [2, 8], [4, 12], [8, 12], [12, 14], [24, 25], [36, 8], [48, 16]];
  // Assumed fair-share factors, one per user, held fixed for the two days.
  var USER_F = [0.95, 0.9, 0.8, 0.72, 0.65, 0.6, 0.55, 0.5, 0.45, 0.42, 0.38, 0.34, 0.3, 0.26, 0.22, 0.18, 0.14, 0.1, 0.07, 0.04];

  function build(seed) {
    var rand = mulberry32(seed), jobs = [], running = [], num = 5551200;
    function makeJob(submit) {
      var shape = pick(rand, SHAPES), wallH = pick(rand, WALLTIMES);
      if (shape.ngpus === 1 && shape.ncpus === 8) wallH = pick(rand, [[1, 4], [2, 4], [4, 2]]);
      var user = Math.floor(rand() * USER_F.length);
      var frac = rand() < 0.2 ? 1 : 0.35 + rand() * 0.6;
      return {
        id: String(++num), user: user, f: USER_F[user],
        ncpus: shape.ncpus, ngpus: shape.ngpus, mem: shape.mem,
        wall: wallH * 60, run: Math.max(10, Math.round(wallH * 60 * frac)), submit: submit
      };
    }
    // Already running at minute 0: fill every GPU.
    NODES.forEach(function (node) {
      var free = node.lanes.slice();
      while (free.length) {
        var j = makeJob(0);
        while (j.ngpus > free.length) j = makeJob(0);
        var elapsed = Math.round(rand() * (j.run - 10));
        j.submit = -elapsed - Math.round(rand() * 600);
        running.push({ job: j, lanes: free.splice(0, j.ngpus), start: -elapsed, end: j.run - elapsed, wallEnd: j.wall - elapsed, role: "earlier" });
      }
    });
    // Already queued at minute 0, having waited up to 60 hours.
    for (var q = 0; q < INITIAL_QUEUE; q++) jobs.push(makeJob(-Math.round(rand() * 60 * 60)));
    // Arrivals over the two days.
    for (var m = 1; m <= RUN_MIN; m++) {
      if (rand() < ARRIVALS_PER_HOUR / 60) jobs.push(makeJob(m));
    }
    return { jobs: jobs, running: running };
  }

  function size(j) { return j.mem / 8 + j.ncpus + 32 * j.ngpus; }
  function base(j) { var f = j.f; return 48 * f + 6 * f * size(j) + 4 * Math.log(Math.max(f, 1e-7)); }
  function waitedHours(j, t) { return Math.max(0, t - j.submit) / 60; }
  function score(j, t) { return base(j) + waitedHours(j, t); }
  function selectLine(j) { return "select=1:ncpus=" + j.ncpus + ":ngpus=" + j.ngpus + ":mem=" + j.mem + "gb:gpu_id=H100"; }

  function laneFree(intervals, lane, a, b) {
    for (var i = 0; i < intervals.length; i++) {
      var iv = intervals[i];
      if (iv.a < b && iv.b > a && iv.lanes.indexOf(lane) >= 0) return false;
    }
    return true;
  }
  function place(intervals, j, a, b) {
    for (var n = 0; n < NODES.length; n++) {
      var free = [];
      for (var k = 0; k < 4 && free.length < j.ngpus; k++) {
        if (laneFree(intervals, NODES[n].lanes[k], a, b)) free.push(NODES[n].lanes[k]);
      }
      if (free.length >= j.ngpus) return free;
    }
    return null;
  }

  function create(seed) {
    var w = build(seed || 20260914);
    return {
      t: -1, all: w.jobs, running: w.running, queue: [], bookings: [], status: {}, events: [], started: {},
      backfilled: 0, fromBooking: 0
    };
  }

  function cycle(s) {
    var t = (s.t += CYCLE_MIN), ev = [];
    var changed = false;
    s.running.forEach(function (r) {
      if (!r.done && r.end <= t) { r.done = true; changed = true; }
    });
    var active = s.running.filter(function (r) { return !r.done; });
    var waiting = s.all.filter(function (j) { return j.submit <= t && !s.started[j.id]; });
    waiting.sort(function (a, b) { return score(b, t) - score(a, t) || a.submit - b.submit; });
    var ranks = {};
    waiting.forEach(function (j, i) { ranks[j.id] = i + 1; });

    // The scheduler plans with requested walltime, not with how long jobs will really run.
    var planned = active.map(function (r) { return { lanes: r.lanes, a: r.start, b: Math.max(r.wallEnd, t + 1) }; });
    var prev = s.status, status = {}, bookings = [], rank = 0;
    waiting.forEach(function (j) {
      var busy = planned.concat(bookings);
      var wasBooked = prev[j.id] && prev[j.id].kind === "booked";
      var lanes = place(busy, j, t, t + j.wall);
      if (lanes) {
        var role = bookings.length && !wasBooked ? "filler" : "top";
        var r = { job: j, lanes: lanes, start: t, end: t + j.run, wallEnd: t + j.wall, role: role };
        s.running.push(r); active.push(r); planned.push({ lanes: lanes, a: t, b: t + j.wall });
        s.started[j.id] = true;
        if (role === "filler") s.backfilled++; else if (wasBooked) s.fromBooking++;
        var guard = null;
        if (role === "filler") {
          var node = NODES.filter(function (nd) { return nd.lanes.indexOf(lanes[0]) >= 0; })[0];
          bookings.forEach(function (b) {
            if (b.lanes.some(function (l) { return node.lanes.indexOf(l) >= 0; }) && (!guard || b.a < guard.a)) guard = b;
          });
        }
        ev.push({
          kind: "start", job: j, role: role, lanes: lanes, rank: ranks[j.id], wasBooked: wasBooked,
          estimate: wasBooked ? prev[j.id].at : null, guard: guard ? { id: guard.job.id, at: guard.a } : null
        });
        return;
      }
      rank++;
      if (bookings.length < DEPTH) {
        var times = [];
        busy.forEach(function (iv) { if (iv.b > t && times.indexOf(iv.b) < 0) times.push(iv.b); });
        times.sort(function (a, b) { return a - b; });
        for (var k = 0; k < times.length; k++) {
          var bl = place(busy, j, times[k], times[k] + j.wall);
          if (bl) {
            bookings.push({ job: j, lanes: bl, a: times[k], b: times[k] + j.wall });
            status[j.id] = { kind: "booked", at: times[k] };
            if (!wasBooked) ev.push({ kind: "booked", job: j, at: times[k], rank: ranks[j.id], fresh: j.submit === t });
            return;
          }
        }
      }
      status[j.id] = { kind: "waiting" };
      if (wasBooked) ev.push({ kind: "lost", job: j, rank: ranks[j.id] });
    });

    waiting.forEach(function (j) {
      if (j.submit === t) {
        var keptAhead = waiting.filter(function (q) {
          return q.id !== j.id && !s.started[q.id] && base(q) < base(j) && score(q, t) > score(j, t);
        }).sort(function (a, b) { return waitedHours(b, t) - waitedHours(a, t); })[0];
        ev.unshift({ kind: "submit", job: j, rank: ranks[j.id], of: waiting.length, keptAhead: keptAhead || null, started: !!s.started[j.id] });
      }
    });

    s.queue = waiting.filter(function (j) { return !s.started[j.id]; });
    s.bookings = bookings;
    s.status = status;
    s.events = ev;
    return s;
  }

  function idleGpus(s) {
    var busy = {};
    s.running.forEach(function (r) { if (!r.done) r.lanes.forEach(function (l) { busy[l] = true; }); });
    return NODES.length * 4 - Object.keys(busy).length;
  }

  root.BackfillEngine = {
    DEPTH: DEPTH, NODES: NODES, RUN_MIN: RUN_MIN, CYCLE_MIN: CYCLE_MIN,
    create: create, cycle: cycle, score: score, base: base, waitedHours: waitedHours, size: size,
    selectLine: selectLine, idleGpus: idleGpus
  };
})(typeof window !== "undefined" ? window : globalThis);

  var TEMPLATE = "<div class=\"frame\" role=\"group\" aria-label=\"Backfill animation\"><div class=\"section head\"><div class=\"bar\"><div class=\"buttons\"><button class=\"icon primary\" id=\"bfa-start\" type=\"button\" aria-label=\"Start\" title=\"Start\"><svg viewBox=\"0 0 24 24\" aria-hidden=\"true\"><path d=\"M8 5.5v13l10.5-6.5z\" fill=\"currentColor\"/></svg></button><button class=\"icon\" id=\"bfa-stop\" type=\"button\" aria-label=\"Stop\" title=\"Stop\"><svg viewBox=\"0 0 24 24\" aria-hidden=\"true\"><rect x=\"6.5\" y=\"6.5\" width=\"11\" height=\"11\" rx=\"1.5\" fill=\"currentColor\"/></svg></button><button class=\"icon\" id=\"bfa-next\" type=\"button\" aria-label=\"Next event\" title=\"Next event\"><svg viewBox=\"0 0 24 24\" aria-hidden=\"true\"><path d=\"M5.5 5.5v13l9-6.5z\" fill=\"currentColor\"/><rect x=\"15.5\" y=\"5.5\" width=\"3\" height=\"13\" rx=\"1\" fill=\"currentColor\"/></svg></button><button class=\"icon\" id=\"bfa-reset\" type=\"button\" aria-label=\"Reset\" title=\"Reset\"><svg viewBox=\"0 0 24 24\" aria-hidden=\"true\"><path d=\"M5 12a7 7 0 1 0 2.05-4.95\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2.2\" stroke-linecap=\"round\"/><path d=\"M4.5 3.5v5h5\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2.2\" stroke-linecap=\"round\" stroke-linejoin=\"round\"/></svg></button></div></div><div class=\"status-row\"><div class=\"clock\" id=\"bfa-clock\"></div><div class=\"stats\"><div class=\"stat\"><b id=\"bfa-queued\">0</b><span>Queued</span></div><div class=\"stat\"><b id=\"bfa-idle\">0</b><span>Idle GPUs</span></div><div class=\"stat\"><b id=\"bfa-filled\">0</b><span>Backfilled</span></div><div class=\"stat\"><b id=\"bfa-booked\">0</b><span>From booking</span></div></div></div></div><div class=\"section\"><div class=\"section-head\"><span class=\"title\">GPU nodes</span><div class=\"legend\"><span><i class=\"sw run\"></i>Running</span><span><i class=\"sw filler\"></i>Backfilled</span><span><i class=\"sw booked\"></i>Booked (top five)</span><span><i class=\"sw hl\"></i>Just changed</span></div></div><div class=\"timeline-wrap\"><div class=\"timeline\" id=\"bfa-timeline\"></div></div></div><div class=\"section\"><div class=\"table-head\"><span class=\"title\">Queue, highest score first</span><span class=\"table-note\">Above the line: the top five, the only jobs with a <code>qstat -T</code> start.</span></div><div class=\"table-wrap\"><table class=\"bfa-table\"><thead><tr><th class=\"num\">Rank</th><th>Job</th><th>Request</th><th class=\"num\">Walltime</th><th class=\"num\">f</th><th class=\"num\">Waited</th><th class=\"num\">Score</th><th><code>qstat -T</code> start</th></tr></thead><tbody id=\"bfa-rows\" class=\"rows\"></tbody></table></div></div><div class=\"section\"><div class=\"section-head\"><span class=\"title\">Latest events</span></div><div class=\"log\" id=\"bfa-log\" aria-live=\"off\"></div></div></div>";

  function mount(rootEl) {
  var E = window.BackfillEngine;
  var MS_PER_MIN = 50, BEFORE = 6 * 60, AFTER = 30 * 60, START_CLOCK = 9 * 60, LOG_LINES = 3, TABLE_ROWS = 6;
  var $ = function (id) { return document.getElementById(id); };
  var state, log = [], rowEls = {}, tableDirty = false, lastClock = "", highlight = {}, strips = [];
  // Bars sit on strips at fixed positions in minutes; each frame slides the strips to the current time.
  var pxPerMin = 1, simTime = 0, playing = false, rafId = 0, lastFrame = 0, builtAt = -1e9, dirty = true;
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var MARGIN = 120, REORDER_GAP = 650, shownKeys = "", lastReorderAt = -1e9;

  function clock(t) {
    var total = START_CLOCK + t, day = Math.floor(total / 1440) + 1, m = ((total % 1440) + 1440) % 1440;
    return { day: day, hm: String(Math.floor(m / 60)).padStart(2, "0") + ":" + String(m % 60).padStart(2, "0") };
  }
  function when(t) { var c = clock(t); return "Day " + c.day + " " + c.hm; }
  function dur(min) { var h = Math.floor(min / 60), m = min % 60; return h && m ? h + " h " + m + " min" : h ? h + " h" : m + " min"; }
  function nodeOf(lane) { return E.NODES[Math.floor(lane / 4)].name; }
  function short(j) { return j.id; }
  function req(j) { return j.ngpus + " GPU" + (j.ngpus > 1 ? "s" : "") + ", " + dur(j.wall); }

  function buildTimeline() {
    var html = "";
    E.NODES.forEach(function (n) {
      html += '<div class="node"><span class="node-name">' + n.name + '</span><div class="gpus">';
      n.lanes.forEach(function (l) { html += '<div class="track"><div class="strip" id="bfa-lane-' + l + '"></div></div>'; });
      html += "</div></div>";
    });
    html += '<div class="axis"><span></span><div class="axis-track"><div class="strip" id="bfa-axis"></div></div></div><i class="now" id="bfa-now"></i>';
    $("bfa-timeline").innerHTML = html;
    strips = Array.prototype.slice.call(document.querySelectorAll("#bfa-timeline .strip"));
  }

  function describe(e, t) {
    var j = e.job;
    switch (e.kind) {
      case "submit": {
        // Plain submissions are counted, not logged; only log one that waiting time keeps behind an older job.
        if (e.started || !e.keptAhead) return null;
        return "<b>" + short(j) + "</b> is submitted (" + req(j) + ", f " + j.f.toFixed(2) + ") and ranks " + e.rank + " of " + e.of +
          ". Without waiting time it would rank above " + short(e.keptAhead) + ", but " + short(e.keptAhead) + " has waited " + Math.floor(E.waitedHours(e.keptAhead, t)) + " h and stays ahead.";
      }
      case "booked":
        return "<b>" + short(j) + "</b> enters the top five and is booked for " + when(e.at) + ". <code>qstat -T</code> now shows that start.";
      case "lost":
        return "<b>" + short(j) + "</b> slips to rank " + e.rank + ", out of the top five, and loses its booking and its <code>qstat -T</code> estimate.";
      case "start":
        if (e.role === "filler") {
          return "<b>" + short(j) + "</b> is <b>backfilled</b> onto " + nodeOf(e.lanes[0]) + " at rank " + e.rank + " (" + req(j) + ")" +
            (e.guard ? ": it ends before " + e.guard.id + "'s booking at " + clock(e.guard.at).hm + "." : ": no booking needs those GPUs before it ends.");
        }
        if (e.wasBooked) {
          var early = e.estimate - t;
          return "<b>" + short(j) + "</b> starts from its booking on " + nodeOf(e.lanes[0]) + (early >= 30 ? ", " + dur(early) + " earlier than its estimate because running jobs finished before their walltime." : ".");
        }
        return "<b>" + short(j) + "</b> starts on " + nodeOf(e.lanes[0]) + " at rank " + e.rank + ": enough GPUs were free.";
    }
    return null;
  }

  function tagFor(e) {
    if (e.kind === "submit") return { label: "Waiting counts", cls: "wait" };
    if (e.kind === "booked") return { label: "Booked", cls: "booked" };
    if (e.kind === "lost") return { label: "Lost booking", cls: "lost" };
    if (e.role === "filler") return { label: "Backfilled", cls: "backfill" };
    if (e.wasBooked) return { label: "From booking", cls: "booked" };
    return { label: "Started", cls: "start" };
  }

  function measure() {
    var track = $("bfa-lane-0").parentNode, tr = track.getBoundingClientRect(), box = $("bfa-timeline").getBoundingClientRect();
    pxPerMin = tr.width / (BEFORE + AFTER);
    $("bfa-now").style.left = (tr.left - box.left + BEFORE * pxPerMin) + "px";
  }

  function bar(cls, a, b, title) {
    a = Math.max(a, builtAt - BEFORE - MARGIN);
    b = Math.min(b, builtAt + AFTER + MARGIN);
    if (b <= a) return "";
    return '<div class="blk ' + cls + '" style="left:' + (a * pxPerMin).toFixed(1) + "px;width:" + ((b - a) * pxPerMin).toFixed(1) + 'px" title="' + title + '"></div>';
  }

  function recent(id) { return highlight[id] !== undefined && state.t - highlight[id] <= 20; }

  // Rebuild the bars only when something on the nodes changed, or once an hour so new bars can slide in.
  function buildStrips() {
    var s = state, lanes = [];
    builtAt = Math.max(s.t, 0);
    for (var i = 0; i < E.NODES.length * 4; i++) lanes.push("");
    s.running.forEach(function (r) {
      var endShown = r.done ? r.end : r.wallEnd;
      if (endShown < builtAt - BEFORE - MARGIN) return;
      var cls = r.role + (r.done ? " done" : "") + (recent(r.job.id) ? " hl" : "") + (r.role !== "earlier" && r.start === s.t ? " enter" : "");
      var title = r.job.id + ": " + req(r.job) + (r.done ? ", finished after " + dur(r.end - r.start) : "");
      r.lanes.forEach(function (l) { lanes[l] += bar(cls, r.start, endShown, title); });
    });
    s.bookings.forEach(function (b) {
      var title = b.job.id + " booked for " + when(b.a);
      b.lanes.forEach(function (l) { lanes[l] += bar("booked" + (recent(b.job.id) ? " hl enter" : ""), b.a, b.b, title); });
    });
    lanes.forEach(function (h, l) { $("bfa-lane-" + l).innerHTML = h; });

    var axis = "", from = builtAt - BEFORE - MARGIN, to = builtAt + AFTER + MARGIN;
    for (var x = Math.ceil((from + START_CLOCK) / 360) * 360 - START_CLOCK; x <= to; x += 360) {
      var c = clock(x), left = (x * pxPerMin).toFixed(1);
      axis += '<i class="gridline" style="left:' + left + 'px"></i><span style="left:' + left + 'px">' + (c.hm === "00:00" ? "Day " + c.day : c.hm) + "</span>";
    }
    $("bfa-axis").innerHTML = axis;
    dirty = false;
  }

  function position() {
    var tf = "translate3d(" + (-(simTime - BEFORE) * pxPerMin).toFixed(2) + "px,0,0)";
    strips.forEach(function (el) { el.style.transform = tf; });
  }

  // Rows persist per job: values change in place and rows move, so a slide is never cut off by a rebuild.
  function shiftOf(tr) {
    var m = getComputedStyle(tr).transform;
    if (!m || m === "none") return 0;
    var parts = m.slice(m.indexOf("(") + 1, -1).split(",");
    return parseFloat(parts[parts.length === 6 ? 5 : 13]) || 0;
  }
  function setCell(td, html, cls, title) {
    if (td._html !== html) { td.innerHTML = html; td._html = html; }
    if (cls !== undefined && td.className !== cls) td.className = cls;
    if (title !== undefined && td.title !== title) td.title = title;
  }
  function makeRow(key, cells) {
    var tr = document.createElement("tr");
    tr.dataset.key = key;
    for (var i = 0; i < cells; i++) {
      var td = document.createElement("td");
      if (cells === 1) td.colSpan = 8;
      tr.appendChild(td);
    }
    if (!reduce) {
      tr.setAttribute("data-new", "");
      setTimeout(function () { tr.removeAttribute("data-new"); }, 600);
    }
    return tr;
  }

  function renderTable(force) {
    var s = state, t = Math.max(s.t, 0), q = s.queue || [], body = $("bfa-rows");
    // Fixed slots keep the table one height: a job or a blank row in each slot, the depth line after slot five, then a summary row.
    var keys = [];
    for (var slot = 0; slot < TABLE_ROWS; slot++) {
      keys.push(slot < q.length ? q[slot].id : "~pad-" + slot);
      if (slot === E.DEPTH - 1) keys.push("~cut");
    }
    keys.push("~more");
    // Let one reorder finish before the next starts; changes that arrive sooner are merged into the next slide.
    var orderChanged = keys.join("|") !== shownKeys;
    if (!force && playing && orderChanged && performance.now() - lastReorderAt < REORDER_GAP) return false;

    // Where every row is on screen now, including any slide still in progress.
    var before = {};
    Object.keys(rowEls).forEach(function (k) { before[k] = rowEls[k].offsetTop + shiftOf(rowEls[k]); });

    var byId = {};
    q.forEach(function (j) { byId[j.id] = j; });
    var wanted = {};
    keys.forEach(function (k, idx) {
      wanted[k] = true;
      var tr = rowEls[k];
      if (k.charAt(0) === "~") {
        if (!tr) {
          tr = rowEls[k] = makeRow(k, 1);
          tr.removeAttribute("data-new");
          tr.className = k === "~cut" ? "cut" : k === "~more" ? "more" : "pad";
        }
        var text = "&nbsp;";
        if (k === "~cut") text = "";
        if (k === "~more" && q.length > TABLE_ROWS) text = "and " + (q.length - TABLE_ROWS) + " more waiting";
        // The first empty slot says why the rest of the table is blank.
        if (k === "~pad-" + q.length) text = q.length ? "No other jobs waiting" : "Nobody is waiting";
        setCell(tr.firstChild, text);
        return;
      }
      var j = byId[k], rank = q.indexOf(j) + 1, st = s.status[j.id] || {}, booked = st.kind === "booked";
      if (!tr) tr = rowEls[k] = makeRow(k, 8);
      var rowCls = booked ? "top" : "out";
      if (tr.className !== rowCls) tr.className = rowCls;
      var c = tr.children;
      setCell(c[0], String(rank), "num");
      setCell(c[1], j.id, "mono");
      setCell(c[2], j.ngpus + " GPU" + (j.ngpus > 1 ? "s" : "") + " &middot; " + j.ncpus + " cores &middot; " + j.mem + " GB", "", E.selectLine(j));
      setCell(c[3], j.wall / 60 + " h", "num mono");
      setCell(c[4], j.f.toFixed(2), "num");
      setCell(c[5], Math.floor(E.waitedHours(j, t)) + " h", "num mono");
      setCell(c[6], String(Math.round(E.score(j, t))), "num mono");
      setCell(c[7], booked ? when(st.at) : "", "mono" + (booked ? " booked" : ""));
    });

    Object.keys(rowEls).forEach(function (k) {
      if (!wanted[k]) { rowEls[k].remove(); delete rowEls[k]; }
    });
    keys.forEach(function (k, i) {
      var tr = rowEls[k];
      if (body.children[i] !== tr) body.insertBefore(tr, body.children[i] || null);
    });

    shownKeys = keys.join("|");
    // A refresh that only changes values must not touch rows that are still sliding.
    if (reduce || !orderChanged) return;
    // Slide each moved row from where it was drawn to its new place.
    var moved = false;
    keys.forEach(function (k) {
      var tr = rowEls[k];
      if (before[k] === undefined) return;
      var dy = before[k] - tr.offsetTop;
      if (Math.abs(dy) < 0.5) {
        if (tr.style.transform) { tr.style.transition = "none"; tr.style.transform = ""; }
        return;
      }
      tr.style.transition = "none";
      tr.style.transform = "translateY(" + dy.toFixed(1) + "px)";
      tr.style.position = "relative";
      tr.style.zIndex = dy > 0 ? "3" : "2";
      tr.getBoundingClientRect();
      tr.style.transition = "transform 0.5s ease";
      tr.style.transform = "";
      // A row moving up is drawn over the rows it overtakes until its slide ends.
      var token = tr._slide = (tr._slide || 0) + 1;
      setTimeout(function () { if (tr._slide === token) { tr.style.zIndex = ""; tr.style.position = ""; } }, 520);
      moved = true;
    });
    if (moved) lastReorderAt = performance.now();
  }

  function renderClock() {
    var t = Math.max(state.t, 0), c = clock(t), text = c.hm + "<small>Day " + c.day + ", " + Math.floor(t / 60) + " of " + E.RUN_MIN / 60 + " h</small>";
    if (text !== lastClock) { $("bfa-clock").innerHTML = text; lastClock = text; }
  }

  function renderStats() {
    var s = state;
    [["bfa-queued", s.queue.length], ["bfa-idle", s.t < 0 ? 0 : E.idleGpus(s)], ["bfa-filled", s.backfilled], ["bfa-booked", s.fromBooking]].forEach(function (p) {
      var el = $(p[0]), v = String(p[1]);
      if (el.textContent !== v) el.textContent = v;
    });
  }

  function renderLog(fresh) {
    $("bfa-log").innerHTML = log.length
      ? log.map(function (e, i) {
          var c = i < fresh ? "new" : "old";
          return '<time class="' + c + '">' + e.time + '</time><span class="tag ' + e.tag.cls + " " + c + '">' + e.tag.label + '</span><p class="' + c + '">' + e.text + "</p>";
        }).join("")
      : '<time></time><span></span><p class="old">Every GPU is busy and ' + state.queue.length + " jobs are already waiting. Press <b>Start</b>.</p>";
  }

  function signature() {
    var done = 0;
    state.running.forEach(function (r) { if (r.done) done++; });
    return done + "|" + state.running.length + "|" + state.bookings.map(function (b) { return b.job.id + "@" + b.a + ":" + b.lanes.join(","); }).join(";");
  }

  // One scheduling cycle: advance the engine, log what matters, refresh the table and counters.
  function runCycle() {
    var sigBefore = signature();
    E.cycle(state);
    var added = 0;
    state.events.forEach(function (e) {
      var text = describe(e, state.t);
      if (!text) return;
      log.unshift({ time: clock(state.t).hm, text: text, tag: tagFor(e) });
      highlight[e.job.id] = state.t;
      added++;
    });
    log = log.slice(0, LOG_LINES);
    if (signature() !== sigBefore || state.t - builtAt >= 60) dirty = true;
    if (added) renderLog(added);
    tableDirty = true;
    renderStats();
    return added;
  }

  function frame(now) {
    if (!playing) return;
    if (!document.body.contains(rootEl)) { stop(); return; }
    var dt = lastFrame ? Math.min(now - lastFrame, 100) : 0;
    lastFrame = now;
    simTime = Math.min(E.RUN_MIN, simTime + dt / MS_PER_MIN);
    while (state.t < Math.floor(simTime)) runCycle();
    if (dirty) buildStrips();
    if (tableDirty && renderTable(false) !== false) tableDirty = false;
    position();
    renderClock();
    if (simTime >= E.RUN_MIN) { stop(); return; }
    rafId = requestAnimationFrame(frame);
  }

  function start() {
    if (playing) return;
    if (state.t >= E.RUN_MIN) reset();
    playing = true;
    lastFrame = 0;
    rafId = requestAnimationFrame(frame);
    buttons();
  }
  function stop() {
    playing = false;
    cancelAnimationFrame(rafId);
    buttons();
  }
  function next() {
    stop();
    var added = 0;
    while (state.t < E.RUN_MIN && !added) added = runCycle();
    simTime = state.t;
    buildStrips(); position(); renderClock();
    renderTable(true); tableDirty = false;
    buttons();
  }
  function reset() {
    stop();
    state = E.create(); log = []; rowEls = {}; tableDirty = false; lastClock = ""; highlight = {};
    $("bfa-rows").innerHTML = "";
    E.cycle(state);
    state.events = [];
    simTime = 0;
    measure(); buildStrips(); position();
    shownKeys = ""; lastReorderAt = -1e9;
    renderClock(); renderStats(); renderTable(true); renderLog(0);
    buttons();
  }
  function buttons() {
    // After instant navigation replaces the page, a last animation frame can still call stop(); the controls are gone.
    if (!$("bfa-start")) return;
    $("bfa-start").disabled = playing;
    $("bfa-stop").disabled = !playing;
    $("bfa-next").disabled = !!state && state.t >= E.RUN_MIN;
  }

  $("bfa-start").addEventListener("click", start);
  $("bfa-stop").addEventListener("click", stop);
  $("bfa-next").addEventListener("click", next);
  $("bfa-reset").addEventListener("click", reset);
  // After instant navigation away from the page, the handler removes itself.
  function onResize() {
    if (!document.body.contains(rootEl)) { window.removeEventListener("resize", onResize); return; }
    if (state) { measure(); buildStrips(); position(); }
  }
  window.addEventListener("resize", onResize);

  buildTimeline();
  reset();
  // Start once the animation scrolls into view, so the two days are not half over before anyone sees them.
  if (!reduce && "IntersectionObserver" in window) {
    var seen = new IntersectionObserver(function (entries) {
      if (entries.some(function (e) { return e.isIntersecting; })) { seen.disconnect(); start(); }
    }, { threshold: 0.35 });
    seen.observe(rootEl);
  }
  }

  function init() {
    var root = document.getElementById("backfill-animation");
    if (!root || root.getAttribute("data-ready")) return;
    root.setAttribute("data-ready", "true");
    root.innerHTML = TEMPLATE;
    mount(root);
  }

  if (typeof document$ !== "undefined") document$.subscribe(init);
  else document.addEventListener("DOMContentLoaded", init);
})();
