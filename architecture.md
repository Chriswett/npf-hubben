# architecture.md
**Projekt:** Samarbets- och analysplattform för NPF-föräldrar  
**Version:** v0.6  
**Datum:** 2026-01-08  
**Status:** Konsoliderad referensarkitektur

---

## 1. Arkitekturens roll

Detta dokument beskriver:
- systemets **tekniska uppbyggnad**
- centrala **arkitekturinvarianter**
- dataflöden och gränser mellan ansvar
- hur funktionella krav operationaliseras säkert

`architecture.md` är **normativ**:
- implementation får variera
- invariants får inte brytas utan medvetet beslut

---

## 2. Arkitekturinvarianter (icke förhandlingsbara)

### 2.1 Dataskydd & anonymitet
- Identitet (PII) och svar lagras i **separata datalager**
- Publika vyer använder **endast aggregerad data och fritext med tillåtna reviewstatusar**
- Small-n-maskning tillämpas konsekvent (`min_responses`)
- Rå fritext exponeras aldrig publikt

### 2.2 Aggregering som gräns
- All analys och rapportering sker mot **aggregat**
- Rådata får aldrig nå rapport-/publiceringslagret
- Aggregat är irreversibla (utanför GDPR)

### 2.3 Reproducerbarhet
- Rapport-rendering är deterministisk för given dataversion
- Preview = public rendering (WYSIWYG)
- Versioner är immutabla efter publicering

### 2.4 Säkerhetsklassning
- Plattformen behandlas som **hög skyddsnivå**
- Skyddsräcken prioriteras framför komplexa spärrar (MVP)

---

## 3. Systemöversikt (logisk arkitektur)

### 3.1 Huvudkomponenter

#### Web Client (SPA)
- Publika sidor:
  - rapportbibliotek
  - rapportläsare
  - nyhetssida
- Parent-flöden:
  - registrering + verifiering
  - enkätflöde (bildstött, låg text)
  - feedback per avsnitt
  - rapportläsning
  - opt-in nätverk
- Analyst-flöden:
  - enkäteditor
  - rapportmall-editor
  - preview (WYSIWYG)
  - publicering / ersättning
- Admin-flöden:
  - roller
  - moderation
  - audit

---

#### API Backend
- Auth & session service
- Survey service
- Response ingest service
- Aggregation service
- Report service (templates, rendering)
- Publishing service (visibility, URLs, redirects)
- Text moderation service
- Network matching service
- Notification service (email)
- Admin service (RBAC, audit)

---

#### Background Workers
- Inkrementell aggregering
- Periodisk full recompute
- Rapport-export (PDF/PNG)
- Mail dispatch
- AI-fördjupning (fasta prompts)

---

## 4. Datamodell (konceptuell)

### 4.1 Identitet & samtycke
- **User**
  - id
  - email (PII)
  - role
- **ConsentRecord**
  - type
  - version
  - status
  - timestamp

PII lagras isolerat och används endast för:
- inloggning
- samtycke
- e-post

---

### 4.2 Enkäter
- **Survey**
  - schema (sektioner/frågor)
  - base_block_policy
  - feedback_mode
  - min_responses_default
- **SurveyResponse**
  - respondent_pseudonym
  - answers
  - raw_text_fields (endast internt)

---

### 4.3 Basblock (kontonivå)
- **BaseProfile**
  - kommun
  - grov kategorisering
- Används för:
  - skip-logik
  - default kommun i rapportvy

---

### 4.4 Analys
- **AggregationDefinition**
- **AggregationSnapshot**
  - data_version_hash
  - metrics

---

### 4.5 Rapportering
- **ReportTemplate**
  - survey_id
  - blocks (text, diagram, AI)
  - placeholders (`$kommun`, `$antal_respondenter`)
  - enkla villkor (MVP)
- **ReportVersion**
  - visibility (internal / auth / public)
  - published_state
  - canonical_url
  - replaced_by

---

### 4.6 Fritext & moderation
- **TextFlag**
- **TextRedactionEvent**
- **TextReview**
  - response_id
  - status (`unreviewed`, `reviewed`, `highlight`, `hide`, `reviewed_after_flagging`)
  - flagged_for_review (bool)
  - reviewed_by
  - reviewed_at

---

### 4.7 Nätverk
- **NetworkPreference**
  - opt_in
- **IntroductionEvent**
  - recipients
  - mail_id (outbox)

---

## 5. Roller & åtkomst

### 5.1 Roller
- **Allmänheten (oinloggad)**
  - läsa publika rapporter och nyheter
  - läsa publicerad fritext enligt tillåtna reviewstatusar
- **Parent**
  - svara på enkäter
  - läsa rapporter
  - flagga fritext
  - opt-in nätverk
- **Analyst**
  - skapa enkäter
  - skapa rapportmallar
  - preview
  - publicera/ersätta
  - redigera fritext
- **Admin**
  - roller
  - kontoradering
  - audit
  - avpublicering

RBAC implementeras centralt i backend.

---

## 6. Nyckelflöden

### 6.1 Enkät → analys
1. Parent registrerar sig och verifierar e-post
2. Basblock visas (om ej redan ifyllt)
3. Enkät besvaras
4. Aggregat uppdateras inkrementellt
5. Snapshot skapas vid behov

---

### 6.2 Rapportvisning
- Kommun väljs via:
  1. query-param
  2. BaseProfile
  3. manuellt val
- Om `n < min_responses`:
  - banner visas
  - kommunvärden maskas (“X”)
- Total-/jämförelsevärden visas om tillräckligt underlag finns

---

### 6.3 Publicering
- Default = internal
- Publicering:
  - skapar stabil canonical URL
- Ersättning:
  - gammal version redirectar till ny
- Avpublicering:
  - tar bort från publik vy
  - historik kvar internt

---

### 6.4 Fritext
- Parent uppmanas att undvika identifierande uppgifter
- Fritext kan flaggas
- Analyst/Admin redigerar och sätter reviewstatus
- Publik visning styrs av reviewstatus (hide visas aldrig)

---

### 6.5 Nätverk
- System identifierar liknande situationer (grov nivå)
- Parent får erbjudande (“X andra i liknande situation”)
- Endast ja-sägare inkluderas
- Introduktionsmail skickas
- Plattformen avslutar ansvar därefter

---

## 7. Säkerhetsmekanismer (översikt)

Detaljer finns i `security.md`. Arkitekturnivå:

- E-postbaserad auth (MVP)
- Rollbaserad åtkomst
- TLS + DB-kryptering
- CSP + X-Frame-Options
- Rate limiting
- Audit-logg på nyckelhändelser

---

## 8. Testbarhet & automation

- Arkitekturen är designad för:
  - API-testning
  - deterministisk rendering
  - isolerade datalager
- Minimal test harness tillåts i test/CI
- Playwright används för kritiska UI-flöden

Se `testplan.md`.

---

## 9. Medvetna öppna beslut

- Exakt maskpolicy per metric (k-värde)
- Prestanda-NFR (ej MVP)
- Framtida MFA
- Eventuell utökad permissionsmodell

---

## 10. Sammanfattning

Arkitekturen:
- är robust men enkel
- skyddar användare genom design
- stödjer analys, publicering och samverkan
- är redo för agent-/Codex-driven utveckling

Komplexitet introduceras först när den behövs.
