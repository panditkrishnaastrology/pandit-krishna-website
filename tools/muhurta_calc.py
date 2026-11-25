#!/usr/bin/env python3
"""
Pandit Krishna Astrology — data for "Know your auspicious time" (muhurta finder).

For N days from today (IST), sunrise to next sunrise at Bhubaneswar, it lists
every change of: tithi, nakshatra, yoga, karana, Moon's rashi and the rising
lagna (sidereal, Lahiri), plus Rahu Kaal, Yamaganda, Gulika, Durmuhurta, Abhijit and the special
yogas (Sarvartha Siddhi and others; the inauspicious ones are added to "bad"), and the signs of the nine grahas at sunrise (with combustion).
The page's script combines these with the visitor's lagna, rashi and
nakshatra to find suitable windows. Times are Unix seconds.

Usage: python3 tools/muhurta_calc.py [--start YYYY-MM-DD] [--days 7] [--out muhurta-data.js]
"""
import argparse, json, os, sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import panchang_calc as pc  # noqa: E402
import swisseph as swe      # noqa: E402

# Varjyam (tyajya): start of the 4-ghati window, in ghatis from the start of each nakshatra
VARJYAM = [50, 24, 30, 40, 14, 21, 30, 20, 32, 30, 20, 18, 21, 20, 14, 14, 10, 14, 56, 24, 20, 10, 10, 18, 16, 24, 30]
GANDANTA_END = {26: 0, 8: 9, 17: 18}   # Revati->Ashwini, Ashlesha->Magha, Jyeshtha->Mula

# Durmuhurta: which of the 15 day-muhurtas (1-based) for each weekday, Sun=0
DURMUHURTA = {0: [14], 1: [9, 12], 2: [4], 3: [8], 4: [6, 12], 5: [4, 9], 6: [1, 2]}


def unix(jd):
    return round((jd - 2440587.5) * 86400)


