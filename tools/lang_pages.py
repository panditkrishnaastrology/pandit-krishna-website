#!/usr/bin/env python3
"""Pages for each site language, so searches in Hindi, Odia and the other
languages can find the site:

  hi/index.html, or/index.html, …   the main site, opening in that language
                                    (a copy of index.html with data-pk-lang)
  hi/blog/YYYY-MM-DD/index.html …   each blog post in that language, from the
  hi/blog/index.html                translations stored in blog-data.js (tr)

Every version links to the others with hreflang. Page wording comes from the
site's own translation files (i18n.js and lang-*.js), read with node.
Legal pages stay in English, as on the main site.

Usage: python tools/lang_pages.py [repo_root]
"""
import html, json, os, re, shutil, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from panchang_pages import CSS, SITE, write_sitemap  # noqa: E402
import blog_pages as BP  # noqa: E402

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
BP.ROOT = ROOT
e = html.escape
CODES = ["hi", "or", "bn", "te", "ta", "gu", "mr", "kn", "ml"]
NUM = {"hi": "०१२३४५६७८९", "mr": "०१२३४५६७८९", "or": "୦୧୨୩୪୫୬୭୮୯", "bn": "০১২৩৪৫৬৭৮৯",
       "gu": "૦૧૨૩૪૫૬૭૮૯", "te": "౦౧౨౩౪౫౬౭౮౯", "kn": "೦೧೨೩೪೫೬೭೮೯"}  # ta, ml keep 0-9 (owner's choice)

NODE_DUMP = r"""
global.window={}; const path=require('path'); const R=process.argv[1];
require(path.join(R,'i18n.js')); const I=window.PK_I18N; const out={};
for(const c of %s){ require(path.join(R,'lang-'+c+'.js')); const d=I.get(c); const i=I.langs.findIndex(l=>l[0]===c)-1;
  out[c]={s:Object.assign({},d.exact,d.text), wd:I._T.wd[i].split('|'), month:I._T.month[i].split('|'), city:I._T.city[i].split('|')[0], name:I.langs[i+1][1]}; }
process.stdout.write(JSON.stringify(out));
""" % json.dumps(CODES)


def load_dicts():
    r = subprocess.run(["node", "-e", NODE_DUMP, os.path.abspath(ROOT)], capture_output=True, text=True, check=True)
    return json.loads(r.stdout)


def num(code, s):
    d = NUM.get(code)
    return re.sub(r"[0-9]", lambda m: d[int(m.group(0))], s) if d else s


def t(D, code, en):
    return D[code]["s"].get(en, en)


def alternates(paths):
    """paths: {code: path}; 'en' is the English page. Adds x-default."""
    links = [f'<link rel="alternate" hreflang="{c}" href="{SITE}{p}">' for c, p in paths.items()]
    if "en" in paths:
        links.append(f'<link rel="alternate" hreflang="x-default" href="{SITE}{paths["en"]}">')
    return "".join(links)


# ---------- language home pages ----------

