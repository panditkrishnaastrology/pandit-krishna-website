#!/usr/bin/env python3
"""Build one plain HTML page per day from panchang-data.js, so each day's
Panchang has its own address (panchang/YYYY-MM-DD.html) that search engines
can find, plus panchang/index.html for today, and refresh sitemap.xml.

Usage: python tools/panchang_pages.py [repo_root]
"""
import html, json, os, re, sys
from datetime import datetime, timedelta, timezone

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
SITE = "https://panditkrishnaastrology.com"
IST = timezone(timedelta(hours=5, minutes=30))
e = html.escape


def load():
    src = open(os.path.join(ROOT, "panchang-data.js"), encoding="utf-8").read()
    src = src[src.index("=") + 1:].strip().rstrip(";")
    return json.loads(src)


def limb(rows):
    out = []
    for r in rows:
        when = ("then, till " if r.get("beyond") else "till ") + r["till"]
        out.append(f"<li><b>{e(r['name'])}</b> <span>{e(when)}</span></li>")
    return "<ul class='limb'>" + "".join(out) + "</ul>"


CSS = """
:root{--violet:#4A1442;--violet-deep:#2E0A28;--gold:#D4AF37;--ink:#3A1832;--muted:#6A4E60;--line:#EAD9C2;--ivory:#FDF6EA;--white:#fff;color-scheme:light}
*{box-sizing:border-box}body{margin:0;font:16px/1.6 Inter,system-ui,-apple-system,'Segoe UI',sans-serif;color:var(--ink);background:var(--ivory)}
a{color:var(--violet)}
header{background:var(--violet);color:#fff}
.wrap{max-width:980px;margin:0 auto;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
header .wrap{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;padding-block:14px}
header a{color:#fff;text-decoration:none}.brand{font:600 20px Georgia,'Times New Roman',serif}.brand small{display:block;color:var(--gold);font:600 11px Inter,sans-serif;letter-spacing:.3em}
.hero{background:var(--violet);color:#F3E3EC;padding-block:28px 40px}
.hero p.k{color:var(--gold);font-size:12px;letter-spacing:.14em;text-transform:uppercase;font-weight:600;margin:0}
h1{font:600 clamp(28px,5vw,42px)/1.15 Georgia,'Times New Roman',serif;color:#fff;margin:8px 0 10px;text-wrap:balance}
h2{font:600 24px Georgia,'Times New Roman',serif;color:var(--violet);margin:0 0 12px}
main .wrap{display:flex;flex-direction:column;gap:28px;padding-block:32px 48px}
.card{background:var(--white);border:1px solid var(--line);border-radius:6px;padding:20px 22px;min-width:0}
.grid{display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(min(100%,210px),1fr))}
.grid h3{font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:#7A5C00;margin:0 0 6px}
.limb{list-style:none;margin:0;padding:0}.limb li{margin:2px 0}.limb span{color:var(--muted);font-size:14px}
dl.kv{display:grid;grid-template-columns:max-content 1fr;gap:6px 18px;margin:0}dl.kv dt{color:var(--muted)}dl.kv dd{margin:0;font-weight:600;color:var(--violet)}
.scroll{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:15px}th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);white-space:nowrap}th{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.days{display:flex;gap:10px;flex-wrap:wrap}.days a{border:1px solid var(--line);background:var(--white);border-radius:4px;padding:6px 12px;text-decoration:none;font-size:14px}
.cta{background:var(--violet);color:#F3E3EC;border-radius:6px;padding:22px}.cta a{color:var(--gold);font-weight:600}
footer{background:var(--violet-deep);color:#CFC4E3;font-size:14px;padding-block:22px}footer a{color:#fff}
.note{color:var(--muted);font-size:14px}
"""


