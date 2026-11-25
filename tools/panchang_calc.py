#!/usr/bin/env python3
"""
Pandit Krishna Astrology — daily Panchang & planetary positions.

Computes, for N days starting from a given IST date:
  * Panchang for Bhubaneswar (vara, tithi, nakshatra, yoga, karana with end times,
    lunar month, samvat, Rahu Kaal, Yamaganda, Gulika, Abhijit, Brahma muhurta,
    moonrise/moonset)
  * Sunrise / sunset for Delhi, Mumbai, Kolkata, Chennai, Bhubaneswar
  * Sidereal (Lahiri) positions of the nine grahas at Bhubaneswar sunrise:
    longitude, rashi, degree in sign, nakshatra & pada, nakshatra lord,
    speed, retrograde, combust, dignity
  * Upcoming sign changes (next 45 days)

Output: a JavaScript file that sets window.PK_PANCHANG = {...}

Usage:  pip install pyswisseph
        python3 panchang_calc.py [--start YYYY-MM-DD] [--days 7] [--out panchang-data.js]
"""
import argparse, json, math
from datetime import datetime, timedelta, timezone
import swisseph as swe

IST = timezone(timedelta(hours=5, minutes=30))
FLAGS = swe.FLG_MOSEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
swe.set_sid_mode(swe.SIDM_LAHIRI)

CITIES = [  # name, lat, lon, altitude (m)
    ("Bhubaneswar", 20.2961, 85.8245, 45),
    ("Kolkata", 22.5726, 88.3639, 9),
    ("Delhi", 28.6139, 77.2090, 216),
    ("Mumbai", 19.0760, 72.8777, 14),
    ("Chennai", 13.0827, 80.2707, 6),
]
BBSR = CITIES[0]

RASHI = ["Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
         "Tula", "Vrishchika", "Dhanu", "Makara", "Kumbha", "Meena"]
RASHI_EN = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
NAK = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu",
       "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta",
       "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha",
       "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
       "Uttara Bhadrapada", "Revati"]
NAK_LORD = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
TITHI = ["Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi", "Saptami",
         "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi"]
YOGA = ["Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda", "Sukarma",
        "Dhriti", "Shula", "Ganda", "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra",
        "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva", "Siddha", "Sadhya", "Shubha",
        "Shukla", "Brahma", "Indra", "Vaidhriti"]
KARANA_MOV = ["Bava", "Balava", "Kaulava", "Taitila", "Garaja", "Vanija", "Vishti (Bhadra)"]
VARA = ["Ravivara (Sunday)", "Somavara (Monday)", "Mangalavara (Tuesday)",
        "Budhavara (Wednesday)", "Guruvara (Thursday)", "Shukravara (Friday)",
        "Shanivara (Saturday)"]
MASA = ["Chaitra", "Vaishakha", "Jyeshtha", "Ashadha", "Shravana", "Bhadrapada",
        "Ashwina", "Kartika", "Margashirsha", "Pausha", "Magha", "Phalguna"]
RITU = ["Vasanta", "Grishma", "Varsha", "Sharad", "Hemanta", "Shishira"]

PLANETS = [  # key, label, swe id, combust orb (direct), combust orb (retro)
    ("sun", "Sun (Surya)", swe.SUN, None, None),
    ("moon", "Moon (Chandra)", swe.MOON, 12, 12),
    ("mars", "Mars (Mangala)", swe.MARS, 17, 17),
    ("mercury", "Mercury (Budha)", swe.MERCURY, 14, 12),
    ("jupiter", "Jupiter (Guru)", swe.JUPITER, 11, 11),
    ("venus", "Venus (Shukra)", swe.VENUS, 10, 8),
    ("saturn", "Saturn (Shani)", swe.SATURN, 15, 15),
    ("rahu", "Rahu", swe.MEAN_NODE, None, None),
    ("ketu", "Ketu", None, None, None),
]
# dignity: exaltation sign, debilitation sign, own signs, moolatrikona (sign, from°, to°)
DIGNITY = {
    "sun": (0, 6, [4], (4, 0, 20)), "moon": (1, 7, [3], (1, 3, 30)),
    "mars": (9, 3, [0, 7], (0, 0, 12)), "mercury": (5, 11, [2, 5], (5, 15, 20)),
    "jupiter": (3, 9, [8, 11], (8, 0, 10)), "venus": (11, 5, [1, 6], (6, 0, 15)),
    "saturn": (6, 0, [9, 10], (10, 0, 20)), "rahu": (1, 7, [], None), "ketu": (7, 1, [], None),
}

