"""🗂️ GROUP ADMIN UI (shared assets)

Dashboard (file card par 🗂 button) aur `/groups` page — dono ek hi modal + JS
use karte hain, isliye grouping ka UI kahin duplicate nahi hai.

Modal ek hi jagah se teeno kaam karta hai:
  • naya group banana (naam + thumbnail),
  • maujooda group ka naam/thumbnail badalna,
  • alag-alag naam wali files ko search karke group me jodna / nikaalna.

Dashboard par group card ka THUMBNAIL tap karne par action row khulti hai:
Manage (yahi modal) / Verify (✅ bharosemand) / Migrate (doosre group me merge) / Delete.
Group ka NAAM tap karne par uski saari files khulti hain. Har group ka 🆔 hota hai;
sirf admin-verified group hi "bharosemand" mana jaata hai.
"""

GROUP_UI_CSS = """<style>
.gm-card{max-width:620px}
.gm-head{display:flex;gap:14px;margin-bottom:12px}
.gm-thumbbox{width:132px;flex-shrink:0}
.gm-thumb{width:100%;aspect-ratio:16/9;border-radius:8px;background:var(--bg3);border:1px solid var(--border);overflow:hidden;display:flex;align-items:center;justify-content:center}
.gm-thumb img{width:100%;height:100%;object-fit:cover}
.gm-thumbph{font-size:28px;opacity:.45}
.gm-filebtn{display:block;text-align:center;background:var(--bg4);border:1px dashed var(--border);padding:8px;border-radius:6px;cursor:pointer;font-weight:700;font-size:11px;margin-top:8px;color:var(--text)}
.gm-filebtn:hover{background:var(--bg3);border-color:var(--accent)}
.gm-members,.gm-results{display:flex;flex-direction:column;gap:6px;max-height:210px;overflow-y:auto;padding-right:2px}
.gm-mrow{display:flex;align-items:center;gap:9px;background:var(--bg3);border:1px solid var(--border);border-radius:8px;padding:6px 8px}
.gm-mthumb{width:54px;height:32px;border-radius:5px;object-fit:cover;background:var(--bg4);flex-shrink:0}
.gm-mbody{flex:1;min-width:0}
.gm-mname{font-size:11.5px;font-weight:700;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.gm-mmeta{font-size:10px;color:var(--muted);margin-top:2px}
.gm-x{background:rgba(160,8,8,.82);border:1px solid rgba(229,9,20,.4);color:#fff;border-radius:5px;width:25px;height:25px;font-size:11px;cursor:pointer;flex-shrink:0}
.gm-add{background:var(--accent);border:0;color:#fff;border-radius:5px;padding:6px 11px;font-size:10.5px;font-weight:800;cursor:pointer;flex-shrink:0}
.gm-add:disabled{opacity:.45;cursor:default}
.gm-searchrow{display:flex;gap:8px;margin-bottom:8px}
.gm-searchrow .em-input{margin-bottom:0;flex:1}
.gm-empty{font-size:11.5px;color:var(--muted);padding:8px 2px}
.gm-actions{display:flex;gap:10px;margin-top:18px}
.gm-actions .em-save-btn{flex:1}
.gm-del-btn{background:transparent;border:1px solid rgba(229,9,20,.6);color:#ff6b6b;border-radius:6px;padding:0 16px;font-weight:800;font-size:12px;cursor:pointer}
.gm-del-btn:hover{background:rgba(229,9,20,.15)}
.gm-hint{font-size:10.5px;color:var(--muted);margin-top:4px;line-height:1.5}
/* /groups page */
.dash-groups-fab{position:fixed;left:16px;bottom:18px;z-index:120;display:inline-flex;align-items:center;gap:8px;background:var(--bg2);border:1px solid var(--border);border-radius:999px;padding:10px 16px;font-size:12px;font-weight:800;color:var(--text);text-decoration:none;box-shadow:0 6px 24px rgba(0,0,0,.45);transition:border-color .15s,transform .15s}
.dash-groups-fab:hover{border-color:var(--accent);transform:translateY(-2px)}
.gm-page-head{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;margin-bottom:18px}
.gm-page-title{font-size:22px;font-weight:900}
.gm-page-sub{font-size:12px;color:var(--muted);margin-top:4px;max-width:640px;line-height:1.55}
.gm-new-btn{background:var(--accent);color:#fff;border:0;border-radius:8px;padding:11px 18px;font-weight:800;font-size:13px;cursor:pointer}
.gm-new-btn:hover{background:var(--accent-hover)}
.gm-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px}
.gm-gcard{background:var(--card);border:1px solid var(--border);border-radius:10px;overflow:hidden;cursor:pointer;transition:transform .18s,border-color .18s;display:flex;flex-direction:column}
.gm-gcard:hover{transform:translateY(-3px);border-color:var(--accent)}
.gm-gposter{position:relative;padding-top:56.25%;background:var(--bg3);overflow:hidden}
.gm-gposter img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.gm-gbadge{position:absolute;left:0;right:0;bottom:0;display:flex;align-items:center;gap:5px;padding:18px 8px 7px;background:linear-gradient(to top,rgba(0,0,0,.92),transparent);font-size:10px;font-weight:900;color:#fff;letter-spacing:.3px}
.gm-gbadge span{background:rgba(229,9,20,.92);border:1px solid rgba(255,255,255,.22);border-radius:5px;padding:2px 7px}
.gm-gbody{padding:9px 11px 11px}
.gm-gname{font-size:12.5px;font-weight:800;color:var(--text);line-height:1.4;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}
.gm-gmeta{font-size:10.5px;color:var(--muted);margin-top:5px;display:flex;gap:6px;flex-wrap:wrap}
.gm-gmeta b{color:#ffd166;font-weight:800}
/* 🔀 migrate popup */
.gm-migrow{cursor:pointer;transition:border-color .15s,background .15s}
.gm-migrow:hover{border-color:var(--accent);background:var(--bg4)}
.gm-migrow .gm-add{margin-left:auto}
.gm-mig-title{font-size:11.5px;font-weight:900;color:#ffd166;margin:2px 0 8px}
/* ✅ verified / ⚠ unverified badges + group id */
.gm-vchip{display:inline-flex;align-items:center;gap:4px;border-radius:5px;padding:2px 7px;font-size:9px;font-weight:900;letter-spacing:.4px}
.gm-vchip.ok{background:rgba(16,120,60,.9);border:1px solid rgba(60,220,130,.45);color:#d1ffe4}
.gm-vchip.warn{background:rgba(140,100,10,.88);border:1px solid rgba(255,209,102,.45);color:#ffe9b0}
.gm-idchip{display:inline-flex;align-items:center;border-radius:5px;padding:2px 6px;font-size:9px;font-weight:900;letter-spacing:.3px;background:rgba(0,0,0,.66);border:1px solid rgba(255,255,255,.22);color:#cfd6e4;font-family:ui-monospace,Menlo,monospace}
.gm-gtop{position:absolute;top:0;left:0;right:0;display:flex;align-items:center;gap:5px;padding:7px 8px;z-index:2}
.gm-vrow{display:flex;align-items:flex-start;gap:9px;margin-top:12px;background:var(--bg3);border:1px solid var(--border);border-radius:8px;padding:9px 11px;cursor:pointer}
.gm-vrow input{margin-top:2px;accent-color:var(--accent);width:15px;height:15px;flex-shrink:0;cursor:pointer}
.gm-vrow b{font-size:12px;display:block;color:var(--text)}
.gm-vrow span{font-size:10.5px;color:var(--muted);line-height:1.5}
/* 🧩 basis dropdown 2 dropdown ke saath fit ho — mobile par wrap */
#cddBasisWrap .cdd-btn{max-width:44vw;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
@media(max-width:560px){.search-row2{flex-wrap:wrap;row-gap:8px}}
</style>"""


