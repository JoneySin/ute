"""🗂️ QUALITY GROUP ADMIN — page + JSON APIs

Admin yahan se:
  • naya group bana sakta hai (naam + thumbnail),
  • group ka naam ya master thumbnail badal sakta hai,
  • alag-alag naam wali files ko search karke group me jod sakta hai,
  • member nikaal sakta hai / poora group delete kar sakta hai,
  • ek group ki saari files doosre group me migrate (merge) kar sakta hai,
  • group ko "verified" mark kar sakta hai (sirf verified id hi bharosemand hai).

Sab kuch MongoDB (FileGroups) me save hota hai — dobara grouping nahi karni padti.
Search results me ye groups web/search_api.py ke `_manual_groups_for()` se merge
hote hain (wahan sirf read hota hai).
"""

import io
import zlib
import logging

from bson.objectid import ObjectId
from aiohttp import web

from info import THUMBNAIL_STORAGE_CHANNEL
from utils import temp, get_size, get_duration_str
from database import file_groups as fg
from database.ia_filterdb import FILE_COLLECTIONS, get_search_results, doc_resolution_text
from web.grouping import (group_key, group_title, shortcut_title, quality_label, suggest_score,
                          match_tag)
from web.web_assets import build_page, get_auth, fast_json
from web.group_ui import (GROUP_UI_CSS, GROUP_MODAL_HTML, GROUP_MIGRATE_HTML, GROUP_UI_JS,
                          GROUP_TAGS_HTML)
from web.search_api import (get_user_role, TRENDING_CACHE, PREFETCH_CACHE,
                            clear_release_tags_cache, get_release_tags)

logger = logging.getLogger(__name__)

group_routes = web.RouteTableDef()

GROUP_FILES_LIMIT = 24          # user-typed search results
GROUP_SUGGEST_LIMIT = 40        # seed file ke same-title suggestions (modal khulte hi)


# ─────────────────────────────────────────────────────────
# 🔧 HELPERS
# ─────────────────────────────────────────────────────────
def _clear_search_caches():
    """Grouping badalne par purane grouped pages / plots cache me na rahein."""
    try:
        TRENDING_CACHE.clear()
        PREFETCH_CACHE.clear()
        clear_release_tags_cache()
    except Exception:
        pass


def _thumb_salt(raw_thumb):
    """Wahi salt jo search_api._build_results_list use karta hai (cache-busting)."""
    raw_thumb = str(raw_thumb or "")
    return f"{zlib.crc32(raw_thumb.encode('utf-8')):08x}" if raw_thumb.startswith("TG_ID:") else "0"


def _thumb_url(fid, col, raw_thumb):
    return f"/api/thumb?file_id={fid}&col={col}&v={_thumb_salt(raw_thumb)}"


def _group_thumb_url(g):
    salt = f"{g.get('thumb_url') or ''}|{g.get('updated_on') or 0}"
    v = f"{zlib.crc32(salt.encode('utf-8')):08x}"
    return f"/api/group_thumb?gid={g['_id']}&v={v}"


def _row_from_doc(doc, tags=None):
    fid = str(doc.get("_id"))
    col = str(doc.get("source_col") or "primary")
    name = str(doc.get("file_name") or "")
    res = doc_resolution_text(doc)
    return {
        "fid": fid,
        "col": col,
        "name": name,
        "size": get_size(doc.get("file_size", 0)),
        "duration": get_duration_str(doc.get("duration")),
        "res": res,
        "ql": quality_label(res, name, tags)[0],
        "brand": match_tag(name, tags),
        "thumb": _thumb_url(fid, col, doc.get("thumb_url", "")),
    }


async def _safe_tags():
    """Custom quality names — DB down ho to grouping phir bhi chale (khali list)."""
    try:
        return await get_release_tags()
    except Exception as e:
        logger.debug(f"Tags load failed: {e}")
        return []


def _payload(g, rows):
    return {
        "gid": str(g["_id"]),
        "title": g.get("title") or "",
        "key": g.get("key") or "",
        "thumb": _group_thumb_url(g),
        "custom_thumb": bool(str(g.get("thumb_url") or "").strip()),
        "verified": bool(g.get("verified")),
        "count": len(rows),
        "members": rows,
        "updated_on": g.get("updated_on") or 0,
    }


async def _group_payload(g):
    members = fg.clean_members(g.get("members"))
    docs = await fg.fetch_member_docs(members)
    tags = await _safe_tags()
    rows = []
    for d in docs:
        r = _row_from_doc(d, tags)
        r["group"] = str(g["_id"])
        rows.append(r)
    return _payload(g, rows)


