// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { readFileSync } from 'node:fs';
import { calculateKpis, importProfiles, parseCSV } from '../public/domain.js';

describe('parcours exécutés dans le DOM', () => {
  beforeEach(async () => {
    vi.resetModules();
    localStorage.clear();
    document.documentElement.innerHTML=readFileSync('index.html','utf8');
    await import('../public/app.js');
  });
  const saved=()=>JSON.parse(localStorage.getItem('eigsi-alumni-state'));
  it('rend accessibles les actions des boutons malgré le module ES', () => {
    expect(typeof window.validateProfile).toBe('function');
    window.go('validation');
    expect(document.querySelector('#validationList').textContent).toContain('Sarah El Mansouri');
    window.validateProfile(3);
    expect(saved().profiles.find(p=>p.id===3).status).toBe('valid');
    expect(saved().profiles.find(p=>p.id===3).review.decision).toBe('APPROVED');
  });
  it('bloque les doublons et permet un examen explicite', () => {
    window.validateProfile(4);
    expect(document.querySelector('#toast').textContent).toContain('doublon');
    window.examineDuplicate(4);
    expect(document.querySelector('#modalRoot button.primary').getAttribute('onclick')).toBe('resolveDuplicate(4)');
    window.resolveDuplicate(4);
    window.validateProfile(4);
    expect(saved().profiles.find(p=>p.id===4).status).toBe('valid');
  });
  it('retire immédiatement un profil sans consentement et refuse sa publication', () => {
    window.revokeConsent();
    window.validateProfile(1);
    expect(document.querySelector('#toast').textContent).toContain('consentement');
    window.go('directory');
    expect(document.querySelector('#directoryList').textContent).not.toContain('Lina Benali');
  });
  it('conserve le motif de correction et neutralise le HTML saisi', () => {
    window.requestChange(3);
    document.querySelector('#reason').value='<img src=x onerror=alert(1)>';
    window.confirmChange(3);
    expect(saved().profiles.find(p=>p.id===3).review.comment).toContain('<img');
    window.go('audit');
    expect(document.querySelector('#app img')).toBeNull();
    expect(document.querySelector('#app').textContent).toContain('<img');
  });
  it('restreint les exports nominatifs dans la vue Direction', () => {
    const select=document.querySelector('#roleSelect');
    select.value='direction';select.dispatchEvent(new Event('change'));
    window.exportCSV();
    expect(document.querySelector('#toast').textContent).toContain('réservé');
  });
  it('affiche un bouton de doublon avec un identifiant interpolé', () => {
    window.go('validation');
    expect(document.querySelector('button.duplicate').getAttribute('onclick')).toBe('examineDuplicate(4)');
  });
  it('interdit à la Direction de modifier une validation', () => {
    const select=document.querySelector('#roleSelect');
    select.value='direction';select.dispatchEvent(new Event('change'));
    window.validateProfile(3);
    expect(saved().profiles.find(p=>p.id===3).status).toBe('pending');
    expect(document.querySelector('#toast').textContent).toContain('réservée');
  });
});

describe('CSV et KPI', () => {
  it('lit séparateurs, guillemets et retours ligne dans les valeurs', () => {
    expect(parseCSV('name;company\r\n"Amal";"Société; ""Data""\nParis"'))
      .toEqual([['name','company'],['Amal','Société; "Data"\nParis']]);
  });
  it('signale les doublons et ne fabrique pas de consentement', () => {
    const csv='name;email;studentId;promo;track;job;city;country\nAmal;a@example.fr;E001;2022;Data;Dev;Paris;France\nAutre;A@example.fr;E002;2022;Data;Dev;Paris;France';
    const result=importProfiles(csv,[]);
    expect(result.profiles).toHaveLength(1);
    expect(result.profiles[0].consent).toBe(false);
    expect(result.errors[0]).toContain('Ligne 3');
  });
  it('calcule la fraîcheur au jour du contrôle et gère une population vide', () => {
    expect(calculateKpis([]).coverage).toBe(0);
    const profiles=[{status:'valid',consent:true,updated:'2025-10-15'}];
    expect(calculateKpis(profiles,new Date('2026-10-22')).fresh).toBe(0);
    expect(calculateKpis(profiles,new Date('2026-10-01')).fresh).toBe(100);
  });
  it('calcule la médiane à partir des décisions datées', () => {
    const profiles=[1,3].map(n=>({status:'valid',consent:true,submittedAt:'2026-10-01',review:{decision:'APPROVED',reviewedAt:`2026-10-0${n+1}`}}));
    expect(calculateKpis(profiles).median).toBe('2 j');
  });
});
