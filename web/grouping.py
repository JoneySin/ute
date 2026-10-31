"""🗂️ QUALITY GROUPING — pure (DB-free) helpers.

Yeh module jaan-boojhkar sirf pure functions rakhta hai (koi motor/aiohttp import
nahi), taaki:

1. search API ka grouped-pagination loop sirf in functions ko call kare aur
   DB/HTTP ka kaam web/search_api.py me hi rahe.
2. `python -m py_compile` ke alawa in rules ka behaviour standalone test bhi ho
   sake (na Mongo chahiye, na Telegram).

Grouping ke do source hain:
  • AUTO   — ek hi title ki alag-alag quality (480p/720p/1080p…) ek card me.
  • MANUAL — admin ne web UI se banaya hua group (DB me persist), jisme alag-alag
             naam wali files bhi jod di jaati hain. Manual group ke paas apna
             title + thumbnail hota hai aur nayi files uske `key` se auto-attach
             ho jaati hain (dobara grouping na karni pade).

Grouping ka AADHAR (basis) admin chun sakta hai:
  • quality — same title, saari qualities ek card (default / purana behaviour).
  • episode — same episode ki qualities ek card (Show S01E01 → 480p+720p+1080p).
  • season  — ek season ke saare episodes ek card (Show S01 → E01…E10).
  • source  — admin ke apne quality names (Sky / UnTuch / FreeMasx / Mydesi) alag-alag.

Admin ke custom names (`tags`) hamesha resolution jaisa treat hote hain:
naam se hata diye jaate hain (isliye "Movie Sky 1080p" aur "Movie UnTuch 720p" ek hi
group me aate hain) aur label me dikhaye jaate hain ("Sky 1080p" / "UnTuch 720p").
"""

import html as _html
import re
import zlib

# ─────────────────────────────────────────────────────────
# 🔤 NAME NORMALISATION
# ─────────────────────────────────────────────────────────
_RES_TOKEN_RE = re.compile(
    r"(?<![A-Za-z0-9])(?:(?:240|360|480|540|576|720|1080|1440|2160|4320)\s*[pP]|4[kK]|8[kK]|[uU][hH][dD])(?![A-Za-z0-9])")
_EXT_TAIL_RE = re.compile(
    r"[\s._\-]*(?<![A-Za-z0-9])(?:mp4|mkv|avi|mov|webm|m4v|ts|wmv|flv|mpg|mpeg)\s*$", re.I)
_SEP_RE = re.compile(r"[\s|_\-–.,:;()\[\]{}+~!@#$%^&*=/\\'\"`<>?·•]+")

# 🎞️ EPISODE / SEASON markers — "S01E02", "1x02", "Episode 2", "Season 1", "S01"
_EP_FULL_RE = re.compile(
    r"(?<![A-Za-z0-9])s(?:eason)?\s*\.?\s*0*(\d{1,2})\s*[._\-\s]*e(?:p|pisode)?\s*\.?\s*0*(\d{1,3})(?![A-Za-z0-9])",
    re.I)
_EP_X_RE = re.compile(r"(?<![A-Za-z0-9])0*(\d{1,2})\s*[xX]\s*0*(\d{1,3})(?![A-Za-z0-9])")
_EP_ONLY_RE = re.compile(r"(?<![A-Za-z0-9])e(?:p|pisode)?\s*\.?\s*0*(\d{1,3})(?![A-Za-z0-9])", re.I)
_SE_ONLY_RE = re.compile(
    r"(?<![A-Za-z0-9])(?:s(?:eason)?)\s*\.?\s*0*(\d{1,2})(?![A-Za-z0-9])", re.I)

GROUP_BASES = ("quality", "episode", "season", "source")