# 🧩 GROUPING BASIS selector — sirf admin ke dashboard me search row me inject hota hai.
GROUP_BASIS_HTML = """
<div class="cdd-wrap" id="cddBasisWrap">
    <div class="cdd-btn" id="cddBasisBtn" onclick="toggleBasis(event)">
        <span id="cddBasisLabel">&#129513; Quality</span>
    </div>
    <span class="cdd-arrow">&#9660;</span>
    <div class="cdd-menu" id="cddBasisMenu" style="display:none">
        <div class="cdd-item selected" data-val="quality" onclick="pickBasis('quality','&#129513; Quality',this)">&#129513; Quality (same title, saari qualities)<span class="cdd-radio"><span class="cdd-radio-dot"></span></span></div>
        <div class="cdd-item" data-val="episode" onclick="pickBasis('episode','&#127902; Episode',this)">&#127902; Episode (har episode ka apna card)<span class="cdd-radio"><span class="cdd-radio-dot"></span></span></div>
        <div class="cdd-item" data-val="season" onclick="pickBasis('season','&#128250; Season',this)">&#128250; Season (ek season ke saare episodes)<span class="cdd-radio"><span class="cdd-radio-dot"></span></span></div>
    </div>
</div>
<script>
(function(){
    var v = 'quality';
    try { v = localStorage.getItem('ff_dashboard_basis') || 'quality'; } catch(e) {}
    if(['quality','episode','season'].indexOf(v) < 0) v = 'quality';
    if(typeof gbasis !== 'undefined') gbasis = v;
    var labels = {quality:'&#129513; Quality', episode:'&#127902; Episode', season:'&#128250; Season'};
    var l = document.getElementById('cddBasisLabel');
    if(l) l.innerHTML = labels[v];
    document.querySelectorAll('#cddBasisMenu .cdd-item').forEach(function(i){
        i.classList.toggle('selected', i.getAttribute('data-val') === v);
    });
})();
</script>
"""


