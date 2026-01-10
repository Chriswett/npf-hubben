# plans-v2.md
**Projekt:** Samarbets- och analysplattform för NPF-föräldrar  
**Version:** v2.0 (ExecPlan-inspirerad)  
**Datum:** 2026-01-09  
**Status:** Levande genomförandeplan (MVP → utbyggnad)

Detta dokument är ett “ExecPlan”-inspirerat PLANS-dokument. Det ska hållas uppdaterat under arbetets gång. Särskilt sektionerna `Progress`, `Surprises & Discoveries`, `Decision Log` och `Outcomes & Retrospective` är obligatoriska och ska uppdateras vid varje stoppunkt.

---

## Purpose / Big Picture

Vi ska bygga en webbaserad plattform där NPF-föräldrar tryggt kan svara på enkäter, få aggregerade insikter via rapporter (inklusive kommunvy med small-n-maskning) och frivilligt kopplas ihop med andra i liknande situation. Analytiker ska kunna komponera enkäter och rapportmallar, publicera rapporter (med versionering och redirect), samt kuratera fritext för att minimera integritetsrisk. Allmänheten ska kunna läsa publicerade rapporter och nyheter.

Efter MVP ska en utomstående person kunna:
1) öppna en publik rapport-URL och läsa rapporten för en vald kommun,
2) se tydlig banner + “X” där underlaget är för litet,
3) registrera sig och svara på en enkät med basblock som bara visas första gången,
4) som analytiker skapa en rapportmall, preview:a WYSIWYG och publicera en ny version som ersätter en tidigare.

---

## Progress

- [x] (2026-01-09) Skapa repo-struktur och lägga in styrdokument (spec.md, architecture.md, security.md, userstories.md, testplan.md, testcases.md).
- [x] (2026-01-09) Sätta upp GitHub Actions: PR-gate + main-gate enligt testplan.md.
- [x] (2026-01-09) Bas-setup backend + migrations + Postgres i CI.
- [x] (2026-01-09) In-memory domänlager, tjänster och testskelett för US/SEC-flöden.
- [x] Implementera Auth (e-postverifiering), RBAC och sessioner.
- [x] Implementera Survey + frågetyper + basblock + svar (en gång per enkät).
- [x] Implementera Aggregation + snapshots + min_responses-maskning.
- [x] Implementera ReportTemplate + rendering + placeholders + villkorstext (MVP).
- [x] Implementera Publishing (visibility, canonical URL, replace→redirect, avpublicering).
- [x] Implementera Moderation: flagga fritext, redaktion/reviewstatus, publika regler per status.
- [x] Implementera Public site: nyheter + rapportbibliotek + rapportläsare (SEO).
- [x] Implementera Network opt-in + matchningsförslag + introduktionsmail via outbox.
- [x] E2E (Playwright) för kritiska flöden + security/privacy tests enligt testcases.md.
- [x] Outcomes & Retrospective: sammanställ MVP-resultat, kända gap och nästa steg.
- [x] (2026-01-10) Milestone 9: Compliance hardening (samtycken, pseudonymisering, immutabla reportversioner, Postgres-migreringar, moderation audit).
- [ ] (2026-01-10) Gap-analys mot arkitektur/security/testplan och uppdatera ExecPlan för åtgärder.
- [ ] (2026-01-10) Förtydliga fritext-reviewflöde (statusar, flaggar, batch-review) i plan och testfall.

---

## Surprises & Discoveries

(Hålls tom tills arbetet startar. Fyll på med korta observationer + evidens.)
- Observation: Milestone 0/1 kan verifieras med in-memory stores och socket-check mot Postgres i CI utan extra beroenden.
  Evidence: CI-workflows kör migrationskontroll och tester mot Postgres service.
- Observation: Samtycken saknas i domänmodell och flöden trots krav på ConsentRecord och stegvis samtycke.
  Evidence: architecture.md kräver ConsentRecord; domain.py saknar ConsentRecord-modell.
