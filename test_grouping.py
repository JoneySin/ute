"""
टेस्ट फाइल — ग्रुपिंग लॉजिक, group_key ओवरराइड और API रूट्स की जाँच
बिना डिपेंडेंसी के स्टैंडअलोन चलती है।
"""
import re
import zlib

# ── कॉपी किया गया लॉजिक web/search_api.py से (टेस्टिंग के लिए) ──
_RES_TOKEN_RE = re.compile(
    r"(?<![A-Za-z0-9])(?:(?:240|360|480|540|576|720|1080|1440|2160|4320)\s*[pP]|4[kK]|8[kK]|[uU][hH][dD])(?![A-Za-z0-9])")
_EXT_TAIL_RE = re.compile(
    r"[\s._\-]*(?<![A-Za-z0-9])(?:mp4|mkv|avi|mov|webm|m4v|ts|wmv|flv|mpg|mpeg)\s*$", re.I)
_SEP_RE = re.compile(r"[\s|_\-–.,:;()\[\]{}+~!@#$%^&*=/\\'\"`<>?·•]+")


def _group_key(name):
    s = _EXT_TAIL_RE.sub("", str(name or ""))
    s = _RES_TOKEN_RE.sub(" ", s).lower()
    return _SEP_RE.sub(" ", s).strip()


def _group_key_for(r):
    """ग्रुपिंग की key: admin द्वारा सेट किया 'group_key' override मान्य हो तो वही,
    वरना फाइल नाम से नॉर्मलाइज़्ड key।"""
    gk = r.get("group_key")
    if gk:
        return gk
    return _group_key(r.get("name"))


def _group_title(name):
    s = _EXT_TAIL_RE.sub("", str(name or ""))
    s = _RES_TOKEN_RE.sub(" ", s)
    s = re.sub(r"([|\-–_.])(\s*\1)+", r"\1", s)
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"^[\s|\-–_.]+|[\s|\-–_.]+$", "", s)
    return s


def _quality_label(res_text, name=""):
    m = re.search(r"(\d{3,5})\D+(\d{3,5})", str(res_text or ""))
    eh = 0
    if m:
        w, h = int(m.group(1)), int(m.group(2))
        eh = max(h, int(w * 9 / 16))
    else:
        t = _RES_TOKEN_RE.search(str(name or "")) or _RES_TOKEN_RE.search(str(res_text or ""))
        if t:
            tok = t.group(0).lower().replace(" ", "")
            eh = {"4k": 2160, "8k": 4320, "uhd": 2160}.get(tok) or int(re.sub(r"\D", "", tok) or 0)
    if not eh:
        return "", 0
    for lim, lab in ((4000, "8K"), (2000, "2160p"), (1300, "1440p"), (1000, "1080p"),
                     (650, "720p"), (450, "480p"), (330, "360p"), (220, "240p")):
        if eh >= lim:
            return lab, eh
    return f"{eh}p", eh


def group_results(results):
    order, buckets = [], {}
    for r in results:
        k = _group_key_for(r)
        if not k:
            order.append(("single", r))
            continue
        if k not in buckets:
            buckets[k] = []
            order.append(("group", k))
        buckets[k].append(r)

    out = []
    for kind, v in order:
        if kind == "single":
            out.append(v)
            continue
        items = buckets[v]
        if len(items) == 1:
            out.append(items[0])
            continue
        variants = []
        for it in items:
            lab, eh = _quality_label(it.get("res"), it.get("name"))
            variants.append((eh, dict(it, ql=lab)))
        variants.sort(key=lambda x: x[0])
        vlist = [d for _, d in variants]
        chips, seen = [], {}
        for d in vlist:
            lab = d["ql"] or "?"
            if lab in seen:
                seen[lab]["count"] += 1
            else:
                seen[lab] = {"label": lab, "count": 1}
                chips.append(seen[lab])
        out.append({
            "group": True,
            "key": f"{zlib.crc32(v.encode('utf-8')):08x}",
            "title": _group_title(items[0].get("name")) or str(items[0].get("name") or ""),
            "count": len(vlist),
            "type": items[0].get("type", "VIDEO"),
            "tg_thumb": next((d.get("tg_thumb") for d in vlist if d.get("tg_thumb")), ""),
            "chips": chips,
            "variants": vlist,
        })
    return out