# Rahu Kaal / Yamaganda / Gulika: eighth-part of daytime, index by weekday (Sun=0)
RAHU_PART = [8, 2, 7, 5, 6, 4, 3]
YAMA_PART = [5, 4, 3, 2, 1, 7, 6]
GULI_PART = [7, 6, 5, 4, 3, 2, 1]


# ---------------- helpers ----------------
def jd_from_dt(dt):
    u = dt.astimezone(timezone.utc)
    return swe.julday(u.year, u.month, u.day, u.hour + u.minute / 60 + u.second / 3600)


def dt_from_jd(jd):
    y, m, d, h = swe.revjul(jd)
    base = datetime(y, m, d, tzinfo=timezone.utc) + timedelta(hours=h)
    return base.astimezone(IST)


def lon(jd, pid):
    return swe.calc_ut(jd, pid, FLAGS)[0]


def sun_moon(jd):
    return lon(jd, swe.SUN)[0], lon(jd, swe.MOON)[0]


def rise_set(jd_local_midnight, city, which, body=swe.SUN):
    _, lat, lng, alt = city
    flag = swe.CALC_RISE if which == "rise" else swe.CALC_SET
    res, t = swe.rise_trans(jd_local_midnight, body, flag, (lng, lat, alt), 1013.25, 15,
                            swe.FLG_MOSEPH)
    return t[0] if res == 0 else None


def fmt_t(jd, ref_date=None):
    d = dt_from_jd(jd)
    s = d.strftime("%I:%M %p").lstrip("0")
    if ref_date and d.date() != ref_date:
        s += ", " + d.strftime("%d %b")
    return s


def dms(x):
    d = int(x); m_f = (x - d) * 60; m = int(m_f); s = int(round((m_f - m) * 60))
    if s == 60: s = 0; m += 1
    if m == 60: m = 0; d += 1
    return f"{d}°{m:02d}′{s:02d}″"


def angle_fn(kind):
    """Return f(jd) -> angle in [0,360) for the panchang limb, and segment width."""
    if kind == "tithi":
        return (lambda jd: (lambda s, m: (m - s) % 360)(*sun_moon(jd))), 12.0
    if kind == "nakshatra":
        return (lambda jd: sun_moon(jd)[1]), 360 / 27
    if kind == "yoga":
        return (lambda jd: (lambda s, m: (s + m) % 360)(*sun_moon(jd))), 360 / 27
    if kind == "karana":
        return (lambda jd: (lambda s, m: (m - s) % 360)(*sun_moon(jd))), 6.0
    raise ValueError(kind)