- Observation: SurveyResponse lagrar user_id i stället för respondent_pseudonym, vilket skapar direkt PII-koppling.
  Evidence: architecture.md beskriver respondent_pseudonym; domain.py använder user_id.
- Observation: Kuraterad fritext kopplas inte till rapportblock och filtreras inte per rapport.
  Evidence: architecture.md kräver block-koppling; PublicSiteService skickar alla curated_texts globalt.
- Observation: Publicerade rapportversioner kan uppdateras (visibility/canonical_url), vilket bryter immutabilitet.
  Evidence: architecture.md kräver immutabla versioner; storage.update_report_version används av PublishingService.
- Observation: data_version_hash kan bli ordningsberoende av response-IDs.
  Evidence: hash byggs av listan i nuvarande ordning utan sortering.
- Observation: Postgres-stöd är endast socket-check; inga riktiga migreringar eller persistens.
  Evidence: migrations.py gör endast create_connection; storage är in-memory.
- Observation: Moderationsåtgärder audit-loggas inte.
  Evidence: userstories.md kräver audit-logg; ModerationService skapar inga AuditEvent.
- Observation: Fritextsvar saknar explicita review-statusar och flagged-for-review-flöde i domänmodell.
  Evidence: userstories.md beskriver reviewstatusar; architecture.md saknar TextReview i tidigare version.
- Observation: CuratedText blir överflödigt när publik visning styrs via TextReview-statusar.
  Evidence: reviewstatusar definierar synlig/ej synlig fritext i publika rapporter.

---

## Decision Log

(Hålls tom tills beslut tas. Fyll på i formatet nedan.)
- Decision: Separera PII- och response-lager i in-memory stores för att spegla arkitekturinvarianter.
  Rationale: Säkerställer tydlig gräns mellan identitet och svar även i MVP-skelettet.
  Date/Author: 2026-01-09 / Codex
- Decision: CI-migrationskontroll görs via socket-anslutning till Postgres för att undvika nya beroenden.
  Rationale: Uppfyller krav på Postgres i CI utan att lägga till DB-drivrutin i MVP-skelettet.
  Date/Author: 2026-01-09 / Codex
- Decision: Inför TextReview som separat modell för att hantera reviewstatusar och flagged-for-review.
  Rationale: Tydlig spårbarhet mellan svar, reviewstatus och kuraterad publikation utan PII-läckage.
  Date/Author: 2026-01-10 / Codex
- Decision: Fasa ut CuratedText och använd TextReview-statusar för publik fritext.
  Rationale: Enhetlig källa för synlighetsregler (hide filtreras, unreviewed/reviewed/highlight kan visas).
  Date/Author: 2026-01-10 / Codex
- Decision: Inför ConsentRecord och samtyckesflöde för grund- och specifika samtycken i PII-zonen.
  Rationale: Säkerställer GDPR-samtycke med versionering utan nya datakategorier.
  Date/Author: 2026-01-10 / Codex
- Decision: Byt SurveyResponse till respondent_pseudonym och flytta idempotensspårning till PII-store.
  Rationale: Förhindrar direkt koppling mellan PII och response-store.
  Date/Author: 2026-01-10 / Codex
- Decision: Lås publicerade reportversioner (immutable) och använd replace/redirect för ändringar.
  Rationale: Uppfyller arkitekturkravet om immutabla publicerade versioner.
  Date/Author: 2026-01-10 / Codex

---

## Outcomes & Retrospective

(Hålls tom tills en milstolpe är klar. Fyll på med vad som uppnåddes, vad som återstår och lärdomar.)

### MVP Outcomes & Retrospective (2026-01-09)
- Uppnått: MVP-flöden för auth, enkät, aggregering, rapportmallar, publicering, moderation, publik läsning, E2E-flöden och nätverksopt-in är implementerade och testade i in-memory-lagret.
- Kända gap: publikt UI/SEO-lager saknar ännu implementation utanför mockad in-memory-server.
- Nästa steg: konkretisera publikt UI/SEO-lager när webbgränssnittet byggs.

