export function escapeHTML(value) {
  return String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

export function isFresh(value, now = new Date()) {
  const cutoff = new Date(now);
  cutoff.setFullYear(cutoff.getFullYear() - 1);
  const date = new Date(value);
  return date >= cutoff && date <= now;
}

export function calculateKpis(profiles, now = new Date()) {
  const validated = profiles.filter(p => p.status === 'valid' && p.consent);
  const percent = (n, d) => d ? Math.round(n / d * 100) : 0;
  const delays = validated.filter(p => p.submittedAt && p.review?.decision === 'APPROVED')
    .map(p => (new Date(p.review.reviewedAt) - new Date(p.submittedAt)) / 86400000)
    .filter(n => Number.isFinite(n) && n >= 0).sort((a,b) => a-b);
  const middle = Math.floor(delays.length / 2);
  const median = delays.length ? (delays.length % 2 ? delays[middle] : (delays[middle-1]+delays[middle])/2) : null;
  return {
    coverage: percent(validated.length, profiles.length),
    complete: percent(validated.filter(p => ['name','email','studentId','promo','track','job','city','country'].every(k => String(p[k] ?? '').trim())).length, validated.length),
    fresh: percent(validated.filter(p => isFresh(p.updated, now)).length, validated.length),
    median: median === null ? 'Non mesuré' : `${median.toLocaleString('fr-FR', {maximumFractionDigits:1})} j`,
  };
}

// Handles RFC 4180 quoting, escaped quotes, semicolons and multiline fields.
export function parseCSV(text) {
  text = text.replace(/^\uFEFF/, '');
  const delimiter = text.split(/\r?\n/,1)[0].includes(';') ? ';' : ',';
  const rows = []; let row = [], field = '', quoted = false;
  for (let i=0; i<text.length; i++) {
    const c=text[i];
    if(c==='"') {
      if(quoted && text[i+1]==='"') { field+='"'; i++; }
      else if(quoted) quoted=false;
      else if(!field) quoted=true;
      else throw new Error('Guillemet inattendu dans le CSV');
    } else if(c===delimiter && !quoted) { row.push(field); field=''; }
    else if((c==='\n'||c==='\r') && !quoted) {
      if(c==='\r' && text[i+1]==='\n') i++;
      row.push(field); if(row.some(Boolean)) rows.push(row); row=[]; field='';
    } else field+=c;
  }
  if(quoted) throw new Error('Guillemets non fermés dans le CSV');
  row.push(field); if(row.some(Boolean)) rows.push(row);
  return rows;
}

export function importProfiles(text, existing) {
  const rows = parseCSV(text);
  if(rows.length < 2) throw new Error('Le fichier CSV est vide');
  const headers = rows.shift().map(s => s.trim());
  const required = ['name','email','studentId','promo','track','job','city','country'];
  if(!required.every(k => headers.includes(k))) throw new Error(`Colonnes obligatoires : ${required.join(', ')}`);
  const profiles=[], errors=[];
  rows.forEach((row,index) => {
    const p=Object.fromEntries(headers.map((key,i) => [key, (row[i]??'').trim()]));
    const all=[...existing,...profiles];
    let error='';
    if(row.length!==headers.length) error='Nombre de colonnes incorrect';
    else if(required.some(k=>!p[k])) error='Champ obligatoire manquant';
    else if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(p.email)) error='E-mail invalide';
    else if(!/^\d{4}$/.test(p.promo)||+p.promo<1950||+p.promo>2100) error='Promotion invalide';
    else if(all.some(x=>x.email.toLowerCase()===p.email.toLowerCase()||x.studentId.toLowerCase()===p.studentId.toLowerCase())) error='E-mail ou matricule déjà présent';
    if(error) errors.push(`Ligne ${index+2} : ${error}`);
    else profiles.push({...p,id:Date.now()+index,status:'pending',updated:new Date().toISOString(),submittedAt:new Date().toISOString(),mentor:false,completeness:100,consent:false});
  });
  return {profiles,errors};
}
