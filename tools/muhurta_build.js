#!/usr/bin/env node
/* Pandit Krishna Astrology — builds the finished results for "Know your auspicious time".
   The rules (muhurta.js) are kept encrypted in tools/muhurta-rules.enc and decrypted only
   inside the nightly GitHub Action; they are never published. This script runs every
   combination of lagna, rashi, nakshatra and purpose and writes only the answers to
   muhurta-results/<purpose>.json.
   Usage: node tools/muhurta_build.js <path to decrypted muhurta.js> [outdir] */
"use strict";
const fs = require("fs"), path = require("path");
const root = path.join(__dirname, "..");
global.window = {};
require(path.join(root, "muhurta-data.js"));
require(path.resolve(process.argv[2]));
const F = window.PK_MUHURTA_FINDER, D = window.PK_MUHURTA;
const out = process.argv[3] || path.join(root, "muhurta-results");
fs.mkdirSync(out, { recursive: true });
const LV = ["Good", "Very good", "Excellent"];
const SHOW = ["W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8", "W9", "W10", "W11", "W12"];

/* every choice a visitor can make: lagna (or none) x rashi (or none) x nakshatra in that rashi (or none) */
const combos = [];
for (let l = -1; l < 12; l++)
  for (let r = -1; r < 12; r++) {
    const naks = r < 0 ? [...Array(27).keys()] : F.naksInRashi(r).map(x => x.n);
    for (const n of [-1, ...naks]) combos.push([l, r, n]);
  }

for (const purpose of Object.keys(F.PURPOSE)) {
  const wins = [], index = new Map(), map = {};
  let days = null;
  for (const [l, r, n] of combos) {
    const res = F.find({ lagna: l < 0 ? null : l, rashi: r < 0 ? null : r, nak: n < 0 ? null : n }, purpose, D.days[0].sunrise - 1);
    if (!days) days = res.map(d => ({
      date: d.day.date, label: d.day.label, jupiter: d.day.planets.jupiter.sign,
      avoid: Object.keys(d.day.bad).flatMap(k => {
        const v = d.day.bad[k]; return (typeof v[0] === "number" ? [v] : v).map(s => [k, s[0], s[1]]);
      }),
      warn: d.warn
    }));
    const ids = [];
    res.forEach((d, di) => d.wins.forEach(w => {
      const f = w.j.facts;
      /* reasons shown to visitors: the list SHOW above (all of them for now) */
      const why = w.j.why.filter(r => SHOW.indexOf(r[0]) >= 0);
      const row = [di, w.start, w.end, LV.indexOf(w.level), f.lagna, f.moon, f.nak, f.tithi, f.yoga, f.karana, f.tara, why, f.lh, f.cb];
      const key = JSON.stringify(row);
      if (!index.has(key)) { index.set(key, wins.length); wins.push(row); }
      ids.push(index.get(key).toString(36));
    }));
    map[[l, r, n].join(",")] = ids.join(".");
  }
  fs.writeFileSync(path.join(out, purpose + ".json"),
    JSON.stringify({ generated: D.generated, purpose, days, wins, map }));
  console.log(purpose, wins.length, "windows,", combos.length, "choices");
}