### Milestone 0–1 (2026-01-09)
- Uppnått: PR/main CI-gates, Postgres-anslutningscheck i migrationssteg, samt auth/RBAC-sessioner med PII-separering.
- Återstår: Implementera Survey, Aggregation, Reports, Publishing, Moderation, Public site och Network enligt kommande milstolpar.
- Lärdomar: In-memory skelett gör det möjligt att verifiera privacy/rbac-krav tidigt innan DB-lager är på plats.

### Milestone 2 (2026-01-09)
- Uppnått: Survey-registrering, basblock-skiplogik och svar som endast accepteras en gång per enkät.
- Återstår: Aggregation, Reports, Publishing, Moderation, Public site och Network enligt kommande milstolpar.
- Lärdomar: Basblock-status behöver vara explicit i survey-start för att UI ska kunna styra flödet.

### Milestone 3 (2026-01-09)
- Uppnått: Aggregationssnapshots med data_version_hash och central small-n-maskning i rapportpayload.
- Återstår: ReportTemplates, Publishing, Moderation, Public site och Network enligt kommande milstolpar.
- Lärdomar: Aggregationslogik måste exponera min_responses tydligt för tester och rapportering.

### Milestone 4 (2026-01-09)
- Uppnått: ReportTemplate-rendering, placeholders, villkorstexter och WYSIWYG-preview via samma renderingsflöde.
- Återstår: Publishing, Moderation, Public site och Network enligt kommande milstolpar.
- Lärdomar: Samma rendering för preview/public minskar risk för inkonsistens.

### Milestone 5 (2026-01-09)
- Uppnått: Publiceringsflöde med canonical URL, ersättning→redirect och avpublicering.
- Återstår: Moderation, Public site och Network enligt kommande milstolpar.
- Lärdomar: En enkel redirect-resolver räcker för att modellera replace-flödet innan webblager finns.

### Milestone 6 (2026-01-09)
- Uppnått: Moderationsflöde med flaggning, redaktion och kuraterad fritext i publik payload.
- Återstår: Public site och Network enligt kommande milstolpar.
- Lärdomar: Kuraterad fritext behöver egen lista i payload för att hålla rådata borta.

### Milestone 7 (2026-01-09)
- Uppnått: Publik nyhetslista, rapportbibliotek och rapportläsning med kommun-fallback till basprofil.
- Återstår: Network enligt kommande milstolpar.
- Lärdomar: Rapportläsning behöver både kommunparam och basprofil-fallback för att fungera för inloggade föräldrar.

### Milestone 8 (2026-01-09)
- Uppnått: Opt-in för nätverk, grov matchningssammanställning och introduktionsmail via outbox.
- Återstår: inget enligt nuvarande milstolpar.
- Lärdomar: Matchningssammanställningar kan byggas på basprofil utan att exponera individdata.

### Milestone 9 (2026-01-10)
- Uppnått: ConsentRecord-flöde, pseudonymiserade SurveyResponse, TextReview-baserad publik fritext, immutabla publicerade reportversioner, deterministisk data_version_hash, Postgres-migreringar samt moderation-audit.
- Återstår: Gap-analys och vidare uppdatering av ExecPlan enligt Progress.
- Lärdomar: PII-separation kräver att idempotens och samtycke hålls strikt i PII-lagret.

---

## Context and Orientation

### Dokument och “source of truth”
- `spec.md`: vad systemet är och ska göra (scope, avgränsningar).
- `architecture.md`: arkitekturinvarianter och dataflöden (normativt).
- `security.md`: security + privacy by design (normativt).
- `userstories.md`: funktionellt beteende + AC + testspårbarhet via TC-ID.
- `testplan.md`: NFR (source of truth) + CI-gates + teststrategi.
- `testcases.md`: detaljerade testfall (U/I/C/E) med gates.

