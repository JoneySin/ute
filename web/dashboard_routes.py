import time
from aiohttp import web
from web.web_assets import build_page, get_auth, form_wrapper, MAX_WEB_RESULTS, require_active_plan, DEFAULT_MEDIA_MODE
from utils import temp
from database.users_chats_db import web_db
# 🗂️ Admin group modal (dashboard file cards ke 🗂 button se khulta hai)
from web.group_ui import GROUP_UI_CSS, GROUP_MODAL_HTML, GROUP_MIGRATE_HTML, GROUP_UI_JS

dashboard_routes = web.RouteTableDef()

# ─────────────────────────────────────────────────────────────────────────────
# 🎨 DASHBOARD SPECIFIC CSS (सिर्फ सर्च बार और ड्रॉपडाउन के लिए, कार्ड्स ग्लोबल हैं)
# ─────────────────────────────────────────────────────────────────────────────
CARD_CSS = """
<style>
/* ── Search zone ── */
.search-zone{padding:16px 20px 0;max-width:1400px;margin:0 auto}
.search-row1{display:flex;align-items:center;gap:10px;margin-bottom:10px}
.search-row2{display:flex;align-items:center;justify-content:center;gap:10px;margin-bottom:16px}
@media(min-width:768px){
  .search-zone{padding:24px 24px 10px;display:flex;align-items:center;justify-content:center;gap:14px;flex-wrap:nowrap}
  .search-row1{flex:1;max-width:650px;margin-bottom:0}
  .search-row2{margin-bottom:0;justify-content:flex-start;flex-shrink:0}
}

.search-wrap{flex:1;min-width:0;display:flex;align-items:center;background:var(--bg3);border:1.5px solid var(--border);border-radius:12px;padding:0 6px 0 18px;gap:8px;overflow:hidden;min-height:38px;transition:border-color .18s}
.search-wrap:focus-within{border-color:var(--border)}
.search-spinner{display:none;width:15px;height:15px;flex-shrink:0;border:2px solid var(--border);border-top-color:var(--accent);border-radius:50%;animation:searchSpin .6s linear infinite}
.search-wrap.loading .search-spinner{display:inline-block}
@keyframes searchSpin{to{transform:rotate(360deg)}}
.search-input{flex:1;min-width:0;width:100%;background:transparent;border:none;outline:none;color:var(--text);caret-color:var(--accent);font-size:14px;font-weight:600;padding:6px 0;font-family:inherit;-webkit-tap-highlight-color:transparent}
.search-input::placeholder{color:var(--muted);font-weight:400}
.search-input:-webkit-autofill,
.search-input:-webkit-autofill:hover,
.search-input:-webkit-autofill:focus,
.search-input:-webkit-autofill:active{
  -webkit-box-shadow:0 0 0 100px var(--bg3) inset !important;
  box-shadow:0 0 0 100px var(--bg3) inset !important;
  -webkit-text-fill-color:var(--text) !important;
  caret-color:var(--accent) !important;
  border-radius:999px;
  transition:background-color 9999s ease-in-out 0s;
}
.search-btn{position:relative;overflow:hidden;flex-shrink:0;background:var(--accent);color:#fff;border:none;border-radius:12px;padding:0 20px;height:38px;font-size:14px;font-weight:700;cursor:pointer;white-space:nowrap;transition:transform .15s,box-shadow .15s,background .15s;letter-spacing:.3px}
.search-btn:hover{background:var(--accent-hover);transform:scale(1.03);box-shadow:0 6px 22px rgba(229,9,20,0.50)}
.search-btn:active{transform:scale(.96)}
/* ripple */
.search-btn::after{content:'';position:absolute;inset:0;background:rgba(255,255,255,0);border-radius:inherit;pointer-events:none}
.search-btn.ripple-go::after{animation:btnRipple .45s ease-out forwards}
@keyframes btnRipple{0%{background:rgba(255,255,255,0.28);transform:scale(.6)}100%{background:rgba(255,255,255,0);transform:scale(1.6)}}

/* ── Custom dropdown ── */
.cdd-wrap{flex:0 1 auto;min-width:0;position:relative;user-select:none}
.cdd-btn{width:170px;background:var(--bg3);color:var(--text);border:1.5px solid var(--border);border-radius:999px;padding:8px 28px 8px 14px;font-size:11px;font-weight:700;cursor:pointer;font-family:inherit;box-sizing:border-box;display:inline-flex;align-items:center;justify-content:flex-start;gap:5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;transition:border-color .15s,box-shadow .15s}
.cdd-btn:hover,.cdd-btn.open{border-color:var(--accent);box-shadow:0 0 0 3px rgba(229,9,20,0.12)}
.cdd-arrow{position:absolute;right:12px;top:50%;transform:translateY(-50%);pointer-events:none;font-size:9px;color:var(--muted);transition:transform .2s}
.cdd-btn.open+.cdd-arrow{transform:translateY(-50%) rotate(180deg)}

.cdd-menu{position:absolute;top:calc(100% + 7px);left:50%;transform:translateX(-50%);min-width:max-content;background:var(--bg2,var(--bg3));border:1.5px solid var(--border);border-radius:16px;overflow:hidden;z-index:9999;box-shadow:0 8px 32px rgba(0,0,0,.45);animation:cddIn .15s ease}
@keyframes cddIn{
    from{opacity:0;transform:translate(-50%, -6px)}
    to{opacity:1;transform:translate(-50%, 0)}
}

.cdd-item{display:flex;align-items:center;gap:10px;padding:13px 14px;font-size:13px;font-weight:700;color:var(--text);cursor:pointer;transition:background .12s;border-bottom:1px solid var(--border)}
.cdd-item:last-child{border-bottom:none}
.cdd-item:hover{background:var(--bg3)}
.cdd-item.selected{color:var(--accent)}
.cdd-radio{width:18px;height:18px;border-radius:50%;border:2px solid var(--border);margin-left:auto;flex-shrink:0;display:flex;align-items:center;justify-content:center;transition:border-color .15s}
.cdd-item.selected .cdd-radio{border-color:var(--accent)}
.cdd-radio-dot{width:8px;height:8px;border-radius:50%;background:var(--accent);display:none}
.cdd-item.selected .cdd-radio-dot{display:block}
/* ── Quality group card ──
   Group ka master thumbnail bilkul normal file card jaisa BADA dikhta hai; bas
   thumbnail ke andar neeche "3 Qualities" + quality labels ka bar hota hai. */
.file-card.grp-card{cursor:default}
.grp-card.open{grid-column:1/-1;border-color:var(--accent);box-shadow:0 8px 28px rgba(0,0,0,.45)}
.grp-poster-box{cursor:pointer}
.grp-manual-chip{background:rgba(229,9,20,.16);color:#ff8a8a;border:1px solid rgba(229,9,20,.45);border-radius:5px;padding:3px 7px;font-size:9px;font-weight:800;letter-spacing:.6px;line-height:1.4}
/* 👇 thumbnail ke ANDAR, neeche quality count */
.grp-qbar{position:absolute;left:0;right:0;bottom:0;display:flex;align-items:center;gap:6px;padding:24px 9px 9px;background:linear-gradient(to top,rgba(0,0,0,.94),rgba(0,0,0,0));z-index:3;pointer-events:none}
.grp-qcount{display:inline-flex;align-items:center;gap:5px;background:var(--accent);color:#fff;border:1px solid rgba(255,255,255,.25);border-radius:6px;padding:3px 9px;font-size:10.5px;font-weight:900;letter-spacing:.4px;white-space:nowrap;box-shadow:0 2px 10px rgba(0,0,0,.45)}
.grp-qlabels{display:flex;gap:4px;overflow:hidden;flex-wrap:nowrap;min-width:0}
.grp-qlabel{background:rgba(0,0,0,.66);color:#ffd166;border:1px solid rgba(255,209,102,.35);border-radius:5px;padding:2px 6px;font-size:9.5px;font-weight:800;white-space:nowrap}
.grp-caret{margin-left:auto;flex-shrink:0;width:19px;height:19px;border-radius:50%;background:rgba(0,0,0,.62);border:1px solid rgba(255,255,255,.22);color:#fff;font-size:9px;display:flex;align-items:center;justify-content:center;transition:transform .2s}
.grp-name{display:flex;align-items:center;gap:6px;cursor:pointer}
.grp-name .grp-caret{margin-left:auto}
.grp-card.open .grp-caret{transform:rotate(180deg)}
/* 📸 Thumbnail tap par admin action row (Manage / Migrate / Delete) khulti hai —
   tab quality bar chhup jaati hai taaki buttons saaf dikhein. */
.grp-card.admin-active .grp-qbar{opacity:0;transition:opacity .15s}
.grp-card .poster-admin .btn-grp{background:rgba(120,90,10,.88)}
.grp-variants{display:none;border-top:1px solid var(--border);background:var(--bg2)}
.grp-card.open .grp-variants{display:grid;grid-template-columns:1fr;gap:8px;padding:10px}
@media(min-width:600px){.grp-card.open .grp-variants{grid-template-columns:repeat(3,1fr)}}
.grp-variants .file-card:hover{transform:none;box-shadow:none;border-color:var(--border)}
.grp-text-info{cursor:pointer}
.grp-text-count{font-size:11px;font-weight:800;color:#ffd166}
.grp-caret-text{margin-left:auto;color:var(--muted);font-size:11px}
.grp-card.open .grp-caret-text{color:var(--accent)}
/* 🗂 admin group button (Edit / Delete ke saath) */
.btn-grp{flex:1;padding:6px 0;border-radius:6px;font-size:11px;font-weight:700;cursor:pointer;border:1px solid rgba(255,209,102,.35);background:rgba(120,90,10,.72);backdrop-filter:blur(10px);color:#ffd166;transition:background .12s}
.btn-grp:hover{background:rgba(180,135,20,.9)}
</style>
"""