def _tag_res(tags):
    """Admin ke tags → compiled matcher (ek hi regex me, case-insensitive)."""
    parts = []
    for t in tags or []:
        t = str(t or "").strip()
        if not t:
            continue
        parts.append(re.escape(t).replace(r"\ ", r"[\s._\-]*"))
    if not parts:
        return None
    return re.compile(r"(?<![A-Za-z0-9])(?:" + "|".join(parts) + r")(?![A-Za-z0-9])", re.I)


def match_tag(text, tags):
    """Naam me se pehla matching custom source/quality name (original case me), warna ''."""
    rx = _tag_res(tags)
    if rx is None:
        return ""
    m = rx.search(str(text or ""))
    if not m:
        return ""
    found = m.group(0).lower()
    for t in tags or []:
        if str(t or "").strip().lower() == found:
            return str(t).strip()
    return m.group(0)


def strip_tags(text, tags):
    """Naam me se admin ke custom names hata do (jagah space), taaki key same rahe."""
    rx = _tag_res(tags)
    if rx is None:
        return str(text or "")
    return rx.sub(" ", str(text or ""))


def _brand_label(tag, res_label):
    """(tag, '1080p') → 'Sky 1080p' | 'Sky' | '1080p'."""
    tag = str(tag or "").strip()
    res_label = str(res_label or "").strip()
    if tag and res_label:
        return f"{tag} {res_label}"
    return tag or res_label


def _clean_basis(basis):
    basis = str(basis or "quality").lower()
    return basis if basis in GROUP_BASES else "quality"


def parse_episode(text):
    """(season, episode, spans) — season/episode numbers + unke match spans.

    Kuch na mile to (None, None, []). Sirf explicit markers pakde jaate hain
    (S01E02 / 1x02 / Episode 2 / Season 1), taaki movie ke numbers galti se
    episode na samajh liye jaayein.
    """
    s = str(text or "")
    m = _EP_FULL_RE.search(s)
    if m:
        return int(m.group(1)), int(m.group(2)), [m.span()]
    m = _EP_X_RE.search(s)
    if m:
        return int(m.group(1)), int(m.group(2)), [m.span()]

    spans, season, episode = [], None, None
    m = _SE_ONLY_RE.search(s)
    if m:
        season = int(m.group(1))
        spans.append(m.span())
    m = _EP_ONLY_RE.search(s)
    if m:
        episode = int(m.group(1))
        spans.append(m.span())
    return season, episode, spans


def _strip_spans(text, spans):
    for a, b in sorted(spans or [], reverse=True):
        text = text[:a] + " " + text[b:]
    return text


def group_key(name, basis="quality", tags=None):
    """Quality/extension hata kar normalized key. Khali ho to '' (matlab group mat karo).

    basis:
      • "quality" — Episode/Season marker title ka hissa hai (purana behaviour).
      • "episode" — Same episode (S01E02 / 1x02 / Episode 2) ek hi key me.
      • "season"  — Episode marker hata kar season (S01) ek key me; season na ho
                    to saare episodes ek hi key me (poora show).
      • "source"  — Admin ke custom names (Sky/UnTuch/FreeMasx/Mydesi) alag-alag.

    `tags` = admin ke custom quality names; wo naam se hata diye jaate hain taaki
    "Movie Sky 1080p" aur "Movie UnTuch 720p" ek hi group me aayein.
    """
    basis = _clean_basis(basis)
    s = _EXT_TAIL_RE.sub("", str(name or ""))
    s = _RES_TOKEN_RE.sub(" ", s)
    s = strip_tags(s, tags)
    if basis == "source":                       # title + brand
        brand = match_tag(name, tags)
        return _SEP_RE.sub(" ", s.lower()).strip() + (f" | {brand.lower()}" if brand else "")
    if basis != "quality":
        season, episode, spans = parse_episode(s)
        if basis == "episode":
            if episode:
                s = _strip_spans(s, spans)
                s = f"{s} s{season:02d}e{episode:02d}" if season else f"{s} e{episode:02d}"
            elif season:                        # sirf season (S03 Complete) — wahi key rakho
                s = _strip_spans(s, spans)
                s = f"{s} s{season:02d}"
        else:                                   # season
            s = _strip_spans(s, spans)
            if season:
                s = f"{s} s{season:02d}"
    return _SEP_RE.sub(" ", s.lower()).strip()