def page(d, days, generated, method, canonical_path, is_today):
    date = d["date"]
    label = d["date_label"]
    title = f"Panchang {label} – Bhubaneswar | Pandit Krishna Astrology"
    t0 = d["tithi"][0]["name"]; n0 = d["nakshatra"][0]["name"]
    desc = (f"Panchang for {label}, Bhubaneswar: {t0}, {n0} nakshatra, {d['yoga'][0]['name']} yoga. "
            f"Sunrise {d['sunrise']}, sunset {d['sunset']}, Rahu Kaal {d['rahu_kaal']}, hora timings and planetary positions.")
    planets = "".join(
        f"<tr><td>{e(p['planet'])}</td><td>{e(p['rashi'])} ({e(p['rashi_en'])})</td><td>{e(p['degree'])}</td>"
        f"<td>{e(p['nakshatra'])} – {p['pada']}</td><td>{'Retrograde' if p.get('retro') else ''}"
        f"{' · ' if p.get('retro') and p.get('combust') else ''}{'Combust' if p.get('combust') else ''}</td></tr>"
        for p in d["planets"])
    cities = "".join(f"<tr><td>{e(c['city'])}</td><td>{e(c['sunrise'])}</td><td>{e(c['sunset'])}</td></tr>" for c in d["cities"])
    specials = "".join(
        f"<dt>{e(y['name'])}</dt><dd>{e(y['time'])} ({'avoid' if y['kind'] == 'bad' else 'special' if y['kind'] == 'mixed' else 'auspicious'})</dd>"
        for y in d.get("special_yogas", []))
    hora = "".join(f"<tr><td>{h['n']}</td><td>{e(h['lord'])}</td><td>{e(h['time'])}</td></tr>" for h in d["hora"]["day"] + d["hora"]["night"])
    links = "".join(
        f"<a href='{x['date']}.html'{' aria-current=\"page\"' if x['date'] == date else ''}>{e(x['date_label'].split(',')[0][:3])}, {int(x['date'][8:])} "
        f"{datetime.strptime(x['date'], '%Y-%m-%d').strftime('%b')}</a>" for x in days)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'none'; style-src 'unsafe-inline'; img-src 'self' data:; object-src 'none'; base-uri 'self'; form-action 'none'; upgrade-insecure-requests"><meta name="referrer" content="strict-origin-when-cross-origin"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(title)}</title><meta name="description" content="{e(desc)}">