def home_pages(D):
    src = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    for code in CODES:
        L = D[code]
        va, bnn, pj, vn = (t(D, code, x) for x in ("Vedic astrology", "Bhrigu Nandi Nadi", "Prasna Jyotish", "Vedic numerology"))
        title = f"Pandit Krishna Astrology | {va}, {bnn}, {pj}, {L['city']}"
        desc = (f"Pandit Krishna Astrology, {L['city']}: {va}, {bnn}, {pj}, {vn}. "
                f"{t(D, code, 'Consultation')} · {t(D, code, 'Learn Astrology')} · {t(D, code, 'Today’s Panchang')}.")
        h = src
        h = h.replace('<html lang="en">', f'<html lang="{code}" data-pk-lang="{code}">', 1)
        h = re.sub(r"<title>.*?</title>", f"<title>{e(title)}</title>", h, count=1)
        h = re.sub(r'<meta name="description" content="[^"]*">', f'<meta name="description" content="{e(desc)}">', h, count=1)
        h = re.sub(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{e(title)}">', h, count=1)
        h = re.sub(r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{e(desc)}">', h, count=1)
        h = h.replace(f'<link rel="canonical" href="{SITE}/">', f'<link rel="canonical" href="{SITE}/{code}/">', 1)
        h = h.replace(f'<meta property="og:url" content="{SITE}/">', f'<meta property="og:url" content="{SITE}/{code}/">', 1)
        h = h.replace('<meta property="og:locale" content="en_IN">', f'<meta property="og:locale" content="{code}_IN">', 1)
        # files sit one folder down: load scripts from the site root
        h = re.sub(r'<script src="(?!/|https?:)([^"]+)"', r'<script src="/\1"', h)
        h = h.replace('sc.src="lang-"', 'sc.src="/lang-"')
        h = h.replace(f'href="{SITE}/blog/"', f'href="/{code}/blog/"')
        for need in (f'data-pk-lang="{code}"', f'canonical" href="{SITE}/{code}/"', 'sc.src="/lang-"'):
            if need not in h:
                raise SystemExit(f"lang page {code}: could not set {need!r}; index.html changed?")
        os.makedirs(os.path.join(ROOT, code), exist_ok=True)
        with open(os.path.join(ROOT, code, "index.html"), "w", encoding="utf-8") as fh:
            fh.write(h)


# ---------- language blog pages ----------

def nice(D, code, date):
    y, m, d = (int(x) for x in date.split("-"))
    from datetime import date as _d
    wd = D[code]["wd"][(_d(y, m, d).weekday() + 1) % 7]
    return num(code, f"{wd}, {d} {D[code]['month'][m - 1]} {y}")


def page(D, code, title, desc, path, alts, body, og="article", ld=""):
    L = D[code]
    return f"""<!doctype html>
<html lang="{code}"><head><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="{BP.CSP}"><meta name="referrer" content="strict-origin-when-cross-origin"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(title)}</title><meta name="description" content="{e(desc)}">
<link rel="canonical" href="{SITE}{path}">{alts}<link rel="icon" href="/favicon.ico" sizes="32x32"><link rel="icon" href="/img/favicon.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="/img/apple-touch-icon.png">
<meta property="og:type" content="{og}"><meta property="og:site_name" content="Pandit Krishna Astrology"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{SITE}{path}"><meta property="og:image" content="{SITE}/img/og-image.png"><meta property="og:locale" content="{code}_IN"><meta name="twitter:card" content="summary_large_image">
{ld}<style>{CSS}{BP.EXTRA_CSS}</style></head><body>
<header><div class="wrap"><a class="brand" href="/{code}/">Pandit Krishna<small>ASTROLOGY</small></a><a href="/{code}/#book">{e(t(D, code, 'Book a consultation'))}</a></div></header>
{body}
<footer><div class="wrap">© Pandit Krishna Astrology · {e(L['city'])} · <a href="/{code}/blog/">{e(t(D, code, 'Daily Blog'))}</a> · <a href="/{code}/#panchang">{e(t(D, code, 'Today’s Panchang'))}</a> · <a href="/#privacy">Privacy Policy</a> · <a href="/#disclaimer">Disclaimer</a></div></footer>
</body></html>
"""


def blog_pages(D):
    today = BP.live_date()
    posts = sorted((p for p in BP.load_posts() if p["date"] <= today), key=lambda p: p["date"], reverse=True)
    built = {}
    for code in CODES:
        out = os.path.join(ROOT, code, "blog")
        mine = [p for p in posts if (p.get("tr") or {}).get(code, {}).get("teaching")]
        keep = {p["date"] for p in mine}
        if os.path.isdir(out):
            for name in os.listdir(out):
                if BP.DATE_RE.fullmatch(name) and name not in keep:
                    shutil.rmtree(os.path.join(out, name))
        for i, p in enumerate(mine):
            tr = {k: num(code, v) for k, v in p["tr"][code].items() if isinstance(v, str)}  # site numerals, as on the main site
            title = tr.get("title") or p.get("title") or t(D, code, "Teaching point")
            newer = mine[i - 1] if i > 0 else None
            older = mine[i + 1] if i + 1 < len(mine) else None
            langs = {"en": f"/blog/{p['date']}/"}
            langs.update({c: f"/{c}/blog/{p['date']}/" for c in CODES if (p.get("tr") or {}).get(c, {}).get("teaching")})
            nav = ""
            if newer or older:
                def lab(q):
                    return e(num(code, q["tr"][code].get("title") or "") or nice(D, code, q["date"]))
                nav = '<nav class="pager">'
                nav += f'<a href="/{code}/blog/{older["date"]}/" rel="prev">← {lab(older)}</a>' if older else "<span></span>"
                nav += f'<a href="/{code}/blog/{newer["date"]}/" rel="next">{lab(newer)} →</a>' if newer else "<span></span>"
                nav += "</nav>"
            ld = {"@context": "https://schema.org", "@type": "BlogPosting", "headline": title[:110],
                  "description": BP.short(tr["teaching"]), "datePublished": p["date"], "inLanguage": code,
                  "mainEntityOfPage": f"{SITE}/{code}/blog/{p['date']}/", "image": f"{SITE}/img/og-image.png",
                  "author": {"@type": "Person", "name": "Pandit Krishna", "url": f"{SITE}/{code}/"},
                  "publisher": {"@type": "Organization", "name": "Pandit Krishna Astrology",
                                "logo": {"@type": "ImageObject", "url": f"{SITE}/img/icon-512.png"}}}
            ld_tag = '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False).replace("</", "<\\/") + "</script>\n"
            pan = f"/panchang/{p['date']}.html" if os.path.isfile(os.path.join(ROOT, "panchang", f"{p['date']}.html")) else "/panchang/"
            body = f"""<section class="hero"><div class="wrap"><p class="k">{e(t(D, code, 'Daily Blog'))} · <a href="/{code}/blog/" style="color:inherit">{e(t(D, code, 'All teaching points'))}</a></p><h1>{e(title)}</h1>
<p class="meta"><time datetime="{p['date']}">{e(nice(D, code, p['date']))}</time> · Pandit Krishna</p></div></section>
<main><div class="wrap">
<article class="post">{BP.paragraphs(tr['teaching'])}</article>
{nav}
<div class="cta"><a href="{pan}">{e(t(D, code, 'See the full Panchang'))}</a> · <a href="/{code}/#book">{e(t(D, code, 'Book a consultation'))}</a> · WhatsApp <a href="https://wa.me/919668024876" rel="noopener">+91 96680 24876</a> · <a href="/blog/{p['date']}/" hreflang="en" lang="en">English</a></div>
<p class="note" lang="en">Teaching points are traditional guidance for learning. They are not a promise of any result and not a substitute for medical, legal or financial advice.</p>
</div></main>"""
            os.makedirs(os.path.join(out, p["date"]), exist_ok=True)
            with open(os.path.join(out, p["date"], "index.html"), "w", encoding="utf-8") as fh:
                fh.write(page(D, code, f"{title} | Pandit Krishna Astrology", BP.short(tr["teaching"]),
                              f"/{code}/blog/{p['date']}/", alternates(langs), body, "article", ld_tag))
        # list page
        items = "".join(
            f'<li><time datetime="{p["date"]}">{e(nice(D, code, p["date"]))}</time><a href="/{code}/blog/{p["date"]}/">'
            f'{e(num(code, p["tr"][code].get("title") or t(D, code, "Teaching point")))}</a><p>{e(num(code, BP.short(p["tr"][code]["teaching"], 180)))}</p></li>'
            for p in mine)
        body = f"""<section class="hero"><div class="wrap"><p class="k">{e(t(D, code, 'Daily Blog'))}</p><h1>{e(t(D, code, 'All teaching points'))}</h1></div></section>
<main><div class="wrap"><ul class="list">{items}</ul>
<div class="cta"><a href="/{code}/#panchang">{e(t(D, code, 'Today’s Panchang'))}</a> · <a href="/{code}/#book">{e(t(D, code, 'Book a consultation'))}</a> · WhatsApp <a href="https://wa.me/919668024876" rel="noopener">+91 96680 24876</a></div>
</div></main>"""
        langs = {"en": "/blog/"}
        langs.update({c: f"/{c}/blog/" for c in CODES})
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, "index.html"), "w", encoding="utf-8") as fh:
            fh.write(page(D, code, f"{t(D, code, 'Daily Blog')} | Pandit Krishna Astrology",
                          f"Pandit Krishna Astrology · {t(D, code, 'Daily Blog')} · {D[code]['city']}",
                          f"/{code}/blog/", alternates(langs), body, "website"))
        built[code] = len(mine)
    return built


def main():
    D = load_dicts()
    home_pages(D)
    built = blog_pages(D)
    n = write_sitemap(ROOT)
    print("language home pages: " + " ".join(CODES) + "; blog posts per language: "
          + ", ".join(f"{c} {k}" for c, k in built.items()) + f"; sitemap has {n} URLs")


if __name__ == "__main__":
    main()