GROUP_MODAL_HTML = """
<div class="edit-modal" id="groupModal" onclick="if(event.target===this)closeGroupModal()">
    <div class="em-card gm-card">
        <button class="em-close" onclick="closeGroupModal()">&#10005;</button>
        <div class="em-title" id="gmHeading">&#128451; Quality Group</div>

        <div class="gm-head">
            <div class="gm-thumbbox">
                <div class="gm-thumb" id="gmThumb"><span class="gm-thumbph">&#127916;</span></div>
                <label class="gm-filebtn">&#128247; Change Thumb
                    <input type="file" id="gmThumbFile" accept="image/*" style="display:none" onchange="gmPickThumb(this)">
                </label>
            </div>
            <div style="flex:1;min-width:0">
                <div class="scard-label">Group Name</div>
                <input type="text" id="gmTitle" class="em-input" placeholder="e.g. Movie Name (2025) Full HD">
                <div class="gm-hint">Naam aur thumbnail search results me master card par dikhte hain. Quality count files se apne aap banta hai.</div>
            </div>
        </div>

        <label class="gm-vrow" for="gmVerified">
            <input type="checkbox" id="gmVerified">
            <span><b>&#9989; Admin-verified group</b>
            Tick karne par ye group + uska ID "bharosemand" maana jayega. Bina tick wale groups auto-detect hue hain &mdash; unme galti ho sakti hai.</span>
        </label>

        <div class="scard-label" style="margin-top:12px">&#128194; Files in this group (<span id="gmCount">0</span>)</div>
        <div class="gm-members" id="gmMembers"></div>

        <div class="scard-label" style="margin-top:12px">&#10133; Add files (alag naam bhi chalega &mdash; search karke add karo)</div>
        <div class="gm-searchrow">
            <input type="text" id="gmSearch" class="em-input" placeholder="File ka naam type karo&hellip;" onkeydown="if(event.key==='Enter'){event.preventDefault();gmSearch();}">
            <button class="em-save-btn" style="width:auto;padding:0 16px" onclick="gmSearch()">Search</button>
        </div>
        <div class="gm-results" id="gmResults"></div>

        <div class="gm-actions">
            <button class="em-save-btn" id="gmSaveBtn" onclick="gmSave()">Save Group</button>
            <button class="gm-del-btn" id="gmDelBtn" style="display:none" onclick="gmDelete()">Delete</button>
        </div>
    </div>
</div>
"""

# 🔀 MIGRATE popup — group ki saari files doosre group me daal do.
GROUP_MIGRATE_HTML = """
<div class="edit-modal" id="grpMigModal" onclick="if(event.target===this)closeGrpMig()">
    <div class="em-card gm-card" style="max-width:540px">
        <button class="em-close" onclick="closeGrpMig()">&#10005;</button>
        <div class="em-title">&#128256; Migrate Group</div>
        <div class="gm-hint" id="grpMigHint">Is group ki saari files unke naye group me chali jayengi. Purana group delete ho jayega &mdash; files delete nahi hongi.</div>
        <div class="gm-mig-title" id="grpMigSrc"></div>
        <input type="text" id="grpMigQ" class="em-input" placeholder="Target group ka naam search karo&hellip;" oninput="grpMigFilter()">
        <div class="gm-results" id="grpMigList"></div>
    </div>
</div>
"""