### Kärnprinciper som måste hållas
- Identitet (PII) och enkätsvar ska vara separerade.
- Publikt får bara aggregerat och/eller kuraterat material visas.
- Small-n-policy: `n < min_responses` → “X” + banner.
- Rapport-rendering ska vara deterministisk för given `data_version_hash`.
- Publicering sker via versioner: ersättning ska ge redirect.

### MVP-avgränsningar
- Endast webb (ingen app).
- Enkel RBAC, ingen MFA i MVP.
- Incident- och DPIA-hantering sker manuellt utanför plattformen.
- Ingen realtidschatt eller intern meddelandetjänst efter introduktionsmail.

---

## Plan of Work

Arbetet delas in i milstolpar som var och en ger ett tydligt, körbart delresultat. Varje milstolpe ska:
- vara verifierbar via test (unit/integration/contract och vid behov E2E),
- hålla arkitekturinvarianter,
- uppdatera `Progress`, samt vid beslut uppdatera `Decision Log`.

### Milestone 0: Repo, verktyg och CI (grundplattan)
Mål: ett repo som bygger, testar och kan köras lokalt, med PR-gate och main-gate.
- Skapa mappstruktur och minimala “hello endpoints” (t.ex. `/health`).
- Lägg in Postgres i CI och migrationskörning.
- Implementera lint + unit test scaffold.
- Lägg in Playwright scaffold men kör endast i main-gate.

Acceptans:
- PR-gate passerar på en tom feature-branch.
- Main-gate kör full suite (även om få tester ännu), och publicerar artifacts vid fel.

### Milestone 1: Auth, RBAC och PII-zone
Mål: säkert konto- och rollsystem, samt teknisk grund för PII-separering.
- Implementera e-postverifiering och sessioner.
- Implementera roller: Allmänheten (implicit), Parent, Analyst, Admin.
- Skapa separata datalager/logiska boundaries: PII-store vs response/aggregation-store.
- Implementera grundläggande rate limiting och max login attempts.

Acceptans:
- Contract tests för RBAC (t.ex. Parent kan inte publicera; Allmänheten kan läsa public).
- Loggpolicy i “prod-mode” verifieras av test (inga payloads/PII).

### Milestone 2: Survey + basblock + svar (en gång)
Mål: Parent kan registrera sig, fylla basblock och svara på en enkät exakt en gång.
- Survey schema (sektioner + frågetyper).
- Basblock-policy: visas bara om saknas; skip annars.
- Response ingest med idempotens: blockera dubbelsvar.

Acceptans:
- `TC-US03-*`, `TC-US04-*` passerar.
- UI-flöde kan köras manuellt: registrera → basblock → enkät → bekräftelse.

### Milestone 3: Aggregation + small-n-maskning
Mål: svar blir aggregat och small-n-policy implementeras centralt.
- Inkrementell aggregation + snapshot med `data_version_hash`.
- Implementera `min_responses` default + per enkät.
- Maskning “X” och banner state i report payload.

Acceptans:
- `TC-US21-03`, `TC-US21-04`, `TC-SEC-01` passerar.
- Edge: kommun under tröskel maskas; total kan visas om total >= tröskel.

### Milestone 4: ReportTemplate + rendering + WYSIWYG-preview
Mål: analytiker kan skapa rapportmallar kopplade till enkät och preview:a deterministiskt.
- Template blocks: text + diagram placeholders (MVP).
- Placeholders: `$kommun`, `$antal_respondenter` m.fl.
- Enkla villkorstexter (MVP).
- Preview ska använda exakt samma rendering som publicering.

Acceptans:
- `TC-US20-*` passerar.
- Reproducerbarhet: samma `data_version_hash` ger samma output.