def group_title(name, basis="quality", tags=None):
    """Dikhane layak saaf title (original case me), quality + extension hata kar.

    basis ke hisaab se episode/season marker canonical form me rakha jaata hai:
      • quality → jaise likha hai waise hi ("Show S01E02")
      • episode → "Show S01E02"
      • season  → "Show S01"
      • source  → "Show S01E02 · Sky" (admin ke custom quality name ke saath)
    """
    basis = _clean_basis(basis)
    brand = match_tag(name, tags)
    s = _EXT_TAIL_RE.sub("", str(name or ""))
    s = _RES_TOKEN_RE.sub(" ", s)
    s = strip_tags(s, tags)
    if basis != "quality":
        season, episode, spans = parse_episode(s)
        if spans and (episode or season):
            if basis == "episode":
                if episode:
                    token = f"S{season:02d}E{episode:02d}" if season else f"E{episode:02d}"
                else:
                    token = f"S{season:02d}"
            else:                               # season
                token = f"S{season:02d}" if season else ""
            s = _strip_spans(s, spans)
            if token:
                s = f"{s} {token}"
    s = re.sub(r"([|\-–_.])(\s*\1)+", r"\1", s)          # '| |' / '..' jaise doble separator
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"^[\s|\-–_.]+|[\s|\-–_.]+$", "", s)
    if basis == "source" and brand:
        s = f"{s} · {brand}" if s else brand
    return s


def shortcut_title(name, tags=None):
    """Search-suggestion ke liye chhota title (pehle 6 meaningful words)."""
    words = [w for w in group_title(name, tags=tags).split() if w]
    return " ".join(words[:6])


def quality_label(res_text, name="", tags=None):
    """(label, sort_height). res "1920×1080" se; na ho to naam ke token se; warna ('', 0).

    Admin ka custom quality name mila to label me pehle wo aata hai:
    "Sky 1080p", "UnTuch 720p", sirf "Sky" (resolution na ho to).
    """
    m = re.search(r"(\d{3,5})\D+(\d{3,5})", str(res_text or ""))
    eh = 0
    if m:
        w, h = int(m.group(1)), int(m.group(2))
        eh = max(h, int(w * 9 / 16))          # 1920×800 (scope) bhi 1080p ginta hai
    else:
        t = _RES_TOKEN_RE.search(str(name or "")) or _RES_TOKEN_RE.search(str(res_text or ""))
        if t:
            tok = t.group(0).lower().replace(" ", "")
            eh = {"4k": 2160, "8k": 4320, "uhd": 2160}.get(tok) or int(re.sub(r"\D", "", tok) or 0)
    brand = match_tag(name or res_text, tags)
    if not eh:
        return brand, 0
    for lim, lab in ((4000, "8K"), (2000, "2160p"), (1300, "1440p"), (1000, "1080p"),
                     (650, "720p"), (450, "480p"), (330, "360p"), (220, "240p")):
        if eh >= lim:
            return _brand_label(brand, lab), eh
    return _brand_label(brand, f"{eh}p"), eh


def _card_key(text):
    return f"{zlib.crc32(str(text or '').encode('utf-8')):08x}"


def _copy(d, **extra):
    """Shallow copy + extra keys. Input dicts kabhi mutate nahi hote (TRENDING_CACHE
    unhi dicts ko share karta hai, isliye yeh zaroori hai)."""
    out = dict(d)
    out.update(extra)
    return out


def _brand_list(variants):
    """Card par dikhane layak custom quality names (admin ke tags)."""
    out = []
    for d in variants or []:
        b = str(d.get("brand") or "").strip()
        if b and b not in out:
            out.append(b)
    return out[:4]