# ─────────────────────────────────────────────────────────────────────────────
# 🎬 JS ENGINE — Smart Double Pre-fetching Engine Live Live
# ─────────────────────────────────────────────────────────────────────────────
JS_ENGINE = """
var curQ='',curOff=0,nextOff='',curCol='all',curPage=1;
var searchReqId=0;
// Dashboard mode has its own preference key so an old shared posterMode value
// cannot override the text-only dashboard default.
var pMode=localStorage.getItem('ff_dashboard_mode')||'__DEFAULT_MEDIA_MODE__';
var LIMIT_VAL = __LIMIT_PLACEHOLDER__;

function closeCdds(){
    document.getElementById('cddColMenu').style.display='none';
    document.getElementById('cddColBtn').classList.remove('open');
    document.getElementById('cddModeMenu').style.display='none';
    document.getElementById('cddModeBtn').classList.remove('open');
}
function toggleCdd(which,e){
    if(e){e.stopPropagation();}
    var menuId=which==='col'?'cddColMenu':'cddModeMenu';
    var btnId=which==='col'?'cddColBtn':'cddModeBtn';
    var otherId=which==='col'?'cddModeMenu':'cddColMenu';
    var otherBtnId=which==='col'?'cddModeBtn':'cddColBtn';
    var menu=document.getElementById(menuId);
    var btn=document.getElementById(btnId);
    var isOpen=menu.style.display!=='none';
    document.getElementById(otherId).style.display='none';
    document.getElementById(otherBtnId).classList.remove('open');
    if(isOpen){menu.style.display='none';btn.classList.remove('open');}
    else{menu.style.display='block';btn.classList.add('open');}
}
function pickCol(val,label,el,e){
    if(e){e.stopPropagation();}
    curCol=val;
    document.getElementById('cddColLabel').textContent=label;
    document.querySelectorAll('#cddColMenu .cdd-item').forEach(function(i){i.classList.remove('selected');});
    el.classList.add('selected');
    document.getElementById('cddColMenu').style.display='none';
    document.getElementById('cddColBtn').classList.remove('open');
    doSearch(0,true);
}
function pickMode(val,label,el,e){
    if(e){e.stopPropagation();}
    pMode=val;
    localStorage.setItem('ff_dashboard_mode',pMode);
    document.getElementById('cddModeLabel').textContent=label;
    document.querySelectorAll('#cddModeMenu .cdd-item').forEach(function(i){i.classList.remove('selected');});
    el.classList.add('selected');
    document.getElementById('cddModeMenu').style.display='none';
    document.getElementById('cddModeBtn').classList.remove('open');
    doSearch(curOff,true);
}
document.addEventListener('click',function(e){
    if(!e.target.closest('.cdd-wrap')){closeCdds();}
});
document.querySelectorAll('.cdd-menu').forEach(function(m){
    m.addEventListener('click',function(e){e.stopPropagation();});
});
function changeCol(val){curCol=val;doSearch(0,true);}

/* ✅ DUPLICATE REMOVED: handleThumbError() यहाँ दोबारा defined था, जबकि
   web_assets.py के global JS में यह पहले से है (और वहाँ वाला version बेहतर है —
   पूरा poster-box overlay करता है, सिर्फ़ छोटा span नहीं)। build_page() global JS
   <head> में डालता है और यह script <body> में बाद में आता है, इसलिए यही कमज़ोर
   copy global वाली को shadow कर रही थी — यानी dashboard पर thumbnail-fail हमेशा
   घटिया दिखता था। अब सिर्फ़ global version चलता है। */

function triggerRipple(btn){btn.classList.remove('ripple-go');void btn.offsetWidth;btn.classList.add('ripple-go');setTimeout(function(){btn.classList.remove('ripple-go');},460);}

var isAdminView=false;
var openGroups={};
/* 📄 Grouped pages ke offsets barabar nahi hote (group boundary par cut hote hain),
   isliye Previous ke liye offset-stack rakhna padta hai. */
var offStack=[0];
/* Manual group ke saare members uske card me hi hote hain, isliye agle page par
   wahi group dobara na dikhe (members door-door hone par duplicate card aata tha). */
var shownManual={};

/* 📄 Ek file ka card (pehle doSearch ke andar forEach me tha — bina badle yahan aa gaya).
   nested=true: group ke andar wala variant card (card-enter animation nahi). */
function cardHtml(f,nested){
            var sc=(f.source||'primary').toLowerCase();
            if(!['primary','cloud','archive'].includes(sc))sc='primary';

            var encName = encodeURIComponent(f.name || '').replace(/'/g, "%27").replace(/"/g, "%22");
            var encCap = encodeURIComponent(f.caption || '').replace(/'/g, "%27").replace(/"/g, "%22");

            var adminBtns='';
            if(isAdminView){
                adminBtns='<div class="poster-admin">'+
                    '<button class="btn-edit" onclick="event.stopPropagation();editFile(\\''+f.file_id+'\\',\\''+f.raw_collection+'\\',\\''+encName+'\\', \\''+encCap+'\\')">&#9999; Edit</button>'+
                    '<button class="btn-grp" onclick="event.stopPropagation();openGroupModal(\\''+f.file_id+'\\',\\''+f.raw_collection+'\\')">&#128451; Group</button>'+
                    '<button class="btn-del" onclick="event.stopPropagation();deleteFile(\\''+f.file_id+'\\',\\''+f.raw_collection+'\\')">&#128465; Delete</button>'+
                '</div>';
            }

            /* ⏱️ Duration chip — sirf tab jab API ne asli duration bheja ho.
               Purani (bina-duration index huyi) files par f.duration khali aata hai,
               tab chip banta hi nahi — "0:00" jaisa bekaar text nahi dikhta. */
            var durChip  = f.duration ? '<span class="dur-chip">'+f.duration+'</span>' : '';
            var durText  = f.duration ? '<span class="tc-dur">'+f.duration+'</span>' : '';
            /* 🖼️ Resolution chip (1280×720 → "720p", 1920×1080 → "1080p") — duration chip
               jaisa hi null-tolerant: data na ho to chip banta hi nahi. */
            var resChip  = f.res ? '<span class="res-chip">'+f.res+'</span>' : '';
            var resText  = f.res ? '<span class="tc-res">'+f.res+'</span>' : '';

            var posterHtml='';
            if(pMode!=='none'){
                posterHtml='<div class="poster-box" id="poster-box-'+f.file_id+'" onclick="toggleAdminBtns(this.closest(\\'.file-card\\'),event)">'+
                    '<img src="'+f.tg_thumb+'" id="img-poster-'+f.file_id+'" class="fc-poster" onload="this.classList.add(\\'loaded\\')" onerror="handleThumbError(\\''+f.file_id+'\\')" loading="lazy" decoding="async">'+
                    '<div class="poster-top">'+
                        '<span class="type-chip">'+f.type.toUpperCase()+'</span>'+
                        '<span class="size-chip">'+f.size+'</span>'+
                        durChip+resChip+
                        '<span class="source-pill '+sc+'"><span class="source-dot"></span>'+sc.toUpperCase()+'</span>'+
                    '</div>'+
                    adminBtns+
                '</div>';
            }

            var textInfo='';
            if(pMode==='none'){
                textInfo='<div class="fc-text-info" onclick="toggleAdminBtns(this.closest(\\'.file-card\\'),event)">'+
                    '<span class="tc-type">'+f.type.toUpperCase()+'</span>'+
                    '<span class="tc-size">'+f.size+'</span>'+
                    durText+resText+
                    '<span class="source-pill '+sc+'" style="margin-left:auto"><span class="source-dot"></span>'+sc.toUpperCase()+'</span>'+
                '</div>';
                if(isAdminView){
                    textInfo+='<div class="text-admin-row">'+
                        '<button class="btn-edit" onclick="event.stopPropagation();editFile(\\''+f.file_id+'\\',\\''+f.raw_collection+'\\',\\''+encName+'\\', \\''+encCap+'\\')">&#9999; Edit</button>'+
                        '<button class="btn-grp" onclick="event.stopPropagation();openGroupModal(\\''+f.file_id+'\\',\\''+f.raw_collection+'\\')">&#128451; Group</button>'+
                        '<button class="btn-del" onclick="event.stopPropagation();deleteFile(\\''+f.file_id+'\\',\\''+f.raw_collection+'\\')">&#128465; Delete</button>'+
                    '</div>';
                }
            }

            return '<div class="file-card'+(nested?'':' card-enter')+'">'+
                posterHtml+
                textInfo+
                '<div class="fc-body">'+
                    '<div class="fc-name" id="name-title-'+f.file_id+'" onclick="window.open(\\''+f.watch+'\\',\\'_blank\\')">'+f.name+'</div>'+
                '</div>'+
            '</div>';
}

/* 🗂️ Ek title ki alag-alag quality ka group card.
   • Naam par click → group khulta hai aur uski saari files dikh jaati hain.
   • Thumbnail par click → admin ke liye action row (Manage / Migrate / Delete),
     bilkul waise hi jaise file card me Edit/Delete ka popup aata hai.
   • Quality count + labels thumbnail ke ANDAR, neeche.
   Naam ke neeche koi extra text/button nahi hota. */
function groupHtml(g){
    var open=openGroups[g.key]?' open':'';
    var vlist=g.variants||[];
    var labels=(g.labels||[]).map(function(l){return '<span class="grp-qlabel">'+l+'</span>';}).join('');
    var labelsText=(g.labels||[]).join(' · ');
    var qWord=(g.count===1?'Quality':'Qualities');
    var master=vlist[0]||{};

    /* admin action row — thumbnail ke neeche wali patti (tap par khulti hai) */
    var adminBtns='';
    if(isAdminView && g.manual && g.gid){
        adminBtns='<div class="poster-admin">'+
            '<button class="btn-edit" onclick="event.stopPropagation();grpManage(\\''+g.gid+'\\')">&#128451; Manage</button>'+
            '<button class="btn-grp" onclick="event.stopPropagation();grpMigrate(\\''+g.gid+'\\')">&#128256; Migrate</button>'+
            '<button class="btn-del" onclick="event.stopPropagation();grpDeleteGroup(\\''+g.gid+'\\')">&#128465; Delete</button>'+
        '</div>';
    } else if(isAdminView && master.file_id){
        /* auto group: pehle manage karke DB group banao */
        adminBtns='<div class="poster-admin">'+
            '<button class="btn-edit" onclick="event.stopPropagation();openGroupModal(\\''+master.file_id+'\\',\\''+(master.raw_collection||'primary')+'\\')">&#128451; Manage</button>'+
        '</div>';
    }
    var tapFn=adminBtns?"toggleAdminBtns(this.closest('.grp-card'),event)":"toggleGroup(this.closest('.grp-card'),event)";

    var poster='';
    if(pMode!=='none'){
        var thumb=g.tg_thumb||master.tg_thumb||'';
        poster='<div class="poster-box grp-poster-box" onclick="'+tapFn+'">'+
            '<img src="'+thumb+'" class="fc-poster" onload="this.classList.add(\\'loaded\\')" onerror="this.style.opacity=0" loading="lazy" decoding="async">'+
            '<div class="poster-top">'+
                '<span class="type-chip">'+String(g.type||'VIDEO').toUpperCase()+'</span>'+
                '<span class="size-chip">'+g.count+' FILES</span>'+
                (g.manual?'<span class="grp-manual-chip">MANUAL</span>':'')+
            '</div>'+
            '<div class="grp-qbar">'+
                '<span class="grp-qcount">&#127916; '+g.count+' '+qWord+'</span>'+
                '<span class="grp-qlabels">'+labels+'</span>'+
            '</div>'+
            adminBtns+
        '</div>';
    } else {
        poster='<div class="fc-text-info grp-text-info" onclick="'+tapFn+'">'+
            '<span class="tc-type">'+String(g.type||'VIDEO').toUpperCase()+'</span>'+
            '<span class="grp-text-count">&#127916; '+g.count+' '+qWord+'</span>'+
            '<span class="tc-res">'+labelsText+'</span>'+
        '</div>';
        if(adminBtns){ poster+=adminBtns.replace('poster-admin','text-admin-row'); }
    }

    var inner='';
    vlist.forEach(function(v){inner+=cardHtml(v,true);});
    return '<div class="file-card grp-card card-enter'+open+'" data-gk="'+g.key+'">'+
        poster+
        '<div class="fc-body">'+
            '<div class="fc-name grp-name" onclick="toggleGroup(this.closest(\\'.grp-card\\'),event)" title="Saari files dekhne ke liye naam par click karein">'+
                '<span class="grp-name-text">'+g.title+'</span>'+
                '<span class="grp-caret">&#9662;</span>'+
            '</div>'+
        '</div>'+
        '<div class="grp-variants">'+inner+'</div>'+
    '</div>';
}
function toggleGroup(el){
    var k=el.getAttribute('data-gk');
    var isOpen=el.classList.toggle('open');
    if(isOpen){openGroups[k]=1;}else{delete openGroups[k];}
}

async function doSearch(o,allowEmpty){
    var q=document.getElementById('q').value.trim();
    if(!q && !allowEmpty){showToast('Please enter a movie name','error');return;}
    curQ=q;curOff=o;if(o===0){curPage=1;offStack=[0];}
    if(q){sessionStorage.setItem('ff_dash_q',q);}else{sessionStorage.removeItem('ff_dash_q');}

    var myReq=++searchReqId;
    var resDiv=document.getElementById('results');
    var qWrap=document.getElementById('qWrap');
    var loadTimer=setTimeout(function(){
        if(myReq!==searchReqId)return;
        if(qWrap)qWrap.classList.add('loading');
    },150);

    try{
        var r=await fetch('/api/search?q='+encodeURIComponent(q)+'&offset='+o+'&col='+curCol+'&mode='+pMode+'&group=1');
        if(myReq!==searchReqId){clearTimeout(loadTimer);if(qWrap)qWrap.classList.remove('loading');return;}
        clearTimeout(loadTimer);
        if(qWrap)qWrap.classList.remove('loading');
        var d=null;
        try{d=await r.json();}catch(parseErr){d=null;}
        if(myReq!==searchReqId)return;
        if(!r.ok || (d && d.error)){
            var msg=(d && d.error)?d.error:('Error fetching (HTTP '+r.status+')');
            showToast(msg,'error');
            if(!allowEmpty || q){
                resDiv.innerHTML='<div class="empty"><div class="empty-icon">&#9888;</div><p>'+msg+'</p></div>';
                document.getElementById('pageBox').style.display='none';
            }
            return;
        }
        document.getElementById('resInfo').style.display='none';
        if(!d.results||!d.results.length){
            resDiv.innerHTML = q
                ? '<div class="empty"><div class="empty-icon">&#9888;</div><p>No titles found for "'+q+'"</p></div>'
                : '<div class="empty"><div class="empty-icon">&#8981;</div><p>No files added yet.</p></div>';
            document.getElementById('pageBox').style.display='none';return;
        }
        var h='';
        isAdminView=!!d.is_admin;
        if(o===0)shownManual={};
        d.results.forEach(function(f){
            if(f.group && f.manual && f.gid){
                if(shownManual[f.gid])return;
                shownManual[f.gid]=1;
            }
            h+=f.group?groupHtml(f):cardHtml(f,false);
        });
        if(!h){ /* poora page duplicate groups ka nikla — phir bhi dikhana zaroori hai */
            d.results.forEach(function(f){
                h+=f.group?groupHtml(f):cardHtml(f,false);
            });
        }
        resDiv.className='res-grid mode-'+pMode;
        resDiv.innerHTML=h;
        staggerCards(resDiv);
        nextOff=d.next_offset;
        document.getElementById('pageBox').style.display='flex';
        document.getElementById('pBtn').disabled=(o===0);
        document.getElementById('nBtn').disabled=!nextOff;
        document.getElementById('pgInfo').textContent='Page '+curPage;

        if(nextOff) {
            fetch('/api/search?q='+encodeURIComponent(q)+'&offset='+nextOff+'&col='+curCol+'&mode='+pMode);
        }
    }catch(e){clearTimeout(loadTimer);if(qWrap)qWrap.classList.remove('loading');showToast('Network error','error');}
}

function next(){if(nextOff){if(offStack[offStack.length-1]!==nextOff)offStack.push(nextOff);curPage=offStack.length;doSearch(nextOff);scrollTo(0,0);}}
function prev(){if(offStack.length>1){offStack.pop();curPage=offStack.length;doSearch(offStack[offStack.length-1]);scrollTo(0,0);}}

document.addEventListener('DOMContentLoaded',function(){
    var q=document.getElementById('q');
    if(q){
        var qLiveTimer;
        q.addEventListener('input',function(){
            clearTimeout(qLiveTimer);
            var val=q.value.trim();
            if(val.length<2){
                searchReqId++;
                curQ='';
                var qw=document.getElementById('qWrap');if(qw)qw.classList.remove('loading');
                var ri=document.getElementById('resInfo');if(ri)ri.style.display='none';
                var pb=document.getElementById('pageBox');if(pb)pb.style.display='none';
                doSearch(0,true);
                return;
            }
            qLiveTimer=setTimeout(function(){doSearch(0);},350);
        });
        q.addEventListener('keydown',function(e){if(e.key==='Enter'){clearTimeout(qLiveTimer);doSearch(0);}});
    }
    var mItems=document.querySelectorAll('#cddModeMenu .cdd-item');
    mItems.forEach(function(i){i.classList.remove('selected');if(i.dataset.val===pMode)i.classList.add('selected');});
    document.getElementById('cddModeLabel').textContent=(pMode==='none')?'\\ud83d\\udcc4 Text Mode':'\\ud83d\\uddbc\\ufe0f Poster Mode';
    var savedQ=sessionStorage.getItem('ff_dash_q');
    if(savedQ && q){q.value=savedQ;doSearch(0);}else{doSearch(0,true);}
});
""".replace("__LIMIT_PLACEHOLDER__", str(MAX_WEB_RESULTS)).replace("__DEFAULT_MEDIA_MODE__", DEFAULT_MEDIA_MODE)

