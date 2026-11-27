#!/usr/bin/env python3
"""Build one plain HTML page per daily blog post from blog-data.js, so every
teaching point keeps its own address that search engines can list:

  blog/YYYY-MM-DD/index.html  ->  https://panditkrishnaastrology.com/blog/YYYY-MM-DD/
  blog/index.html             ->  https://panditkrishnaastrology.com/blog/  (all posts)

Posts dated after today (IST) are skipped; they are built on the night their
date arrives, matching the main site. Pages of posts removed from
blog-data.js are deleted. sitemap.xml is refreshed.

Usage: python tools/blog_pages.py [repo_root]
"""
import html, json, os, re, shutil, sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from panchang_pages import CSS, IST, SITE, write_sitemap  # noqa: E402

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
e = html.escape
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")

CSP = ("default-src 'self'; script-src 'none'; style-src 'unsafe-inline'; img-src 'self' data:; "
       "object-src 'none'; base-uri 'self'; form-action 'none'; upgrade-insecure-requests")

EXTRA_CSS = """
article.post{background:var(--white);border:1px solid var(--line);border-radius:6px;padding:26px 28px;max-width:720px}
article.post p{margin:0 0 16px;font-size:17px;line-height:1.75}article.post p:last-child{margin-bottom:0}
.meta{color:#E8D3E2;margin:0}
.pager{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;max-width:720px}
.pager a{text-decoration:none;border:1px solid var(--line);background:var(--white);border-radius:4px;padding:8px 14px;font-size:15px;max-width:48%}
.list{list-style:none;margin:0;padding:0;display:flex;flex-direction:column;gap:14px}
.list li{background:var(--white);border:1px solid var(--line);border-radius:6px;padding:18px 20px}
.list time{display:block;color:var(--muted);font-size:13px;letter-spacing:.06em;text-transform:uppercase}
.list a{font:600 20px/1.3 Georgia,'Times New Roman',serif;text-decoration:none}
.list p{margin:6px 0 0;color:var(--muted);font-size:15px}
"""


def load_posts():
    src = open(os.path.join(ROOT, "blog-data.js"), encoding="utf-8").read()
    body = src[src.index("posts:[") + 6: src.rindex("]") + 1]
    posts = json.loads(body)
    return [p for p in posts if DATE_RE.fullmatch(p.get("date", "")) and p.get("teaching")]


def nice(date):
    d = datetime.strptime(date, "%Y-%m-%d")
    return d.strftime("%A, ") + str(d.day) + d.strftime(" %B %Y")


def short(text, n=155):
    t = " ".join(text.split())
    if len(t) <= n:
        return t
    cut = t[:n].rsplit(" ", 1)[0].rstrip(",;:.")
    return cut + "…"


def paragraphs(text):
    return "".join(f"<p>{e(p.strip())}</p>" for p in re.split(r"\n\s*\n", text.strip()) if p.strip())


def head(title, desc, canonical, og_type, extra=""):
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="{CSP}"><meta name="referrer" content="strict-origin-when-cross-origin"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(title)}</title><meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canonical}"><link rel="icon" href="/favicon.ico" sizes="32x32"><link rel="icon" href="/img/favicon.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="/img/apple-touch-icon.png">
<meta property="og:type" content="{og_type}"><meta property="og:site_name" content="Pandit Krishna Astrology"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{canonical}"><meta property="og:image" content="{SITE}/img/og-image.png"><meta name="twitter:card" content="summary_large_image">
{extra}<style>{CSS}{EXTRA_CSS}</style></head><body>
<header><div class="wrap"><a class="brand" href="/">Pandit Krishna<small>ASTROLOGY</small></a><a href="/#book">Book a consultation</a></div></header>
"""


FOOT = """<footer><div class="wrap">© Pandit Krishna Astrology · Bhubaneswar, Odisha · <a href="/blog/">Daily blog</a> · <a href="/panchang/">Today’s Panchang</a> · <a href="/#privacy">Privacy Policy</a> · <a href="/#disclaimer">Disclaimer</a></div></footer>
</body></html>
"""


def post_page(p, newer, older):
    date, title = p["date"], p.get("title") or "Teaching point"
    url = f"{SITE}/blog/{date}/"
    desc = short(p["teaching"])
    ld = {
        "@context": "https://schema.org", "@type": "BlogPosting",
        "headline": title[:110], "description": desc, "datePublished": date, "dateModified": date,
        "inLanguage": "en", "mainEntityOfPage": url, "image": f"{SITE}/img/og-image.png",
        "author": {"@type": "Person", "name": "Pandit Krishna", "url": f"{SITE}/"},
        "publisher": {"@type": "Organization", "name": "Pandit Krishna Astrology",
                      "logo": {"@type": "ImageObject", "url": f"{SITE}/img/icon-512.png"}},
    }
    ld_tag = '<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False).replace("</", "<\\/") + "</script>\n"
    panchang = os.path.isfile(os.path.join(ROOT, "panchang", f"{date}.html"))
    pan_link = (f'<a href="/panchang/{date}.html">See the full Panchang for this day</a>. ' if panchang
                else '<a href="/panchang/">See today’s Panchang</a>. ')
    nav = ""
    if newer or older:
        nav = '<nav class="pager" aria-label="More posts">'
        nav += f'<a href="/blog/{older["date"]}/" rel="prev">← {e(older.get("title") or nice(older["date"]))}</a>' if older else "<span></span>"
        nav += f'<a href="/blog/{newer["date"]}/" rel="next">{e(newer.get("title") or nice(newer["date"]))} →</a>' if newer else "<span></span>"
        nav += "</nav>"
    return head(f"{title} | Pandit Krishna Astrology", desc, url, "article", ld_tag) + f"""<section class="hero"><div class="wrap"><p class="k">Daily blog · <a href="/blog/" style="color:inherit">All teaching points</a></p><h1>{e(title)}</h1>
