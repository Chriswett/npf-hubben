# testplan.md
**Projekt:** Samarbets- och analysplattform för NPF-föräldrar  
**Version:** v1.1  
**Datum:** 2026-01-08  
**Status:** Fastställd – Teststrategi, NFR och CI-gates

---

## 1. Syfte

Detta dokument är **source of truth** för:
- hur kvalitet, säkerhet och integritet verifieras
- vilka icke-funktionella krav (NFR) som gäller
- hur tester automatiseras i CI
- när kod får mergas och deployeras

`testplan.md` är normativ:  
om något testas här ska det implementeras så att testen passerar.

---

## 2. Globala icke-funktionella krav (NFR)

Dessa krav gäller hela systemet om inget annat anges.
De dupliceras inte i user stories utan verifieras via tester.

### 2.1 Säkerhet & integritet
- Publika sidor och API:er får inte exponera PII eller rådata.
- Endast aggregerade data och fritext enligt reviewstatus får visas publikt.
- Fritext med status **hide** får aldrig exponeras publikt.
- Produktionsloggar får inte innehålla:
  - personuppgifter
  - enkätpayloads
- Följande headers ska vara aktiva:
  - Content-Security-Policy (CSP)
  - X-Frame-Options
- Rate limiting och max antal inloggningsförsök ska vara aktiverat.

### 2.2 Anonymisering & small-n
- Alla kommun- eller urvalsvärden med `n < min_responses` ska maskas (“X”).
- Banner ska visas när small-n-maskning tillämpas.
- Maskning ska ske konsekvent i:
  - UI
  - API-responser
  - exporter (PDF/PNG)

### 2.3 Åtkomst & roller
- Åtkomst styrs via RBAC enligt `architecture.md`.
- Felaktig åtkomst ska resultera i 401/403.
- Otillåten åtkomst ska aldrig “läcka information via felmeddelanden”.

### 2.4 Reproducerbarhet & korrekthet
- Rapport-rendering ska vara deterministisk för givet `data_version_hash`.
- Preview och publicerad rapport ska vara semantiskt identiska (WYSIWYG).
- Publicerad rapport får inte ändras i efterhand (endast ersättas).

### 2.5 Tillgänglighet & UX (MVP-nivå)
- Kärnflöden ska fungera på mobil och desktop:
  - registrering
  - svara på enkät
  - läsa rapport
- UI ska inte kräva långa textförklaringar för att förstå nästa steg.
- Stabil testautomation ska möjliggöras via `data-testid`.

### 2.6 Drift & CI
- Systemet ska kunna köras lokalt och i CI med Postgres.
- Databasmigreringar ska köras automatiskt i CI.
- Tester ska vara deterministiska och fria från tidsberoenden.

---

## 3. Teststrategi (översikt)

### 3.1 Testpyramid (MVP)

1. **Unit tests**
   - affärslogik
   - maskning
   - villkorstexter
   - placeholder-interpolation

2. **Integration tests**
   - API + DB + workers
   - ingest → aggregation → report rendering
   - publicering och redirect

3. **Contract tests**
   - RBAC
   - publika vs skyddade endpoints
   - felkoder och svarsbeteende

4. **E2E (Playwright)**
   - kritiska användarflöden
   - happy path + viktiga edge cases

5. **Security/Privacy tests**
   - small-n
   - PII-skydd
   - headers
   - rate limiting

---

## 4. Testmiljöer och data

### 4.1 Miljöpolicy
- **Production**
  - inga payloads eller PII i loggar
- **Test/CI**
  - endast syntetisk eller anonymiserad testdata
- Verklig användardata får aldrig förekomma i test.

### 4.2 Testdata
- **Default:** syntetisk data via fixtures/factories
- **Komplement:** liten, realistisk anonymiserad dataset för:
  - aggregerings-edge cases
  - rapport-rendering

---

## 5. Minimal test harness (test-only)

Princip: testa via riktiga API:er där möjligt.

Tillåtet i test/CI:
- seed/reset av DB
- mail outbox (för e-postverifiering och introduktionsmail)

Krav:
- hårt avstängt i prod
- skyddat via env-flagga + auth

---

## 6. E-post i test

- I test skrivs mejl till **Outbox-tabell**
- Tester verifierar:
  - mottagare
  - ämne
  - obligatorisk “varför du får detta mail”-text
- Inga riktiga mejl skickas i CI

---

## 7. CI-struktur (GitHub Actions)

### 7.1 PR-gate (snabb)
Blockerar merge vid fel.

Kör:
- lint/format
- unit tests
- snabb integration smoke (API + DB + migrering)

### 7.2 Main-gate (strikt)
Måste passera innan deploy.

Kör:
- full integration test suite
- contract tests
- Playwright E2E
- security/privacy tests
- build artifacts

---

## 8. Playwright (E2E)

Playwright används för:
- kritiska happy paths
- viktiga edge cases (small-n, redirect, publik visning)

Exempel:
- publik rapport kan läsas av allmänheten
- kommunparameter styr vy
- “X”-värden visas vid lågt underlag
- redirect fungerar vid ersättning av rapport

Playwright är **komplement**, inte primär testmetod.

---

## 9. Security & Privacy – maskintestade krav

Automatiserade tester ska verifiera:

- inga PII i publika svar
- small-n-maskning
- RBAC enforcement
- CSP och X-Frame-Options headers
- rate limiting för inloggningsförsök
- loggpolicy i prod-mode
- fritext-reviewstatus respekteras (hide aldrig publikt)

Testfall refereras via `TC-SEC-xx`.

---

## 10. Spårbarhet

- Funktionella krav → `userstories.md`
- Detaljerade testfall → `testcases.md`
- NFR → detta dokument
- CI-gates säkerställer efterlevnad

Ingen story är “klar” utan:
- relevanta testfall
- passerande CI

---

## 11. Definition of Done (testperspektiv)

En feature anses klar när:
- alla relevanta tester passerar
- inga NFR bryts
- testfall är uppdaterade eller tillagda
- CI-gates är gröna

---

## 12. Sammanfattning

Testplanen säkerställer att plattformen:
- fungerar korrekt
- skyddar användare även vid misstag
- kan utvecklas iterativt utan regressionsrisk
- är redo för agent-/Codex-driven utveckling