def segment_end(kind, jd):
    """Index of the segment current at jd, and jd when it ends."""
    f, w = angle_fn(kind)
    a0 = f(jd)
    idx = int(a0 // w)
    target = (idx + 1) * w  # may be 360
    # step forward until crossed
    step = 0.05
    lo, a_lo = jd, a0
    while True:
        hi = lo + step
        a_hi = f(hi)
        unwrapped = a_hi if a_hi >= a_lo - 180 else a_hi + 360
        if unwrapped >= target:
            break
        lo, a_lo = hi, a_hi
    for _ in range(40):
        mid = (lo + hi) / 2
        am = f(mid)
        am_u = am if am >= a0 - 180 else am + 360
        if am_u >= target:
            hi = mid
        else:
            lo = mid
    return idx, hi


def karana_name(idx):  # idx 0..59 over the lunar month
    if idx == 0:
        return "Kimstughna"
    if idx >= 57:
        return ["Shakuni", "Chatushpada", "Naga"][idx - 57]
    return KARANA_MOV[(idx - 1) % 7]


def tithi_name(idx):  # 0..29
    paksha = "Shukla" if idx < 15 else "Krishna"
    n = idx % 15
    if n == 14:
        name = "Purnima" if idx < 15 else "Amavasya"
    else:
        name = TITHI[n]
    return paksha, name


def segments(kind, jd_start, jd_stop, namer):
    out, jd = [], jd_start
    while jd < jd_stop:
        idx, end = segment_end(kind, jd)
        out.append((namer(idx), end))
        jd = end + 1e-6
    return out


def new_moon_before(jd):
    f, _ = angle_fn("tithi")
    # step back until elongation wraps from small to large
    t = jd
    a = f(t)
    while True:
        t2 = t - 0.5
        a2 = f(t2)
        if a2 > a + 180:  # crossed 0 going backwards
            lo, hi = t2, t
            break
        t, a = t2, a2
    for _ in range(40):
        mid = (lo + hi) / 2
        if f(mid) > 180:
            lo = mid
        else:
            hi = mid
    return hi


def nak_info(longitude):
    n = int(longitude // (360 / 27))
    pada = int((longitude % (360 / 27)) // (360 / 108)) + 1
    return NAK[n], pada, NAK_LORD[n % 9]


def dignity(key, sign, deg):
    if key not in DIGNITY:
        return ""
    ex, deb, own, mt = DIGNITY[key]
    if sign == ex:
        return "Exalted"
    if sign == deb:
        return "Debilitated"
    if mt and sign == mt[0] and mt[1] <= deg < mt[2]:
        return "Moolatrikona"
    if sign in own:
        return "Own sign"
    return ""


def planet_positions(jd):
    sun = lon(jd, swe.SUN)
    rows = []
    rahu_lon = None
    for key, label, pid, orb_d, orb_r in PLANETS:
        if key == "ketu":
            L = (rahu_lon + 180) % 360
            speed = rahu_speed
        else:
            r = lon(jd, pid)
            L, speed = r[0], r[3]
            if key == "rahu":
                rahu_lon, rahu_speed = L, speed
        sign = int(L // 30)
        deg = L % 30
        nk, pada, lord = nak_info(L)
        retro = speed < 0 if key not in ("rahu", "ketu") else True
        combust = False
        if orb_d is not None:
            sep = abs((L - sun[0] + 180) % 360 - 180)
            combust = sep <= (orb_r if speed < 0 else orb_d)
        rows.append({
            "key": key, "planet": label,
            "longitude": round(L, 4), "longitude_dms": dms(L),
            "rashi": RASHI[sign], "rashi_en": RASHI_EN[sign], "rashi_no": sign + 1,
            "degree": dms(deg),
            "nakshatra": nk, "pada": pada, "nak_lord": lord,
            "speed": round(speed, 4),
            "retro": bool(retro and key not in ("sun", "moon")),
            "combust": bool(combust),
            "dignity": dignity(key, sign, deg),
        })
    return rows


def _short(label):
    return label.split(" (")[0]


def planet_note(sr, sr_next, date):
    """Factual one-paragraph transit note for the panchang day (sunrise to sunrise)."""
    a = {p["key"]: p for p in planet_positions(sr)}
    b = {p["key"]: p for p in planet_positions(sr_next)}
    parts = []
    m = a["moon"]
    s = f"The Moon is in {m['rashi']}, {m['nakshatra']} nakshatra"
    if b["moon"]["rashi"] != m["rashi"]:
        # find Moon ingress time
        lo, hi = sr, sr_next
        for _ in range(40):
            mid = (lo + hi) / 2
            if RASHI[int(lon(mid, swe.MOON)[0] // 30)] == m["rashi"]:
                lo = mid
            else:
                hi = mid
        s += f", entering {b['moon']['rashi']} at {fmt_t(hi, date)}"
    parts.append(s + ".")
    for key in ("sun", "mars", "mercury", "jupiter", "venus", "saturn", "rahu"):
        if a[key]["rashi"] != b[key]["rashi"]:
            pid = next(p[2] for p in PLANETS if p[0] == key)
            lo, hi = sr, sr_next
            for _ in range(40):
                mid = (lo + hi) / 2
                if RASHI[int(lon(mid, pid)[0] // 30)] == a[key]["rashi"]:
                    lo = mid
                else:
                    hi = mid
            nm = _short(a[key]["planet"])
            parts.append(f"{nm} enters {b[key]['rashi']} at {fmt_t(hi, date)}"
                         + (f" (Ketu enters {b['ketu']['rashi']})" if key == "rahu" else "") + ".")
    for key in ("mars", "mercury", "jupiter", "venus", "saturn"):
        nm = _short(a[key]["planet"])
        if a[key]["retro"] != b[key]["retro"]:
            parts.append(f"{nm} turns {'retrograde' if b[key]['retro'] else 'direct'} today.")
        if a[key]["combust"] != b[key]["combust"]:
            parts.append(f"{nm} {'becomes combust' if b[key]['combust'] else 'comes out of combustion'} today.")
    retro = [_short(a[k]["planet"]) + f" in {a[k]['rashi']}"
             for k in ("mars", "mercury", "jupiter", "venus", "saturn") if a[k]["retro"]]
    comb = [_short(a[k]["planet"]) for k in ("moon", "mars", "mercury", "jupiter", "venus", "saturn")
            if a[k]["combust"]]
    if retro:
        parts.append("Retrograde: " + ", ".join(retro) + ".")
    if comb:
        parts.append("Combust: " + ", ".join(comb) + ".")
    return " ".join(parts)


def upcoming_ingresses(jd0, days=45):
    out = []
    for key, label, pid, *_ in PLANETS:
        if key in ("moon", "ketu"):
            continue
        def L(j):
            return lon(j, pid)[0]
        step = 0.25
        j = jd0
        s0 = int(L(j) // 30)
        while j < jd0 + days:
            j2 = j + step
            s1 = int(L(j2) // 30)
            if s1 != s0:
                lo, hi = j, j2
                for _ in range(40):
                    mid = (lo + hi) / 2
                    if int(L(mid) // 30) == s0:
                        lo = mid
                    else:
                        hi = mid
                out.append({"planet": label, "from": RASHI[s0], "to": RASHI[s1],
                            "when_jd": hi})
                if key == "rahu":
                    out.append({"planet": "Ketu", "from": RASHI[(s0 + 6) % 12],
                                "to": RASHI[(s1 + 6) % 12], "when_jd": hi})
                s0 = s1
            j = j2
    out.sort(key=lambda x: x["when_jd"])
    for o in out:
        d = dt_from_jd(o.pop("when_jd"))
        o["when"] = d.strftime("%d %b %Y, %I:%M %p").replace(" 0", " ")
        o["date"] = d.strftime("%Y-%m-%d")
    return out



# ---- special yogas (vara with nakshatra or tithi), Muhurta Chintamani tables ----
# nakshatra numbers 0..26 (Ashwini..Revati); weekdays Sun=0
_N = {n: i for i, n in enumerate(["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya",
      "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
      "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
      "Uttara Bhadrapada", "Revati"])}


def _ns(*names):
    return [_N[n] for n in names]


SARVARTHA = {0: _ns("Hasta", "Mula", "Uttara Phalguni", "Uttara Ashadha", "Uttara Bhadrapada", "Pushya", "Ashwini"),
             1: _ns("Shravana", "Rohini", "Mrigashira", "Pushya", "Anuradha"),
             2: _ns("Ashwini", "Uttara Bhadrapada", "Krittika", "Ashlesha"),
             3: _ns("Rohini", "Anuradha", "Hasta", "Krittika", "Mrigashira"),
             4: _ns("Revati", "Anuradha", "Ashwini", "Punarvasu", "Pushya"),
             5: _ns("Revati", "Anuradha", "Ashwini", "Punarvasu", "Shravana"),
             6: _ns("Shravana", "Rohini", "Swati")}
AMRITA = dict(enumerate(_ns("Hasta", "Mrigashira", "Ashwini", "Anuradha", "Pushya", "Revati", "Rohini")))
MRITYU = dict(enumerate(_ns("Anuradha", "Uttara Ashadha", "Shatabhisha", "Ashwini", "Mrigashira", "Ashlesha", "Hasta")))
UTPATA = dict(enumerate(_ns("Vishakha", "Purva Ashadha", "Dhanishta", "Revati", "Rohini", "Pushya", "Uttara Phalguni")))
YAMAGHANTA = dict(enumerate(_ns("Magha", "Vishakha", "Ardra", "Mula", "Krittika", "Rohini", "Hasta")))
DAGDHA = {0: [12], 1: [11], 2: [5], 3: [2, 3], 4: [6], 5: [8], 6: [9]}   # tithi number in the paksha
RAVI_YOGA = [4, 6, 9, 10, 13, 20]          # Moon's nakshatra counted from the Sun's
DWIPADA = _ns("Mrigashira", "Chitra", "Dhanishta")
TRIPADA = _ns("Krittika", "Punarvasu", "Uttara Phalguni", "Vishakha", "Uttara Ashadha", "Purva Bhadrapada")
YOGA_KIND = {"Sarvartha Siddhi Yoga": "good", "Amrita Siddhi Yoga": "good", "Ravi Yoga": "good",
             "Guru Pushya Yoga": "good", "Ravi Pushya Yoga": "good",
             "Dwipushkar Yoga": "mixed", "Tripushkar Yoga": "mixed",
             "Mrityu Yoga": "bad", "Utpata Yoga": "bad", "Yamaghanta Yoga": "bad", "Dagdha Yoga": "bad"}


def _spans(kind, a, b):
    out, jd = [], a
    while jd < b:
        idx, end = segment_end(kind, jd)
        out.append((idx, jd, min(end, b)))
        jd = end + 1e-6
    return out


def special_yogas(sr, sr_next, weekday):
    """[(name, kind, start_jd, end_jd)] for the vara from sunrise to the next sunrise."""
    naks, tithis, found = _spans("nakshatra", sr, sr_next), _spans("tithi", sr, sr_next), []

    def add(name, a, b):
        if b - a < 1 / 1440:
            return
        if found and found[-1][0] == name and abs(found[-1][3] - a) < 1 / 1440:
            found[-1] = (name, found[-1][1], found[-1][2], b)    # join touching spans
        else:
            found.append((name, YOGA_KIND[name], a, b))

    for n, a, b in naks:
        if n in SARVARTHA[weekday]:
            add("Sarvartha Siddhi Yoga", a, b)
    for n, a, b in naks:
        if n == AMRITA[weekday]:
            add("Amrita Siddhi Yoga", a, b)
        if n == _N["Pushya"] and weekday == 4:
            add("Guru Pushya Yoga", a, b)
        if n == _N["Pushya"] and weekday == 0:
            add("Ravi Pushya Yoga", a, b)
    for n, a, b in naks:
        sun_nak = int(lon(a + (b - a) / 2, swe.SUN)[0] // (360 / 27))
        if (n - sun_nak) % 27 + 1 in RAVI_YOGA:
            add("Ravi Yoga", a, b)
    if weekday in (0, 2, 6):
        for t, ta, tb in tithis:
            if t % 15 + 1 in (2, 7, 12):
                for n, a, b in naks:
                    lo, hi = max(a, ta), min(b, tb)
                    if hi > lo and n in DWIPADA:
                        add("Dwipushkar Yoga", lo, hi)
                    if hi > lo and n in TRIPADA:
                        add("Tripushkar Yoga", lo, hi)
    for name, table in (("Mrityu Yoga", MRITYU), ("Utpata Yoga", UTPATA), ("Yamaghanta Yoga", YAMAGHANTA)):
        for n, a, b in naks:
            if n == table[weekday]:
                add(name, a, b)
    for t, a, b in tithis:
        if t % 15 + 1 in DAGDHA[weekday] and t % 15 != 14:
            add("Dagdha Yoga", a, b)
    return found

def day_panchang(date):
    """Panchang for one civil date (IST) at Bhubaneswar."""
    midnight = datetime(date.year, date.month, date.day, tzinfo=IST)
    jd_mid = jd_from_dt(midnight)
    sr = rise_set(jd_mid, BBSR, "rise")
    ss = rise_set(jd_mid, BBSR, "set")
    sr_next = rise_set(jd_mid + 1, BBSR, "rise")
    mr = rise_set(jd_mid, BBSR, "rise", swe.MOON)
    ms = rise_set(jd_mid, BBSR, "set", swe.MOON)

    weekday = (midnight.weekday() + 1) % 7  # Sun=0

    def namer_t(i):
        p, n = tithi_name(i)
        return f"{p} {n}"

    tithis = segments("tithi", sr, sr_next, namer_t)
    naks = segments("nakshatra", sr, sr_next, lambda i: NAK[i])
    yogas = segments("yoga", sr, sr_next, lambda i: YOGA[i])
    karanas = segments("karana", sr, sr_next, karana_name)

    def seq(items):
        return [{"name": n, "till": fmt_t(e, date), "beyond": e >= sr_next} for n, e in items]

    s_sr, m_sr = sun_moon(sr)
    t_idx = int(((m_sr - s_sr) % 360) // 12)
    paksha = "Shukla Paksha" if t_idx < 15 else "Krishna Paksha"

    # lunar month (amanta): Sun's sign at the preceding new moon
    nm = new_moon_before(sr)
    sun_nm = lon(nm, swe.SUN)[0]
    am_idx = (int(sun_nm // 30) + 1) % 12   # Sun in Meena (11) -> Chaitra (0)
    pu_idx = (am_idx + 1) % 12 if t_idx >= 15 else am_idx
    # samvat
    vs = date.year + 57
    if am_idx >= 9 and date.month <= 4:   # Pausha..Phalguna in Jan-Apr
        vs = date.year + 56
    shaka = vs - 135

    # day/night parts
    day_len = ss - sr
    part = day_len / 8

    def part_span(n):
        a = sr + (n - 1) * part
        return f"{fmt_t(a)} – {fmt_t(a + part)}"

    mid_day = sr + day_len / 2
    muhurta = day_len / 15
    night_len = sr_next - ss
    brahma_start = sr_next - 2 * (night_len / 15)
    sun_sign = int(s_sr // 30)

    note = planet_note(sr, sr_next, date)

    # hora: 12 equal parts of the day (sunrise to sunset) and 12 of the night
    # (sunset to next sunrise). The first hora belongs to the weekday lord; the
    # rest follow the order Sun, Venus, Mercury, Moon, Saturn, Jupiter, Mars.
    hora_seq = ["sun", "venus", "mercury", "moon", "saturn", "jupiter", "mars"]
    day_lord = ["sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"][weekday]
    labels = {k: lab for k, lab, *_ in PLANETS}
    h0 = hora_seq.index(day_lord)

    def hora_rows(start, length, offset):
        rows = []
        for i in range(12):
            a = start + i * length / 12
            b = start + (i + 1) * length / 12
            key = hora_seq[(h0 + offset + i) % 7]
            rows.append({"n": offset + i + 1, "key": key, "lord": labels[key],
                         "time": f"{fmt_t(a)} – {fmt_t(b)}",
                         "t0": round((a - 2440587.5) * 86400), "t1": round((b - 2440587.5) * 86400)})
        return rows

    hora = {"day": hora_rows(sr, day_len, 0), "night": hora_rows(ss, night_len, 12)}

    specials = [{"name": n, "kind": k, "time": f"{fmt_t(a, date)} – {fmt_t(b, date)}",
                 "whole": a - sr < 1 / 1440 and sr_next - b < 1 / 1440}
                for n, k, a, b in special_yogas(sr, sr_next, weekday)]

    return {
        "planet_note": note,
        "special_yogas": specials,
        "hora": hora,
        "date": date.isoformat(),
        "date_label": midnight.strftime("%A, %d %B %Y").replace(" 0", " "),
        "vara": VARA[weekday],
        "sunrise": fmt_t(sr), "sunset": fmt_t(ss),
        "moonrise": fmt_t(mr, date) if mr else "—",
        "moonset": fmt_t(ms, date) if ms else "—",
        "paksha": paksha,
        "tithi": seq(tithis), "nakshatra": seq(naks), "yoga": seq(yogas),
        "karana": seq(karanas),
        "moon_rashi": RASHI[int(m_sr // 30)], "sun_rashi": RASHI[sun_sign],
        "masa_amanta": MASA[am_idx], "masa_purnimanta": MASA[pu_idx],
        "ritu": RITU[((sun_sign - 11) % 12) // 2],
        "ayana": "Uttarayana" if sun_sign in (9, 10, 11, 0, 1, 2) else "Dakshinayana",
        "vikram_samvat": vs, "shaka_samvat": shaka,
        "rahu_kaal": part_span(RAHU_PART[weekday]),
        "yamaganda": part_span(YAMA_PART[weekday]),
        "gulika": part_span(GULI_PART[weekday]),
        "abhijit": "—" if weekday == 3 else f"{fmt_t(mid_day - muhurta / 2)} – {fmt_t(mid_day + muhurta / 2)}",
        "brahma_muhurta": f"{fmt_t(brahma_start)} – {fmt_t(brahma_start + night_len / 15)}",
        "ayanamsa": dms(swe.get_ayanamsa_ut(sr)),
        "positions_at": f"Bhubaneswar sunrise, {fmt_t(sr)} IST",
        "cities": [
            {"city": c[0],
             "sunrise": fmt_t(rise_set(jd_mid, c, "rise")),
             "sunset": fmt_t(rise_set(jd_mid, c, "set"))} for c in CITIES
        ],
        "planets": planet_positions(sr),
        "_jd_sunrise": sr,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", help="YYYY-MM-DD (IST); default today in IST")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--out", default="panchang-data.js")
    a = ap.parse_args()
    start = (datetime.strptime(a.start, "%Y-%m-%d").date() if a.start
             else datetime.now(IST).date())
    days = [day_panchang(start + timedelta(days=i)) for i in range(a.days)]
    ingress = upcoming_ingresses(days[0]["_jd_sunrise"])
    for d in days:
        d.pop("_jd_sunrise")
    data = {
        "generated": datetime.now(IST).strftime("%Y-%m-%d %H:%M IST"),
        "method": "Swiss Ephemeris, sidereal zodiac, Lahiri (Chitrapaksha) ayanamsa, mean Rahu",
        "days": days,
        "ingresses": ingress,
    }
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write("window.PK_PANCHANG = ")
        json.dump(data, fh, ensure_ascii=False, indent=1)
        fh.write(";\n")
    print(f"wrote {a.out}: {len(days)} days from {start}, {len(ingress)} ingresses")


if __name__ == "__main__":
    main()
