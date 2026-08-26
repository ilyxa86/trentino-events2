(() => {
  const state = { events: [], lang: "de" };
  const $ = (s) => document.querySelector(s);

  const i18n = {
    de: {
      eyebrow:"Rovereto · Vallagarina · Trento · Alto Garda · Trentino",
      title:"Das Beste aus dem Trentino – Event für Event.",
      subtitle:"Märkte, Festivals, Genuss, Kultur, Familie und Outdoor-Erlebnisse – an einem Ort gebündelt und regelmäßig geprüft.",
      updatedDaily:"Datenbank wird regelmäßig geprüft", thisWeekend:"kurze Events dieses Wochenende", lastVerified:"letzte Datenprüfung",
      handpicked:"Aktuell ausgewählt", featured:"Highlights", viewAll:"Alle Events anzeigen →", freshlyUpdated:"Frisch aktualisiert", whatsChanged:"Neu & geändert",
      makePlans:"Wochenende planen", weekendHighlights:"Dieses Wochenende", showWeekend:"Alle Wochenend-Events →", exploreByPlace:"Nach Region entdecken",
      regions:"Wohin möchtest du?", findYourEvent:"Finde dein Event", browseAll:"Alle Events durchsuchen",
      today:"Heute", thisWeek:"Diese Woche", nextWeek:"Nächste Woche", weekend:"Wochenende", thisMonth:"Dieser Monat", all12:"Nächste 12 Monate",
      from:"Von", to:"Bis", area:"Region", category:"Kategorie", search:"Suche", reset:"Zurücksetzen", sort:"Sortierung",
      soonest:"Nächste zuerst", latest:"Späteste zuerst", place:"Nach Ort", discover:"Trentino entdecken", shortEvents:"Termine & Kurzveranstaltungen",
      longRunning:"Langzeit & Dauerausstellungen", longRunningIntro:"Ausstellungen, Saisonprogramme und wiederkehrende Angebote, die über mehrere Wochen laufen.",
      noShort:"Für diesen Zeitraum gibt es aktuell keine kurzen Einzeltermine. Langzeitangebote findest du separat darunter.",
      nothing:"Keine Events passen zu diesen Filtern.", tryAgain:"Probiere einen anderen Zeitraum, eine Region oder Kategorie.", details:"Details",
      notConfirmed:"Noch nicht bestätigt", date:"Datum", time:"Uhrzeit", location:"Ort", venue:"Veranstaltungsort", organizer:"Veranstalter", admission:"Eintritt",
      source:"Quelle", verified:"Geprüft", official:"Offizielle Eventseite", footerA:"Zeitraum:", footerB:"Daten und Programme können sich ändern. Maßgeblich ist die offizielle Veranstalterseite.",
      footerTagline:"Ein kuratierter Eventguide für das gesamte Trentino.", allAreas:"Alle Regionen", allCategories:"Alle Kategorien", events:"Events", eventSingular:"Event",
      statusChanged:"Status geändert", noWeekend:"Derzeit sind keine kurzen Wochenend-Events in der Datenbank.", all:"Alle", longTag:"Langzeit",
      statuses:{NEW:"Neu",UPDATED:"Aktualisiert",CONFIRMED:"Bestätigt",CANCELLED:"Abgesagt",REMOVED:"Entfernt"},
      categories:{
        "Markets & Shopping":"Märkte & Shopping","Festival":"Festival","Family & Festival":"Familie & Festival","Concert":"Konzert",
        "Agriculture & Tradition":"Landwirtschaft & Tradition","Culture & Music":"Kultur & Musik","Culture & Dance":"Kultur & Tanz","Culture & Exhibition":"Kultur & Ausstellung",
        "Sport":"Sport","Family & Culture":"Familie & Kultur","Wine & Gastronomy":"Wein & Genuss","Sport & Culture":"Sport & Kultur",
        "Food & Agriculture":"Genuss & Landwirtschaft","Film & Culture":"Film & Kultur","Business & Innovation":"Business & Innovation","Business & Wine":"Business & Wein",
        "Christmas Market":"Weihnachtsmarkt","Trade Fair":"Messe","Sport & Outdoor":"Sport & Outdoor","Business & Networking":"Business & Networking","Other":"Sonstiges"
      }
    },
    en: {
      eyebrow:"Rovereto · Vallagarina · Trento · Alto Garda · Trentino", title:"The best of Trentino, one event at a time.",
      subtitle:"Markets, festivals, food, culture, family and outdoor experiences — continuously verified in one place.",
      updatedDaily:"Database checked regularly", thisWeekend:"short events this weekend", lastVerified:"last database check",
      handpicked:"Handpicked now", featured:"Featured events", viewAll:"View all events →", freshlyUpdated:"Freshly updated", whatsChanged:"What’s new & changed",
      makePlans:"Make plans", weekendHighlights:"This weekend", showWeekend:"Show all weekend events →", exploreByPlace:"Explore by place", regions:"Where do you want to go?",
      findYourEvent:"Find your event", browseAll:"Browse all events", today:"Today", thisWeek:"This week", nextWeek:"Next week", weekend:"Weekend", thisMonth:"This month", all12:"Next 12 months",
      from:"From", to:"To", area:"Area", category:"Category", search:"Search", reset:"Reset", sort:"Sort", soonest:"Soonest first", latest:"Latest first", place:"By place",
      discover:"Discover Trentino", shortEvents:"Dates & short events", longRunning:"Long-running events & exhibitions",
      longRunningIntro:"Exhibitions, seasonal programmes and recurring activities that run for several weeks.", noShort:"There are currently no short one-off events for this period. Long-running activities are shown separately below.",
      nothing:"No events match these filters.", tryAgain:"Try another date range, area or category.", details:"Details", notConfirmed:"Not yet confirmed", date:"Date", time:"Time",
      location:"Location", venue:"Venue", organizer:"Organizer", admission:"Admission", source:"Source", verified:"Verified", official:"Official event page", footerA:"Rolling window:",
      footerB:"Dates and programmes can change. The official organizer page remains the source of truth.", footerTagline:"A curated guide to what’s happening across Trentino.",
      allAreas:"All areas", allCategories:"All categories", events:"events", eventSingular:"event", statusChanged:"Status changed", noWeekend:"No short weekend events are currently in the database.", all:"All", longTag:"Long-running",
      statuses:{NEW:"New",UPDATED:"Updated",CONFIRMED:"Confirmed",CANCELLED:"Cancelled",REMOVED:"Removed"},
      categories:{
        "Markets & Shopping":"Markets & shopping","Festival":"Festival","Family & Festival":"Family & festival","Concert":"Concert",
        "Agriculture & Tradition":"Agriculture & tradition","Culture & Music":"Culture & music","Culture & Dance":"Culture & dance","Culture & Exhibition":"Culture & exhibition",
        "Sport":"Sport","Family & Culture":"Family & culture","Wine & Gastronomy":"Wine & gastronomy","Sport & Culture":"Sport & culture",
        "Food & Agriculture":"Food & agriculture","Film & Culture":"Cinema & culture","Business & Innovation":"Business & innovation","Business & Wine":"Business & wine",
        "Christmas Market":"Christmas market","Trade Fair":"Trade fair","Sport & Outdoor":"Sport & outdoor","Business & Networking":"Business & networking","Other":"Other"
      }
    },
    it: {
      eyebrow:"Rovereto · Vallagarina · Trento · Alto Garda · Trentino", title:"Il meglio del Trentino, un evento alla volta.",
      subtitle:"Mercati, festival, gastronomia, cultura, famiglia e outdoor — verificati continuamente in un unico posto.",
      updatedDaily:"Database controllato regolarmente", thisWeekend:"eventi brevi questo weekend", lastVerified:"ultimo controllo database",
      handpicked:"Da non perdere", featured:"Eventi in evidenza", viewAll:"Vedi tutti gli eventi →", freshlyUpdated:"Appena aggiornato", whatsChanged:"Novità & aggiornamenti",
      makePlans:"Organizza il weekend", weekendHighlights:"Questo weekend", showWeekend:"Vedi tutti gli eventi del weekend →", exploreByPlace:"Esplora per zona", regions:"Dove vuoi andare?",
      findYourEvent:"Trova il tuo evento", browseAll:"Esplora tutti gli eventi", today:"Oggi", thisWeek:"Questa settimana", nextWeek:"Prossima settimana", weekend:"Weekend", thisMonth:"Questo mese", all12:"Prossimi 12 mesi",
      from:"Da", to:"A", area:"Zona", category:"Categoria", search:"Cerca", reset:"Azzera", sort:"Ordina", soonest:"Prima i più vicini", latest:"Prima i più lontani", place:"Per luogo",
      discover:"Scopri il Trentino", shortEvents:"Appuntamenti ed eventi brevi", longRunning:"Eventi di lunga durata e mostre",
      longRunningIntro:"Mostre, programmi stagionali e attività ricorrenti che durano diverse settimane.", noShort:"Per questo periodo non ci sono appuntamenti brevi. Le attività di lunga durata sono mostrate separatamente qui sotto.",
      nothing:"Nessun evento corrisponde ai filtri.", tryAgain:"Prova un altro intervallo, zona o categoria.", details:"Dettagli", notConfirmed:"Non ancora confermato", date:"Data", time:"Ora",
      location:"Località", venue:"Luogo", organizer:"Organizzatore", admission:"Ingresso", source:"Fonte", verified:"Verificato", official:"Pagina ufficiale", footerA:"Finestra mobile:",
      footerB:"Date e programmi possono cambiare. Fa fede la pagina ufficiale dell’organizzatore.", footerTagline:"Una guida curata agli eventi in tutto il Trentino.",
      allAreas:"Tutte le zone", allCategories:"Tutte le categorie", events:"eventi", eventSingular:"evento", statusChanged:"Stato modificato", noWeekend:"Al momento non ci sono eventi brevi per il weekend.", all:"Tutte", longTag:"Lunga durata",
      statuses:{NEW:"Nuovo",UPDATED:"Aggiornato",CONFIRMED:"Confermato",CANCELLED:"Annullato",REMOVED:"Rimosso"},
      categories:{
        "Markets & Shopping":"Mercati e shopping","Festival":"Festival","Family & Festival":"Famiglia e festival","Concert":"Concerto",
        "Agriculture & Tradition":"Agricoltura e tradizione","Culture & Music":"Cultura e musica","Culture & Dance":"Cultura e danza","Culture & Exhibition":"Cultura e mostra",
        "Sport":"Sport","Family & Culture":"Famiglia e cultura","Wine & Gastronomy":"Vino e gastronomia","Sport & Culture":"Sport e cultura",
        "Food & Agriculture":"Cibo e agricoltura","Film & Culture":"Cinema e cultura","Business & Innovation":"Business e innovazione","Business & Wine":"Business e vino",
        "Christmas Market":"Mercatino di Natale","Trade Fair":"Fiera","Sport & Outdoor":"Sport e outdoor","Business & Networking":"Business e networking","Other":"Altro"
      }
    }
  };

  const imagePools = {
    default:["https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1000&q=80","https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1000&q=80"],
    market:["https://images.unsplash.com/photo-1488459716781-31db52582fe9?auto=format&fit=crop&w=1000&q=80","https://images.unsplash.com/photo-1472851294608-062f824d29cc?auto=format&fit=crop&w=1000&q=80"],
    food:["https://images.unsplash.com/photo-1555939594-58d7cb561ad1?auto=format&fit=crop&w=1000&q=80","https://images.unsplash.com/photo-1510812431401-41d2bd2722f3?auto=format&fit=crop&w=1000&q=80"],
    festival:["https://images.unsplash.com/photo-1517457373958-b7bdd4587205?auto=format&fit=crop&w=1000&q=80","https://images.unsplash.com/photo-1506157786151-b8491531f063?auto=format&fit=crop&w=1000&q=80"],
    culture:["https://images.unsplash.com/photo-1487958449943-2429e8be8625?auto=format&fit=crop&w=1000&q=80","https://images.unsplash.com/photo-1485846234645-a62644f84728?auto=format&fit=crop&w=1000&q=80"],
    business:["https://images.unsplash.com/photo-1521791136064-7986c2920216?auto=format&fit=crop&w=1000&q=80","https://images.unsplash.com/photo-1521737711867-e3b97375f902?auto=format&fit=crop&w=1000&q=80"],
    christmas:["https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=1000&q=80","https://images.unsplash.com/photo-1512389142860-9c449e58a543?auto=format&fit=crop&w=1000&q=80"],
    outdoor:["https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1000&q=80","https://images.unsplash.com/photo-1461896836934-ffe607ba8211?auto=format&fit=crop&w=1000&q=80"]
  };
  const areaImages = {
    "Rovereto & Vallagarina":"https://images.unsplash.com/photo-1467269204594-9661b134dd2b?auto=format&fit=crop&w=800&q=78",
    "Trento":"https://images.unsplash.com/photo-1529260830199-42c24126f198?auto=format&fit=crop&w=800&q=78",
    "Alto Garda":"https://images.unsplash.com/photo-1530789253388-582c481c54b0?auto=format&fit=crop&w=800&q=78",
    "Other Trentino":"https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=800&q=78"
  };
  const fallbackImage=imagePools.default[0];
  const locale=()=>state.lang==="de"?"de-DE":state.lang==="it"?"it-IT":"en-GB";

  function hashText(value){let h=0;for(const ch of String(value||""))h=(h*31+ch.charCodeAt(0))>>>0;return h;}
  function poolImage(pool,e){const list=imagePools[pool]||imagePools.default;return list[hashText(e.id)%list.length];}
  function currentRomeDate(){const parts=new Intl.DateTimeFormat("en-CA",{timeZone:"Europe/Rome",year:"numeric",month:"2-digit",day:"2-digit"}).formatToParts(new Date());const get=t=>parts.find(p=>p.type===t)?.value;return `${get("year")}-${get("month")}-${get("day")}`;}
  const TODAY=currentRomeDate();
  function dateOnly(s){const [y,m,d]=String(s).split("-").map(Number);return new Date(Date.UTC(y,m-1,d));}
  function iso(d){return d.toISOString().slice(0,10);}
  function addDays(s,n){const d=dateOnly(s);d.setUTCDate(d.getUTCDate()+n);return iso(d);}
  function addMonths12(s){const d=dateOnly(s);d.setUTCFullYear(d.getUTCFullYear()+1);return iso(d);}
  function fmtDate(s,opts={day:"numeric",month:"short",year:"numeric"}){return new Intl.DateTimeFormat(locale(),{...opts,timeZone:"UTC"}).format(dateOnly(s));}
  function fmtRange(a,b){return a===b?fmtDate(a):`${fmtDate(a)} – ${fmtDate(b)}`;}
  function categoryLabel(c){return i18n[state.lang].categories[c]||c||"";}
  function eventName(e){return e.name?.[state.lang]||e.name?.it||e.name?.en||"";}
  function rawDescription(e){return e.description?.[state.lang]||e.description?.en||e.description?.it||"";}
  function imageFor(e){if(e.image)return e.image;const c=(e.category||"").toLowerCase();if(c.includes("christmas"))return poolImage("christmas",e);if(c.includes("market")||c.includes("shopping"))return poolImage("market",e);if(c.includes("wine")||c.includes("gastronomy")||c.includes("food")||c.includes("agriculture"))return poolImage("food",e);if(c.includes("sport")||c.includes("outdoor"))return poolImage("outdoor",e);if(c.includes("business")||c.includes("trade fair"))return poolImage("business",e);if(c.includes("culture")||c.includes("film")||c.includes("dance")||c.includes("exhibition"))return poolImage("culture",e);if(c.includes("concert")||c.includes("festival"))return poolImage("festival",e);return poolImage("default",e);}
  function isActiveEvent(e){return e.status!=="REMOVED"&&e.status!=="CANCELLED"&&e.endDate>=TODAY;}
  function overlaps(e,from,to){return e.endDate>=from&&e.startDate<=to;}
  function durationDays(e){if(!e.startDate||!e.endDate)return 0;return Math.round((dateOnly(e.endDate)-dateOnly(e.startDate))/86400000)+1;}
  function isLongRunning(e){return durationDays(e)>21||Boolean(e.recurrence)||(Array.isArray(e.occurrences)&&e.occurrences.length>5);}
  function statusDate(e){return e.statusDate||e.verified||null;}
  function statusIsFresh(e){if(!e.status)return false;const d=statusDate(e);if(!d)return false;const age=Math.floor((dateOnly(TODAY)-dateOnly(d))/86400000);return age>=0&&age<=7;}

  function isBoilerplate(text){return /Aktuelle Details finden Sie auf der offiziellen Veranstaltungsseite|See the official event page for the latest details|Consulta la pagina ufficiale per i dettagli aggiornati/i.test(text||"");}
  function dateSentence(e){
    const place=e.municipality||e.area||"Trentino";
    if(state.lang==="de")return e.startDate===e.endDate?`„${eventName(e)}“ findet am ${fmtDate(e.startDate)} in ${place} statt.`:`„${eventName(e)}“ läuft vom ${fmtDate(e.startDate)} bis ${fmtDate(e.endDate)} in ${place}.`;
    if(state.lang==="it")return e.startDate===e.endDate?`“${eventName(e)}” si svolge il ${fmtDate(e.startDate)} a ${place}.`:`“${eventName(e)}” si svolge dal ${fmtDate(e.startDate)} al ${fmtDate(e.endDate)} a ${place}.`;
    return e.startDate===e.endDate?`“${eventName(e)}” takes place on ${fmtDate(e.startDate)} in ${place}.`:`“${eventName(e)}” runs from ${fmtDate(e.startDate)} to ${fmtDate(e.endDate)} in ${place}.`;
  }
  function categorySentence(e){
    const c=(e.category||"").toLowerCase();
    const map={
      de:{food:"Im Mittelpunkt stehen Genuss, regionale Produkte und Begegnungen rund um die kulinarische Seite des Trentino.",culture:"Das Angebot richtet sich an Kulturinteressierte und verbindet das Thema mit einem konkreten Programm vor Ort.",sport:"Im Mittelpunkt stehen Bewegung, Sport und das gemeinsame Erlebnis in der Region.",family:"Das Programm eignet sich besonders für Familien und verbindet Unterhaltung mit einem unkomplizierten Ausflug.",market:"Hier treffen lokales Einkaufen, Marktleben und regionale Atmosphäre aufeinander.",festival:"Das Event bündelt mehrere Programmpunkte und bietet einen lebendigen Anlass für einen Besuch vor Ort.",business:"Die Veranstaltung bringt Fachthemen, Austausch und Begegnungen in einem gemeinsamen Rahmen zusammen.",other:`Die Veranstaltung gehört zum Bereich ${categoryLabel(e.category)} und lässt sich als eigener Programmpunkt in einen Besuch im Trentino einbauen.`},
      en:{food:"The focus is on local food, regional products and the culinary side of Trentino.",culture:"The programme is aimed at culture lovers and connects the theme with an on-site cultural experience.",sport:"The focus is on movement, sport and a shared experience in the region.",family:"The programme is especially suitable for families and combines entertainment with an easy day out.",market:"Local shopping, market life and regional atmosphere come together here.",festival:"The event brings several programme elements together and offers a lively reason to visit.",business:"The event combines professional topics, exchange and networking in one setting.",other:`The event belongs to the ${categoryLabel(e.category)} category and works well as a dedicated stop during a visit to Trentino.`},
      it:{food:"Al centro ci sono sapori, prodotti locali e la dimensione gastronomica del Trentino.",culture:"La proposta è pensata per chi ama la cultura e collega il tema a un'esperienza concreta sul territorio.",sport:"Al centro ci sono movimento, sport e un'esperienza condivisa sul territorio.",family:"Il programma è particolarmente adatto alle famiglie e unisce intrattenimento e una piacevole uscita.",market:"Qui si incontrano shopping locale, vita di mercato e atmosfera del territorio.",festival:"L'evento riunisce più momenti di programma e offre un'occasione vivace per visitare la località.",business:"L'evento unisce temi professionali, confronto e networking in un unico contesto.",other:`L'evento rientra nella categoria ${categoryLabel(e.category)} e può diventare una tappa dedicata durante una visita in Trentino.`}
    }[state.lang];
    if(c.includes("wine")||c.includes("food")||c.includes("gastronomy")||c.includes("agriculture"))return map.food;
    if(c.includes("culture")||c.includes("film")||c.includes("dance")||c.includes("exhibition")||c.includes("concert"))return map.culture;
    if(c.includes("sport")||c.includes("outdoor"))return map.sport;
    if(c.includes("family"))return map.family;
    if(c.includes("market")||c.includes("shopping"))return map.market;
    if(c.includes("festival")||c.includes("fair"))return map.festival;
    if(c.includes("business")||c.includes("network"))return map.business;
    return map.other;
  }
  function venueSentence(e){if(!e.venue||e.venue===e.municipality)return "";if(state.lang==="de")return `Veranstaltungsort ist ${e.venue}.`;if(state.lang==="it")return `La sede indicata è ${e.venue}.`;return `The listed venue is ${e.venue}.`;}
  function friendlySummary(e){return [dateSentence(e),categorySentence(e),venueSentence(e)].filter(Boolean).join(" ");}
  function eventDescription(e){const text=rawDescription(e);return !text||isBoilerplate(text)?friendlySummary(e):text;}

  async function load(){
    try{const res=await fetch("data/events.json",{cache:"no-store"});if(!res.ok)throw new Error("Could not load events");state.events=await res.json();}
    catch(e){$("#eventsGrid").innerHTML="<p>data/events.json konnte nicht geladen werden.</p>";return;}
    init();
  }
  function init(){$("#fromDate").value=TODAY;$("#toDate").value=addMonths12(TODAY);buildFilters();bind();applyLanguage();renderAll();}

  function buildFilters(){
    const selectedArea=$("#areaFilter").value,selectedCat=$("#categoryFilter").value;
    const areas=[...new Set(state.events.map(e=>e.area).filter(Boolean))].sort();const cats=[...new Set(state.events.map(e=>e.category).filter(Boolean))].sort();
    $("#areaFilter").innerHTML=`<option value="">${i18n[state.lang].allAreas}</option>`+areas.map(v=>`<option value="${escapeAttr(v)}">${escapeHtml(v)}</option>`).join("");
    $("#categoryFilter").innerHTML=`<option value="">${i18n[state.lang].allCategories}</option>`+cats.map(v=>`<option value="${escapeAttr(v)}">${escapeHtml(categoryLabel(v))}</option>`).join("");
    $("#areaFilter").value=selectedArea;$("#categoryFilter").value=selectedCat;buildCategoryChips(cats,selectedCat);
  }
  function buildCategoryChips(cats,selected){
    const root=$("#categoryChips");root.innerHTML=`<button type="button" class="category-chip ${selected?"":"active"}" data-category="">${i18n[state.lang].all}</button>`+cats.map(c=>`<button type="button" class="category-chip ${selected===c?"active":""}" data-category="${escapeAttr(c)}">${escapeHtml(categoryLabel(c))}</button>`).join("");
    root.querySelectorAll(".category-chip").forEach(btn=>btn.addEventListener("click",()=>{$("#categoryFilter").value=btn.dataset.category;root.querySelectorAll(".category-chip").forEach(x=>x.classList.toggle("active",x===btn));renderGrid();}));
  }
  function bind(){
    document.querySelectorAll(".lang").forEach(b=>b.addEventListener("click",()=>{state.lang=b.dataset.lang;document.querySelectorAll(".lang").forEach(x=>x.classList.toggle("active",x===b));applyLanguage();buildFilters();renderAll();}));
    ["fromDate","toDate","areaFilter","categoryFilter","searchInput","sortSelect"].forEach(id=>$("#"+id).addEventListener(id==="searchInput"?"input":"change",renderGrid));
    $("#resetFilters").addEventListener("click",()=>{$("#fromDate").value=TODAY;$("#toDate").value=addMonths12(TODAY);$("#areaFilter").value="";$("#categoryFilter").value="";$("#searchInput").value="";$("#sortSelect").value="soonest";setQuickActive("all");buildCategoryChips([...new Set(state.events.map(e=>e.category).filter(Boolean))].sort(),"");renderGrid();});
    document.querySelectorAll("[data-quick]").forEach(b=>b.addEventListener("click",()=>quick(b.dataset.quick)));
    document.querySelectorAll("[data-jump]").forEach(b=>b.addEventListener("click",()=>{const w=b.dataset.jump;if(w==="weekend")quick("weekend");else quick("all");$("#discover").scrollIntoView({behavior:"smooth",block:"start"});}));
    $("#closeDialog").addEventListener("click",()=>$("#eventDialog").close());$("#eventDialog").addEventListener("click",ev=>{if(ev.target===$("#eventDialog"))$("#eventDialog").close();});
  }
  function applyLanguage(){
    document.documentElement.lang=state.lang;document.querySelectorAll("[data-i18n]").forEach(el=>{const key=el.dataset.i18n;if(i18n[state.lang][key])el.textContent=i18n[state.lang][key];});
    document.querySelectorAll("[data-i18n-option]").forEach(el=>{const key=el.dataset.i18nOption;if(i18n[state.lang][key])el.textContent=i18n[state.lang][key];});
    const placeholder=state.lang==="de"?"Event, Ort, Veranstaltungsort…":state.lang==="it"?"Evento, località, luogo…":"Event, place, venue…";$("#searchInput").placeholder=placeholder;
    $("#rollingWindow").textContent=`${fmtDate(TODAY)} – ${fmtDate(addMonths12(TODAY))}`;
  }

  function setQuickActive(which){document.querySelectorAll("[data-quick]").forEach(b=>b.classList.toggle("active",b.dataset.quick===which));}
  function quick(which){
    let from=TODAY,to=addMonths12(TODAY);const d=dateOnly(TODAY),dow=d.getUTCDay();
    if(which==="today")to=from;
    if(which==="week")to=addDays(TODAY,6);
    if(which==="nextweek"){const daysToMon=(8-dow)%7||7;from=addDays(TODAY,daysToMon);to=addDays(from,6);}
    if(which==="weekend"){const daysToSat=(6-dow+7)%7;from=addDays(TODAY,daysToSat);to=addDays(from,1);}
    if(which==="month"){const end=new Date(Date.UTC(d.getUTCFullYear(),d.getUTCMonth()+1,0));to=iso(end);}
    $("#fromDate").value=from;$("#toDate").value=to;setQuickActive(which);renderGrid();
  }
  function getFiltered(){
    const from=$("#fromDate").value||TODAY,to=$("#toDate").value||addMonths12(TODAY),area=$("#areaFilter").value,cat=$("#categoryFilter").value,q=$("#searchInput").value.trim().toLowerCase();
    let arr=state.events.filter(isActiveEvent).filter(e=>overlaps(e,from,to)).filter(e=>!area||e.area===area).filter(e=>!cat||e.category===cat).filter(e=>{if(!q)return true;return [e.name?.de,e.name?.en,e.name?.it,e.municipality,e.area,e.venue,e.category,e.description?.de,e.description?.en,e.description?.it].filter(Boolean).join(" ").toLowerCase().includes(q);});
    const sort=$("#sortSelect").value;arr.sort((a,b)=>sort==="latest"?b.startDate.localeCompare(a.startDate):sort==="place"?String(a.municipality).localeCompare(String(b.municipality)):a.startDate.localeCompare(b.startDate));return arr;
  }
  function badge(e){const bits=[];if(statusIsFresh(e)&&i18n[state.lang].statuses[e.status])bits.push(`<span class="badge ${e.status.toLowerCase()}">${escapeHtml(i18n[state.lang].statuses[e.status])}</span>`);if(!e.confirmed)bits.push(`<span class="badge unconfirmed">${escapeHtml(i18n[state.lang].notConfirmed)}</span>`);return bits.join("");}

  function renderAll(){renderSummary();renderEditorial();renderGrid();}
  function renderSummary(){
    const active=state.events.filter(isActiveEvent).filter(e=>!isLongRunning(e));const d=dateOnly(TODAY),dow=d.getUTCDay(),daysToSat=(6-dow+7)%7,sat=addDays(TODAY,daysToSat),sun=addDays(sat,1);
    $("#nextWeekendCount").textContent=active.filter(e=>overlaps(e,sat,sun)).length;const latest=state.events.map(e=>e.verified).filter(Boolean).sort().at(-1);$("#lastVerified").textContent=latest?fmtDate(latest,{day:"2-digit",month:"short"}):"—";
  }
  function chooseFeatured(){const candidates=state.events.filter(isActiveEvent).filter(e=>!isLongRunning(e)).sort((a,b)=>a.startDate.localeCompare(b.startDate));const picked=[],seen=new Set();for(const e of candidates){if(!seen.has(e.category)){picked.push(e);seen.add(e.category);}if(picked.length===4)break;}for(const e of candidates){if(picked.length===4)break;if(!picked.includes(e))picked.push(e);}return picked;}
  function renderEditorial(){
    const featured=chooseFeatured();$("#featuredGrid").innerHTML=featured.map((e,i)=>`<article class="feature-card ${i===0?"main":""}"><img src="${escapeAttr(imageFor(e))}" alt="${escapeAttr(eventName(e))}" loading="lazy"><div class="feature-content"><span class="feature-label">${escapeHtml(categoryLabel(e.category))}</span><h3>${escapeHtml(eventName(e))}</h3><p class="feature-meta">${escapeHtml(e.municipality||"")} · ${fmtRange(e.startDate,e.endDate)}</p></div><button type="button" class="feature-open" data-open="${escapeAttr(e.id)}">${escapeHtml(i18n[state.lang].details)}</button></article>`).join("");
    const changes=state.events.filter(e=>e.status&&statusDate(e)).sort((a,b)=>statusDate(b).localeCompare(statusDate(a))).slice(0,4);$("#changesSection").hidden=changes.length===0;$("#changesGrid").innerHTML=changes.map(e=>`<article class="change-card"><div class="change-icon ${(e.status||"").toLowerCase()}">${statusSymbol(e.status)}</div><div><strong>${escapeHtml(eventName(e))}</strong><p>${escapeHtml(i18n[state.lang].statuses[e.status]||i18n[state.lang].statusChanged)} · ${statusDate(e)?fmtDate(statusDate(e),{day:"2-digit",month:"short"}):""}</p></div></article>`).join("");
    const d=dateOnly(TODAY),dow=d.getUTCDay(),daysToSat=(6-dow+7)%7,sat=addDays(TODAY,daysToSat),sun=addDays(sat,1);const weekend=state.events.filter(isActiveEvent).filter(e=>!isLongRunning(e)).filter(e=>overlaps(e,sat,sun)).sort((a,b)=>a.startDate.localeCompare(b.startDate)).slice(0,3);
    $("#weekendGrid").innerHTML=weekend.length?weekend.map(e=>`<article class="mini-event"><div class="mini-event-image"><img src="${escapeAttr(imageFor(e))}" alt="${escapeAttr(eventName(e))}" loading="lazy"></div><div class="mini-event-body"><div class="mini-category">${escapeHtml(categoryLabel(e.category))}</div><h3>${escapeHtml(eventName(e))}</h3><p>${escapeHtml(e.municipality||"")} · ${fmtRange(e.startDate,e.endDate)}</p><button type="button" data-open="${escapeAttr(e.id)}">${escapeHtml(i18n[state.lang].details)} →</button></div></article>`).join(""):`<p>${escapeHtml(i18n[state.lang].noWeekend)}</p>`;
    const areas=[...new Set(state.events.filter(isActiveEvent).map(e=>e.area).filter(Boolean))];$("#areaCards").innerHTML=areas.map(area=>{const count=state.events.filter(isActiveEvent).filter(e=>e.area===area).length;const img=areaImages[area]||areaImages["Other Trentino"];return `<button type="button" class="area-card" data-area="${escapeAttr(area)}"><img src="${escapeAttr(img)}" alt="" loading="lazy"><span class="area-card-content"><strong>${escapeHtml(area)}</strong><span>${count} ${escapeHtml(count===1?i18n[state.lang].eventSingular:i18n[state.lang].events)}</span></span></button>`;}).join("");
    document.querySelectorAll("[data-open]").forEach(b=>b.addEventListener("click",()=>openEvent(b.dataset.open)));document.querySelectorAll(".area-card").forEach(b=>b.addEventListener("click",()=>{$("#areaFilter").value=b.dataset.area;renderGrid();$("#discover").scrollIntoView({behavior:"smooth",block:"start"});}));document.querySelectorAll("#featuredGrid img,#weekendGrid img").forEach(img=>img.addEventListener("error",()=>{img.src=fallbackImage;}));
  }

  function renderEventCard(e){const dd=dateOnly(e.startDate),day=String(dd.getUTCDate()).padStart(2,"0"),mon=new Intl.DateTimeFormat(locale(),{month:"short",timeZone:"UTC"}).format(dd);return `<article class="event-card"><div class="event-image-wrap"><img class="event-image" src="${escapeAttr(imageFor(e))}" alt="${escapeAttr(eventName(e))}" loading="lazy"><div class="image-shade"></div><div class="date-chip"><div class="day">${day}</div><div class="mon">${escapeHtml(mon)}</div></div><div class="badges card-badges">${badge(e)}</div></div><div class="card-body"><div class="category">${escapeHtml(categoryLabel(e.category))}</div><h3>${escapeHtml(eventName(e))}</h3><p class="meta"><strong>${escapeHtml(e.municipality||"")}</strong>${e.venue&&e.venue!==e.municipality?` · ${escapeHtml(e.venue)}`:""}<br>${fmtRange(e.startDate,e.endDate)}${e.startTime?` · ${escapeHtml(e.startTime)}`:""}</p><p class="desc">${escapeHtml(eventDescription(e))}</p><div class="card-actions"><span class="source-mini">${escapeHtml(e.source||"")}</span><button type="button" class="details-btn" data-id="${escapeAttr(e.id)}">${escapeHtml(i18n[state.lang].details)} →</button></div></div></article>`;}
  function renderLongCard(e){return `<article class="long-event-card"><div class="long-event-image"><img src="${escapeAttr(imageFor(e))}" alt="${escapeAttr(eventName(e))}" loading="lazy"></div><div class="long-event-body"><div class="category">${escapeHtml(categoryLabel(e.category))}</div><h3>${escapeHtml(eventName(e))}</h3><p class="meta"><strong>${escapeHtml(e.municipality||"")}</strong> · ${fmtRange(e.startDate,e.endDate)}</p><p class="desc">${escapeHtml(eventDescription(e))}</p><div class="long-event-actions"><span class="longterm-tag">${escapeHtml(i18n[state.lang].longTag)}</span><button type="button" class="details-btn" data-id="${escapeAttr(e.id)}">${escapeHtml(i18n[state.lang].details)} →</button></div></div></article>`;}
  function renderGrid(){
    const all=getFiltered(),short=all.filter(e=>!isLongRunning(e)),long=all.filter(isLongRunning),grid=$("#eventsGrid"),longGrid=$("#longTermGrid"),from=$("#fromDate").value||TODAY,to=$("#toDate").value||addMonths12(TODAY);
    $("#rangeLabel").textContent=fmtRange(from,to);$("#emptyState").hidden=all.length>0;
    grid.innerHTML=short.length?short.map(renderEventCard).join(""):`<div class="short-list-empty">${escapeHtml(i18n[state.lang].noShort)}</div>`;
    $("#longTermSection").hidden=long.length===0;longGrid.innerHTML=long.map(renderLongCard).join("");
    document.querySelectorAll("#eventsGrid img,#longTermGrid img").forEach(img=>img.addEventListener("error",()=>{img.src=fallbackImage;}));document.querySelectorAll("#eventsGrid .details-btn,#longTermGrid .details-btn").forEach(b=>b.addEventListener("click",()=>openEvent(b.dataset.id)));
  }
  function openEvent(id){
    const e=state.events.find(x=>x.id===id);if(!e)return;$("#dialogBody").innerHTML=`<div class="detail-hero"><img src="${escapeAttr(imageFor(e))}" alt="${escapeAttr(eventName(e))}"></div><div class="detail-content"><div class="detail-kicker">${escapeHtml(categoryLabel(e.category))} · ${escapeHtml(e.area||"")}</div><h2>${escapeHtml(eventName(e))}</h2><div class="badges">${badge(e)}</div><p>${escapeHtml(eventDescription(e))}</p><div class="detail-grid">${detail(i18n[state.lang].date,fmtRange(e.startDate,e.endDate))}${detail(i18n[state.lang].time,e.startTime||"—")}${detail(i18n[state.lang].location,e.municipality||"—")}${detail(i18n[state.lang].venue,e.venue||"—")}${detail(i18n[state.lang].organizer,e.organizer||"—")}${detail(i18n[state.lang].admission,e.price||"—")}${detail(i18n[state.lang].source,e.source||"—")}${detail(i18n[state.lang].verified,e.verified?fmtDate(e.verified):"—")}</div>${e.officialUrl?`<a class="official-link" href="${escapeAttr(e.officialUrl)}" target="_blank" rel="noopener noreferrer">${escapeHtml(i18n[state.lang].official)} ↗</a>`:""}</div>`;const im=$("#dialogBody .detail-hero img");im?.addEventListener("error",()=>{im.src=fallbackImage;});$("#eventDialog").showModal();
  }
  function statusSymbol(status){return status==="NEW"?"+":status==="UPDATED"?"↻":status==="CONFIRMED"?"✓":status==="CANCELLED"?"×":"•";}
  function detail(label,value){return `<div class="detail-item"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`;}
  function escapeHtml(s){return String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}[c]));}
  function escapeAttr(s){return escapeHtml(s).replace(/`/g,"&#096;");}
  load();
})();