# 🎛️ Default mode dropdown state (centralized via DEFAULT_MEDIA_MODE in web_assets.py)
_MODE_TG_LBL = '\U0001f5bc\ufe0f Poster Mode'
_MODE_NONE_LBL = '\U0001f4c4 Text Mode'
_DEF_MODE_LBL = _MODE_NONE_LBL if DEFAULT_MEDIA_MODE == 'none' else _MODE_TG_LBL
_SEL_TG = ' selected' if DEFAULT_MEDIA_MODE == 'tg' else ''
_SEL_NONE = ' selected' if DEFAULT_MEDIA_MODE == 'none' else ''

# ─────────────────────────────────────────────────────────────────────────────
# 🏠 SEARCH ZONE HTML
# ─────────────────────────────────────────────────────────────────────────────
SEARCH_ZONE = (
    '<div class="search-zone">'
        '<div class="search-row1">'
            '<div class="search-wrap" id="qWrap">'
                '<input class="search-input" id="q" placeholder="Titles, people, genres\u2026">'
                '<span class="search-spinner" id="qSpinner"></span>'
            '</div>'
        '</div>'
        '<div class="search-row2">'
            '<div class="cdd-wrap" id="cddColWrap">'
                '<div class="cdd-btn" id="cddColBtn" onclick="toggleCdd(\'col\')">'
                    '<span id="cddColLabel">\U0001f4c2 All Collections</span>'
                '</div>'
                '<span class="cdd-arrow">&#9660;</span>'
                '<div class="cdd-menu" id="cddColMenu" style="display:none">'
                    '<div class="cdd-item selected" data-val="all" onclick="pickCol(\'all\',\'\U0001f4c2 All Collections\',this)">\U0001f4c2 All Collections<span class="cdd-radio"><span class="cdd-radio-dot"></span></span></div>'
                    '<div class="cdd-item" data-val="primary" onclick="pickCol(\'primary\',\'\U0001f7e2 Primary\',this)">\U0001f7e2 Primary<span class="cdd-radio"><span class="cdd-radio-dot"></span></span></div>'
                    '<div class="cdd-item" data-val="cloud" onclick="pickCol(\'cloud\',\'\U0001f535 Cloud\',this)">\U0001f535 Cloud<span class="cdd-radio"><span class="cdd-radio-dot"></span></span></div>'
                    '<div class="cdd-item" data-val="archive" onclick="pickCol(\'archive\',\'\U0001f7e0 Archive\',this)">\U0001f7e0 Archive<span class="cdd-radio"><span class="cdd-radio-dot"></span></span></div>'
                '</div>'
            '</div>'
            '<div class="cdd-wrap" id="cddModeWrap">'
                '<div class="cdd-btn" id="cddModeBtn" onclick="toggleCdd(\'mode\')">'
                    '<span id="cddModeLabel">' + _DEF_MODE_LBL + '</span>'
                '</div>'
                '<span class="cdd-arrow">&#9660;</span>'
                '<div class="cdd-menu" id="cddModeMenu" style="display:none">'
                    '<div class="cdd-item' + _SEL_TG + '" data-val="tg" onclick="pickMode(\'tg\',\'\U0001f5bc\ufe0f Poster Mode\',this)">\U0001f5bc\ufe0f Poster Mode<span class="cdd-radio"><span class="cdd-radio-dot"></span></span></div>'
                    '<div class="cdd-item' + _SEL_NONE + '" data-val="none" onclick="pickMode(\'none\',\'\U0001f4c4 Text Mode\',this)">\U0001f4c4 Text Mode<span class="cdd-radio"><span class="cdd-radio-dot"></span></span></div>'
                '</div>'
            '</div>'
        '</div>'
    '</div>'
    '<div class="main" style="padding-top:4px;">'
        '<div class="results-info" id="resInfo" style="padding:0 12px 8px;">'
            '<span class="results-count" id="resCount"></span>'
        '</div>'
        '<div style="padding:0 2px">'
            '<div id="results" class="res-grid">'
                '<div class="empty"><div class="empty-icon">&#8981;</div>'
                '<p>Find your favorite movies and TV shows.</p></div>'
            '</div>'
            '<div class="pagination" id="pageBox" style="display:none;">'
                '<button class="pg-btn" id="pBtn" onclick="prev()" disabled>Previous</button>'
                '<span class="pg-info" id="pgInfo">Page 1</span>'
                '<button class="pg-btn" id="nBtn" onclick="next()">Next</button>'
            '</div>'
        '</div>'
    '</div>'
    '<div class="toast" id="toast"></div>'
)

