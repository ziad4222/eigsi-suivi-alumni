import {escapeHTML as esc, parseCSV} from './domain.js';

const app=document.querySelector('#app');
const nav=document.querySelector('#mainNav');
const roles={ALUMNI:'Alumni',SERVICE:'Service Alumni',ADMIN:'Administrateur',DIRECTION:'Direction'};
const statuses={DRAFT:'À compléter',PENDING:'À valider',VALIDATED:'Validé',REJECTED:'Rejeté'};
let user=null, view='directory', generation=0;
let currentFilters=new URLSearchParams();

export async function request(path, options={}) {
  const response=await fetch('/api'+path,{credentials:'same-origin',...options,
    headers:{'Content-Type':'application/json',...options.headers}});
  if(!response.ok){
    let message='Service indisponible';
    try {const body=await response.json();message=typeof body.detail==='string'?body.detail:'Vérifiez les champs du formulaire';} catch { /* Proxy errors can be plain text. */ }
    const error=new Error(message);error.status=response.status;throw error;
  }
  return response.status===204?null:response.json();
}
const send=(path,body,method='POST')=>request(path,{method,body:JSON.stringify(body)});
function notice(message){const t=document.querySelector('#toast');t.textContent=message;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),4500);}
function fail(error){notice(error.message || 'Connexion au serveur impossible');}
function button(text,action,id=''){return `<button class="secondary" data-action="${action}" data-id="${esc(id)}">${text}</button>`;}
function header(title){document.querySelector('#pageTitle').textContent=title;document.querySelector('#pageEyebrow').textContent=user?roles[user.role]:'ESPACE EIGSI';}
function loginScreen(message='') {
  user=null;nav.innerHTML='';header('Connexion au réseau Alumni');
  document.querySelector('#roleSelect').disabled=true;
  document.querySelector('#resetButton').hidden=true;
  document.querySelector('.privacy small').textContent='Connexion sécurisée · données serveur';
  app.innerHTML=`<article class="card" style="max-width:520px;margin:auto"><h2>Bienvenue sur EIGSI Alumni</h2><p>Connectez-vous pour retrouver votre profil et le réseau.</p><p role="alert" id="authError">${esc(message)}</p><form id="authForm" class="grid"><div class="field"><label for="email">E-mail</label><input id="email" name="email" type="email" autocomplete="username" required></div><div class="field"><label for="password">Mot de passe (10 caractères minimum)</label><input id="password" name="password" type="password" minlength="10" maxlength="128" autocomplete="current-password" required></div><button class="primary" type="submit">Se connecter</button><button class="secondary" type="submit" name="register" value="yes">Créer mon compte Alumni</button></form><p>Les comptes du Service Alumni, de la Direction et de l’Administrateur sont créés par l’administrateur du serveur.</p></article>`;
  document.querySelector('#authForm').onsubmit=async event=>{
    event.preventDefault();const form=event.currentTarget;const submit=event.submitter;
    form.querySelectorAll('button').forEach(b=>b.disabled=true);
    try{
      const values=Object.fromEntries(new FormData(form));
      user=await send(submit?.name==='register'?'/auth/register':'/auth/login',values);
      setup();await render();
    }catch(error){document.querySelector('#authError').textContent=error.message || 'Le serveur API est inaccessible';}
    finally{form.querySelectorAll('button').forEach(b=>b.disabled=false);}
  };
}
function setup(){
  document.querySelector('#resetButton').hidden=false;
  document.querySelector('#resetButton').textContent='Se déconnecter';
  const select=document.querySelector('#roleSelect');select.value=user.role.toLowerCase();select.disabled=true;
  document.querySelector('.avatar').textContent=user.email.slice(0,2).toUpperCase();
  document.querySelector('.privacy small').textContent='Données enregistrées en base';
  view=user.role==='ALUMNI'?'profile':'dashboard';
  const items=[...(user.role==='ALUMNI'?[['profile','Mon profil']]:[['dashboard','Pilotage']]),['directory','Annuaire'],
    ...(['ADMIN','SERVICE'].includes(user.role)?[['validation','Validations'],['campaigns','Campagnes'],['audit','Journal d’activité']]:[]),
    ...(user.role==='ADMIN'?[['import','Importer CSV']]:[])];
  nav.innerHTML=items.map(([id,label])=>`<button data-view="${id}">${label}</button>`).join('');
  nav.querySelectorAll('button').forEach(b=>b.onclick=()=>{view=b.dataset.view;currentFilters=new URLSearchParams();render();});
}
async function render(){
  const current=++generation;
  app.innerHTML='<article class="card">Chargement des données…</article>';
  document.querySelector('#sidebar').classList.remove('open');
  nav.querySelectorAll('button').forEach(b=>b.classList.toggle('active',b.dataset.view===view));
  try{
    const painters={profile, dashboard, directory, validation, campaigns, audit, import:importScreen};
    const paint=await painters[view]();
    if(current!==generation)return;
    paint();
  }catch(error){
    if(current!==generation)return;
    if(error.status===401){loginScreen('Votre session a expiré. Reconnectez-vous.');return;}
    app.innerHTML=`<article class="card"><h2>Chargement impossible</h2><p role="alert">${esc(error.message)}</p>${button('Réessayer','retry')}</article>`;
  }
}
const profileFields=[['full_name','Nom complet'],['student_number','Matricule'],['graduation_year','Promotion'],['program','Filière'],['employment_status','Métier / situation'],['company','Entreprise'],['city','Ville'],['country','Pays'],['sector','Domaine']];
async function profile(){
  const p=await request('/me/profile')||{};
  return ()=>{
    header('Mon profil');
    app.innerHTML=`<article class="card"><h2>Informations professionnelles</h2><p>${esc(user.email)} · ${esc(statuses[p.status]||'Nouveau profil')}</p>${p.review?.comment?`<p>Retour du Service Alumni : ${esc(p.review.comment)}</p>`:''}<form id="profileForm" class="grid form-grid">${profileFields.map(([key,label])=>`<div class="field"><label for="${key}">${label}${['company','sector'].includes(key)?'':' *'}</label><input id="${key}" name="${key}" ${key==='graduation_year'?'type="number" min="1950" max="2100"':'maxlength="160"'} ${['company','sector'].includes(key)?'':'required'} value="${esc(p[key]??'')}"></div>`).join('')}<label class="consent full"><input name="mentor" type="checkbox" ${p.mentor?'checked':''}>Je suis disponible pour du mentorat.</label><label class="consent full"><input name="consent" type="checkbox" ${p.consent?'checked':''}>J’accepte l’utilisation de mes données pour le suivi Alumni et la publication de mes informations professionnelles dans l’annuaire (politique v1.0). Ce consentement est révocable.</label><p class="full">Sans consentement, le profil reste en brouillon et n’est pas publié.</p><button class="primary" type="submit">Enregistrer mon profil</button></form>${p.consent?button('Révoquer mon consentement','revoke'):''}</article>`;
    document.querySelector('#profileForm').onsubmit=async e=>{
      e.preventDefault();const fd=new FormData(e.currentTarget);const body=Object.fromEntries(fd);
      body.graduation_year=Number(body.graduation_year);body.mentor=fd.has('mentor');body.consent=fd.has('consent');
      const b=e.currentTarget.querySelector('button');b.disabled=true;
      try{await send('/me/profile',body,'PUT');notice(body.consent?'Profil soumis pour validation':'Brouillon enregistré');await render();}catch(error){fail(error);b.disabled=false;}
    };
  };
}
async function dashboard(){
  const data=await request('/dashboard');
  const percent=(n,d)=>d?Math.round(n/d*100)+' %':'0 %';
  return ()=>{header('Pilotage du réseau');app.innerHTML=`<div class="grid metrics">${[
    [percent(data.validated_count,data.alumni_count),'Validés / fiches recensées'],
    [percent(data.complete_count,data.validated_count),'Profils validés complets'],
    [percent(data.fresh_count,data.validated_count),'Validés à jour (< 365 jours)'],
    [data.median_days===null?'Non mesuré':data.median_days.toLocaleString('fr-FR',{maximumFractionDigits:2})+' j','Délai médian (jours calendaires)'],
  ].map(([value,label])=>`<article class="metric"><b>${value}</b><p>${label}</p></article>`).join('')}</div><article class="card" style="margin-top:20px"><h2>Répartition par promotion</h2><p>Actualisé le ${new Date(data.updated_at).toLocaleString('fr-FR')} · ${data.pending_count} profil(s) à valider.</p>${Object.entries(data.promotions).map(([year,count])=>`<div class="progress-top"><span>${esc(year)}</span><b>${count}</b></div>`).join('')||'<p>Aucun profil recensé.</p>'}</article>`;};
}
function filterForm(){return `<form id="filters" class="toolbar"><input name="q" placeholder="Nom, entreprise, métier ou ville" value="${esc(currentFilters.get('q')||'')}"><input name="graduation_year" type="number" placeholder="Promotion" value="${esc(currentFilters.get('graduation_year')||'')}"><input name="program" placeholder="Filière exacte" value="${esc(currentFilters.get('program')||'')}"><input name="country" placeholder="Pays exact" value="${esc(currentFilters.get('country')||'')}"><button class="primary">Rechercher</button></form>`;}
function bindFilters(){document.querySelector('#filters').onsubmit=e=>{e.preventDefault();currentFilters=new URLSearchParams([...new FormData(e.currentTarget)].filter(([,v])=>v.trim()));render();};}
async function directory(){
  const rows=await request('/directory?'+currentFilters);
  return ()=>{header('Annuaire des Alumni');app.innerHTML=filterForm()+`<p>${rows.length} profil(s) publié(s)</p><div class="grid directory">${rows.map(p=>`<article class="profile-card"><h3>${esc(p.full_name)}</h3><p>Promotion ${p.graduation_year} · ${esc(p.program)}</p><p><b>${esc(p.employment_status)}</b><br>${esc(p.company)} · ${esc(p.city)}, ${esc(p.country)}</p><span class="chip">${esc(p.sector)}</span>${p.mentor?'<span class="chip">Disponible mentorat</span>':''}</article>`).join('')||'<p>Aucun résultat.</p>'}</div>`;bindFilters();};
}
async function validation(){
  const rows=await request('/profiles?'+currentFilters);
  return ()=>{header('Validation des profils');app.innerHTML=filterForm()+`<article class="card"><p>${rows.length} fiche(s). L’examen de l’unicité doit précéder toute validation.</p>${user.role==='ADMIN'?button('Exporter la sélection CSV','export'):''}<div class="table-wrap"><table><thead><tr><th>Alumni</th><th>Promotion / filière</th><th>Situation</th><th>Statut</th><th>Actions</th></tr></thead><tbody>${rows.map(p=>`<tr><td>${esc(p.full_name)}<small style="display:block">${esc(p.email)}<br>${esc(p.student_number)}</small></td><td>${p.graduation_year}<br>${esc(p.program)}</td><td>${esc(p.employment_status)}<br>${esc(p.company)}</td><td>${esc(statuses[p.status])}<br>${p.consent?'Consentement actif':'Sans consentement'}${p.review?.comment?`<br>${esc(p.review.comment)}`:''}</td><td><div class="row-actions">${!p.duplicate_checked?button('Examiner l’unicité','duplicate',p.id):'<span class="badge valid">Unicité examinée</span>'}${button('Valider','approve',p.id)}${button('Corriger','correct',p.id)}${button('Rejeter','reject',p.id)}</div></td></tr>`).join('')}</tbody></table></div></article>`;bindFilters();};
}
async function audit(){
  const rows=await request('/audit');
  return ()=>{header('Journal d’activité');app.innerHTML=`<article class="card"><h2>Actions enregistrées sur le serveur</h2><div class="activity">${rows.map(r=>`<div><b>${esc(r.action)}</b><p>${new Date(r.created_at+'Z').toLocaleString('fr-FR')} · Auteur ${esc(r.actor_user_id)} · Fiche ${esc(r.entity_id)}</p></div>`).join('')||'<p>Aucune action.</p>'}</div></article>`;};
}
async function campaigns(){
  const rows=await request('/campaigns');
  return ()=>{header('Campagnes de relance');app.innerHTML=`<article class="card"><h2>Préparer la relance annuelle</h2><p>La cible comprend les profils non confirmés depuis plus de 365 jours. Aucun e-mail n’est envoyé. Le suivi compte les profils confirmés après préparation.</p><form id="campaignForm" class="grid"><div class="field"><label for="campaignName">Nom</label><input id="campaignName" name="name" required minlength="2" maxlength="160"></div><div class="field"><label for="campaignMessage">Message</label><textarea id="campaignMessage" name="message" required minlength="10" maxlength="4000">Bonjour, merci de confirmer ou mettre à jour votre profil Alumni.</textarea></div><button class="primary">Préparer la campagne</button></form></article><article class="card" style="margin-top:20px"><h2>Campagnes préparées</h2>${rows.map(c=>`<div class="campaign"><div><h3>${esc(c.name)}</h3><p>${c.recipient_count} destinataire(s), ${c.responses} profil(s) confirmé(s) depuis la préparation.</p></div><span class="badge pending">Brouillon</span></div>`).join('')||'<p>Aucune campagne.</p>'}</article>`;document.querySelector('#campaignForm').onsubmit=async e=>{e.preventDefault();const b=e.currentTarget.querySelector('button');b.disabled=true;try{await send('/campaigns',Object.fromEntries(new FormData(e.currentTarget)));notice('Campagne préparée en base');await render();}catch(error){fail(error);b.disabled=false;}};};
}
async function importScreen(){
  return ()=>{header('Importer des profils');app.innerHTML=`<article class="card"><h2>Import CSV</h2><p>Utilisez le format de l’export : full_name, email, student_number, graduation_year, program, employment_status, company, city, country, sector. Les comptes importés restent verrouillés jusqu’à une invitation administrateur ; aucun consentement n’est présumé.</p><input id="importFile" type="file" accept=".csv,text/csv"><div id="preview"></div></article>`;
    document.querySelector('#importFile').onchange=async e=>{
      try{
        const file=e.target.files[0];if(!file)return;
        const rows=parseCSV(await file.text());if(rows.length<2)throw new Error('Le CSV est vide');
        const headers=rows.shift().map(v=>v.trim());
        const required=profileFields.filter(([k])=>!['company','sector'].includes(k)).map(([k])=>k).concat('email');
        if(required.some(k=>!headers.includes(k)))throw new Error('Colonnes obligatoires : '+required.join(', '));
        const payloads=rows.map(row=>({...Object.fromEntries(headers.map((k,i)=>[k,row[i]?.trim()||''])),graduation_year:Number(row[headers.indexOf('graduation_year')]),mentor:false,consent:false}));
        document.querySelector('#preview').innerHTML=`<p>${payloads.length} ligne(s) à contrôler et importer.</p><ul>${payloads.map(p=>`<li>${esc(p.full_name)} · ${esc(p.email)}</li>`).join('')}</ul><button id="confirmImport" class="primary">Confirmer l’import sans consentement</button><div id="importResults" role="status"></div>`;
        document.querySelector('#confirmImport').onclick=async event=>{
          event.currentTarget.disabled=true;const results=[];
          for(const [index,p] of payloads.entries()){try{await send('/profiles',p);results.push(`Ligne ${index+2} : importée`);}catch(error){results.push(`Ligne ${index+2} : ${error.message}`);}}
          document.querySelector('#importResults').innerHTML=results.map(r=>`<p>${esc(r)}</p>`).join('');
        };
      }catch(error){fail(error);}
    };
  };
}
function decisionDialog(id,decision){
  const root=document.querySelector('#modalRoot');
  root.innerHTML=`<div class="modal-backdrop"><form id="reviewForm" class="modal"><h2>${decision==='CORRECTION'?'Demander une correction':'Rejeter la fiche'}</h2><div class="field"><label for="comment">Motif obligatoire</label><textarea id="comment" name="comment" required maxlength="2000"></textarea></div><div class="modal-actions">${button('Annuler','close')}<button class="primary">Enregistrer la décision</button></div></form></div>`;
  document.querySelector('#reviewForm').onsubmit=async e=>{e.preventDefault();try{await send(`/profiles/${id}/review`,{decision,comment:new FormData(e.currentTarget).get('comment')});root.innerHTML='';await render();}catch(error){fail(error);}};
}
document.addEventListener('click',async event=>{
  const b=event.target.closest('[data-action]');if(!b)return;
  const {action,id}=b.dataset;b.disabled=true;
  try{
    if(action==='close'){document.querySelector('#modalRoot').innerHTML='';return;}
    if(action==='retry'){await render();return;}
    if(action==='correct'||action==='reject'){decisionDialog(id,action==='correct'?'CORRECTION':'REJECTED');return;}
    if(action==='duplicate'){
      document.querySelector('#modalRoot').innerHTML=`<div class="modal-backdrop"><div class="modal"><h2>Examen de l’unicité</h2><p>Comparez le nom, l’e-mail, le matricule et la promotion aux autres fiches. Les doublons exacts d’e-mail et de matricule sont bloqués en base ; aucune fusion automatique n’est effectuée.</p><div class="modal-actions">${button('Annuler','close')}${button('Confirmer l’examen','checked',id)}</div></div></div>`;return;
    }
    if(action==='checked'){await send(`/profiles/${id}/duplicates/checked`,{});document.querySelector('#modalRoot').innerHTML='';}
    if(action==='approve')await send(`/profiles/${id}/review`,{decision:'APPROVED',comment:''});
    if(action==='revoke')await send('/me/consent/revoke',{});
    if(action==='export'){
      const response=await fetch('/api/export?'+currentFilters,{credentials:'same-origin'});
      if(!response.ok)throw new Error('Export refusé');
      const href=URL.createObjectURL(await response.blob());const link=document.createElement('a');link.href=href;link.download='alumni-eigsi.csv';link.click();setTimeout(()=>URL.revokeObjectURL(href),1000);return;
    }
    await render();
  }catch(error){fail(error);}finally{b.disabled=false;}
});
document.querySelector('#resetButton').onclick=async()=>{try{await send('/auth/logout',{});generation++;loginScreen();}catch(error){fail(error);}};
document.querySelector('#menuButton').onclick=()=>document.querySelector('#sidebar').classList.toggle('open');
try{user=await request('/auth/me');setup();await render();}catch(error){loginScreen(error.status===401?'':'Le serveur API est inaccessible. Lancez le backend puis réessayez.');}