async def _find_doc(fid, col=""):
    """fid (string) → DB doc, collection bhi tag karke (col preference ke saath)."""
    if not fid:
        return None
    order = []
    if col in FILE_COLLECTIONS:
        order.append((col, FILE_COLLECTIONS[col]))
    for name, c in FILE_COLLECTIONS.items():
        if name != col:
            order.append((name, c))

    ids = [str(fid)]
    try:
        ids.append(ObjectId(str(fid)))
    except Exception:
        pass

    for name, c in order:
        try:
            doc = await c.find_one({"_id": {"$in": ids}})
        except Exception:
            doc = None
        if doc:
            doc["file_id"] = doc["_id"]
            doc["source_col"] = name
            return doc
    return None


def _name_query_variants(name, max_variants=3, tags=None):
    """Naam se search ke liye 6→4→3→2 word wale queries (AND semantics ke liye).

    Strict `$text` search har word maangta hai, isliye "Alpha Movie 2025 Hindi
    Dubbed" jaisa lamba naam sirf "Alpha Movie 2025 1080p" wali file ko nahi
    dhoondh paata. Chhote queries se recall badhta hai aur ranking Jaccard score
    se hoti hai, isliye sabse milti-julti files hi upar aati hain.
    """
    words = [w for w in group_title(name, tags=tags).split() if w]
    out = []
    for n in (6, 4, 3, 2):
        if len(words) < n:
            continue
        q = " ".join(words[:n])
        if q.lower() not in [x.lower() for x in out]:
            out.append(q)
        if len(out) >= max_variants:
            break
    return out


async def _suggest_docs_for_name(name, limit=GROUP_SUGGEST_LIMIT, tags=None):
    """Naam ke close files (same title ke variants) — Jaccard score se ranked."""
    seen, docs = {}, []
    for q in _name_query_variants(name, tags=tags):
        if len(docs) >= limit:
            break
        try:
            found, _, _, _ = await get_search_results(q, limit, 0, collection_type="all", bypass_count=True)
        except Exception as e:
            logger.debug(f"Group suggestion search failed for {q!r}: {e}")
            continue
        for d in found:
            key = str(d.get("_id"))
            if key not in seen:
                seen[key] = d
                docs.append(d)
    docs.sort(key=lambda d: -suggest_score(name, d.get("file_name", "")))
    return docs[:limit]


async def _rekey_groups(tags=None):
    """Tags badalne par manual groups ka auto-attach `key` dobara compute karo.

    Warna naye tag ke saath aane wali same-title file purane group se attach nahi hoti.
    Members list par koi asar nahi — sirf key update hoti hai.
    """
    groups = await fg.list_groups(limit=500)
    if not groups:
        return 0
    fids = [m["fid"] for g in groups for m in fg.clean_members(g.get("members"))]
    docs = await fg.docs_for_fids(fids)
    changed = 0
    for g in groups:
        first = next((docs[m["fid"]] for m in fg.clean_members(g.get("members")) if m["fid"] in docs), None)
        if first:
            new_key = group_key(first.get("file_name", ""), tags=tags)
        else:
            new_key = group_key(g.get("title", ""), tags=tags)
        if new_key and new_key != (g.get("key") or ""):
            await fg.update_group(str(g["_id"]), key=new_key)
            changed += 1
    if changed:
        logger.info(f"🔁 {changed} group key(s) re-computed after tag change")
    return changed


def _forbidden():
    return web.json_response({"error": "Core Admin Authorization Required!"}, status=403, dumps=fast_json)


# ─────────────────────────────────────────────────────────
# 🏷️ CUSTOM QUALITY / SOURCE NAMES  (Sky, UnTuch, FreeMasx, Mydesi…)
# ─────────────────────────────────────────────────────────
@group_routes.get("/api/group/tags")
async def api_group_tags(req):
    """Admin ke apne quality names + kaunsi quality kis file me mili (live preview)."""
    role, _ = await get_user_role(req)
    if role != "admin":
        return _forbidden()
    tags = await _safe_tags()
    return web.json_response({"tags": tags, "total": len(tags)}, dumps=fast_json)


