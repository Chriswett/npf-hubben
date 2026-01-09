# plans.md
**Projekt:** Samarbets- och analysplattform för NPF-föräldrar  
**Version:** v1.1  
**Datum:** 2026-01-08  
**Status:** Konsoliderad genomförandeplan (MVP → utbyggnad)

---

## 1. Syfte med plans.md

Detta dokument beskriver:
- hur projektet ska **byggas stegvis**
- vilka **medvetna avgränsningar** som gäller i MVP
- hur arbetet kan **automatiseras och agent-drivas**
- hur kvalitet, säkerhet och integritet säkerställs under resans gång

`plans.md` är avsedd att fungera som:
- instruktion till utvecklare / Codex-agent
- gemensam referens för prioriteringar
- beslutslogg på hög nivå

---

## 2. Övergripande målbild

Bygga en webbaserad plattform som:

- samlar in enkätdata från NPF-föräldrar på ett tryggt sätt
- anonymiserar och aggregerar svar
- genererar rapporter, infographics och kommunanalyser
- möjliggör frivillig nätverkskoppling mellan föräldrar
- publicerar resultat publikt på ett kontrollerat sätt

**Kärnprinciper**
- Låg tröskel för föräldrar
- Hög integritet och tydliga skyddsräcken
- Aggregering och small-n-maskning som default
- Analytiker i kontroll över publicering

---

## 3. Roller (operativt perspektiv)

- **Allmänheten**: läser publika rapporter och nyheter
- **Parent**: registrerar sig, svarar på enkäter, läser rapporter, opt-in nätverk
- **Analyst**: skapar enkäter, rapportmallar, analyser, publicerar
- **Admin**: roller, moderation, radering, audit

Roller och åtkomst styrs enligt `architecture.md` och `security.md`.

---

## 4. MVP-omfång (vad som ska byggas först)

### 4.1 Ingår i MVP

**Enkäter**
- Skapa enkäter med flera frågetyper
- Basblock (visas en gång per användare)
- Feedback efter avsnitt (default)
- Enkät kan besvaras löpande över tid

**Analys & rapporter**
- Aggregering per enkät
- Rapportmallar kopplade till enkät
- Kommunparameter + min_responses-logik
- “X”-maskning och banner
- WYSIWYG-preview
- Reversibel publicering + redirect

**Publicering**
- Publik rapportsida (SEO-indexerbar)
- Rapportbibliotek med filter/sök
- Nyhetssida (enkel CMS-funktion)

**Nätverk**
- Identifiera liknande situationer (grov nivå)
- Opt-in per förälder
- Introduktionsmail (plattformen släpper sedan ansvaret)

**Security & privacy**
- Samtycke (stegvis)
- Anonymisering
- Fritext-flagga + redaktion
- RBAC
- Loggpolicy, CSP, rate limiting

---

### 4.2 Medvetna avgränsningar i MVP

- Ingen mobilapp (endast webb)
- Ingen avancerad permissionsmodell (enkel RBAC)
- Ingen MFA i MVP
- Ingen real-time-uppdatering (batch/incrementell räcker)
- Ingen fullständig DPIA-automation (manuellt ansvar)

---

## 5. Iterativ byggordning (rekommenderad)

### Steg 0 – Grund & CI
- Repo-struktur
- GitHub Actions (PR-gate + main-gate)
- Postgres i CI
- Test harness (minimal)
- Lint + unit tests

### Steg 1 – Kärnmodell
- User / Consent / Roles
- Survey + Response
- Aggregation engine
- Small-n-maskning

### Steg 2 – Enkätflöde (Parent)
- Registrering + verifiering
- Basblock + skip-logik
- Avsnittsfeedback
- Response ingest

### Steg 3 – Analytikerverktyg
- Skapa enkäter
- Skapa rapportmallar
- Preview (deterministisk rendering)
- Publicering / ersättning

### Steg 4 – Publik läsning
- Rapportvy (publik)
- Kommunval
- Maskning + banner
- SEO-vänliga URL:er

### Steg 5 – Nätverk
- Matchningslogik
- Opt-in-flöde
- Introduktionsmail (outbox)

### Steg 6 – Moderation & admin
- Fritext-flagga
- Redaktion / kuratering
- Rolladmin
- Audit-logg

---

## 6. Kvalitet & verifiering

- **Funktionella krav** verifieras via `testcases.md`
- **Icke-funktionella krav (NFR)** ägs av `testplan.md`
- CI-gates:
  - PR: lint + unit + snabb integration
  - Main: full integration + Playwright + security/privacy checks

Ingen feature anses klar utan:
- uppdaterade testfall
- passerande CI

---

## 7. Agent-/Codex-arbetsmodell

Projektet är avsett att fungera väl med:
- Codex / agent som implementerar stegvis
- tydliga invariants i `architecture.md` och `security.md`
- verifierbarhet via `testplan.md`

**Arbetsloop**
1. Välj user story
2. Läs arkitektur + security-invariants
3. Implementera minsta fungerande lösning
4. Lägg/uppdatera testfall
5. Passera PR-gate
6. Merge → main-gate

---

## 8. Förväntade framtida utökningar (ej MVP)

- Fler användargrupper (t.ex. skolpersonal/visselblåsare)
- Mer avancerade rapportvillkor
- Mer granular matchning
- Prestanda-NFR
- Formell DPIA-dokumentation

---

## 9. Sammanfattning

Denna plan:
- prioriterar trygghet och användbarhet
- håller MVP smalt men komplett
- skapar god grund för tillväxt
- är anpassad för automatiserad utveckling och test

Planen är avsiktligt pragmatisk – funktion först, utan att kompromissa
med integritet eller kvalitet.
