"""🗂️ MANUAL QUALITY GROUPS (DB-backed)

Admin jab web UI se kuch files ko ek group me daalta hai (chahe unke naam thode
alag hon), wo grouping yahan MongoDB me save hoti hai — isliye baar-baar grouping
nahi karni padti aur thumbnail/naam bhi permanent rehta hai.

Doc schema (collection: FileGroups):
    {
      "_id":       ObjectId,        # gid (web UI me string ke roop me)
      "title":     str,             # admin ka diya hua naam (editable)
      "key":       str,             # auto-group key (nayi same-title files auto attach)
      "thumb_url": "TG_ID:..." | "",# custom master thumbnail (editable)
      "members":   [{"fid": str, "col": "primary|cloud|archive"}, ...],
      "verified":  bool,            # admin ne check karke "haan ye group sahi hai" kaha
      "created_on": float, "updated_on": float
    }

`verified` sirf admin ka bharosa hai: auto (bina verify) groups ko UI "unverified"
dikhata hai. Group ID har group ke paas hota hai, lekin bharosemand sirf verified.

Custom quality/source names (Sky, UnTuch, FreeMasx, Mydesi…) `GroupSettings`
collection me ek doc `_id="release_tags"` ke andar `tags: [...]` ki tarah rehte hain.

Ek file sirf EK manual group me rah sakti hai — `add` karte waqt baaki groups se
$pull kar diya jaata hai (web/group_routes.py isi helper ko use karta hai).
"""

import logging
import time

from bson.objectid import ObjectId

from database.ia_filterdb import db, FILE_COLLECTIONS

logger = logging.getLogger(__name__)

file_groups = db["FileGroups"]

# 🏷️ Admin ke apne quality/source names (Sky, UnTuch, FreeMasx, Mydesi…) —
# alag chhoti collection me ek hi doc ("release_tags"), taaki groups saath na uljhein.
group_settings = db["GroupSettings"]
_TAGS_ID = "release_tags"

# File collections hi (actors ka schema alag hai — wahan file_name/thumb_url nahi hote)
_GROUP_COLS = {k: v for k, v in FILE_COLLECTIONS.items()}


async def ensure_group_indexes():
    """Startup par ek baar — members ke fid aur key par index (search fast rahe)."""
    try:
        await file_groups.create_index("members.fid", name="fg_members_fid")
        await file_groups.create_index("key", name="fg_key")
        await file_groups.create_index([("updated_on", -1)], name="fg_updated")
        logger.info("✅ Manual Group indexes OK")
    except Exception as e:
        if "already exists" not in str(e) and "IndexKeySpecsConflict" not in str(e):
            logger.warning(f"Group index warning: {e}")


async def get_tags():
    """Admin ke custom quality/source names (list of str, original case)."""
    try:
        doc = await group_settings.find_one({"_id": _TAGS_ID}) or {}
    except Exception as e:
        logger.warning(f"Tags read failed: {e}")
        return []
    return clean_tags(doc.get("tags"))


def clean_tags(tags):
    """["Sky","UnTuch", ...] → trimmed, dedupe (case-insensitive), max 60 tags."""
    out, seen = [], set()
    for t in tags or []:
        t = str(t or "").strip()
        if not t or len(t) > 32:
            continue
        k = t.lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(t)
        if len(out) >= 60:
            break
    return out


async def set_tags(tags):
    """Poori list replace (web UI se). Return: saaf ki hui list."""
    clean = clean_tags(tags)
    await group_settings.update_one(
        {"_id": _TAGS_ID},
        {"$set": {"tags": clean, "updated_on": time.time()}},
        upsert=True,
    )
    return clean


async def add_tag(tag):
    tags = await get_tags()
    if str(tag or "").strip().lower() in {t.lower() for t in tags}:
        return tags
    return await set_tags(tags + [tag])


async def remove_tag(tag):
    tags = await get_tags()
    low = str(tag or "").strip().lower()
    return await set_tags([t for t in tags if t.lower() != low])


def _oid(gid):
    try:
        return ObjectId(str(gid))
    except Exception:
        return None


def clean_members(members):
    """[fid...] ya [{"fid","col"}...] → [{"fid","col"}] (dedupe + valid collection)."""
    out, seen = [], set()
    for m in members or []:
        if isinstance(m, dict):
            fid = str(m.get("fid") or m.get("file_id") or "").strip()
            col = str(m.get("col") or m.get("collection") or "primary").strip().lower()
        else:
            fid, col = str(m or "").strip(), "primary"
        if not fid or fid in seen:
            continue
        if col not in _GROUP_COLS:
            col = "primary"
        seen.add(fid)
        out.append({"fid": fid, "col": col})
    return out


async def _detach_from_others(keep_id, members):
    """In files ko baaki groups se nikaal do — ek file = ek group."""
    fids = [m["fid"] for m in members]
    if not fids:
        return
    try:
        await file_groups.update_many(
            {"_id": {"$ne": keep_id}, "members.fid": {"$in": fids}},
            {"$pull": {"members": {"fid": {"$in": fids}}}, "$set": {"updated_on": time.time()}},
        )
    except Exception as e:
        logger.warning(f"Group detach failed: {e}")


