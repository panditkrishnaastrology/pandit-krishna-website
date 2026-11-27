#!/usr/bin/env python3
"""Build stand-alone pages for the main sections of the site, so each one has
its own address, title and description in search results:

  consultation/index.html  ->  /consultation/   (services, fees, booking FAQ)
  courses/index.html       ->  /courses/        (courses, fees, syllabi)
  about/index.html         ->  /about/          (Pandit Krishna, testimonials)
  muhurta/index.html       ->  /muhurta/        (about the free muhurta finder)

The text, prices and syllabi are copied from index.html every time this runs,
so the pages always match the main site. Edit index.html, never these pages.
The interactive site (10 languages, Panchang, muhurta finder) stays at /.

Usage: python tools/site_pages.py [repo_root]
"""
import base64, html, json, os, re, sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from panchang_pages import CSS, IST, SITE, write_sitemap  # noqa: E402

ROOT = sys.argv[1] if len(sys.argv) > 1 else "."
e = html.escape
CSP = ("default-src 'self'; script-src 'none'; style-src 'unsafe-inline'; img-src 'self' data:; "
       "object-src 'none'; base-uri 'self'; form-action 'none'; upgrade-insecure-requests")
WA = "https://wa.me/919668024876"

EXTRA_CSS = """
.hero .lead{max-width:680px;margin:0}.hero .lead+.lead{margin-top:6px}
.grid2{display:grid;gap:16px;grid-template-columns:repeat(auto-fit,minmax(min(100%,280px),1fr))}
.card h2,.card h3{font:600 22px/1.25 Georgia,'Times New Roman',serif;color:var(--violet);margin:0 0 6px}
.eyebrow{color:#7A5C00;font-size:12px;letter-spacing:.12em;text-transform:uppercase;font-weight:600;margin:0 0 4px}
.muted{color:var(--muted)}.small{font-size:14px}
.price{margin:10px 0;font-size:17px}.price strong{color:var(--violet);font-size:22px}
dl.pricelist,dl.facts{margin:10px 0;display:flex;flex-direction:column;gap:6px;border-top:1px solid var(--line);padding-top:10px}
dl.pricelist div,dl.facts div{display:flex;justify-content:space-between;gap:12px}dl.pricelist dt,dl.facts dt{color:var(--muted)}
dl.pricelist dd,dl.facts dd{margin:0;font-weight:600;color:var(--violet);white-space:nowrap}
.card{display:flex;flex-direction:column}.card .go{margin-top:auto;padding-top:12px;font-weight:600}
details.syl{margin:8px 0 4px;border-top:1px solid var(--line);padding-top:8px}details summary{cursor:pointer;font-weight:600;color:var(--violet)}
details.syl ol{padding-left:20px;margin:10px 0}details.syl li{margin:0 0 8px}details.syl li p{margin:2px 0 0;color:var(--muted);font-size:14px}
.syl-h{display:flex;justify-content:space-between;gap:10px}.syl-h span{color:var(--muted);font-size:13px;white-space:nowrap}
.callout{background:var(--white);border-left:4px solid var(--gold);padding:14px 18px;margin:0;border-radius:4px}
.faq details{background:var(--white);border:1px solid var(--line);border-radius:6px;padding:14px 18px;margin:0 0 10px}.faq p{margin:8px 0 0}
.prose{max-width:720px}.prose p{font-size:17px;line-height:1.75;margin:0 0 16px}
.about{display:grid;gap:28px;grid-template-columns:minmax(0,260px) minmax(0,1fr);align-items:start}
.about img{width:100%;height:auto;border-radius:6px;border:1px solid var(--line)}
@media (max-width:700px){.about{grid-template-columns:1fr}.about img{max-width:240px}}
.stats{display:flex;gap:14px;flex-wrap:wrap;margin:6px 0 0}.stat{background:var(--white);border:1px solid var(--line);border-radius:6px;padding:12px 16px}
.stat b{display:block;font:600 24px Georgia,serif;color:var(--violet)}.stat span{color:var(--muted);font-size:14px}
.links{display:flex;gap:10px;flex-wrap:wrap}.links a{border:1px solid var(--line);background:var(--white);border-radius:4px;padding:6px 12px;text-decoration:none;font-size:14px}
blockquote{margin:0}blockquote p{margin:0;line-height:1.7}figure.testi{margin:0}figure.testi figcaption{margin-top:10px;font-size:14px;color:var(--muted)}figure.testi b{color:var(--violet);display:block}
.btn{display:inline-block;background:var(--gold);color:var(--violet-deep);font-weight:700;text-decoration:none;padding:12px 20px;border-radius:4px}
ul.rules{margin:0;padding-left:20px}ul.rules li{margin:0 0 8px}
.pause-note{background:#F7EAF0;border-bottom:2px solid var(--gold);color:var(--ink);font-size:15px;line-height:1.5}.pause-note .wrap{padding-block:10px}.pause-note strong{color:var(--violet)}
"""