@group_routes.post("/api/group/tags")
async def api_group_tags_save(req):
    """Add / remove / replace — {tags:[...]}  ya  {add:"Sky"}  ya  {remove:"Sky"}."""
    role, _ = await get_user_role(req)
    if role != "admin":
        return _forbidden()

    try:
        data = await req.json()
    except Exception:
        return web.json_response({"error": "Invalid payload!"}, status=400, dumps=fast_json)

    try:
        if data.get("add") is not None:
            tags = await fg.add_tag(data.get("add"))
        elif data.get("remove") is not None:
            tags = await fg.remove_tag(data.get("remove"))
        elif isinstance(data.get("tags"), list):
            tags = await fg.set_tags(data.get("tags"))
        else:
            return web.json_response({"error": "tags / add / remove chahiye!"}, status=400, dumps=fast_json)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500, dumps=fast_json)

    try:
        await _rekey_groups(tags)
    except Exception as e:
        logger.warning(f"Group rekey failed: {e}")
    _clear_search_caches()          # grouping badli → purane grouped pages stale
    return web.json_response({"success": True, "tags": tags, "total": len(tags)}, dumps=fast_json)


@group_routes.get("/api/group/tags/scan")
async def api_group_tags_scan(req):
    """Search box wale naam se dekho kaunsi custom quality kis file me mili (count ke saath)."""
    role, _ = await get_user_role(req)
    if role != "admin":
        return _forbidden()

    q = (req.query.get("q") or "").strip()
    tags = await _safe_tags()
    if not q:
        return web.json_response({"tags": tags, "found": {}, "checked": 0}, dumps=fast_json)

    try:
        docs, _, _, _ = await get_search_results(q, 120, 0, collection_type="all", bypass_count=True)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500, dumps=fast_json)

    found, unknown = {}, 0
    for d in docs:
        name = str(d.get("file_name") or "")
        tag = match_tag(name, tags)
        if tag:
            found[tag] = found.get(tag, 0) + 1
        else:
            unknown += 1
    return web.json_response(
        {"tags": tags, "found": found, "checked": len(docs), "untagged": unknown}, dumps=fast_json
    )


# ─────────────────────────────────────────────────────────
# 📋 LIST + LOOKUP
# ─────────────────────────────────────────────────────────
@group_routes.get("/api/groups")
async def api_groups(req):
    role, _ = await get_user_role(req)
    if role != "admin":
        return _forbidden()

    q = (req.query.get("q") or "").strip()
    try:
        groups = await fg.list_groups(limit=200, q=q)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500, dumps=fast_json)

    all_fids = [m["fid"] for g in groups for m in fg.clean_members(g.get("members"))]
    docs = await fg.docs_for_fids(all_fids)
    tags = await _safe_tags()

    out = []
    for g in groups:
        rows = []
        for m in fg.clean_members(g.get("members")):
            d = docs.get(m["fid"])
            if not d:
                continue
            r = _row_from_doc(d, tags)
            r["group"] = str(g["_id"])
            rows.append(r)
        out.append(_payload(g, rows))

    return web.json_response({"groups": out, "total": len(out)}, dumps=fast_json)