### Milestone 5: Publishing (visibility, canonical URL, replace→redirect)
Mål: publicering fungerar med stabil URL och ersättning via redirect.
- Default internal.
- Public: canonical URL.
- Replace: redirect gammal→ny.
- Avpublicering: tar bort från publik index men behåller intern historik.

Acceptans:
- `TC-US22-*` passerar (inkl. Playwright redirect).
- Allmänheten kan läsa publicerad rapport, men saknar access till skyddade endpoints.

### Milestone 6: Moderation & reviewstatus i publika rapporter
Mål: fritext kan flaggas och reviewas; publika regler styrs av status.
- UI: tydliga uppmaningar att inte lämna identifierande info.
- Flagga-funktion.
- Analyst/Admin: reviewstatus (**reviewed**/**highlight**/**hide**).
- Public rendering: `hide` filtreras bort.

Acceptans:
- `TC-US15-01..03` passerar.
- Negativt: `hide` ska aldrig synas i publik vy (`TC-US15-02`).

### Milestone 6b: Fritext-reviewflöde (status + flaggning)
Mål: analytiker kan granska fritext per enkät och hantera flaggningar över tid.
- Fritextsvar skapas som `unreviewed`.
- Reviewstatusar: `reviewed`, `highlight`, `hide`.
- Flagging: `flagged_for_review` och `reviewed_after_flagging`.
- Batch-review av kvarvarande svar i en enkät.
- Fälttyper (ExecPlan):
  - TextReview.id:int, response_id:int, status:str, flagged_for_review:bool, reviewed_by:int, reviewed_at:datetime
  - TextFlag.id:int, response_id:int, reason:str, flagged_at:datetime

Acceptans:
- `TC-US15-04` och `TC-US16-01..03` passerar.
- Publik payload innehåller aldrig `hide`.

### Milestone 7: Public site (nyheter + rapportbibliotek)
Mål: en publik “webb” med SEO-indexering, sök/filter och rapportläsning.
- Startsida/nyheter.
- Rapportbibliotek.
- Rapportläsare med kommunval via query param och fallback till basprofil.

Acceptans:
- Manuell: öppna public URL utan inloggning.
- E2E: läsa rapport + kommunparam + banner/X vid small-n.

### Milestone 8: Network opt-in + introduktionsmail (outbox)
Mål: erbjuda nätverk, endast ja-sägare kopplas och mail skapas.
- Matchningsförslag på grov nivå.
- Opt-in och introduction event.
- Mail outbox med “varför du får detta mail”.

Acceptans:
- `TC-US08-*`, `TC-US09-*` passerar.
- Inga nätverksendpoints åtkomliga för Allmänheten.

### Milestone 9: Compliance Hardening (arkitektur + security + NFR-gap)
Mål: åtgärda identifierade gap mot arkitektur/security/testplan utan att bryta MVP-scope.
- Lägg till ConsentRecord-modell och flöde för grund- och specifika samtycken (utan nya datakategorier).
- Byt SurveyResponse till pseudonym/anon-ID och säkra att PII aldrig korsas med response-store.
- Ersätt CuratedText med reviewstatusar i publika rapporter (hide filtreras).
- Gör publicerade ReportVersion immutabla (ersättningsflöde används i stället för mutation).
- Gör data_version_hash deterministisk genom stabil sortering eller hash av snapshot-id.
- Inför riktig Postgres-persistens + migreringar i CI enligt testplan.md.
- Audit-logga moderationsåtgärder (flagga/redaktion/kuratering).
- Dokumentera nya fält/invariansändringar i Decision Log innan implementation.
- Lista tydliga fälttyper i ExecPlan för varje ny/ändrad modell (t.ex. ConsentRecord.id:int, type:str, version:str, status:str, timestamp:datetime).