# ✅ OPTIMIZATION 1: Pre-compile the entire body string ONCE when the app starts.
DASHBOARD_BODY = CARD_CSS + SEARCH_ZONE + f"<script>{JS_ENGINE}</script>"


@dashboard_routes.get('/dashboard')
async def dash(req):
    role, tg_id = await get_auth(req)
    if not role:
        return web.HTTPFound('/login')
    if not await require_active_plan(role, tg_id):
        return web.HTTPFound('/premium_expired')

    body = DASHBOARD_BODY
    if role == "admin":
        # Group modal + shortcut sirf admin ke page par (users ko extra JS/CSS nahi)
        body = (DASHBOARD_BODY + GROUP_UI_CSS + GROUP_MODAL_HTML + GROUP_MIGRATE_HTML + GROUP_UI_JS
                + '<a href="/groups" class="dash-groups-fab" title="Saare quality groups manage karo">'
                  '<span style="font-size:15px">&#128451;</span> Quality Groups</a>')
    return build_page("Home - Fast Finder", body, "", "dash", role)


@dashboard_routes.get('/logout')
async def logout(req):
    s_user = req.cookies.get('user_session')
    temp.USER_SESSIONS.pop(s_user, None)
    if s_user:
        await web_db.delete_session(s_user)
    res = web.HTTPFound('/login')
    res.del_cookie('user_session', path='/')
    return res