<p class="meta"><time datetime="{date}">{e(nice(date))}</time> · Pandit Krishna, Bhubaneswar</p></div></section>
<main><div class="wrap">
<article class="post">{paragraphs(p["teaching"])}</article>
{nav}
<div class="cta">{pan_link}For a personal reading, Prasna or a course, <a href="/#book">book with Pandit Krishna</a> by WhatsApp or phone, +91 96680 24876. <a href="/#blog">Read today’s post in 10 languages</a> on the main site.</div>
<p class="note">Teaching points are traditional guidance for learning. They are not a promise of any result and not a substitute for medical, legal or financial advice.</p>
</div></main>
""" + FOOT


def index_page(posts):
    items = "".join(
        f'<li><time datetime="{p["date"]}">{e(nice(p["date"]))}</time><a href="/blog/{p["date"]}/">{e(p.get("title") or "Teaching point")}</a>'
        f'<p>{e(short(p["teaching"], 180))}</p></li>' for p in posts)
    desc = ("Daily astrology teaching points by Pandit Krishna, Bhubaneswar: Bhrigu Nandi Nadi lessons on the day’s sky, "
            "festivals and vrats, nakshatras, Prasna, numerology and simple remedies.")
    return head("Daily Astrology Blog | Pandit Krishna Astrology", desc, f"{SITE}/blog/", "website") + f"""<section class="hero"><div class="wrap"><p class="k">Daily blog</p><h1>Daily teaching points</h1>
<p>One short lesson every day from Pandit Krishna, based on the day’s Panchang and planets.</p></div></section>
<main><div class="wrap">
<ul class="list">{items}</ul>
<div class="cta"><a href="/panchang/">See today’s Panchang</a> · <a href="/#book">Book a consultation</a> by WhatsApp or phone, +91 96680 24876.</div>
</div></main>
""" + FOOT


def main():
    today = datetime.now(IST).date().isoformat()
    posts = sorted((p for p in load_posts() if p["date"] <= today), key=lambda p: p["date"], reverse=True)
    out = os.path.join(ROOT, "blog")
    os.makedirs(out, exist_ok=True)
    keep = {p["date"] for p in posts}
    for name in os.listdir(out):  # remove pages of posts no longer published
        path = os.path.join(out, name)
        if DATE_RE.fullmatch(name) and name not in keep and os.path.isdir(path):
            shutil.rmtree(path)
    for i, p in enumerate(posts):
        newer = posts[i - 1] if i > 0 else None
        older = posts[i + 1] if i + 1 < len(posts) else None
        os.makedirs(os.path.join(out, p["date"]), exist_ok=True)
        with open(os.path.join(out, p["date"], "index.html"), "w", encoding="utf-8") as fh:
            fh.write(post_page(p, newer, older))
    with open(os.path.join(out, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(index_page(posts))
    n = write_sitemap(ROOT)
    print(f"wrote {len(posts)} blog post pages + blog index; sitemap has {n} URLs")


if __name__ == "__main__":
    main()