@group_routes.get("/api/group/files")
async def api_group_files(req):
    """Modal ka data source.

    ?gid=…        → us group ka payload (members ke saath)
    ?file_id=…    → us file ka group (agar hai) + same-title suggestions
    ?q=…          → naam se files (alag naam wali file jodne ke liye)
    """
    role, _ = await get_user_role(req)
    if role != "admin":
        return _forbidden()

    gid = (req.query.get("gid") or "").strip()
    fid = (req.query.get("file_id") or "").strip()
    col = (req.query.get("col") or "primary").lower()
    q = (req.query.get("q") or "").strip()
    typed_q = bool(q)          # user ne khud search box me type kiya (seed suggestions nahi)

    tags = await _safe_tags()
    group = None
    seed_doc = None
    seed_row = None

    try:
        if gid:
            g = await fg.get_group(gid)
            if not g:
                return web.json_response({"error": "Group not found!"}, status=404, dumps=fast_json)
            group = await _group_payload(g)
        elif fid:
            seed_doc = await _find_doc(fid, col)
            if seed_doc:
                gm = await fg.groups_for_fids([str(fid)])
                g = gm.get(str(fid))
                if g:
                    group = await _group_payload(g)
                seed_row = _row_from_doc(seed_doc, tags)
                seed_row["group"] = group["gid"] if group else ""
                seed_row["same_key"] = True
                if not q:
                    q = shortcut_title(seed_doc.get("file_name", ""), tags)
        elif not q:
            return web.json_response(
                {"group": None, "files": [], "seed": None, "title": ""}, dumps=fast_json
            )
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500, dumps=fast_json)

    files = []
    if q:
        try:
            if seed_doc and not typed_q:
                docs = await _suggest_docs_for_name(seed_doc.get("file_name", ""), tags=tags)
            else:
                docs, _, _, _ = await get_search_results(
                    q, GROUP_FILES_LIMIT, 0, collection_type="all", bypass_count=True
                )
        except Exception as e:
            logger.warning(f"Group file search failed: {e}")
            docs = []

        rows = [_row_from_doc(d, tags) for d in docs]

        # kis file ka group pehle se hai (dusre group me add karte waqt warning ke liye)
        try:
            gm = await fg.groups_for_fids([r["fid"] for r in rows] + ([fid] if fid else []))
        except Exception:
            gm = {}
        for r in rows:
            g2 = gm.get(r["fid"])
            r["group"] = str(g2["_id"]) if g2 else ""
            r["same_key"] = False

        if seed_doc:
            base_name = seed_doc.get("file_name", "")
            seed_id = str(seed_doc["_id"])
            seed_row = seed_row or _row_from_doc(seed_doc, tags)
            if not any(r["fid"] == seed_id for r in rows):
                rows.insert(0, seed_row)
            base_key = group_key(base_name, tags=tags)
            for r in rows:
                r["same_key"] = bool(base_key) and base_key == group_key(r.get("name"), tags=tags)
            rows.sort(key=lambda r: -suggest_score(base_name, r.get("name")))
            seed_row = next((r for r in rows if r["fid"] == seed_id), seed_row)

        files = rows

    return web.json_response({
        "group": group,
        "files": files,
        "seed": seed_row,
        "title": (group["title"] if group else (group_title(seed_doc.get("file_name", ""), tags=tags) if seed_doc else "")),
    }, dumps=fast_json)


# ─────────────────────────────────────────────────────────
# ✏️ CREATE / UPDATE / DELETE
# ─────────────────────────────────────────────────────────
@group_routes.post("/api/group/save")
async def api_group_save(req):
    role, _ = await get_user_role(req)
    if role != "admin":
        return _forbidden()

    try:
        data = await req.json()
    except Exception:
        return web.json_response({"error": "Invalid payload!"}, status=400, dumps=fast_json)

    gid = str(data.get("gid") or "").strip()
    title = str(data.get("title") or "").strip()
    members = fg.clean_members(data.get("members"))
    verified = data.get("verified", None)          # None = jo hai wahi rehne do
    verified = None if verified is None else bool(verified)

    if not title:
        return web.json_response({"error": "Group name is required!"}, status=400, dumps=fast_json)

    try:
        docs = await fg.docs_for_fids([m["fid"] for m in members])
        # collection DB doc se correct karo (galat col se thumb/stream na toote)
        fixed = []
        for m in members:
            d = docs.get(m["fid"])
            fixed.append({"fid": m["fid"], "col": (d.get("source_col") if d else m["col"]) or "primary"})
        members = fixed

        first_name = next((docs[m["fid"]].get("file_name", "") for m in members if m["fid"] in docs), "")
        tags = await _safe_tags()
        key = group_key(first_name, tags=tags) if first_name else group_key(title, tags=tags)

        g = None
        if gid:
            g = await fg.get_group(gid)
            if not g:
                return web.json_response({"error": "Group not found!"}, status=404, dumps=fast_json)
            await fg.set_members(gid, members)
            g = await fg.update_group(gid, title=title, key=key, verified=verified)
        else:
            # same key ka manual group pehle se hai → duplicate card banane ki jagah usi me merge
            existing = await fg.find_by_key(key) if key else None
            if existing:
                await fg.set_members(str(existing["_id"]), members)
                g = await fg.update_group(str(existing["_id"]), title=title, key=key, verified=verified)
            else:
                g = await fg.create_group(title, members, key=key, verified=bool(verified))

        _clear_search_caches()
        return web.json_response({"success": True, "group": await _group_payload(g)}, dumps=fast_json)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500, dumps=fast_json)