Fälttyper (ExecPlan):
- ConsentRecord: id:int, user_id:int, consent_type:str, version:str, status:str, timestamp:datetime(ISO).
- SurveyResponse: respondent_pseudonym:str, answers:dict, raw_text_fields:dict.
- TextReview: id:int, response_id:int, status:str, flagged_for_review:bool, reviewed_by:int?, reviewed_at:datetime(ISO)?.
- ReportVersion: published_state:str (draft/published).

Acceptans:
- Nya/uppdaterade testfall täcker samtycken, immutabilitet, audit-logg för moderation.
- `TC-SEC-*` + relevanta US/TC passerar mot Postgres-backend.

---

## Concrete Steps

(Anpassas efter vald teknisk stack. Fylls på när repo finns.)
Exempel på vad som ska gå att köra i slutet av Milestone 0:
- I repo-root:
    - install dependencies
    - run unit tests
    - run integration tests with Postgres
    - start server
- Öppna i browser:
    - http://localhost:<port>/health → 200 OK

Varje milstolpe ska uppdatera denna sektion med exakta kommandon och korta förväntade outputs.

Milestone 9 (Compliance hardening):
- I repo-root:
  - `python -m backend.migrations` → skapar/uppdaterar Postgres-tabeller.
  - `python -m unittest` → gröna unit/integration-tester inklusive consent/review/immutability.

---

## Validation and Acceptance

Validering ska vara beteendebaserad och verifierbar:
- Test:
  - Kör projektets testkommandon och förvänta “grönt”.
  - Nya tester ska kunna visas “röda före / gröna efter” när rimligt.
- Manuell proof:
  - Starta server, utför ett litet end-to-end scenario:
    1) registrera Parent, svara på enkät
    2) skapa rapportmall som Analyst, publicera
    3) öppna publik rapport som Allmänheten och verifiera kommunvy + small-n

Acceptance för MVP är att Milestone 0–8 är uppfyllda, och att `testplan.md` NFR är maskintestade enligt `testcases.md` där sådana TC finns.

---

## Idempotence and Recovery

- Alla migrations och seeds ska vara idempotenta i CI och lokalt.
- Seed/reset (test-only) ska kunna köras flera gånger utan drift.
- Replace→redirect ska vara säker att köra även om publicering avbryts halvvägs:
  - rollback eller “mark as replaced” ska vara transaktionellt tydligt.

---

## Artifacts and Notes

Lägg här (som korta indenterade block, inte nya code fences):
- korta terminalutdrag som visar lyckad körning av tester
- korta HTTP-exempel (request/response) som visar ny funktion
- viktiga diff-utdrag om ett beslut var känsligt

---

## Interfaces and Dependencies

### Rekommenderade huvudgränssnitt (konceptuellt)
- Auth:
  - `POST /auth/start` (skapa verifieringskod/länk)
  - `POST /auth/verify` (verifiera och skapa session)
- Survey:
  - `POST /surveys` (Analyst)
  - `GET /surveys/{id}` (Parent)
  - `POST /surveys/{id}/responses` (Parent)
- Reports:
  - `POST /report-templates` (Analyst)
  - `GET /reports/{canonical}` (Allmänheten/Parent)
  - `POST /reports/{id}/publish` (Analyst)
  - `POST /reports/{id}/replace` (Analyst)
- Moderation:
  - `POST /text/flags` (Parent)
  - `POST /text/curate` (Analyst/Admin)
- Network:
  - `POST /network/opt-in` (Parent)
  - `POST /network/introduce` (system/worker)

### Testautomation
- Backend: pytest (U/I/C)
- E2E: Playwright (E) i main-gate
- Mail: Outbox-tabell i test

Varje ny dependency ska motiveras: varför den behövs och hur den testas.

---

## Change Notes (planrevisioner)

- (2026-01-09) Skapade plans-v2.md genom att kombinera befintlig plans.md (v1.1) med ExecPlan-inspirerad struktur (levande plan, progress/decision log/acceptans, milstolpar med verifiering).