def _episode_count(variants):
    """Variants me kitne alag episodes hain (season grouping ka label)."""
    seen = set()
    for d in variants or []:
        se, ep, _ = parse_episode(d.get("name"))
        if ep:
            seen.add((se or 0, ep))
    return len(seen)


def _chips_and_labels(variants):
    chips, seen, labels = [], {}, []
    for d in variants:
        lab = d.get("ql") or ""
        if not lab:
            continue
        if lab in seen:
            seen[lab]["count"] += 1
        else:
            seen[lab] = {"label": lab, "count": 1}
            chips.append(seen[lab])
            labels.append(lab)
    return chips, labels


# ─────────────────────────────────────────────────────────
# 🧩 CORE: results → cards
# ─────────────────────────────────────────────────────────
def build_groups(results, manual=None, basis="quality", tags=None):
    """Results list ko group cards me badalta hai.

    results : web result dicts (ranking order me, `file_id` ke saath)
    basis   : "quality" | "episode" | "season" | "source" — grouping ka aadhar
    tags    : admin ke custom quality names ["Sky","UnTuch","FreeMasx","Mydesi"]
              (naam se hata kar label me dikhaye jaate hain)
    manual  : {gid: {"gid", "title", "key", "thumb", "verified", "members": [fid...],
                     "variants": [result dict...]}}
              (manual group ke saare saved members ke result dicts — chahe wo is
               page par hon ya na hon — plus admin ka diya title/thumbnail)

    Return: list of cards. Har card par `_first` = results me uski pehli position
    (pagination isi se next raw offset nikalta hai). Single (akeli) file bhi copy
    hoti hai taaki `_first` input dicts ko dirty na kare.

    Cards:
      • single file  → waisa hi result dict (+ `_first`)
      • auto group   → {"group": True, "manual": False, "key", "title", "count",
                        "type", "tg_thumb", "chips", "labels", "variants", "_first"}
      • manual group → same + {"gid", "manual": True, "tg_thumb": /api/group_thumb…}
    """
    basis = _clean_basis(basis)
    manual = manual or {}

    fid_to_gid, key_to_gid = {}, {}
    for gid, g in manual.items():
        for m in (g.get("members") or []):
            fid_to_gid[m] = gid
        k = (g.get("key") or "").strip()
        if k:
            key_to_gid.setdefault(k, gid)

    order = []                       # ("single", idx) | ("group", key) | ("manual", gid)
    auto_buckets = {}                # key -> [(idx, result), ...]
    manual_seen = {}                 # gid -> [(idx, result), ...]  (ranking order)

    for idx, r in enumerate(results):
        fid = r.get("file_id")
        gid = fid_to_gid.get(fid)
        if not gid:
            k = group_key(r.get("name"), basis, tags)
            gid = key_to_gid.get(k) if k else None
        if gid:
            if gid not in manual_seen:
                manual_seen[gid] = []
                order.append(("manual", gid))
            manual_seen[gid].append((idx, r))
            continue

        k = group_key(r.get("name"), basis, tags)
        if not k:
            order.append(("single", idx))
            continue
        if k not in auto_buckets:
            auto_buckets[k] = []
            order.append(("group", k))
        auto_buckets[k].append((idx, r))

    out = []
    for kind, v in order:
        if kind == "single":
            out.append(_copy(results[v], _first=v, brand=match_tag(results[v].get("name"), tags)))
            continue

        if kind == "manual":
            g = manual.get(v) or {}
            stored = g.get("variants") or []
            page_items = manual_seen.get(v) or []
            page_rows = [r for _, r in page_items]
            variants, seen_fids = [], set()
            for it in stored:                       # saved members pehle (admin ka order)
                fid = it.get("file_id")
                if fid in seen_fids:
                    continue
                seen_fids.add(fid)
                variants.append(it)
            for it in page_rows:                    # key se auto-attach hui nayi files
                fid = it.get("file_id")
                if fid in seen_fids:
                    continue
                seen_fids.add(fid)
                variants.append(it)
            if not variants:
                continue

            labelled = []
            for it in variants:
                lab, eh = quality_label(it.get("res"), it.get("name"), tags)
                labelled.append((eh, _copy(it, ql=lab, brand=match_tag(it.get("name"), tags))))
            labelled.sort(key=lambda x: x[0])        # stable: barabar quality me original order
            vlist = [d for _, d in labelled]

            master = page_rows[0] if page_rows else variants[0]
            chips, labels = _chips_and_labels(vlist)
            brands = _brand_list(vlist)
            title = str(g.get("title") or "").strip() or group_title(master.get("name"), basis, tags) \
                or str(master.get("name") or "")
            thumb = str(g.get("thumb") or "").strip() or master.get("tg_thumb") or ""
            out.append({
                "group": True,
                "manual": True,
                "gid": str(g.get("gid") or v),
                "key": str(g.get("gid") or v),
                "title": _html.escape(title),
                "raw_title": title,
                "verified": bool(g.get("verified")),
                "basis": basis,
                "ep_count": _episode_count(vlist),
                "count": len(vlist),
                "type": str(master.get("type") or "VIDEO").upper(),
                "tg_thumb": thumb,
                "chips": chips,
                "labels": labels[:4],
            "brands": brands,
                "brands": brands,
                "variants": vlist,
                "_first": page_items[0][0] if page_items else 0,
            })
            continue

        # ── auto group ──
        items = auto_buckets.get(v) or []
        if len(items) == 1:
            idx, only = items[0]
            out.append(_copy(only, _first=idx, brand=match_tag(only.get("name"), tags)))
            continue
        labelled = []
        for _, it in items:
            lab, eh = quality_label(it.get("res"), it.get("name"), tags)
            labelled.append((eh, _copy(it, ql=lab, brand=match_tag(it.get("name"), tags))))
        labelled.sort(key=lambda x: x[0])
        vlist = [d for _, d in labelled]
        chips, labels = _chips_and_labels(vlist)
        brands = _brand_list(vlist)
        master = items[0][1]
        title = group_title(master.get("name"), basis, tags) or str(master.get("name") or "")
        # master thumbnail = ranking me pehli (best match) file ka poster, warna koi bhi
        thumb = master.get("tg_thumb") or next((d.get("tg_thumb") for d in vlist if d.get("tg_thumb")), "")
        out.append({
            "group": True,
            "manual": False,
            "gid": "",
            "key": _card_key(v),
            "title": _html.escape(title),
            "raw_title": title,
            "verified": False,
            "basis": basis,
            "ep_count": _episode_count(vlist),
            "count": len(vlist),
            "type": str(master.get("type") or "VIDEO").upper(),
            "tg_thumb": thumb,
            "chips": chips,
            "labels": labels[:4],
            "brands": brands,
            "variants": vlist,
            "_first": items[0][0],
        })
    return out


def plan_page(cards, target):
    """(page_cards, cut_delta) — cut_delta None matlab poora window hi page hai.

    cut_delta = us agle card ki position jo page me nahi aaya; caller ise raw
    offset me add karke next_offset banata hai (group boundary par hi cut hota
    hai, isliye koi group beech se nahi tootta).
    """
    if target <= 0 or len(cards) <= target:
        return cards, None
    return cards[:target], int(cards[target].get("_first") or 0)


def strip_internal(cards):
    """Pagination ke andar ka `_first` hata do (JSON/cache me nahi jaana chahiye)."""
    for c in cards:
        c.pop("_first", None)
    return cards


def suggest_score(base_name, cand_name):
    """Do naam kitne milte hain (0..1, token Jaccard). Suggestions sort karne ke liye."""
    a = set(group_key(base_name).split())
    b = set(group_key(cand_name).split())
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)