async def find_by_key(key):
    """Same auto-key wala pehle se bana manual group (duplicate card na bane)."""
    key = str(key or "").strip()
    if not key:
        return None
    return await file_groups.find_one({"key": key})


async def get_group(gid):
    oid = _oid(gid)
    if not oid:
        return None
    return await file_groups.find_one({"_id": oid})


async def get_group_raw(gid):
    """gid (ObjectId/str) → doc, bina ObjectId validate kiye (str `_id` bhi try)."""
    doc = await get_group(gid)
    if doc:
        return doc
    return await file_groups.find_one({"_id": str(gid)})


async def create_group(title, members=None, thumb_url="", key="", verified=False):
    now = time.time()
    doc = {
        "title": str(title or "").strip(),
        "key": str(key or "").strip(),
        "thumb_url": str(thumb_url or "").strip(),
        "members": clean_members(members),
        "verified": bool(verified),
        "created_on": now,
        "updated_on": now,
    }
    res = await file_groups.insert_one(doc)
    doc["_id"] = res.inserted_id
    await _detach_from_others(res.inserted_id, doc["members"])
    return doc


async def update_group(gid, title=None, thumb_url=None, key=None, verified=None):
    oid = _oid(gid)
    if not oid:
        return None
    payload = {"updated_on": time.time()}
    if title is not None:
        payload["title"] = str(title).strip()
    if thumb_url is not None:
        payload["thumb_url"] = str(thumb_url).strip()
    if key is not None:
        payload["key"] = str(key).strip()
    if verified is not None:
        payload["verified"] = bool(verified)
    await file_groups.update_one({"_id": oid}, {"$set": payload})
    return await file_groups.find_one({"_id": oid})


async def set_members(gid, members):
    """Poori member list replace (web modal 'Save' isi ko call karta hai)."""
    oid = _oid(gid)
    if not oid:
        return None
    clean = clean_members(members)
    await _detach_from_others(oid, clean)
    await file_groups.update_one(
        {"_id": oid},
        {"$set": {"members": clean, "updated_on": time.time()}},
    )
    return await file_groups.find_one({"_id": oid})


async def set_verified(gid, verified=True):
    """Admin verify/unverify — sirf flag badalta hai (title/members waise hi)."""
    return await update_group(gid, verified=bool(verified))


async def delete_group(gid):
    oid = _oid(gid)
    if not oid:
        return False
    res = await file_groups.delete_one({"_id": oid})
    return bool(res.deleted_count)


async def list_groups(limit=300, q=""):
    flt = {}
    q = str(q or "").strip()
    if q:
        flt = {"title": {"$regex": q, "$options": "i"}}
    cursor = file_groups.find(flt).sort([("updated_on", -1)]).limit(max(1, min(int(limit), 500)))
    return await cursor.to_list(length=limit)


async def groups_for_page(fids=None, keys=None):
    """Ek hi query me page ke fids + auto-keys se jude manual groups.

    `fids` se wo groups milte hain jinme page ki koi saved member file hai;
    `keys` se wo groups milte hain jinki title-key page ke kisi file se match
    karti hai (isliye nayi same-title file khud group me aa jaati hai).
    """
    ors = []
    fids = [str(f) for f in (fids or []) if f][:250]
    keys = [str(k) for k in (keys or []) if k][:250]
    if fids:
        ors.append({"members.fid": {"$in": fids}})
    if keys:
        ors.append({"key": {"$in": keys}})
    if not ors:
        return []
    flt = ors[0] if len(ors) == 1 else {"$or": ors}
    return await file_groups.find(flt).to_list(length=100)


async def groups_for_fids(fids):
    """{fid: group_doc} — sirf member-based lookup (thumb fallback ke liye)."""
    fids = [str(f) for f in (fids or []) if f][:250]
    if not fids:
        return {}
    out = {}
    async for g in file_groups.find({"members.fid": {"$in": fids}}):
        for m in g.get("members") or []:
            out.setdefault(m.get("fid"), g)
    return out


async def docs_for_fids(fids):
    """{fid: doc} — ek-ek collection par sirf ek query (bulk list ke liye).

    `_id` dono roop me try hota hai (string file_id aur ObjectId), kyunki purane
    docs me kabhi string `_id` bhi ho sakta hai.
    """
    fids = [str(f) for f in (fids or []) if f]
    if not fids:
        return {}
    wanted = set(fids)
    ids = list(wanted)
    for f in fids:
        try:
            ids.append(ObjectId(f))
        except Exception:
            pass

    found = {}
    for _name, col in _GROUP_COLS.items():
        try:
            async for doc in col.find({"_id": {"$in": ids}}):
                doc["file_id"] = doc["_id"]
                doc["source_col"] = col.name.lower()
                key = str(doc["_id"])
                if key in wanted:
                    found.setdefault(key, doc)
        except Exception as e:
            logger.debug(f"group member fetch failed [{col.name}]: {e}")
    return found


async def fetch_member_docs(members):
    """Member list (order preserve) → DB docs. Delete ho chuki files skip hoti hain."""
    members = clean_members(members)
    if not members:
        return []
    found = await docs_for_fids([m["fid"] for m in members])
    return [found[m["fid"]] for m in members if m["fid"] in found]


async def count_groups():
    try:
        return await file_groups.count_documents({})
    except Exception:
        return 0