GROUP_UI_JS = """<script>
/* 🗂️ GROUP ADMIN UI — dashboard + /groups page dono me same modal */
var GMOD = {gid:'', title:'', members:[], thumb:'', thumbFile:null, fileMap:{}, preview:'', verified:false};

function gmMode(){ return (typeof pMode !== 'undefined' && pMode) ? pMode : 'tg'; }
function gmEsc(s){ return String(s===undefined||s===null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];}); }
function gmPayload(){ return {gid:GMOD.gid||'', title:GMOD.title||'', members:GMOD.members.map(function(m){return {fid:m.fid,col:m.col};}), verified:!!GMOD.verified}; }

function gmMemberRow(m){
    return '<div class="gm-mrow">'+
        '<img class="gm-mthumb" src="'+gmEsc(m.thumb||'')+'" loading="lazy" onerror="this.style.visibility=\\'hidden\\'">'+
        '<div class="gm-mbody"><div class="gm-mname">'+gmEsc(m.name)+'</div>'+
        '<div class="gm-mmeta">'+gmEsc(m.ql||m.res||'FILE')+(m.size?' &middot; '+gmEsc(m.size):'')+' &middot; '+gmEsc(String(m.col||'primary').toUpperCase())+'</div></div>'+
        '<button class="gm-x" title="Remove" onclick="gmRemove(\\''+m.fid+'\\')">&#10005;</button></div>';
}
function gmFoundRow(f){
    var added = GMOD.members.some(function(m){return m.fid===f.fid;});
    var otherGroup = f.group && f.group!==GMOD.gid;
    return '<div class="gm-mrow">'+
        '<img class="gm-mthumb" src="'+gmEsc(f.thumb||'')+'" loading="lazy" onerror="this.style.visibility=\\'hidden\\'">'+
        '<div class="gm-mbody"><div class="gm-mname">'+gmEsc(f.name)+'</div>'+
        '<div class="gm-mmeta">'+gmEsc(f.ql||f.res||'FILE')+(f.size?' &middot; '+gmEsc(f.size):'')+(otherGroup?' &middot; kisi aur group me hai':'')+'</div></div>'+
        '<button class="gm-add" '+(added?'disabled':'')+' onclick="gmAdd(\\''+f.fid+'\\')">'+(added?'Added':'+ Add')+'</button></div>';
}

function gmRender(){
    document.getElementById('gmCount').textContent = GMOD.members.length;
    document.getElementById('gmMembers').innerHTML = GMOD.members.length
        ? GMOD.members.map(gmMemberRow).join('')
        : '<div class="gm-empty">Abhi koi file nahi hai &mdash; neeche se search karke add karo.</div>';
    document.getElementById('gmDelBtn').style.display = GMOD.gid ? '' : 'none';
    document.getElementById('gmHeading').innerHTML = GMOD.gid ? '&#128451; Edit Quality Group' : '&#128451; Create Quality Group';

    var preview = GMOD.preview || GMOD.thumb || (GMOD.members[0] && GMOD.members[0].thumb) || '';
    document.getElementById('gmThumb').innerHTML = preview
        ? '<img src="'+gmEsc(preview)+'" onerror="this.style.display=\\'none\\'">'
        : '<span class="gm-thumbph">&#127916;</span>';
}

function gmRenderResults(files){
    var box = document.getElementById('gmResults');
    if(!files || !files.length){ box.innerHTML=''; return; }
    box.innerHTML = files.map(gmFoundRow).join('');
}

function openGroupModal(fid, col, gid){
    GMOD = {gid:gid||'', title:'', members:[], thumb:'', thumbFile:null, fileMap:{}, preview:'', searchFiles:[], verified:false};
    var vBox = document.getElementById('gmVerified');
    if(vBox) vBox.checked = false;
    document.getElementById('gmTitle').value = '';
    document.getElementById('gmSearch').value = '';
    document.getElementById('gmResults').innerHTML = '';
    document.getElementById('gmMembers').innerHTML = '<div class="gm-empty">Loading&hellip;</div>';
    document.getElementById('gmThumb').innerHTML = '<span class="gm-thumbph">&#127916;</span>';
    document.getElementById('gmSaveBtn').disabled = false;
    document.getElementById('gmSaveBtn').textContent = 'Save Group';
    document.getElementById('groupModal').classList.add('open');

    var url = null;
    if(gid){ url = '/api/group/files?gid='+encodeURIComponent(gid)+'&mode='+encodeURIComponent(gmMode()); }
    else if(fid){ url = '/api/group/files?file_id='+encodeURIComponent(fid)+'&col='+encodeURIComponent(col||'primary')+'&mode='+encodeURIComponent(gmMode()); }
    if(!url){ gmRender(); return; }

    fetch(url).then(function(r){return r.json();}).then(function(d){
        if(d.error){ showToast(d.error,'error'); }
        var files = d.files || [];
        GMOD.searchFiles = files;
        files.forEach(function(f){ GMOD.fileMap[f.fid]=f; });

        if(d.group){
            GMOD.gid = d.group.gid;
            GMOD.title = d.group.title || '';
            GMOD.thumb = d.group.thumb || '';
            GMOD.verified = !!d.group.verified;
            var vBox2 = document.getElementById('gmVerified');
            if(vBox2) vBox2.checked = GMOD.verified;
            (d.group.members||[]).forEach(function(m){ GMOD.members.push(m); GMOD.fileMap[m.fid]=m; });
        } else {
            GMOD.title = d.title || '';
            /* ek hi title ki qualities pehle se select — sirf 1 click me group ban jaaye */
            files.forEach(function(f){
                if(f.same_key && !f.group && !GMOD.members.some(function(m){return m.fid===f.fid;})){ GMOD.members.push(f); }
            });
            if(d.seed && !GMOD.members.some(function(m){return m.fid===d.seed.fid;})){ GMOD.members.unshift(d.seed); }
        }
        document.getElementById('gmTitle').value = GMOD.title;
        gmRender();
        gmRenderResults(files);
    }).catch(function(){ showToast('Group data load nahi hua','error'); gmRender(); });
}

function closeGroupModal(){ document.getElementById('groupModal').classList.remove('open'); }

function gmAdd(fid){
    var f = GMOD.fileMap[fid];
    if(!f) return;
    if(GMOD.members.some(function(m){return m.fid===fid;})) return;
    GMOD.members.push({fid:f.fid, col:f.col, name:f.name, size:f.size, res:f.res, ql:f.ql, thumb:f.thumb});
    gmRender();
    gmRenderResults((GMOD.searchFiles||[]));
}

function gmRemove(fid){
    GMOD.members = GMOD.members.filter(function(m){return m.fid!==fid;});
    gmRender();
    gmRenderResults((GMOD.searchFiles||[]));
}

function gmPickThumb(input){
    if(!(input.files && input.files[0])) return;
    GMOD.thumbFile = input.files[0];
    var reader = new FileReader();
    reader.onload = function(e){ GMOD.preview = e.target.result; gmRender(); };
    reader.readAsDataURL(input.files[0]);
}

function gmSearch(){
    var q = document.getElementById('gmSearch').value.trim();
    if(!q){ showToast('File ka naam likho','error'); return; }
    var box = document.getElementById('gmResults');
    box.innerHTML = '<div class="gm-empty">Searching&hellip;</div>';
    fetch('/api/group/files?q='+encodeURIComponent(q)+'&mode='+encodeURIComponent(gmMode()))
        .then(function(r){return r.json();}).then(function(d){
            if(d.error){ showToast(d.error,'error'); box.innerHTML=''; return; }
            var files = d.files || [];
            files.forEach(function(f){ GMOD.fileMap[f.fid]=f; });
            GMOD.searchFiles = files;
            gmRenderResults(files);
            if(!files.length){ box.innerHTML='<div class="gm-empty">Koi file nahi mili.</div>'; }
        }).catch(function(){ box.innerHTML='<div class="gm-empty">Search failed.</div>'; });
}

function gmUploadThumb(gid, file){
    var fd = new FormData();
    fd.append('group_id', gid);
    fd.append('image', file);
    return fetch('/api/group/thumb',{method:'POST',body:fd}).then(function(r){return r.json();});
}

function gmSave(){
    var title = document.getElementById('gmTitle').value.trim();
    if(!title){ showToast('Group ka naam likho','error'); return; }
    var vBox = document.getElementById('gmVerified');
    GMOD.verified = !!(vBox && vBox.checked);
    if(!GMOD.members.length && !GMOD.gid && !confirm('Group me koi file nahi hai. Khali group bana dein?')) return;

    var btn = document.getElementById('gmSaveBtn');
    btn.disabled = true; btn.textContent = 'Saving...';

    fetch('/api/group/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(gmPayload())})
        .then(function(r){return r.json();}).then(function(d){
            if(!d.success){ showToast(d.error||'Save failed','error'); btn.disabled=false; btn.textContent='Save Group'; return; }
            var gid = d.group.gid;
            GMOD.gid = gid;
            var after = function(){
                showToast('\\u2705 Group saved');
                closeGroupModal();
                if(typeof gmPageReload === 'function'){ gmPageReload(); } else { refreshGridAfterEdit(); }
            };
            if(GMOD.thumbFile){
                gmUploadThumb(gid, GMOD.thumbFile).then(function(u){
                    if(u && u.success===false) showToast(u.error||'Thumbnail upload failed','error');
                    after();
                }).catch(function(){ showToast('Thumbnail upload failed','error'); after(); });
            } else { after(); }
        }).catch(function(){
            showToast('Network error','error'); btn.disabled=false; btn.textContent='Save Group';
        });
}

function gmDelete(){
    if(!GMOD.gid) return;
    if(!confirm('Ye group delete kar dein? Files delete nahi hongi, sirf grouping hat jayegi.')) return;
    fetch('/api/group/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({gid:GMOD.gid})})
        .then(function(r){return r.json();}).then(function(d){
            if(!d.success){ showToast(d.error||'Delete failed','error'); return; }
            showToast('\\u2705 Group deleted');
            closeGroupModal();
            if(typeof gmPageReload === 'function'){ gmPageReload(); } else { refreshGridAfterEdit(); }
        }).catch(function(){ showToast('Network error','error'); });
}

/* ── 🗂️ Group card ke thumbnail popup ke actions ──
   Sab actions card ke `key` se chalte hain (GRP_DATA map dashboard JS bharta hai),
   taaki auto (bina-save) group bhi manage/verify/migrate ho sake. */
function grpCard(k){ return (typeof GRP_DATA !== 'undefined' && GRP_DATA[k]) ? GRP_DATA[k] : null; }
function grpMembers(g){ return (g.variants||[]).map(function(v){return {fid:v.file_id, col:v.raw_collection||'primary'};}); }

function grpManage(k){
    var g = grpCard(k);
    if(!g) return;
    if(g.gid){ openGroupModal(null, null, g.gid); return; }
    var m = (g.variants||[])[0];
    if(m) openGroupModal(m.file_id, m.raw_collection||'primary');
}

/* ✅ Verify: DB group ho to flag toggle, auto group ho to pehle save karke verify */
function grpVerify(k){
    var g = grpCard(k);
    if(!g) return;
    if(g.verified){
        fetch('/api/group/verify',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({gid:g.gid,verified:false})})
            .then(function(r){return r.json();}).then(function(d){
                if(!d.success){ showToast(d.error||'Verify failed','error'); return; }
                showToast('Group unverified');
                grpAfterChange();
            }).catch(function(){ showToast('Network error','error'); });
        return;
    }
    if(g.gid){
        fetch('/api/group/verify',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({gid:g.gid,verified:true})})
            .then(function(r){return r.json();}).then(function(d){
                if(!d.success){ showToast(d.error||'Verify failed','error'); return; }
                showToast('\u2705 Group verified');
                grpAfterChange();
            }).catch(function(){ showToast('Network error','error'); });
        return;
    }
    /* auto group — save karte waqt hi verified mark */
    var body = {gid:'', title:g.raw_title||g.title||'', members:grpMembers(g), verified:true};
    fetch('/api/group/save',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})
        .then(function(r){return r.json();}).then(function(d){
            if(!d.success){ showToast(d.error||'Verify failed','error'); return; }
            showToast('\u2705 Group verified');
            grpAfterChange();
        }).catch(function(){ showToast('Network error','error'); });
}

/* 🔀 Migrate: is group (ya auto group) ki saari files kisi doosre group me merge */
function grpMigrate(k){
    var g = grpCard(k);
    if(!g) return;
    openMigrateModal(g.gid||'', grpMembers(g), g.raw_title||g.title||'');
}

function grpDeleteGroup(k){
    var g = grpCard(k);
    if(!g || !g.gid) return;
    if(!confirm('Ye group delete kar dein? Files delete nahi hongi, sirf grouping hat jayegi.')) return;
    fetch('/api/group/delete',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({gid:g.gid})})
        .then(function(r){return r.json();}).then(function(d){
            if(!d.success){ showToast(d.error||'Delete failed','error'); return; }
            showToast('\u2705 Group deleted');
            grpAfterChange();
        }).catch(function(){ showToast('Network error','error'); });
}

function grpAfterChange(){
    if(typeof gmPageReload === 'function'){ gmPageReload(); return; }
    if(typeof refreshGridAfterEdit === 'function'){ refreshGridAfterEdit(); }
}

/* 🔀 Migrate: is group ki saari files kisi doosre group me merge (ID add) */
var GMIG = {gid:'', groups:[], members:[], title:''};

function openMigrateModal(gid, members, title){
    GMIG = {gid:gid||'', groups:[], members:members||[], title:title||''};
    var el = document.getElementById('grpMigModal');
    if(!el) return;
    if(!GMIG.gid && !GMIG.members.length) return;
    document.getElementById('grpMigQ').value = '';
    document.getElementById('grpMigSrc').textContent = GMIG.title
        ? 'Source: '+GMIG.title+(GMIG.members.length?' ('+GMIG.members.length+' files)':'')
        : '';
    document.getElementById('grpMigList').innerHTML = '<div class="gm-empty">Loading&hellip;</div>';
    el.classList.add('open');
    fetch('/api/groups').then(function(r){return r.json();}).then(function(d){
        GMIG.groups = (d.groups||[]).filter(function(g){return !GMIG.gid || g.gid!==GMIG.gid;});
        if(GMIG.gid && !GMIG.title){
            var src = (d.groups||[]).filter(function(g){return g.gid===GMIG.gid;})[0];
            if(src){ document.getElementById('grpMigSrc').textContent = 'Source: '+src.title+' ('+src.count+' files)'; }
        }
        grpMigFilter();
    }).catch(function(){
        document.getElementById('grpMigList').innerHTML = '<div class="gm-empty">Groups load nahi hue.</div>';
    });
}

function closeGrpMig(){
    var el = document.getElementById('grpMigModal');
    if(el) el.classList.remove('open');
}

function grpMigFilter(){
    var q = (document.getElementById('grpMigQ').value||'').toLowerCase();
    var list = GMIG.groups.filter(function(g){
        return !q || String(g.title||'').toLowerCase().indexOf(q) >= 0;
    });
    var box = document.getElementById('grpMigList');
    if(!list.length){ box.innerHTML = '<div class="gm-empty">Koi doosra group nahi mila.</div>'; return; }
    box.innerHTML = list.map(function(g){
        var vchip = g.verified ? ' &#10003;' : '';
        return '<div class="gm-mrow gm-migrow" onclick="grpMigDo(\\''+g.gid+'\\')">'+
            '<img class="gm-mthumb" src="'+gmEsc(g.thumb||'')+'" loading="lazy" onerror="this.style.visibility=\\'hidden\\'">'+
            '<div class="gm-mbody"><div class="gm-mname">'+gmEsc(g.title)+vchip+'</div>'+
            '<div class="gm-mmeta">'+g.count+' files &middot; #'+gmEsc(String(g.gid||'').slice(-6))+'</div></div>'+
            '<button class="gm-add">&#128256; Merge</button></div>';
    }).join('');
}

function grpMigDo(target){
    if(!target || (!GMIG.gid && !GMIG.members.length)) return;
    var body = {gid:GMIG.gid||'', target:target, members:GMIG.members||[]};
    fetch('/api/group/migrate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)})
        .then(function(r){return r.json();}).then(function(d){
            if(!d.success){ showToast(d.error||'Migrate failed','error'); return; }
            showToast('\u2705 Group migrated');
            closeGrpMig();
            grpAfterChange();
        }).catch(function(){ showToast('Network error','error'); });
}
</script>"""