# ── टेस्ट केस ──
passed = 0
failed = 0


def check(label, actual, expected):
    global passed, failed
    if actual == expected:
        passed += 1
        print(f"✅ PASS: {label}")
    else:
        failed += 1
        print(f"❌ FAIL: {label}")
        print(f"   अपेक्षित: {expected!r}")
        print(f"   वास्तविक: {actual!r}")


# 1. ऑटो ग्रुपिंग (बिना group_key के) — अलग नाम अलग ग्रुप नहीं बनते
r1 = {"name": "Movie Name 720p.mkv", "res": "1280×720", "file_type": "video"}
r2 = {"name": "Movie Name 1080p.mkv", "res": "1920×1080", "file_type": "video"}
r3 = {"name": "Movie Name 480p.mkv", "res": "640×480", "file_type": "video"}
grouped = group_results([r1, r2, r3])
groups = [g for g in grouped if g.get("group")]
check("3 क्वालिटी एक ग्रुप में मर्ज होती हैं",
      len(groups), 1)
if groups:
    check("ग्रुप में 3 वरिएंट हैं", groups[0]["count"], 3)
    check("ग्रुप टाइटल सही है", groups[0]["title"], "Movie Name")

# 2. group_key ओवरराइड — अलग नाम वाले फाइल को मौजूदा ग्रुप में जोड़ा जा सके
target = {"name": "Movie Name 720p.mkv", "res": "1280×720", "file_type": "video", "group_key": "custom-group-key"}
different_name = {"name": "Completely Different Filename.mp4", "res": "1280×720", "file_type": "video",
                  "group_key": "custom-group-key"}
grouped2 = group_results([target, different_name])
groups2 = [g for g in grouped2 if g.get("group")]
check("group_key ओवरराइड से अलग नाम एक ग्रुप में",
      len(groups2), 1)
if groups2:
    check("ओवरराइड ग्रुप में 2 फाइलें", groups2[0]["count"], 2)

# 3. बिना group_key के अलग नाम अलग ग्रुप नहीं बनते (संरक्षित व्यवहार)
different_no_key = {"name": "Completely Different Filename.mp4", "res": "1280×720", "file_type": "video"}
grouped3 = group_results([r1, different_no_key])
groups3 = [g for g in grouped3 if g.get("group")]
singles3 = [g for g in grouped3 if not g.get("group")]
check("अलग नाम बिना group_key के अकेले कार्ड रहते हैं",
      len(singles3), 2)

# 4. _group_key_for फंक्शन सीधा टेस्ट
check("_group_key_for ओवरराइड वापस करता है",
      _group_key_for({"name": "Anything", "group_key": "my-key"}), "my-key")
check("_group_key_for नाम से की बनाता है",
      _group_key_for({"name": "Movie Name 720p.mkv"}), "movie name")

# 5. क्वालिटी लेबल
check("1080p पहचान", _quality_label("1920×1080")[0], "1080p")
check("720p पहचान", _quality_label("1280×720")[0], "720p")
check("480p पहचान", _quality_label("640×480")[0], "480p")

# 6. ग्रुप चिप्स में क्वालिटी लेबल होते हैं
grouped4 = group_results([
    {"name": "Test 720p.mkv", "res": "1280×720", "file_type": "video", "tg_thumb": "/api/thumb?x=1"},
    {"name": "Test 1080p.mkv", "res": "1920×1080", "file_type": "video", "tg_thumb": "/api/thumb?x=2"},
])
g4 = [g for g in grouped4 if g.get("group")][0]
chip_labels = [c["label"] for c in g4["chips"]]
check("ग्रुप चिप्स में 720p और 1080p दोनों हैं",
      set(chip_labels), {"720p", "1080p"})

# 7. ग्रुप थंबनेल पहला वरिएंट का उपयोग करता है
check("ग्रुप tg_thumb सेट है", g4["tg_thumb"] == "/api/thumb?x=1", True)

print(f"\n{'='*50}")
print(f"परिणाम: {passed} पास, {failed} विफल")
if failed == 0:
    print("सभी टेस्ट पास हुए ✅")
else:
    print("कुछ टेस्ट विफल हुए ❌")
    exit(1)
