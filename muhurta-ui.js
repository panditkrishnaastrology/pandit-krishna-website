/* Pandit Krishna Astrology — "Know your auspicious time": the form and the results.
   The times are worked out in the visitor's own browser (muhurta-engine.js) from the
   day's Panchang data (muhurta-data.js). Nothing entered is stored or sent anywhere,
   so the page puts no load on any server.
   Text is built here in the visitor's language (English below; other languages
   come from lang-xx.js under keys "MH.…"). */
(function () {
  "use strict";
  var I = window.PK_I18N;
  var $ = function (id) { return document.getElementById(id); };
  var lg = $("mhLagna"), rs = $("mhRashi"), nk = $("mhNak"), form = $("mhForm"), out = $("mhOut");
  if (!form) return;

  var EN = {
    "notknown": "Not known", "pada": "pada {1}",
    "h": "Auspicious times for {1}", "h_name": "{2}: auspicious times for {1}",
    "p.general": "general work", "p.marriage": "marriage", "p.travel": "travel",
    "p.meeting": "a meeting or agreement", "p.job": "a job or joining work", "p.dating": "dating", "p.purchase": "a purchase", "p.sale": "a sale",
    "count": "{1} suitable windows in the next 7 days (Bhubaneswar time).", "count1": "1 suitable window in the next 7 days (Bhubaneswar time).",
    "none7": "No suitable window in the next 7 days for these details. Please contact Pandit Krishna for a personal muhurta.",
    "gen": "These times are general, from the day’s Panchang. They are not specific to you. Add your lagna, rashi and nakshatra for times suited to your own chart.",
    "partial": "Not given: {1}. Those checks were skipped. Add them for more personal results.",
    "it.lagna": "lagna", "it.rashi": "rashi", "it.nak": "nakshatra", "and": " and ",
    "avoid": "Avoid:", "bad.Rahu Kaal": "Rahu Kaal", "bad.Yamaganda": "Yamaganda", "bad.Gulika Kaal": "Gulika Kaal", "bad.Durmuhurta": "Durmuhurta",
    "bad.Varjyam": "Varjyam", "bad.Gandanta": "Gandanta",
    "bad.Mrityu Yoga": "Mrityu Yoga", "bad.Utpata Yoga": "Utpata Yoga", "bad.Yamaghanta Yoga": "Yamaghanta Yoga", "bad.Dagdha Yoga": "Dagdha Yoga", "bad.Visha Yoga": "Visha Yoga",
    "special": "Special yogas:", "S_good": "{1} (auspicious yoga)", "S_bad": "{1} (inauspicious yoga)", "S_mixed": "{1}: the result of the act repeats",
    "noday": "No suitable time on this day.",
    "D1": "Disha shool: avoid starting a journey towards the {1} today.",
    "dir.East": "East", "dir.West": "West", "dir.North": "North", "dir.South": "South",
    "C1": "{1} is combust (asta): marriage is traditionally not fixed now.",
    "C2": "Chaturmas (Ashadha Shukla Ekadashi to Kartika Shukla Ekadashi): marriage is traditionally not held now.",
    "C3": "Sun in {1} (Kharmas): marriage is traditionally not held now.",
    "G1": "Guru in Simha (Simhastha Guru) is inauspicious for marriage. The marriage times below are given without considering Guru in Simha.",
    "lv.Excellent": "Excellent", "lv.Very good": "Very good", "lv.Good": "Good",
    "F_lagna": "{1} lagna", "F_moon": "Moon in {1}", "F_nak": "{1} nakshatra", "F_nakT": "{1} nakshatra · {2} tara",
    "W1": "{1} nakshatra suits {2}", "W2": "{1} tithi is favourable", "W3": "{1} lagna suits {2}",
    "W4": "Jupiter in a kendra from the lagna", "W5": "Venus in a kendra from the lagna",
    "W6": "Sun or Jupiter in the 10th from the lagna", "W7": "Mercury in a kendra from the lagna", "W8": "Abhijit muhurta",
    "W9": "{1} tara from your birth star", "W10": "Chandra bala: Moon in the {1} from your rashi", "W12": "Moon in the {1} from the muhurta lagna",
    "tara.Janma": "Janma", "tara.Sampat": "Sampat", "tara.Vipat": "Vipat", "tara.Kshema": "Kshema", "tara.Pratyak": "Pratyak",
    "tara.Sadhaka": "Sadhaka", "tara.Naidhana": "Naidhana", "tara.Mitra": "Mitra", "tara.Parama Mitra": "Parama Mitra", "F_yoga": "{1} yoga", "F_kar": "{1} karana",
    "dl_all": "Save all 7 days as PDF", "dl_day": "Save this day as PDF",
    "prepd": "Prepared on {1}", "pdf": "Auspicious times",
    "tag": "Vedic, Nadi and Prasna Jyotish · Vedic Numerology",
    "det": "Lagna: {1} · Rashi: {2} · Nakshatra: {3}", "c_time": "Time (IST)", "c_rate": "Rating", "c_pan": "Panchang at that time", "c_why": "Notes", "pf": "For a personal muhurta based on your full birth chart, contact Pandit Krishna.",
    "loading": "Loading…", "failed": "The times could not be loaded. Please check your connection and try again."
  };
  var LV = ["Good", "Very good", "Excellent"];
  var RS_EN = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"];
  var RS = ["Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya", "Tula", "Vrishchika", "Dhanu", "Makara", "Kumbha", "Meena"];
  var NAK = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha",
    "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula",
    "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"];
  var MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  var NUM = { hi: "०१२३४५६७८९", mr: "०१२३४५६७८९", or: "୦୧୨୩୪୫୬୭୮୯", bn: "০১২৩৪৫৬৭৮৯", gu: "૦૧૨૩૪૫૬૭૮૯", te: "౦౧౨౩౪౫౬౭౮౯", kn: "೦೧೨೩೪೫೬೭೮೯" };

  function lang() { return document.documentElement.lang || "en"; }
  function dict() { return I && lang() !== "en" ? I.get(lang()) : null; }
  function t(key, args) {
    var d = dict(), s = (d && d.text && d.text["MH." + key]) || EN[key] || key;
    return s.replace(/\{(\d)\}/g, function (m, n) { return args[+n - 1]; });
  }
  function name(x) { var d = dict(); return d ? d.phrase(String(x)) : String(x); }
  function yname(x) { var d = dict(); return (d && d.text && d.text[x]) || name(x); }
  function ord(n) {
    if (lang() !== "en") return String(n);
    var s = n % 100 > 10 && n % 100 < 14 ? "th" : ({ 1: "st", 2: "nd", 3: "rd" })[n % 10] || "th";
    return n + s;
  }
  function num(s) {
    var d = NUM[lang()]; if (!d) return s;
    return s.replace(/[0-9]/g, function (c) { return d.charAt(+c); });
  }
  function el(tag, cls, txt) { var e = document.createElement(tag); if (cls) e.className = cls; if (txt != null) e.textContent = num(txt); return e; }

  /* time in IST, with the date added when it falls after midnight */
  function fmt(ts) {
    var d = new Date((ts + 19800) * 1000), h = d.getUTCHours(), m = d.getUTCMinutes();
    return (h % 12 || 12) + ":" + (m < 10 ? "0" : "") + m + " " + (h >= 12 ? "PM" : "AM");
  }
  function time(ts, dayIso) {
    var d = new Date((ts + 19800) * 1000);
    return fmt(ts) + (d.toISOString().slice(0, 10) !== dayIso ? " (" + name(d.getUTCDate() + " " + MON[d.getUTCMonth()]) + ")" : "");
  }

  function span(s, e, dayIso) {
    var a = time(s, dayIso), b = time(e, dayIso), ia = a.indexOf(" ("), ib = b.indexOf(" (");
    if (ia > 0 && ib > 0 && a.slice(ia) === b.slice(ib)) a = a.slice(0, ia);
    return a + "–" + b;
  }

  /* nakshatras (with padas) that fall in a rashi */
  function naksInRashi(r) {
    var res = [], w = 360 / 27;
    for (var n = 0; n < 27; n++) {
      var padas = [];
      for (var p = 0; p < 4; p++) if (Math.floor((n * w + p * w / 4 + 0.001) / 30) === r) padas.push(p + 1);
      if (padas.length) res.push({ n: n, padas: padas });
    }
    return res;
  }

  /* ---- the three lists ---- */
  function fillSelect(sel, items) {
    var keep = sel.value; sel.textContent = "";
    sel.appendChild(new Option(t("notknown"), ""));
    items.forEach(function (it) { sel.appendChild(new Option(it[1], it[0])); });
    sel.value = items.some(function (it) { return String(it[0]) === keep; }) ? keep : "";
  }
  function rashiLabel(i) { return lang() === "en" ? RS[i] + " (" + RS_EN[i] + ")" : name(RS[i]); }
  function lists() {
    var r = RS.map(function (_, i) { return [i, rashiLabel(i)]; });
    fillSelect(lg, r); fillSelect(rs, r);
    var naks = rs.value === "" ? NAK.map(function (_, n) { return { n: n, padas: [1, 2, 3, 4] }; }) : naksInRashi(+rs.value);
    fillSelect(nk, naks.map(function (x) {
      return [x.n, name(NAK[x.n]) + (x.padas.length === 4 ? "" : " (" + num(t("pada", [x.padas.join(", ")])) + ")")];
    }));
  }
  rs.addEventListener("change", lists);

  /* ---- results ---- */
  var last = null;
  /* reasons shown to visitors: the classical ones only */
  var SHOW = ["W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8", "W9", "W10", "W12"];
  function compute(natal, purpose) {
    var F = window.PK_MUHURTA_FINDER, D = window.PK_MUHURTA;
    if (!F || !D || !D.days || !D.days.length) throw new Error("data");
    var res = F.find({ lagna: natal.lagna, rashi: natal.rashi, nak: natal.nak }, purpose, D.days[0].sunrise - 1);
    var wins = [], days = res.map(function (d) {
      return { date: d.day.date, label: d.day.label, jupiter: d.day.planets.jupiter.sign, warn: d.warn, special: d.day.special || [],
        avoid: Object.keys(d.day.bad).reduce(function (a, k) {
          var v = d.day.bad[k]; (typeof v[0] === "number" ? [v] : v).forEach(function (s) { a.push([k, s[0], s[1]]); }); return a;
        }, []) };
    });
    res.forEach(function (d, di) {
      d.wins.forEach(function (w) {
        var f = w.j.facts;
        wins.push([di, w.start, w.end, LV.indexOf(w.level), f.lagna, f.moon, f.nak, f.tithi, f.yoga, f.karana, f.tara,
          w.j.why.filter(function (r) { return SHOW.indexOf(r[0]) >= 0; })]);
      });
    });
    return { days: days, wins: wins };
  }

  function factsOf(w) {
    return [t("F_lagna", [name(w[4])]), t("F_moon", [name(w[5])]), w[10] ? t("F_nakT", [name(w[6]), t("tara." + w[10])]) : t("F_nak", [name(w[6])]),
      name(w[7]), t("F_yoga", [name(w[8])]), t("F_kar", [name(w[9])])];
  }
  function whyOf(w, d) {
    var res = [];
    d.special.filter(function (x) { return x[2] < w[2] && x[3] > w[1]; }).forEach(function (x) {
      res.push({ s: t(x[1] === "good" ? "S_good" : x[1] === "bad" ? "S_bad" : "S_mixed", [yname(x[0])]), cls: x[1] === "good" ? "mh-sy" : x[1] === "bad" ? "mh-sb" : null });
    });
    (w[11] || []).forEach(function (r) {
      var k = r[0], s;
      if (k === "W1" || k === "W3") s = t(k, [name(r[1]), t("p." + r[2])]);
      else if (k === "W2") s = t(k, [name(r[1])]);
      else if (k === "W9") s = t(k, [t("tara." + r[1])]);
      else if (k === "W10" || k === "W12") s = t(k, [ord(r[1])]);
      else s = t(k, []);
      res.push({ s: s, cls: null });
    });
    return res;
  }
  function avoidOf(d) { return d.avoid.map(function (x) { return t("bad." + x[0]) + " " + span(x[1], x[2], d.date); }).join(" · "); }
  function specialOf(d) { return d.special.map(function (x) { return yname(x[0]) + " " + span(x[2], x[3], d.date); }).join(" · "); }
  function warnOf(w) { return w[0] === "D1" ? t("D1", [t("dir." + w[1])]) : w[0] === "C2" ? t("C2", []) : t(w[0], [name(w[1])]); }
  var shown = [], notices = [], countLine = "";

  function render(data) {
    if (!last) return;
    if (!data) { out.textContent = ""; out.appendChild(el("p", "mh-none", t("loading"))); return; }
    var natal = last.natal, purpose = last.purpose, now = Math.floor(Date.now() / 1000);
    var byDay = data.days.map(function () { return []; });
    data.wins.forEach(function (w) { if (w[2] > now) byDay[w[0]].push(w); });
    var total = byDay.reduce(function (a, d) { return a + d.length; }, 0);

    out.textContent = ""; shown = []; notices = [];
    var head = el("div", "mh-res-head"), who = last.name;
    head.appendChild(el("h3", null, who ? t("h_name", [t("p." + purpose), who]) : t("h", [t("p." + purpose)])));
    countLine = total === 1 && lang() === "en" ? t("count1", []) : total ? t("count", [String(total)]) : t("none7");
    head.appendChild(el("p", null, countLine));
    var miss = [];
    if (natal.lagna == null) miss.push(t("it.lagna"));
    if (natal.rashi == null) miss.push(t("it.rashi"));
    if (natal.nak == null) miss.push(t("it.nak"));
    if (miss.length === 3) notices.push(["", t("gen")]);
    else if (miss.length) notices.push(["", t("partial", [miss.join(t("and"))])]);
    if (purpose === "marriage" && data.days.some(function (d) { return d.jupiter === 4; })) notices.push([" mh-warn", t("G1")]);
    notices.forEach(function (n) { head.appendChild(el("p", "mh-gen" + n[0], n[1])); });
    var dlAll = el("button", "mh-dl", t("dl_all")); dlAll.type = "button"; dlAll.setAttribute("data-mh-dl", "all");
    head.appendChild(dlAll);
    out.appendChild(head);

    data.days.forEach(function (d, di) {
      var dayEnd = d.avoid.reduce(function (a, x) { return Math.max(a, x[2]); }, 0);
      if (dayEnd && dayEnd < now && !byDay[di].length) return;   // a day that is already over
      shown.push({ d: d, di: di, wins: byDay[di] });
      var box = el("div", "mh-day"), top = el("div", "mh-day-top");
      top.appendChild(el("h4", null, name(d.label)));
      var dl = el("button", "mh-dl mh-dl-s", t("dl_day")); dl.type = "button"; dl.setAttribute("data-mh-dl", String(di));
      top.appendChild(dl); box.appendChild(top); box.setAttribute("data-mh-day", String(di));
      var av = el("p", "mh-avoid"); av.appendChild(el("b", null, t("avoid") + " "));
      av.appendChild(document.createTextNode(num(avoidOf(d)))); box.appendChild(av);
      if (d.special.length) {
        var sp = el("p", "mh-avoid mh-special"); sp.appendChild(el("b", null, t("special") + " "));
        sp.appendChild(document.createTextNode(num(specialOf(d))));
        box.appendChild(sp);
      }
      d.warn.forEach(function (w) {
        box.appendChild(el("p", "mh-avoid", warnOf(w)));
      });
      if (!byDay[di].length) box.appendChild(el("p", "mh-none", t("noday")));
      byDay[di].forEach(function (w) {
        var level = LV[w[3]];
        var c = el("div", "mh-win"), top = el("div", "mh-win-top");
        top.appendChild(el("span", "mh-time", span(w[1], w[2], d.date).replace("–", " – ")));
        top.appendChild(el("span", "mh-badge" + (level === "Excellent" ? " ex" : ""), t("lv." + level)));
        c.appendChild(top);
        var chips = el("div", "mh-facts");
        factsOf(w).forEach(function (x) { chips.appendChild(el("span", null, x)); });
        c.appendChild(chips);
        var why = whyOf(w, d);
        if (why.length) {
          var ul = el("ul", "mh-why");
          why.forEach(function (r) { ul.appendChild(el("li", r.cls, r.s)); });
          c.appendChild(ul);
        }
        box.appendChild(c);
      });
      out.appendChild(box);
    });
  }
  function show() {
    if (!last) return;
    var data;
    try { data = compute(last.natal, last.purpose); }
    catch (e) { out.textContent = ""; out.appendChild(el("p", "mh-none", t("failed"))); return; }
    render(data);
  }

  form.addEventListener("submit", function (ev) {
    ev.preventDefault();
    var v = function (e) { return e.value === "" ? null : +e.value; };
    last = { natal: { lagna: v(lg), rashi: v(rs), nak: v(nk) },
      purpose: (form.querySelector("input[name=mhP]:checked") || {}).value || "general",
      name: $("mhName").value.trim().slice(0, 40) };
    show();
    out.scrollIntoView({ behavior: "smooth", block: "start" });
  });

  /* save as PDF: the browser prints only the chosen day(s) with a branded header.
     The PDF is made on the visitor's device; nothing is sent anywhere. */
  function savePdf(which) {
    var old = document.getElementById("mhPrint"); if (old) old.remove();
    var pr = document.createElement("div"); pr.id = "mhPrint"; pr.setAttribute("data-noi18n", "");
    function raw(tag, cls, txt) { var s = document.createElement(tag); if (cls) s.className = cls; s.textContent = txt; return s; }
    function cell(tag, cls, txt, span) { var c = el(tag, cls, txt); if (span) c.colSpan = span; return c; }
    var now = new Date(Date.now() + 19800000);
    var when = name(now.getUTCDate() + " " + MON[now.getUTCMonth()]) + " " + now.getUTCFullYear();

    /* page frame: the footer repeats on every page */
    var frame = document.createElement("table"); frame.className = "mhp-frame";
    var tf = document.createElement("tfoot"), tb = document.createElement("tbody");
    var fr = document.createElement("tr"), fc = document.createElement("td"); fc.className = "mhp-foot";
    fc.appendChild(el("span", null, t("pf")));
    fc.appendChild(raw("span", null, "Pandit Krishna Astrology  ·  +91 96680 24876  ·  panditkrishnaastrology.com"));
    fr.appendChild(fc); tf.appendChild(fr);
    var br = document.createElement("tr"), body = document.createElement("td"); br.appendChild(body); tb.appendChild(br);
    frame.appendChild(tf); frame.appendChild(tb); pr.appendChild(frame);

    /* letterhead */
    var hd = el("div", "mhp-head"), logo = document.querySelector(".site-header .logo");
    if (logo) { var lg2 = logo.cloneNode(true); lg2.setAttribute("width", "70"); lg2.setAttribute("height", "70"); hd.appendChild(lg2); }
    var bt = el("div", "mhp-brand");
    bt.appendChild(raw("b", null, "Pandit Krishna Astrology"));
    bt.appendChild(el("span", "mhp-tag", t("tag")));
    bt.appendChild(raw("span", null, "Lane-7, Mallik Complex, Jagamara, Bhubaneswar, Odisha – 751030"));
    bt.appendChild(raw("span", null, "Phone / WhatsApp: +91 96680 24876  ·  Email: panditkrishnaastrology2026@gmail.com"));
    bt.appendChild(raw("span", null, "Web: panditkrishnaastrology.com"));
    hd.appendChild(bt); body.appendChild(hd);

    /* title block */
    var tl = el("div", "mhp-title");
    tl.appendChild(el("h1", null, last.name ? t("h_name", [t("p." + last.purpose), last.name]) : t("h", [t("p." + last.purpose)])));
    var nat = last.natal, nk = function (v, f) { return v == null ? t("notknown") : f(v); };
    tl.appendChild(el("p", "mhp-meta", t("det", [nk(nat.lagna, function (v) { return name(RS[v]); }), nk(nat.rashi, function (v) { return name(RS[v]); }), nk(nat.nak, function (v) { return name(NAK[v]); })])
      + "  ·  " + t("prepd", [when])));
    tl.appendChild(el("p", "mhp-meta", countLine));
    notices.forEach(function (n) { tl.appendChild(el("p", "mhp-notice" + n[0], n[1])); });
    body.appendChild(tl);

    /* one table per day; its date band repeats if the day runs onto the next page */
    shown.forEach(function (s) {
      if (which !== "all" && String(s.di) !== which) return;
      var d = s.d, tbl = document.createElement("table"); tbl.className = "mhp-day";
      var th = document.createElement("thead"), r1 = document.createElement("tr"), r2 = document.createElement("tr");
      r1.appendChild(cell("th", "mhp-date", name(d.label) + " " + d.date.slice(0, 4), 4));
      [t("c_time"), t("c_rate"), t("c_pan"), t("c_why")].forEach(function (x) { r2.appendChild(cell("th", "mhp-col", x)); });
      th.appendChild(r1); th.appendChild(r2); tbl.appendChild(th);
      var tbd = document.createElement("tbody");
      var info = document.createElement("tr"), ic = document.createElement("td"); ic.colSpan = 4; ic.className = "mhp-info";
      var pa = el("p", null); pa.appendChild(el("b", null, t("avoid") + " ")); pa.appendChild(document.createTextNode(num(avoidOf(d)))); ic.appendChild(pa);
      if (d.special.length) { var ps = el("p", null); ps.appendChild(el("b", null, t("special") + " ")); ps.appendChild(document.createTextNode(num(specialOf(d)))); ic.appendChild(ps); }
      d.warn.forEach(function (w) { ic.appendChild(el("p", null, warnOf(w))); });
      info.appendChild(ic); tbd.appendChild(info);
      if (!s.wins.length) { var nr = document.createElement("tr"); nr.appendChild(cell("td", "mhp-none", t("noday"), 4)); tbd.appendChild(nr); }
      s.wins.forEach(function (w) {
        var tr = document.createElement("tr"), lv = LV[w[3]];
        tr.appendChild(cell("td", "mhp-time", span(w[1], w[2], d.date)));
        tr.appendChild(cell("td", "mhp-rate" + (lv === "Excellent" ? " ex" : ""), t("lv." + lv)));
        tr.appendChild(cell("td", "mhp-pan", factsOf(w).join(" · ")));
        var wc = document.createElement("td"); wc.className = "mhp-why";
        whyOf(w, d).forEach(function (r) { wc.appendChild(el("div", r.cls, r.s)); });
        tr.appendChild(wc); tbd.appendChild(tr);
      });
      tbl.appendChild(tbd); body.appendChild(tbl);
    });

    var note = document.querySelector('[data-view="muhurta"] .mh-note');
    if (note) { var nn = note.cloneNode(true); nn.className = "mhp-note"; body.appendChild(nn); }
    document.body.appendChild(pr);

    var title = document.title;
    document.title = t("pdf") + " – " + (last.name ? last.name + " – " : "") + t("p." + last.purpose) + " | Pandit Krishna Astrology";
    document.documentElement.classList.add("mh-printing");
    function done() {
      document.documentElement.classList.remove("mh-printing"); document.title = title;
      window.removeEventListener("afterprint", done);
    }
    window.addEventListener("afterprint", done);
    setTimeout(function () { window.print(); }, 50);   /* the class only affects printing, so it can stay until afterprint */
  }
  out.addEventListener("click", function (e) {
    var b = e.target.closest && e.target.closest("[data-mh-dl]");
    if (b && last) savePdf(b.getAttribute("data-mh-dl"));
  });

  /* links elsewhere on the site can preselect a purpose: data-mh-purpose="marriage" */
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("[data-mh-purpose]"); if (!a) return;
    var r = form.querySelector('input[name=mhP][value="' + a.getAttribute("data-mh-purpose") + '"]');
    if (r) r.checked = true;
  });

  /* redraw in the new language when it changes, and when its text file arrives */
  function redo() { lists(); if (last) show(); }
  new MutationObserver(redo).observe(document.documentElement, { attributes: true, attributeFilter: ["lang"] });
  if (I) { var prev = I.onText; I.onText = function (c) { if (prev) prev(c); redo(); }; }
  lists();
})();