@group_routes.post("/api/group/thumb")
async def api_group_thumb_upload(req):
    role, _ = await get_user_role(req)
    if role != "admin":
        return _forbidden()

    try:
        reader = await req.multipart()
        gid, image_bytes = None, None
        while True:
            part = await reader.next()
            if part is None:
                break
            if part.name == "group_id":
                gid = (await part.read()).decode().strip()
            elif part.name == "image":
                image_bytes = await part.read()

        if not gid or not image_bytes:
            return web.json_response({"error": "Missing group_id or image!"}, status=400, dumps=fast_json)

        g = await fg.get_group(gid)
        if not g:
            return web.json_response({"error": "Group not found!"}, status=404, dumps=fast_json)

        with io.BytesIO(image_bytes) as img_buffer:
            img_buffer.name = "group-poster.jpg"
            msg = await temp.BOT.send_photo(chat_id=THUMBNAIL_STORAGE_CHANNEL, photo=img_buffer)

        if not msg or not msg.photo:
            return web.json_response({"error": "Telegram upload failed!"}, status=500, dumps=fast_json)

        new_thumb_id = (
            msg.photo.sizes[-1].file_id
            if hasattr(msg.photo, "sizes") and msg.photo.sizes
            else msg.photo.file_id
        )
        g = await fg.update_group(gid, thumb_url=f"TG_ID:{new_thumb_id}")
        _clear_search_caches()
        return web.json_response({"success": True, "group": await _group_payload(g)}, dumps=fast_json)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500, dumps=fast_json)


@group_routes.post("/api/group/delete")
async def api_group_delete(req):
    role, _ = await get_user_role(req)
    if role != "admin":
        return _forbidden()

    try:
        data = await req.json()
    except Exception:
        return web.json_response({"error": "Invalid payload!"}, status=400, dumps=fast_json)

    gid = str(data.get("gid") or "").strip()
    if not gid:
        return web.json_response({"error": "Missing group id!"}, status=400, dumps=fast_json)

    ok = await fg.delete_group(gid)
    _clear_search_caches()
    return web.json_response({"success": ok}, dumps=fast_json)


@group_routes.post("/api/group/verify")
async def api_group_verify(req):
    """Admin ka bharosa (verified) flag on/off — group id ko "official" banata hai."""
    role, _ = await get_user_role(req)
    if role != "admin":
        return _forbidden()

    try:
        data = await req.json()
    except Exception:
        return web.json_response({"error": "Invalid payload!"}, status=400, dumps=fast_json)

    gid = str(data.get("gid") or "").strip()
    if not gid:
        return web.json_response({"error": "Missing group id!"}, status=400, dumps=fast_json)

    g = await fg.get_group(gid)
    if not g:
        return web.json_response({"error": "Group not found!"}, status=404, dumps=fast_json)

    g = await fg.set_verified(gid, bool(data.get("verified", True)))
    _clear_search_caches()
    return web.json_response({"success": True, "group": await _group_payload(g)}, dumps=fast_json)


@group_routes.post("/api/group/migrate")
async def api_group_migrate(req):
    """Source group ki saari files target group me merge karke source delete.

    Files delete nahi hoti — sirf grouping move hoti hai. Merge ke baad target
    group ka title/thumbnail/key waisa hi rehta hai.
    """
    role, _ = await get_user_role(req)
    if role != "admin":
        return _forbidden()

    try:
        data = await req.json()
    except Exception:
        return web.json_response({"error": "Invalid payload!"}, status=400, dumps=fast_json)

    gid = str(data.get("gid") or "").strip()
    target = str(data.get("target") or "").strip()
    if not target:
        return web.json_response({"error": "Missing target group id!"}, status=400, dumps=fast_json)
    if gid == target:
        return web.json_response({"error": "Same group me migrate nahi kar sakte!"}, status=400, dumps=fast_json)

    try:
        dst = await fg.get_group(target)
        if not dst:
            return web.json_response({"error": "Group not found!"}, status=404, dumps=fast_json)

        if gid:
            src = await fg.get_group(gid)
            if not src:
                return web.json_response({"error": "Group not found!"}, status=404, dumps=fast_json)
            src_members = fg.clean_members(src.get("members"))
        else:
            # DB me save na hua (auto) group: card ke members hi source hain
            src_members = fg.clean_members(data.get("members"))
            if not src_members:
                return web.json_response({"error": "Group me koi file nahi mili!"}, status=400, dumps=fast_json)

        members = fg.clean_members(dst.get("members"))
        seen = {m["fid"] for m in members}
        for m in src_members:
            if m["fid"] not in seen:
                seen.add(m["fid"])
                members.append(m)

        g = await fg.set_members(target, members)
        if gid:
            await fg.delete_group(gid)
        _clear_search_caches()
        return web.json_response({"success": True, "group": await _group_payload(g)}, dumps=fast_json)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500, dumps=fast_json)