@dashboard_routes.get('/premium_expired')
async def premium_expired(req):
    role, tg_id = await get_auth(req)
    if not role:
        return web.HTTPFound('/login')
    content = (
        '<div style="text-align:center;">'
        '<div style="font-size:50px;margin-bottom:15px;">&#9203;</div>'
        '<p style="color:var(--muted);margin-bottom:30px;">Your access to Fast Finder Web has expired. '
        'Please renew your plan via our Telegram Bot.</p>'
        '<div class="scard red" style="text-align:left;margin-bottom:25px;padding:15px;">'
        '<div class="scard-label">How to Renew?</div>'
        '<div class="scard-sub" style="color:var(--text)">1. Go to Telegram Bot</div>'
        '<div class="scard-sub" style="color:var(--text)">2. Use command <b>/plan</b></div>'
        '<div class="scard-sub" style="color:var(--text)">3. Pay & Activate instantly</div>'
        '</div>'
        f'<a href="https://t.me/{temp.U_NAME}" class="submit-btn" style="text-decoration:none;display:block;">Open Telegram Bot</a>'
        '<a href="/logout" style="display:block;margin-top:20px;color:var(--muted);text-decoration:none;">Sign Out</a>'
        '</div>'
    )
    return build_page("Premium Expired", form_wrapper("Premium Expired", content), "login-bg")


# ✅ OPTIMIZATION 2: Koyeb Health Check Route
# ✅ DEDUPE: /health पहले यहाँ और bot.py — दोनों में रजिस्टर था। web/__init__.py
# पहले चलने की वजह से यही वाला match होता था, bot.py वाला कभी execute नहीं होता था
# (dead code)। अब route एक ही है, और bot.py वाले handler का useful हिस्सा (uptime)
# यहाँ merge कर दिया गया है।
@dashboard_routes.get('/health')
async def koyeb_health_check(req):
    return web.json_response({
        "status": "alive",
        "platform": "koyeb",
        "uptime_seconds": round(time.time() - temp.START_TIME, 2),
    })