NOTICE = ""  # set in main() from index.html


def load_index():
    return open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()


def section(src, sid):
    m = re.search(r'<section class="[^"]*" id="%s">(.*?)\n </section>' % re.escape(sid), src, re.S)
    if not m:
        raise SystemExit(f"section #{sid} not found in index.html")
    return m.group(1)


def fix_links(h):
    """In-page links (#book) point back to the main site; drop JS-only attributes."""
    h = re.sub(r'href="#([\w-]*)"', lambda m: f'href="/#{m.group(1)}"', h)
    h = re.sub(r'\s(data-service|data-terms|data-k|data-nav)(="[^"]*")?', "", h)
    return h


def strip_tags(h):
    return html.unescape(re.sub(r"<[^>]+>", "", h)).strip()


def head(title, desc, path, ld):
    url = f"{SITE}/{path}"
    tags = "".join('<script type="application/ld+json">' + json.dumps(x, ensure_ascii=False).replace("</", "<\\/") + "</script>\n" for x in ld)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="{CSP}"><meta name="referrer" content="strict-origin-when-cross-origin"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(title)}</title><meta name="description" content="{e(desc)}">
<link rel="canonical" href="{url}"><link rel="icon" href="/favicon.ico" sizes="32x32"><link rel="icon" href="/img/favicon.svg" type="image/svg+xml"><link rel="apple-touch-icon" href="/img/apple-touch-icon.png">
<meta property="og:type" content="website"><meta property="og:site_name" content="Pandit Krishna Astrology"><meta property="og:title" content="{e(title)}"><meta property="og:description" content="{e(desc)}"><meta property="og:url" content="{url}"><meta property="og:image" content="{SITE}/img/og-image.png"><meta name="twitter:card" content="summary_large_image">
{tags}<style>{CSS}{EXTRA_CSS}</style></head><body>
<header><div class="wrap"><a class="brand" href="/">Pandit Krishna<small>ASTROLOGY</small></a><a href="/#book">Book a consultation</a></div></header>
""" + NOTICE


def notice(src):
    """The main site's break notice (#pauseNote), shown until its end date.
    Static pages have no scripts, so the nightly build removes it after the break."""
    m = re.search(r'(<div class="pause-note" id="pauseNote" role="note">.*?</div></div>)', src, re.S)
    if not m:
        return ""
    till = re.search(r'till=Date\.parse\("([^"]+)"\)', src)
    if till and datetime.now(IST) >= datetime.fromisoformat(till.group(1)):
        return ""
    return m.group(1).replace(' id="pauseNote"', "") + "\n"


def hero(kicker, h1, *leads):
    ps = "".join(f'<p class="lead">{x}</p>' for x in leads)
    return f'<section class="hero"><div class="wrap"><p class="k">{e(kicker)}</p><h1>{e(h1)}</h1>{ps}</div></section>\n<main><div class="wrap">\n'


NAV = ('<nav class="links" aria-label="Pages"><a href="/consultation/">Consultation</a><a href="/courses/">Courses</a>'
       '<a href="/about/">About Pandit Krishna</a><a href="/muhurta/">Auspicious time</a><a href="/panchang/">Today’s Panchang</a>'
       '<a href="/blog/">Daily blog</a></nav>\n')

CTA = (f'<div class="cta">Book by WhatsApp or phone, <a href="{WA}" rel="noopener">+91 96680 24876</a>. '
       'Monday to Saturday 5–9 PM, Sunday 10 AM–8 PM (IST). <a href="/#book">How booking works</a>.</div>\n')

FOOT = """</div></main>
<footer><div class="wrap">© Pandit Krishna Astrology · Lane-7, Mallik Complex, Jagamara, Bhubaneswar, Odisha 751030 · <a href="/">Home</a> · <a href="/#privacy">Privacy Policy</a> · <a href="/#refund">Refund Policy</a> · <a href="/#disclaimer">Disclaimer</a> · <a href="/#contact">Contact</a></div></footer>
</body></html>
"""

PROVIDER = {"@type": "Organization", "name": "Pandit Krishna Astrology", "url": f"{SITE}/"}


def breadcrumb(name, path):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE}/"},
        {"@type": "ListItem", "position": 2, "name": name, "item": f"{SITE}/{path}"}]}


def faq_items(src, wanted):
    out = []
    for q, a in re.findall(r"<details><summary>(.*?)</summary><p>(.*?)</p></details>", section(src, "faq"), re.S):
        if any(w in q for w in wanted):
            out.append(f"<details><summary>{q}</summary><p>{fix_links(a)}</p></details>")
    return '<section class="faq"><h2>Questions</h2>' + "".join(out) + "</section>\n" if out else ""


def cards(block, cls):
    items = re.findall(r'<article class="%s">(.*?)</article>' % cls, block, re.S)
    out = []
    for it in items:
        it = fix_links(it).strip()
        it = re.sub(r'<a class="textlink" href="/#book">([^<]*)</a>', r'<a class="go" href="/#book">\1</a>', it)
        out.append(f'<article class="card">{it}</article>')
    return items, '<div class="grid2">' + "".join(out) + "</div>\n"


def head_texts(block):
    m = re.search(r'<div class="head">(.*?)</div>', block, re.S)
    return [x for x in re.findall(r'<p class="muted">(.*?)</p>', m.group(1))] if m else []


def consultation(src):
    block = section(src, "consultation")
    items, grid = cards(block, "service")
    names = [strip_tags(re.search(r"<h3>(.*?)</h3>", x).group(1)) for x in items]
    leads = head_texts(block)
    title = "Astrology Consultation in Bhubaneswar and Online | Pandit Krishna Astrology"
    desc = ("Consult Pandit Krishna for Vedic astrology, Bhrigu Nandi Nadi, Prasna Jyotish and Vedic numerology, "
            "in person in Bhubaneswar or online. Fees from ₹500. Free written report as PDF.")
    offers = []
    for x in items:
        n = strip_tags(re.search(r"<h3>(.*?)</h3>", x).group(1))
        d = strip_tags(re.search(r'<p class="muted">(.*?)</p>', x).group(1))
        pm = re.search(r"₹([\d,]+)", x)
        o = {"@type": "Offer", "itemOffered": {"@type": "Service", "name": n, "description": d, "provider": PROVIDER}}
        if pm:
            o.update(price=pm.group(1).replace(",", ""), priceCurrency="INR")
        offers.append(o)
    ld = [{"@context": "https://schema.org", "@type": "OfferCatalog", "name": "Astrology consultations", "url": f"{SITE}/consultation/", "itemListElement": offers},
          breadcrumb("Consultation", "consultation/")]
    body = hero("Consultation · Bhubaneswar and online", "Astrology consultation with Pandit Krishna", *leads)
    body += NAV + '<section><h2>Choose the reading that fits your question</h2>' + grid + "</section>\n"
    body += ('<section class="card prose"><h2>How a consultation works</h2><p>Send a WhatsApp message or call with the service you want and a '
             'preferred day and time. For a birth-chart reading, share your date, exact time and place of birth; Prasna Jyotish needs only your question. '
             'Payment is by UPI or bank transfer before the session. After the reading, a written report is sent as a PDF, free of charge.</p>'
             '<p class="muted small">Readings depend on the birth details you give, so please check them before your session. See the '
             '<a href="/#refund">Refund Policy</a> and <a href="/#disclaimer">Disclaimer</a>.</p></section>\n')
    body += faq_items(src, ["book", "details", "another city", "pay", "report", "languages", "cancel"])
    body += CTA
    return head(title, desc, "consultation/", ld) + body + FOOT, names


def courses(src):
    block = section(src, "learn")
    items, grid = cards(block, "course")
    callout = re.search(r'<p class="callout">(.*?)</p>', block, re.S)
    title = "Learn Astrology: Vedic, Nadi, Prasna, Panchang and Numerology Courses | Pandit Krishna Astrology"
    desc = ("Astrology courses by Pandit Krishna, Bhubaneswar: Vedic astrology basic and advanced, Bhrigu Nandi Nadi, Prasna Jyotish, "
            "Panchang and Vedic numerology. First class free. Full syllabus and fees.")
    clist = []
    for i, x in enumerate(items, 1):
        n = strip_tags(re.search(r"<h3>(.*?)</h3>", x).group(1))
        topics = [strip_tags(t) for t in re.findall(r"<b>(.*?)</b>", x)]
        fee = re.search(r"Course fee</dt><dd>₹([\d,]+)", x)
        hrs = re.search(r"Duration</dt><dd>(\d+) hours", x)
        c = {"@type": "Course", "name": n, "description": f"{n} course by Pandit Krishna: " + ", ".join(topics) + ".",
             "provider": PROVIDER, "url": f"{SITE}/courses/"}
        if fee:
            c["offers"] = {"@type": "Offer", "category": "Paid", "price": fee.group(1).replace(",", ""), "priceCurrency": "INR"}
        if hrs:
            c["hasCourseInstance"] = {"@type": "CourseInstance", "courseMode": ["Online", "Onsite"], "courseWorkload": f"PT{hrs.group(1)}H",
                                      "location": "Bhubaneswar, Odisha"}
        clist.append({"@type": "ListItem", "position": i, "item": c})
    ld = [{"@context": "https://schema.org", "@type": "ItemList", "name": "Astrology courses", "itemListElement": clist},
          breadcrumb("Courses", "courses/")]
    body = hero("Learn astrology", "Astrology courses with Pandit Krishna",
                "Study the classical methods step by step with a teacher, from the basics to advanced Nadi techniques. "
                "The first class of every course is free.")
    body += NAV + "<section><h2>Courses, fees and syllabus</h2>" + grid + "</section>\n"
    if callout:
        body += f'<p class="callout">{fix_links(callout.group(1))}</p>\n'
    body += ('<section class="card prose"><h2>How the classes work</h2><p>Each class is 1.5 hours, online or in person in Bhubaneswar. '
             'Classes are taught in Odia, Hindi or English. Fees are paid by UPI or bank transfer. Book your free first class by WhatsApp or phone.</p></section>\n')
    body += faq_items(src, ["courses work", "languages", "pay"])
    body += CTA
    return head(title, desc, "courses/", ld) + body + FOOT, [strip_tags(re.search(r"<h3>(.*?)</h3>", x).group(1)) for x in items]


def about(src):
    block = section(src, "about")
    m = re.search(r'<img src="data:image/(jpeg|png|webp);base64,([^"]+)" width="(\d+)" height="(\d+)" alt="([^"]*)"', block)
    img = ""
    if m:
        ext = "jpg" if m.group(1) == "jpeg" else m.group(1)
        os.makedirs(os.path.join(ROOT, "img"), exist_ok=True)
        with open(os.path.join(ROOT, "img", f"pandit-krishna.{ext}"), "wb") as fh:
            fh.write(base64.b64decode(m.group(2)))
        img = f'<img src="/img/pandit-krishna.{ext}" width="{m.group(3)}" height="{m.group(4)}" alt="{m.group(5)}">'
    text = re.search(r'<div class="about-text">(.*?)<div class="stats">', block, re.S).group(1)
    paras = re.findall(r"<p>(.*?)</p>", text, re.S)
    stats = re.search(r'(<div class="stats">.*?</div></div></div>)', block, re.S)
    links = re.findall(r'<a class="pill \w+" href="([^"]+)"[^>]*>.*?<span>([^<]+)</span></a>', block, re.S)
    testi = []
    for fig in re.findall(r'<figure class="testi[^"]*">(.*?)</figure>', section(src, "testimonials"), re.S):
        q = re.search(r"<blockquote>(.*?)</blockquote>", fig, re.S)
        name = re.search(r"<b>(.*?)</b>", fig)
        role = re.search(r"</b><span>(.*?)</span>", fig)
        if q and name:
            testi.append(f'<figure class="testi card"><blockquote>{q.group(1)}</blockquote><figcaption><b>{name.group(1)}</b>'
                         f'{role.group(1) if role else ""}</figcaption></figure>')
    note = re.search(r'<p class="muted small t-note">(.*?)</p>', section(src, "testimonials"), re.S)
    title = "About Pandit Krishna: Vedic and Nadi Astrologer, Bhubaneswar | Pandit Krishna Astrology"
    desc = ("Pandit Krishna is an astrologer and professor in Bhubaneswar with 19+ years of practice in Vedic astrology, "
            "Bhrigu Nandi Nadi, Prasna Jyotish and Vedic numerology. Read his story and client testimonials.")
    person = {"@context": "https://schema.org", "@type": "Person", "name": "Pandit Krishna", "jobTitle": "Astrologer and professor",
              "url": f"{SITE}/about/", "worksFor": PROVIDER, "knowsLanguage": ["or", "hi", "en"],
              "knowsAbout": ["Vedic astrology", "Bhrigu Nandi Nadi", "Prasna Jyotish", "Kasyapa Hora", "Vedic numerology", "Panchang"],
              "address": {"@type": "PostalAddress", "addressLocality": "Bhubaneswar", "addressRegion": "Odisha", "addressCountry": "IN"},
              "sameAs": [u for u, _ in links]}
    if img:
        person["image"] = f"{SITE}/img/pandit-krishna.jpg"
    ld = [person, breadcrumb("About", "about/")]
    body = hero("About", "Pandit Krishna, astrologer and professor",
                "Vedic astrology, Bhrigu Nandi Nadi, Prasna Jyotish and Vedic numerology, in Bhubaneswar and online.")
    body += NAV + f'<section class="about">{img}<div class="prose">' + "".join(f"<p>{fix_links(p)}</p>" for p in paras)
    body += (stats.group(1) if stats else "") + "</div></section>\n"
    if links:
        body += '<section><h2>Follow Pandit Krishna</h2><div class="links">' + "".join(
            f'<a href="{u}" rel="noopener">{e(n)}</a>' for u, n in links) + "</div></section>\n"
    if testi:
        body += '<section><h2>What clients and students say</h2><div class="grid2">' + "".join(testi) + "</div>"
        body += (f'<p class="note">{note.group(1)}</p>' if note else "") + "</section>\n"
    body += CTA
    return head(title, desc, "about/", ld) + body + FOOT


def muhurta(src):
    m = re.search(r'<details class="mh-rules">\s*<summary>.*?</summary>\s*<ul>(.*?)</ul>\s*<p>(.*?)</p>', src, re.S)
    rules, basis = (m.group(1), m.group(2)) if m else ("", "")
    purposes = re.findall(r'name="mhP" value="\w+"[^>]*><span>([^<]+)</span>', src)
    note = re.search(r'<p class="mh-note">(.*?)</p>', src, re.S)
    title = "Know Your Auspicious Time: Free Muhurta Finder | Pandit Krishna Astrology"
    desc = ("Free muhurta finder by Pandit Krishna Astrology: auspicious times for the next 7 days for "
            + ", ".join(p.lower() for p in purposes) + ", with tara bala, chandra bala and special yogas. Times for Bhubaneswar (IST).")
    ld = [{"@context": "https://schema.org", "@type": "WebApplication", "name": "Know your auspicious time (muhurta finder)",
           "url": f"{SITE}/muhurta/", "applicationCategory": "LifestyleApplication", "operatingSystem": "Any",
           "offers": {"@type": "Offer", "price": "0", "priceCurrency": "INR"}, "provider": PROVIDER},
          breadcrumb("Muhurta finder", "muhurta/")]
    body = hero("Muhurta finder · Bhubaneswar", "Know your auspicious time",
                "A free tool that finds the auspicious times in the next 7 days for the work you plan. Add your lagna, rashi and birth "
                "nakshatra if you know them, for times suited to you.")
    body += NAV + ('<p><a class="btn" href="/#muhurta">Open the muhurta finder</a></p>\n'
                   '<section class="card prose"><h2>What it does</h2><p>Choose a purpose: ' + e(", ".join(purposes)) + '. '
                   'The finder checks the Panchang for each day and lists the good times with a rating of Good, Very good or Excellent, '
                   'and the reasons for each. It runs on your own device, so your details are never sent anywhere.</p></section>\n')
    if rules:
        body += f'<section class="card"><h2>How the times are chosen</h2><ul class="rules">{fix_links(rules)}</ul><p class="note">{fix_links(basis)}</p></section>\n'
    if note:
        body += f'<p class="note">{fix_links(note.group(1))}</p>\n'
    body += ('<div class="cta">For marriage and other major events, ask Pandit Krishna for a muhurta based on your full birth chart: '
             f'WhatsApp or call <a href="{WA}" rel="noopener">+91 96680 24876</a>. <a href="/#muhurta">Open the muhurta finder</a>.</div>\n')
    return head(title, desc, "muhurta/", ld) + body + FOOT


def write(path, text):
    os.makedirs(os.path.join(ROOT, path), exist_ok=True)
    with open(os.path.join(ROOT, path, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(text)


def main():
    global NOTICE
    src = load_index()
    NOTICE = notice(src)
    c, services = consultation(src)
    k, course_names = courses(src)
    write("consultation", c)
    write("courses", k)
    write("about", about(src))
    write("muhurta", muhurta(src))
    n = write_sitemap(ROOT)
    print(f"wrote consultation ({len(services)} services), courses ({len(course_names)}), about, muhurta; sitemap has {n} URLs")


if __name__ == "__main__":
    main()
