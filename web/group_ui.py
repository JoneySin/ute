"""🗂️ GROUP ADMIN UI (shared assets)

Dashboard (file card par 🗂 button) aur `/groups` page — dono ek hi modal + JS
use karte hain, isliye grouping ka UI kahin duplicate nahi hai.

Modal ek hi jagah se teeno kaam karta hai:
  • naya group banana (naam + thumbnail),
  • maujooda group ka naam/thumbnail badalna,
  • alag-alag naam wali files ko search karke group me jodna / nikaalna.
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
</style>"""


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


GROUP_UI_JS = """<script>
/* 🗂️ GROUP ADMIN UI — dashboard + /groups page dono me same modal */
var GMOD = {gid:'', title:'', members:[], thumb:'', thumbFile:null, fileMap:{}, preview:''};

function gmMode(){ return (typeof pMode !== 'undefined' && pMode) ? pMode : 'tg'; }
function gmEsc(s){ return String(s===undefined||s===null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];}); }
function gmPayload(){ return {gid:GMOD.gid||'', title:GMOD.title||'', members:GMOD.members.map(function(m){return {fid:m.fid,col:m.col};})}; }

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
    GMOD = {gid:gid||'', title:'', members:[], thumb:'', thumbFile:null, fileMap:{}, preview:'', searchFiles:[]};
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
</script>"""
