/*
 * Interactive score explorer for "The Queue Is Not a Line".
 *
 * Builds itself inside the element with id "queue-score-explorer". It hooks
 * into Material for MkDocs' document$ stream so it also builds after instant
 * navigation, the same way javascripts/katex.js renders maths.
 */
(function () {
  "use strict";

  var FORMULAS = {
    bonus48: { bonus: 48, size: 6, pen: 4, color: "--c-bonus48", dash: "",    label: "48f + 6f R + h + 4 ln f", tex: "48f + 6f\\,R + h + 4\\,\\ln\\,f" },
    size6:   { bonus: 0,  size: 6, pen: 4, color: "--c-size6",   dash: "7 4", label: "6f R + h + 4 ln f",       tex: "6f\\,R + h + 4\\,\\ln\\,f" },
    size8:   { bonus: 0,  size: 8, pen: 3, color: "--c-size8",   dash: "2 4", label: "8f R + h + 3 ln f",       tex: "8f\\,R + h + 3\\,\\ln\\,f" }
  };
  var ORDER = ["bonus48", "size6", "size8"];
  var STANDARD = { gpus: 1, cores: 12, mem: 64, x: 1, hours: 0 };
  var HOUR_POINTS = 0.000278 * 3600;
  var VIEWS = { full: { a: 0, b: 6, step: 1 }, zoom: { a: 3, b: 6, step: 0.5 } };
  var W = 620, H = 340, PL = 54, PR = 18, PT = 16, PB = 60;
  var SVGNS = "http://www.w3.org/2000/svg";

  var SWATCH =
    '<i style="background:var(--t-bonus)"></i><i style="background:var(--t-size)"></i>' +
    '<i style="background:var(--t-wait)"></i><i style="background:var(--t-pen)"></i>';

  function formulaOption(key, dashClass, texSrc, plain, desc, checked, live) {
    return [
      '<div class="formula-opt">',
      '  <input type="radio" name="qse-formula" id="qse-f-' + key + '" value="' + key + '"' + (checked ? " checked" : "") + '>',
      '  <label for="qse-f-' + key + '">',
      '    <span class="key' + dashClass + '" style="border-top-color:var(' + FORMULAS[key].color + ')"></span>',
      '    <span class="expr"><span class="tex" data-tex="' + texSrc + '">' + plain + '</span>' + (live ? '<span class="tag">Live</span>' : "") + '</span>',
      '    <span class="desc">' + desc + '</span>',
      '  </label>',
      '</div>'
    ].join("");
  }

  function numberControl(name, label, min, max) {
    return [
      '<div class="ctl">',
      '  <div class="ctl-head"><label for="qse-' + name + '-num">' + label + '</label>',
      '  <input type="number" id="qse-' + name + '-num" min="' + min + '" max="' + max + '" step="1"></div>',
      '  <input type="range" id="qse-' + name + '-range" min="' + min + '" max="' + max + '" step="1" aria-label="' + label + '">',
      '</div>'
    ].join("");
  }

  var TEMPLATE = [
    '<section class="explorer" aria-label="Queue score explorer">',
    '<div class="controls">',
    '  <fieldset>',
    '    <legend class="group-label">Highlighted formula</legend>',
    '    <div class="formulas">',
    formulaOption("bonus48", "", FORMULAS.bonus48.tex, FORMULAS.bonus48.label, "Flat 48-point fair-share bonus on top", true, true),
    formulaOption("size6", " dash6", FORMULAS.size6.tex, FORMULAS.size6.label, "No bonus, stronger penalty", false, false),
    formulaOption("size8", " dash8", FORMULAS.size8.tex, FORMULAS.size8.label, "No bonus, size weighted most", false, false),
    '    </div>',
    '  </fieldset>',
    '  <div>',
    '    <div class="group-label">Request</div>',
    '    <div class="stack">',
    numberControl("gpus", "GPUs", 0, 8),
    numberControl("cores", "CPU cores", 1, 256),
    numberControl("mem", "Memory, GB", 1, 1920),
    '      <div class="size-line" id="qse-size-line"></div>',
    '    </div>',
    '  </div>',
    '  <div class="ctl">',
    '    <div class="ctl-head"><label for="qse-usage-range">Recent usage ÷ your share</label></div>',
    '    <input type="range" id="qse-usage-range" min="0" max="6" step="0.05">',
    '    <div class="def" id="qse-usage-readout"></div>',
    '  </div>',
    numberControl("hours", "Hours your job has waited", 0, 336).replace(
      /<\/div>$/, '<div class="def"><span class="tex" data-tex="h = \\text{hours waited}">h = hours waited</span></div></div>'),
    '  <div class="walltime">Walltime is not in any of the formulas, so no walltime value can change these scores. It only matters for backfilling.</div>',
    '</div>',
    '<div class="results">',
    '  <section class="part" aria-label="Score against recent usage">',
    '    <div class="part-head">',
    '      <div class="part-title">Score as your recent usage grows</div>',
    '      <button type="button" class="switch" id="qse-zoom-switch" role="switch" aria-checked="false">',
    '        <span class="switch-track"><span class="switch-knob"></span></span>',
    '        <span>Zoom: 3× to 6× your share</span>',
    '      </button>',
    '    </div>',
    '    <div class="display-math"><div class="main" id="qse-formula-display"></div></div>',
    '    <div class="plot-wrap">',
    '      <svg class="plot" id="qse-plot" viewBox="0 0 620 340" role="img" tabindex="0" aria-label="Score curves for the three formulas. Use the left and right arrow keys to change your recent usage."></svg>',
    '      <div class="tip" id="qse-tip" hidden></div>',
    '    </div>',
    '  </section>',
    '  <section class="part" aria-label="Your job against a fresh account" aria-live="polite">',
    '    <div class="part-head">',
    '      <div class="part-title">Your job against a fresh account</div>',
    '      <span class="chip" id="qse-chip"></span>',
    '    </div>',
    '    <div class="key" aria-hidden="true">',
    '      <span><span class="sw">' + SWATCH + '</span>Your job</span>',
    '      <span><span class="sw fresh">' + SWATCH + '</span>Fresh account, same request, submitted now</span>',
    '    </div>',
    '    <div class="terms" id="qse-terms"></div>',
    '  </section>',
    '</div>',
    '</section>'
  ].join("\n");

  function mount(root) {
    var state = Object.assign({ formula: "bonus48", view: "full" }, STANDARD);
    var $ = function (id) { return document.getElementById("qse-" + id); };

    function clamp(v, lo, hi) { return Math.min(hi, Math.max(lo, v)); }
    function fmt(v) { return Math.round(v).toLocaleString("en-AU"); }
    function num(v, d) { return (Math.round(v * Math.pow(10, d)) / Math.pow(10, d)).toString(); }
    function sizeR() { return state.mem / 8 + state.cores + 32 * state.gpus; }
    function tex(src, display) {
      if (!window.katex) return null;
      return window.katex.renderToString(src, { throwOnError: false, displayMode: !!display });
    }
    function setTex(node, src, fallback, display) {
      var html = tex(src, display);
      if (html) node.innerHTML = html; else node.textContent = fallback;
    }

    function terms(v, f, R, hours) {
      return {
        bonus: v.bonus * f,
        size: v.size * f * R,
        wait: HOUR_POINTS * hours,
        pen: v.pen * Math.log(Math.max(f, 1e-7))
      };
    }
    function total(t) { return t.bonus + t.size + t.wait + t.pen; }
    function scoreAt(key, x) { return total(terms(FORMULAS[key], Math.pow(2, -x), sizeR(), state.hours)); }

    /* ---------- controls ---------- */
    function pair(name, lo, hi) {
      var n = $(name + "-num"), r = $(name + "-range");
      function set(v, from) {
        v = clamp(Math.round(Number(v)), lo, hi);
        if (isNaN(v)) v = lo;
        state[name] = v;
        if (from !== n) n.value = v;
        if (from !== r) r.value = v;
        render();
      }
      r.addEventListener("input", function () { set(r.value, r); });
      n.addEventListener("change", function () { set(n.value, null); });
      return set;
    }
    var setGpus = pair("gpus", 0, 8);
    var setCores = pair("cores", 1, 256);
    var setMem = pair("mem", 1, 1920);
    var setHours = pair("hours", 0, 336);

    var usage = $("usage-range");
    function setX(x) {
      state.x = clamp(Number(x), 0, 6);
      usage.value = state.x;
      render();
    }
    usage.addEventListener("input", function () { setX(usage.value); });
    Array.prototype.forEach.call(root.querySelectorAll('input[name="qse-formula"]'), function (r) {
      r.addEventListener("change", function () { state.formula = r.value; render(); });
    });

    /* ---------- plot ---------- */
    var svg = $("plot"), tip = $("tip");
    var hoverX = null;

    function setView(v) { state.view = v; hoverX = null; tip.hidden = true; render(); }
    $("zoom-switch").addEventListener("click", function () { setView(state.view === "zoom" ? "full" : "zoom"); });

    function el(name, attrs, parent) {
      var node = document.createElementNS(SVGNS, name);
      for (var k in attrs) node.setAttribute(k, attrs[k]);
      if (parent) parent.appendChild(node);
      return node;
    }
    function niceDomain(lo, hi) {
      var span = Math.max(hi - lo, 1);
      var raw = span / 6;
      var mag = Math.pow(10, Math.floor(Math.log10(raw)));
      var norm = raw / mag;
      var step = (norm < 1.5 ? 1 : norm < 3 ? 2 : norm < 7 ? 5 : 10) * mag;
      return { lo: Math.floor(lo / step) * step, hi: Math.ceil(hi / step) * step, step: step };
    }
    function geometry() {
      var view = VIEWS[state.view];
      var xs = [];
      for (var i = 0; i <= 240; i++) xs.push(view.a + (view.b - view.a) * i / 240);
      var lo = 0, hi = 0;
      xs.forEach(function (x) {
        ORDER.forEach(function (k) { var s = scoreAt(k, x); lo = Math.min(lo, s); hi = Math.max(hi, s); });
      });
      var d = niceDomain(lo, hi);
      return {
        view: view, xs: xs, d: d,
        X: function (x) { return PL + (x - view.a) / (view.b - view.a) * (W - PL - PR); },
        Y: function (v) { return PT + (d.hi - v) / (d.hi - d.lo) * (H - PT - PB); }
      };
    }

    function drawPlot() {
      svg.textContent = "";
      var g = geometry(), X = g.X, Y = g.Y, d = g.d, view = g.view;

      for (var v = d.lo; v <= d.hi + 1e-9; v += d.step) {
        el("line", { x1: PL, x2: W - PR, y1: Y(v), y2: Y(v), stroke: "var(--grid)", "stroke-width": 1 }, svg);
        el("text", { x: PL - 8, y: Y(v) + 4, "text-anchor": "end" }, svg).textContent = fmt(v);
      }
      for (var t = view.a; t <= view.b + 1e-9; t += view.step) {
        var atA = Math.abs(t - view.a) < 1e-9, atB = Math.abs(t - view.b) < 1e-9;
        var anchor = atA ? "start" : atB ? "end" : "middle";
        el("line", { x1: X(t), x2: X(t), y1: PT, y2: H - PB, stroke: "var(--grid)", "stroke-width": 1 }, svg);
        el("text", { x: X(t), y: H - PB + 16, "text-anchor": anchor }, svg).textContent = num(t, 1) + "×";
        var fv = Math.pow(2, -t);
        var lab = el("text", { x: X(t), y: H - PB + 30, "text-anchor": anchor, class: "stop-label" }, svg);
        if (atA) {
          el("tspan", { class: "it" }, lab).textContent = "f";
          lab.appendChild(document.createTextNode(" = "));
        }
        lab.appendChild(document.createTextNode(fv >= 0.1 ? num(fv, 2) : num(fv, 3)));
      }
      el("text", { x: (PL + W - PR) / 2, y: H - 8, "text-anchor": "middle", class: "axis-title" }, svg).textContent = "recent usage ÷ your share, where each 1× step halves f";
      el("text", { x: 14, y: (PT + H - PB) / 2, "text-anchor": "middle", class: "axis-title", transform: "rotate(-90 14 " + ((PT + H - PB) / 2) + ")" }, svg).textContent = "score";

      if (d.lo < 0) el("line", { x1: PL, x2: W - PR, y1: Y(0), y2: Y(0), stroke: "var(--axis)", "stroke-width": 1.5 }, svg);
      el("line", { x1: PL, x2: PL, y1: PT, y2: H - PB, stroke: "var(--axis)", "stroke-width": 1 }, svg);

      function path(fn) {
        return g.xs.map(function (x, i) { return (i ? "L" : "M") + X(x).toFixed(1) + " " + Y(fn(x)).toFixed(1); }).join("");
      }

      var drawOrder = ORDER.filter(function (k) { return k !== state.formula; }).concat([state.formula]);
      drawOrder.forEach(function (k) {
        var f = FORMULAS[k], sel = k === state.formula;
        el("path", {
          d: path(function (x) { return scoreAt(k, x); }), fill: "none", stroke: "var(" + f.color + ")",
          "stroke-width": sel ? 3 : 1.8, "stroke-dasharray": f.dash,
          "stroke-linejoin": "round", "stroke-linecap": "round", opacity: sel ? 1 : 0.75
        }, svg);
      });

      if (state.x >= view.a - 1e-9 && state.x <= view.b + 1e-9) {
        el("line", { x1: X(state.x), x2: X(state.x), y1: PT, y2: H - PB, stroke: "var(--fg)", "stroke-width": 1, "stroke-dasharray": "3 3", opacity: 0.5 }, svg);
        drawOrder.forEach(function (k) {
          var sel = k === state.formula;
          el("circle", { cx: X(state.x), cy: Y(scoreAt(k, state.x)), r: sel ? 5.5 : 3.5, fill: "var(" + FORMULAS[k].color + ")", stroke: "var(--bg)", "stroke-width": 2 }, svg);
        });
        var sNow = scoreAt(state.formula, state.x);
        var right = X(state.x) < W - PR - 90;
        el("text", { x: X(state.x) + (right ? 12 : -12), y: Y(sNow) - 12, "text-anchor": right ? "start" : "end", class: "val-label" }, svg).textContent = "you " + fmt(sNow);
      }

      if (view.a === 0 && state.x > 0.05) {
        var sFresh = total(terms(FORMULAS[state.formula], 1, sizeR(), 0));
        el("circle", { cx: X(0), cy: Y(sFresh), r: 5, fill: "var(--bg)", stroke: "var(" + FORMULAS[state.formula].color + ")", "stroke-width": 2 }, svg);
        el("text", { x: X(0) + 12, y: Y(sFresh) + 4, "text-anchor": "start", class: "val-label" }, svg).textContent = "fresh " + fmt(sFresh);
      }

      if (hoverX !== null) {
        el("line", { x1: X(hoverX), x2: X(hoverX), y1: PT, y2: H - PB, stroke: "var(--accent)", "stroke-width": 1 }, svg);
        ORDER.forEach(function (k) {
          el("circle", { cx: X(hoverX), cy: Y(scoreAt(k, hoverX)), r: 3, fill: "var(" + FORMULAS[k].color + ")" }, svg);
        });
      }
    }

    function xFromEvent(e) {
      var rect = svg.getBoundingClientRect();
      var view = VIEWS[state.view];
      var px = (e.clientX - rect.left) / rect.width * W;
      return clamp(view.a + (px - PL) / (W - PL - PR) * (view.b - view.a), view.a, view.b);
    }
    function showTip(x) {
      hoverX = x;
      var view = VIEWS[state.view];
      var pct = (PL + (x - view.a) / (view.b - view.a) * (W - PL - PR)) / W * 100;
      tip.style.left = clamp(pct, 20, 80) + "%";
      var f = Math.pow(2, -x);
      var head = tex("\\text{usage} \\div \\text{share} = " + x.toFixed(2) + ",\\quad f = " + f.toFixed(3)) ||
        ("usage ÷ share = " + x.toFixed(2) + ", f = " + f.toFixed(3));
      tip.innerHTML = "<div>" + head + "</div>" + ORDER.map(function (k) {
        return "<div class=\"row\"><span class=\"k\" style=\"border-top-color:var(" + FORMULAS[k].color + ")\"></span>" +
          (tex(FORMULAS[k].tex) || FORMULAS[k].label) + "<b>" + fmt(scoreAt(k, x)) + "</b></div>";
      }).join("");
      tip.hidden = false;
    }
    var dragging = false;
    svg.addEventListener("pointerdown", function (e) {
      dragging = true;
      svg.setPointerCapture(e.pointerId);
      var x = xFromEvent(e);
      showTip(x);
      setX(x);
    });
    svg.addEventListener("pointermove", function (e) {
      var x = xFromEvent(e);
      showTip(x);
      if (dragging) setX(x); else drawPlot();
    });
    svg.addEventListener("pointerup", function () { dragging = false; });
    svg.addEventListener("pointercancel", function () { dragging = false; });
    svg.addEventListener("keydown", function (e) {
      var view = VIEWS[state.view];
      var step = (view.b - view.a) / 60;
      if (e.key === "ArrowLeft") { e.preventDefault(); setX(state.x - step); }
      else if (e.key === "ArrowRight") { e.preventDefault(); setX(state.x + step); }
    });
    svg.addEventListener("pointerleave", function () {
      if (dragging) return;
      hoverX = null;
      tip.hidden = true;
      drawPlot();
    });

    /* ---------- term comparison ---------- */
    function drawTerms(v, you, fresh) {
      var rows = [];
      if (v.bonus) rows.push({ name: "Fair-share bonus", tex: v.bonus + "f", plain: v.bonus + "f", color: "--t-bonus", you: you.bonus, fresh: fresh.bonus });
      rows.push({ name: "Size × factor", tex: v.size + "f\\,R", plain: v.size + "f R", color: "--t-size", you: you.size, fresh: fresh.size });
      rows.push({ name: "Waiting", tex: "h", plain: "h", color: "--t-wait", you: you.wait, fresh: fresh.wait });
      rows.push({ name: "Log penalty", tex: v.pen + "\\,\\ln\\,f", plain: v.pen + " ln f", color: "--t-pen", you: you.pen, fresh: fresh.pen });
      rows.push({ name: "Total score", you: total(you), fresh: total(fresh), isTotal: true });

      var lo = 0, hi = 1;
      rows.forEach(function (r) { lo = Math.min(lo, r.you, r.fresh); hi = Math.max(hi, r.you, r.fresh); });
      [you, fresh].forEach(function (t) { hi = Math.max(hi, t.bonus + t.size + t.wait); });
      var span = hi - lo, zero = (-lo / span) * 100;

      function seg(left, width, color) {
        return "<span style=\"left:" + left + "%;width:" + width + "%;background:var(" + color + ")\"></span>";
      }
      function bar(val, color, cls) {
        var w = Math.abs(val) / span * 100;
        return "<div class=\"term-bar " + cls + "\">" + seg(val >= 0 ? zero : zero - w, w, color) + "</div>";
      }
      function stacked(t, cls) {
        var html = "<div class=\"term-bar " + cls + "\">", cum = 0;
        [["bonus", "--t-bonus"], ["size", "--t-size"], ["wait", "--t-wait"]].forEach(function (p) {
          var w = t[p[0]] / span * 100;
          html += seg(zero + cum, w, p[1]);
          cum += w;
        });
        if (t.pen < 0) {
          var pw = -t.pen / span * 100;
          html += seg(zero - pw, pw, "--t-pen");
        }
        return html + "</div>";
      }
      function show(val, isTotal) {
        return isTotal ? fmt(val) : (val < -0.05 ? "−" : "") + Math.abs(val).toFixed(1);
      }
      $("terms").innerHTML = rows.map(function (r) {
        var c = r.isTotal ? " total" : "";
        var sub = r.tex ? "<span class=\"sub\">" + (tex(r.tex) || r.plain) + "</span>" : "";
        var bars = r.isTotal
          ? stacked(you, "you") + stacked(fresh, "fresh")
          : bar(r.you, r.color, "you") + bar(r.fresh, r.color, "fresh");
        return "<div class=\"term-name" + c + "\">" + r.name + sub + "</div>" +
          "<div class=\"term-bars" + c + "\">" + bars +
          "<div class=\"term-zero\" style=\"left:calc(" + zero + "% - 0.5px)\"></div></div>" +
          "<div class=\"term-vals" + c + "\"><b>" + show(r.you, r.isTotal) + "</b><span>" + show(r.fresh, r.isTotal) + "</span></div>";
      }).join("");
    }

    function render() {
      var v = FORMULAS[state.formula];
      var f = Math.pow(2, -state.x);
      var R = sizeR();
      var you = terms(v, f, R, state.hours);
      var fresh = terms(v, 1, R, 0);

      $("zoom-switch").setAttribute("aria-checked", state.view === "zoom" ? "true" : "false");
      setTex($("usage-readout"),
        "f = 2^{-\\,\\text{usage}/\\text{share}} = 2^{-" + state.x.toFixed(2) + "} = " + f.toFixed(3),
        "f = 2^(−usage/share) = 2^(−" + state.x.toFixed(2) + ") = " + f.toFixed(3));
      setTex($("formula-display"),
        "\\text{score} = " + (v.bonus ? v.bonus + "f + " : "") + v.size + "f\\,R + h + " + v.pen + "\\,\\ln\\!\\left(\\max\\left(f,\\,10^{-7}\\right)\\right)",
        "score = " + (v.bonus ? v.bonus + "f + " : "") + v.size + "f R + h + " + v.pen + " ln(max(f, 1e-7))", true);
      var rDef = tex("\\tfrac{\\text{mem}}{8\\,\\text{GB}} + \\text{ncpus} + 32\\,\\text{ngpus}");
      if (rDef) {
        $("size-line").innerHTML = "<div class=\"eq-grid\">" +
          "<span>" + tex("R") + "</span><span>" + tex("=") + "</span><span>" + rDef + "</span>" +
          "<span></span><span>" + tex("=") + "</span><span>" +
          tex("\\tfrac{" + state.mem + "}{8} + " + state.cores + " + 32 \\times " + state.gpus + " = " + num(R, 1)) + "</span></div>";
      } else {
        $("size-line").textContent = "R = mem/8 GB + ncpus + 32 ngpus = " + num(state.mem / 8, 1) + " + " + state.cores + " + " + (32 * state.gpus) + " = " + num(R, 1);
      }

      drawTerms(v, you, fresh);

      var gap = total(fresh) - total(you);
      var chip = $("chip");
      if (Math.abs(gap) < 0.5) { chip.className = "chip ok"; chip.textContent = "Level"; }
      else if (gap > 0) { chip.className = "chip bad"; chip.textContent = "Behind by " + fmt(gap) + " points"; }
      else { chip.className = "chip ok"; chip.textContent = "Ahead by " + fmt(-gap) + " points"; }

      drawPlot();
      if (hoverX !== null && !tip.hidden) showTip(hoverX);
    }

    Array.prototype.forEach.call(root.querySelectorAll(".tex[data-tex]"), function (n) {
      setTex(n, n.getAttribute("data-tex"), n.textContent);
    });
    setGpus(STANDARD.gpus); setCores(STANDARD.cores); setMem(STANDARD.mem); setHours(STANDARD.hours); setX(STANDARD.x);
  }

  function init() {
    var root = document.getElementById("queue-score-explorer");
    if (!root || root.getAttribute("data-ready")) return;
    root.setAttribute("data-ready", "true");
    root.innerHTML = TEMPLATE;
    mount(root);
  }

  if (typeof document$ !== "undefined") document$.subscribe(init);
  else document.addEventListener("DOMContentLoaded", init);
})();