<link rel="canonical" href="{SITE}/{canonical_path}"><link rel="icon" href="../favicon.ico">
<meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:image" content="{SITE}/img/og-image.png">
<style>{CSS}</style></head><body>
<header><div class="wrap"><a class="brand" href="../">Pandit Krishna<small>ASTROLOGY</small></a><a href="../#book">Book a consultation</a></div></header>
<section class="hero"><div class="wrap"><p class="k">{'Today’s ' if is_today else ''}Panchang · Bhubaneswar</p><h1>{e(label)}</h1>
<p>{e(d['vara'])} · {e(d['paksha'])} · {e(d['masa_purnimanta'])} (Purnimanta) · Vikram Samvat {d['vikram_samvat']}</p></div></section>
<main><div class="wrap">
<nav class="days" aria-label="Other days">{links}</nav>
<section><h2>Pancha anga</h2><div class="grid">
<div class="card"><h3>Tithi</h3>{limb(d['tithi'])}</div>
<div class="card"><h3>Nakshatra</h3>{limb(d['nakshatra'])}</div>
<div class="card"><h3>Yoga</h3>{limb(d['yoga'])}</div>
<div class="card"><h3>Karana</h3>{limb(d['karana'])}</div></div></section>
<section class="grid">
<div class="card"><h2>Sun and Moon</h2><dl class="kv"><dt>Sunrise</dt><dd>{e(d['sunrise'])}</dd><dt>Sunset</dt><dd>{e(d['sunset'])}</dd><dt>Moonrise</dt><dd>{e(d['moonrise'])}</dd><dt>Moonset</dt><dd>{e(d['moonset'])}</dd><dt>Moon sign</dt><dd>{e(d['moon_rashi'])}</dd><dt>Sun sign</dt><dd>{e(d['sun_rashi'])}</dd></dl></div>
<div class="card"><h2>Timings</h2><dl class="kv"><dt>Rahu Kaal</dt><dd>{e(d['rahu_kaal'])}</dd><dt>Yamaganda</dt><dd>{e(d['yamaganda'])}</dd><dt>Gulika</dt><dd>{e(d['gulika'])}</dd><dt>Abhijit</dt><dd>{e(d['abhijit'])}</dd><dt>Brahma muhurta</dt><dd>{e(d['brahma_muhurta'])}</dd>{specials}</dl></div>
<div class="card"><h2>Calendar</h2><dl class="kv"><dt>Month (Amanta)</dt><dd>{e(d['masa_amanta'])}</dd><dt>Month (Purnimanta)</dt><dd>{e(d['masa_purnimanta'])}</dd><dt>Ritu</dt><dd>{e(d['ritu'])}</dd><dt>Ayana</dt><dd>{e(d['ayana'])}</dd><dt>Shaka Samvat</dt><dd>{d['shaka_samvat']}</dd></dl></div>
</section>
<section class="card"><h2>Planetary positions</h2><p class="note">Sidereal (Lahiri), at {e(d['positions_at'])}. {e(d['planet_note'])}</p>
<div class="scroll"><table><thead><tr><th>Graha</th><th>Rashi</th><th>Degree</th><th>Nakshatra – pada</th><th>Status</th></tr></thead><tbody>{planets}</tbody></table></div></section>
<section class="grid">
<div class="card"><h2>Sunrise and sunset</h2><div class="scroll"><table><thead><tr><th>City</th><th>Sunrise</th><th>Sunset</th></tr></thead><tbody>{cities}</tbody></table></div></div>
<div class="card"><h2>Hora lords</h2><div class="scroll"><table><thead><tr><th>#</th><th>Lord</th><th>Time (IST)</th></tr></thead><tbody>{hora}</tbody></table></div><p class="note">Hours 1–12 run from sunrise to sunset, 13–24 from sunset to the next sunrise.</p></div>
</section>
<div class="cta">For a personal reading, Prasna or a course, <a href="../#book">book with Pandit Krishna</a> by WhatsApp or phone, +91 96680 24876. <a href="../#panchang">Open the interactive Panchang</a> in 10 languages.</div>
<p class="note">All times IST for Bhubaneswar unless stated. {e(method)}. Updated {e(generated)}.</p>
</div></main>
<footer><div class="wrap">© Pandit Krishna Astrology · Bhubaneswar, Odisha · <a href="../#privacy">Privacy Policy</a> · <a href="../#disclaimer">Disclaimer</a></div></footer>
</body></html>
"""


def main():
    data = load()
    days = data["days"]
    out = os.path.join(ROOT, "panchang")
    os.makedirs(out, exist_ok=True)
    today = datetime.now(IST).date().isoformat()
    for d in days:
        with open(os.path.join(out, d["date"] + ".html"), "w", encoding="utf-8") as fh:
            fh.write(page(d, days, data["generated"], data["method"], f"panchang/{d['date']}.html", False))
    first = next((d for d in days if d["date"] == today), days[0])
    with open(os.path.join(out, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(page(first, days, data["generated"], data["method"], "panchang/", True))
    n = write_sitemap(ROOT)
    print(f"wrote {len(days)} day pages + index; sitemap has {n} URLs")


def write_sitemap(root):
    """sitemap.xml: home, Panchang (today + every dated page), the section pages
    (consultation, courses, about, muhurta), blog list and every published blog
    post page. Shared with blog_pages.py and site_pages.py."""
    today = datetime.now(IST).date().isoformat()
    urls = [(f"{SITE}/", today, "weekly", "1.0"), (f"{SITE}/panchang/", today, "daily", "0.9")]
    for page, freq, prio in (("consultation", "monthly", "0.9"), ("courses", "monthly", "0.9"),
                             ("about", "monthly", "0.8"), ("muhurta", "weekly", "0.8")):
        f = os.path.join(root, page, "index.html")
        if os.path.isfile(f) and 'http-equiv="refresh"' not in open(f, encoding="utf-8").read(2000):
            urls.append((f"{SITE}/{page}/", today, freq, prio))
    pdir = os.path.join(root, "panchang")
    dated = sorted(f[:-5] for f in os.listdir(pdir) if re.fullmatch(r"\d{4}-\d{2}-\d{2}\.html", f)) if os.path.isdir(pdir) else []
    bdir = os.path.join(root, "blog")
    posts = sorted((x for x in os.listdir(bdir) if re.fullmatch(r"\d{4}-\d{2}-\d{2}", x)
                    and os.path.isfile(os.path.join(bdir, x, "index.html"))), reverse=True) if os.path.isdir(bdir) else []
    if posts:
        urls.append((f"{SITE}/blog/", posts[0], "daily", "0.8"))
        urls += [(f"{SITE}/blog/{x}/", x, "monthly", "0.6") for x in posts]
    urls += [(f"{SITE}/panchang/{x}.html", x if x <= today else today, "monthly", "0.5") for x in dated]
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    xml += [f"  <url><loc>{u}</loc><lastmod>{m}</lastmod><changefreq>{c}</changefreq><priority>{p}</priority></url>" for u, m, c, p in urls]
    xml.append("</urlset>")
    open(os.path.join(root, "sitemap.xml"), "w", encoding="utf-8").write("\n".join(xml) + "\n")
    return len(urls)


if __name__ == "__main__":
    main()