# ─────────────────────────────────────────────────────────
# 📄 ADMIN PAGE — /groups
# ─────────────────────────────────────────────────────────
_GROUPS_PAGE_HTML = """
<div class="main" style="padding-top:22px;max-width:1200px;margin:0 auto;padding-left:16px;padding-right:16px">
  <div class="gm-page-head">
    <div>
      <div class="gm-page-title">&#128451; Quality Groups</div>
      <div class="gm-page-sub">Yahan se master group ka naam / thumbnail badlo, alag naam wali files jodo,
      member hatao ya group delete karo. Har group ka apna &#128279; ID hota hai &mdash; do group ek jaise hon to
      <b>Migrate</b> se ek ID doosre me daal do, dono ek group ban jayenge.
      <b>&#9989; Verified</b> wahi group maana jayega jise admin ne khud check karke tick kiya ho;
      baaki groups auto-detect hue hain, unme galti ho sakti hai.<br>
      <b>&#127991; Meri Quality Names</b> (Sky / UnTuch / FreeMasx / Mydesi) yahan add karo &mdash;
      in naam wali files ek hi title ke saath ek card me aayengi (jaise 1080p/720p).</div>
    </div>
    <button class="gm-new-btn" onclick="openGroupModal(null,null,null)">&#10133; New Group</button>
  </div>
  <div id="gmTagsSlot"></div>
  <div class="gm-grid" id="groupGrid"></div>
</div>
"""

_GROUPS_PAGE_JS = """<script>
function gmGroupCard(g){
    var labels=[];
    (g.members||[]).forEach(function(m){ if(m.ql && labels.indexOf(m.ql)===-1) labels.push(m.ql); });
    var vchip = g.verified
        ? '<span class="gm-vchip ok">&#10003; VERIFIED</span>'
        : '<span class="gm-vchip warn">&#9888; UNVERIFIED</span>';
    var idchip = '<span class="gm-idchip">#'+gmEsc(String(g.gid||'').slice(-6))+'</span>';
    return '<div class="gm-gcard" onclick="openGroupModal(null,null,\\''+g.gid+'\\')">'+
        '<div class="gm-gposter"><img src="'+g.thumb+'" loading="lazy" onerror="this.style.display=\\'none\\'">'+
        '<div class="gm-gtop">'+vchip+idchip+'</div>'+
        '<div class="gm-gbadge"><span>&#127916; '+g.count+' '+(g.count===1?'Quality':'Qualities')+'</span></div></div>'+
        '<div class="gm-gbody"><div class="gm-gname">'+gmEsc(g.title)+'</div>'+
        '<div class="gm-gmeta">'+labels.map(function(l){return '<b>'+gmEsc(l)+'</b>';}).join('')+'</div></div></div>';
}
async function gmPageReload(){
    var grid=document.getElementById('groupGrid');
    if(!grid) return;
    grid.innerHTML='<div class="empty"><div class="spinner"></div></div>';
    try{
        var r=await fetch('/api/groups');
        var d=await r.json();
        var gs=d.groups||[];
        if(!gs.length){
            grid.innerHTML='<div class="empty"><div class="empty-icon">&#128451;</div><p>Abhi koi manual group nahi hai. "New Group" dabao ya dashboard par kisi file card ke &#128451; button se group banao.</p></div>';
            return;
        }
        grid.innerHTML=gs.map(gmGroupCard).join('');
    }catch(e){
        grid.innerHTML='<div class="empty"><p>Groups load nahi hue. Refresh karo.</p></div>';
    }
}
document.addEventListener('DOMContentLoaded', function(){
    /* 🏷️ tags panel (GROUP_TAGS_HTML) ko page ke theek upar wale slot me daal do */
    var slot = document.getElementById('gmTagsSlot');
    var panel = document.querySelector('.gm-tagpanel');
    if(slot && panel){ slot.appendChild(panel); }
    gmPageReload();
    if(typeof gmTagLoad === 'function') gmTagLoad();
});
</script>"""


@group_routes.get('/groups')
async def groups_page(req):
    role, tg_id = await get_auth(req)
    if not role:
        return web.HTTPFound('/login')
    if role != 'admin':
        return web.HTTPFound('/dashboard')

    body = (GROUP_UI_CSS + _GROUPS_PAGE_HTML + GROUP_MODAL_HTML + GROUP_MIGRATE_HTML
            + GROUP_TAGS_HTML + _GROUPS_PAGE_JS + GROUP_UI_JS)
    return build_page("Quality Groups - Fast Finder", body, "", "groups", role)
