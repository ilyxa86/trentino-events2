
(() => {
  const FIXED_TODAY = "2026-08-25";
  const state = { events: [], lang: "en" };
  const $ = (s) => document.querySelector(s);

  const i18n = {
    en:{
      eyebrow:"Rovereto · Vallagarina · Trento · Alto Garda · Trentino",
      title:"What’s happening in Trentino?",
      subtitle:"A rolling 12-month event guide with verified dates, places and sources.",
      eventsFound:"events found",thisWeekend:"this weekend",lastVerified:"last verified",
      today:"Today",thisWeek:"This week",weekend:"Weekend",thisMonth:"This month",all12:"Next 12 months",
      from:"From",to:"To",area:"Area",category:"Category",search:"Search",reset:"Reset",sort:"Sort",
      soonest:"Soonest first",latest:"Latest first",place:"By place",
      nothing:"No events match these filters.",tryAgain:"Try another date range, area or category.",
      details:"Details",notConfirmed:"Not yet confirmed",confirmed:"Confirmed",
      date:"Date",time:"Time",location:"Location",venue:"Venue",organizer:"Organizer",admission:"Admission",
      source:"Source",verified:"Verified",official:"Official event page",footerA:"Rolling window:",
      footerB:"Dates and programmes can change. Official organizer pages are the source of truth.",
      allAreas:"All areas",allCategories:"All categories",events:"events"
    },
    it:{
      eyebrow:"Rovereto · Vallagarina · Trento · Alto Garda · Trentino",
      title:"Cosa succede in Trentino?",
      subtitle:"Una guida eventi sui prossimi 12 mesi con date, luoghi e fonti verificate.",
      eventsFound:"eventi trovati",thisWeekend:"questo weekend",lastVerified:"ultima verifica",
      today:"Oggi",thisWeek:"Questa settimana",weekend:"Weekend",thisMonth:"Questo mese",all12:"Prossimi 12 mesi",
      from:"Da",to:"A",area:"Zona",category:"Categoria",search:"Cerca",reset:"Azzera",sort:"Ordina",
      soonest:"Prima i più vicini",latest:"Prima i più lontani",place:"Per luogo",
      nothing:"Nessun evento corrisponde ai filtri.",tryAgain:"Prova un altro intervallo, zona o categoria.",
      details:"Dettagli",notConfirmed:"Non ancora confermato",confirmed:"Confermato",
      date:"Data",time:"Ora",location:"Località",venue:"Luogo",organizer:"Organizzatore",admission:"Ingresso",
      source:"Fonte",verified:"Verificato",official:"Pagina ufficiale",footerA:"Finestra mobile:",
      footerB:"Date e programmi possono cambiare. Fa fede la pagina ufficiale dell'organizzatore.",
      allAreas:"Tutte le zone",allCategories:"Tutte le categorie",events:"eventi"
    }
  };

  function dateOnly(s){ const [y,m,d]=s.split("-").map(Number); return new Date(Date.UTC(y,m-1,d)); }
  function iso(d){ return d.toISOString().slice(0,10); }
  function addDays(s,n){ const d=dateOnly(s); d.setUTCDate(d.getUTCDate()+n); return iso(d); }
  function addMonths12(s){ const d=dateOnly(s); d.setUTCFullYear(d.getUTCFullYear()+1); return iso(d); }

  function fmtDate(s, opts={day:"numeric",month:"short",year:"numeric"}){
    return new Intl.DateTimeFormat(state.lang==="it"?"it-IT":"en-GB",{...opts,timeZone:"UTC"}).format(dateOnly(s));
  }
  function fmtRange(a,b){
    return a===b ? fmtDate(a) : `${fmtDate(a)} – ${fmtDate(b)}`;
  }

  async function load(){
    try{
      const res = await fetch("data/events.json",{cache:"no-store"});
      if(!res.ok) throw new Error("Could not load events");
      state.events = await res.json();
    }catch(e){
      $("#eventsGrid").innerHTML = `<p>Unable to load data/events.json. Serve this folder with a web server.</p>`;
      return;
    }
    init();
  }

  function init(){
    $("#fromDate").value = FIXED_TODAY;
    $("#toDate").value = addMonths12(FIXED_TODAY);
    $("#rollingWindow").textContent = `${fmtDate(FIXED_TODAY)} – ${fmtDate(addMonths12(FIXED_TODAY))}`;
    buildFilters();
    bind();
    applyLanguage();
    render();
  }

  function buildFilters(){
    const areas=[...new Set(state.events.map(e=>e.area))].sort();
    const cats=[...new Set(state.events.map(e=>e.category))].sort();
    const area=$("#areaFilter"), cat=$("#categoryFilter");
    area.innerHTML=`<option value="">${i18n[state.lang].allAreas}</option>`+areas.map(v=>`<option>${v}</option>`).join("");
    cat.innerHTML=`<option value="">${i18n[state.lang].allCategories}</option>`+cats.map(v=>`<option>${v}</option>`).join("");
  }

  function bind(){
    document.querySelectorAll(".lang").forEach(b=>b.addEventListener("click",()=>{
      state.lang=b.dataset.lang;
      document.querySelectorAll(".lang").forEach(x=>x.classList.toggle("active",x===b));
      buildFilters(); applyLanguage(); render();
    }));
    ["fromDate","toDate","areaFilter","categoryFilter","searchInput","sortSelect"].forEach(id=>{
      $("#"+id).addEventListener(id==="searchInput"?"input":"change",render);
    });
    $("#resetFilters").addEventListener("click",()=>{
      $("#fromDate").value=FIXED_TODAY; $("#toDate").value=addMonths12(FIXED_TODAY);
      $("#areaFilter").value=""; $("#categoryFilter").value=""; $("#searchInput").value=""; $("#sortSelect").value="soonest";
      setQuickActive("all"); render();
    });
    document.querySelectorAll("[data-quick]").forEach(b=>b.addEventListener("click",()=>quick(b.dataset.quick)));
    $("#closeDialog").addEventListener("click",()=>$("#eventDialog").close());
    $("#eventDialog").addEventListener("click",(ev)=>{ if(ev.target===$("#eventDialog")) $("#eventDialog").close(); });
  }

  function applyLanguage(){
    document.documentElement.lang=state.lang;
    document.querySelectorAll("[data-i18n]").forEach(el=>{
      const key=el.dataset.i18n; if(i18n[state.lang][key]) el.textContent=i18n[state.lang][key];
    });
    document.querySelectorAll("[data-i18n-option]").forEach(el=>{
      const key=el.dataset.i18nOption; if(i18n[state.lang][key]) el.textContent=i18n[state.lang][key];
    });
    $("#searchInput").placeholder = state.lang==="it" ? "Evento, località, luogo…" : "Event, place, venue…";
    $("#rollingWindow").textContent = `${fmtDate(FIXED_TODAY)} – ${fmtDate(addMonths12(FIXED_TODAY))}`;
  }

  function setQuickActive(which){
    document.querySelectorAll("[data-quick]").forEach(b=>b.classList.toggle("active",b.dataset.quick===which));
  }

  function quick(which){
    let from=FIXED_TODAY,to=addMonths12(FIXED_TODAY);
    const d=dateOnly(FIXED_TODAY), dow=d.getUTCDay();
    if(which==="today"){to=from}
    if(which==="week"){to=addDays(FIXED_TODAY,6)}
    if(which==="weekend"){
      const daysToSat=(6-dow+7)%7;
      from=addDays(FIXED_TODAY,daysToSat); to=addDays(from,1);
    }
    if(which==="month"){
      const end=new Date(Date.UTC(d.getUTCFullYear(),d.getUTCMonth()+1,0)); to=iso(end);
    }
    $("#fromDate").value=from; $("#toDate").value=to; setQuickActive(which); render();
  }

  function overlaps(e,from,to){ return e.endDate>=from && e.startDate<=to; }

  function getFiltered(){
    const from=$("#fromDate").value || FIXED_TODAY;
    const to=$("#toDate").value || addMonths12(FIXED_TODAY);
    const area=$("#areaFilter").value, cat=$("#categoryFilter").value;
    const q=$("#searchInput").value.trim().toLowerCase();
    let arr=state.events.filter(e=>overlaps(e,from,to))
      .filter(e=>!area||e.area===area).filter(e=>!cat||e.category===cat)
      .filter(e=>{
        if(!q)return true;
        const blob=[e.name.en,e.name.it,e.municipality,e.area,e.venue,e.category,e.description.en,e.description.it].join(" ").toLowerCase();
        return blob.includes(q);
      });
    const sort=$("#sortSelect").value;
    arr.sort((a,b)=>sort==="latest"?b.startDate.localeCompare(a.startDate):
      sort==="place"?a.municipality.localeCompare(b.municipality):a.startDate.localeCompare(b.startDate));
    return arr;
  }

  function badge(e){
    const confirmed = e.confirmed
      ? `<span class="badge confirmed">${i18n[state.lang].confirmed}</span>`
      : `<span class="badge unconfirmed">${i18n[state.lang].notConfirmed}</span>`;
    const status = e.status ? `<span class="badge ${e.status.toLowerCase()}">${e.status}</span>` : "";
    return status+confirmed;
  }

  function render(){
    const arr=getFiltered(), grid=$("#eventsGrid");
    const from=$("#fromDate").value, to=$("#toDate").value;
    $("#eventCount").textContent=arr.length;
    const d=dateOnly(FIXED_TODAY), dow=d.getUTCDay(), daysToSat=(6-dow+7)%7;
    const sat=addDays(FIXED_TODAY,daysToSat), sun=addDays(sat,1);
    $("#nextWeekendCount").textContent=state.events.filter(e=>overlaps(e,sat,sun)).length;
    const latestVerify=[...state.events].map(e=>e.verified).sort().at(-1);
    $("#lastVerified").textContent=latestVerify ? fmtDate(latestVerify,{day:"2-digit",month:"short"}) : "—";
    $("#rangeLabel").textContent=`${fmtRange(from,to)} · ${arr.length} ${i18n[state.lang].events}`;
    $("#emptyState").hidden=arr.length>0;

    grid.innerHTML=arr.map(e=>{
      const dd=dateOnly(e.startDate), day=String(dd.getUTCDate()).padStart(2,"0");
      const mon=new Intl.DateTimeFormat(state.lang==="it"?"it-IT":"en-GB",{month:"short",timeZone:"UTC"}).format(dd);
      return `<article class="event-card">
        <div class="card-top">
          <div class="date-chip"><div class="day">${day}</div><div class="mon">${mon}</div></div>
          <div class="badges">${badge(e)}</div>
        </div>
        <h2>${escapeHtml(e.name[state.lang])}</h2>
        <p class="meta">${escapeHtml(e.municipality)} · ${escapeHtml(e.venue)}<br>${fmtRange(e.startDate,e.endDate)}${e.startTime?` · ${e.startTime}`:""}</p>
        <p class="desc">${escapeHtml(e.description[state.lang])}</p>
        <div class="card-actions"><span class="category">${escapeHtml(e.category)}</span><button type="button" class="details-btn" data-id="${e.id}">${i18n[state.lang].details} →</button></div>
      </article>`;
    }).join("");
    grid.querySelectorAll(".details-btn").forEach(b=>b.addEventListener("click",()=>openEvent(b.dataset.id)));
  }

  function openEvent(id){
    const e=state.events.find(x=>x.id===id); if(!e)return;
    $("#dialogBody").innerHTML=`
      <div class="detail-kicker">${escapeHtml(e.category)} · ${escapeHtml(e.area)}</div>
      <h2>${escapeHtml(e.name[state.lang])}</h2>
      <div class="badges" style="justify-content:flex-start">${badge(e)}</div>
      <p>${escapeHtml(e.description[state.lang])}</p>
      <div class="detail-grid">
        ${detail(i18n[state.lang].date,fmtRange(e.startDate,e.endDate))}
        ${detail(i18n[state.lang].time,e.startTime||"—")}
        ${detail(i18n[state.lang].location,e.municipality)}
        ${detail(i18n[state.lang].venue,e.venue)}
        ${detail(i18n[state.lang].organizer,e.organizer||"—")}
        ${detail(i18n[state.lang].admission,e.price||"—")}
        ${detail(i18n[state.lang].source,e.source||"—")}
        ${detail(i18n[state.lang].verified,fmtDate(e.verified))}
      </div>
      <a class="official-link" href="${e.officialUrl}" target="_blank" rel="noopener noreferrer">${i18n[state.lang].official} ↗</a>`;
    $("#eventDialog").showModal();
  }

  function detail(label,value){return `<div class="detail-item"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`}
  function escapeHtml(s){return String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]))}

  load();
})();