def asc_sign(jd):
    _, lat, lng, _alt = pc.BBSR
    _cusps, ascmc = swe.houses_ex(jd, lat, lng, b"P", swe.FLG_SIDEREAL)
    return int(ascmc[0] // 30)


def moon_sign(jd):
    return int(pc.lon(jd, swe.MOON)[0] // 30)


def changes(fn, a, b, step=2 / 1440):
    """[(index, start_jd, end_jd)] for a step function fn over [a, b)."""
    out, t, cur, start = [], a, fn(a), a
    while t < b:
        t2 = min(t + step, b)
        v = fn(t2)
        if v != cur:
            lo, hi = t, t2
            for _ in range(30):
                mid = (lo + hi) / 2
                if fn(mid) == cur:
                    lo = mid
                else:
                    hi = mid
            out.append((cur, start, hi))
            cur, start = v, hi
        t = t2
    out.append((cur, start, b))
    return out


def limb(kind, a, b):
    out, jd = [], a
    while jd < b:
        idx, end = pc.segment_end(kind, jd)
        out.append([idx, unix(jd), unix(min(end, b))])
        jd = end + 1e-6
    return out


def nak_spans(a, b):
    """Whole nakshatras (true start and end) that overlap [a, b)."""
    out, jd = [], a - 1.2
    while jd < b:
        idx, end = pc.segment_end("nakshatra", jd)
        out.append((idx, jd, end))
        jd = end + 1e-6
    # the first entry starts at an arbitrary point; drop spans that end before a
    return [(i, s, e) for k, (i, s, e) in enumerate(out) if k > 0 and e > a]


def day_data(date):
    midnight = datetime(date.year, date.month, date.day, tzinfo=pc.IST)
    jd_mid = pc.jd_from_dt(midnight)
    sr = pc.rise_set(jd_mid, pc.BBSR, "rise")
    ss = pc.rise_set(jd_mid, pc.BBSR, "set")
    sr2 = pc.rise_set(jd_mid + 1, pc.BBSR, "rise")
    wd = (midnight.weekday() + 1) % 7
    part = (ss - sr) / 8
    mu = (ss - sr) / 15

    def span(n):
        return [unix(sr + (n - 1) * part), unix(sr + n * part)]

    varjyam, gandanta = [], []
    for i, st, en in nak_spans(sr, sr2):
        ln = en - st
        v0 = st + VARJYAM[i] / 60 * ln
        v1 = v0 + 4 / 60 * ln
        if v1 > sr and v0 < sr2:
            varjyam.append([unix(v0), unix(v1)])
        if i in GANDANTA_END:  # one ghati (about 24 minutes) on each side of the junction
            g0, g1 = en - 1 / 60, en + 1 / 60
            if g1 > sr and g0 < sr2:
                gandanta.append([unix(g0), unix(g1)])
    # lunar month (amanta) and Chaturmas: Ashadha Shukla Ekadashi to Kartika Shukla Ekadashi
    s_sr, m_sr = pc.sun_moon(sr)
    t_idx = int(((m_sr - s_sr) % 360) // 12)
    nm = pc.new_moon_before(sr)
    masa = (int(pc.lon(nm, swe.SUN)[0] // 30) + 1) % 12
    chaturmas = (masa == 3 and t_idx >= 10) or masa in (4, 5, 6) or (masa == 7 and t_idx < 10)

    specials = pc.special_yogas(sr, sr2, wd)
    planets = {}
    for p in pc.planet_positions(sr):
        planets[p["key"]] = {"sign": p["rashi_no"] - 1, "combust": p["combust"], "retro": p["retro"]}
    return {
        "date": date.isoformat(),
        "label": midnight.strftime("%a, %d %b").replace(" 0", " "),
        "weekday": wd,
        "sunrise": unix(sr), "sunset": unix(ss), "next_sunrise": unix(sr2),
        "tithi": limb("tithi", sr, sr2),
        "nakshatra": limb("nakshatra", sr, sr2),
        "yoga": limb("yoga", sr, sr2),
        "karana": limb("karana", sr, sr2),
        "moon": [[i, unix(a), unix(b)] for i, a, b in changes(moon_sign, sr, sr2, 30 / 1440)],
        "lagna": [[i, unix(a), unix(b)] for i, a, b in changes(asc_sign, sr, sr2)],
        "bad": {
            "Rahu Kaal": span(pc.RAHU_PART[wd]),
            "Yamaganda": span(pc.YAMA_PART[wd]),
            "Gulika Kaal": span(pc.GULI_PART[wd]),
            "Durmuhurta": [[unix(sr + (n - 1) * mu), unix(sr + n * mu)] for n in DURMUHURTA[wd]],
            "Varjyam": varjyam,
            "Gandanta": gandanta,
            **{n: [[unix(x[2]), unix(x[3])] for x in specials if x[0] == n]
               for n in {x[0] for x in specials if x[1] == "bad"}},
        },
        "special": [[n, k, unix(a), unix(b)] for n, k, a, b in specials if k != "bad"],
        "masa": masa, "chaturmas": chaturmas,
        "abhijit": None if wd == 3 else [unix(sr + 7 * mu), unix(sr + 8 * mu)],
        "planets": planets,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--out", default="muhurta-data.js")
    a = ap.parse_args()
    start = (datetime.strptime(a.start, "%Y-%m-%d").date() if a.start
             else datetime.now(pc.IST).date())
    days = [day_data(start + timedelta(days=i)) for i in range(a.days)]
    data = {"generated": datetime.now(pc.IST).strftime("%Y-%m-%d %H:%M IST"),
            "place": "Bhubaneswar", "days": days}
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write("window.PK_MUHURTA = ")
        json.dump(data, fh, separators=(",", ":"))
        fh.write(";\n")
    print(f"wrote {a.out}: {len(days)} days from {start}")


if __name__ == "__main__":
    main()
