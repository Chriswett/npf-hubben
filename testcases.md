# testcases.md
**Projekt:** Samarbets- och analysplattform för NPF-föräldrar  
**Version:** v1.2  
**Datum:** 2026-01-09  
**Status:** Fastställd – verifierbara testfall (koherensfix US-04/05/06)

Notation:
- **U** = Unit test
- **I** = Integration test (API + DB + workers)
- **C** = Contract test (RBAC, endpoints, felkoder)
- **E** = E2E (Playwright)
- **Gate**: PR = körs i PR-gate, MAIN = körs i main-gate

---

## US-01 – Snabb registrering via publik enkät

### TC-US01-01 (I, PR+MAIN)
**Scenario:** Konto skapas med e-postverifiering  
- Given: publik enkät-URL  
- When: användare registrerar e-post  
- Then: konto skapas men session aktiveras först efter verifiering

### TC-US01-02 (C, PR+MAIN)
**Scenario:** Oidentifierad kan inte svara  
- When: POST response utan verifierad session  
- Then: 401/403 returneras

---

## US-02 – Anonymitet som default

### TC-US02-01 (C, MAIN)
**Scenario:** Publika vyer innehåller ingen PII  
- When: hämta publik rapport (UI/API)  
- Then: inga identifierande fält förekommer

### TC-US02-02 (I, MAIN)
**Scenario:** Dataseparation  
- Then: Response store saknar direkt PII (endast pseudonym)

---

## US-03 – Skapa enkät

### TC-US03-01 (U, PR+MAIN)
**Scenario:** Validera enkät-schema  
- Then: schema accepterar alla stödda frågetyper

### TC-US03-02 (I, PR+MAIN)
**Scenario:** Basblock default  
- Then: base_block_policy = enabled

### TC-US03-03 (I, PR+MAIN)
**Scenario:** Feedback-mode default  
- Then: feedback_mode = section

---

## US-04 – Basblock visas bara en gång

### TC-US04-01 (I, PR+MAIN)
**Scenario:** Basblock visas för ny användare  
- Given: användare utan BaseProfile/basblock  
- When: användaren startar första enkätflödet  
- Then: basblock presenteras före enkäten  
- And: basblock-svar lagras i BaseProfile (eller motsv.)

### TC-US04-02 (I, PR+MAIN)
**Scenario:** Basblock hoppas över för återkommande  
- Given: användare med redan ifyllt basblock  
- When: användaren startar en ny enkät  
- Then: basblock visas inte  
- And: enkätstart går direkt till första sektionen

---

## US-05 – Enkät kan bara besvaras en gång

### TC-US05-01 (C, PR+MAIN)
**Scenario:** Dubbelsvar blockeras (idempotens per enkät och konto)  
- Given: ett konto som redan lämnat response för survey X  
- When: samma konto försöker POST:a response för survey X igen  
- Then: 409 (eller definierad felkod) returneras  
- And: inga nya rader skapas  
- And: aggregering förändras inte

---

## US-06 – Svara på äldre enkäter

### TC-US06-01 (I, MAIN)
**Scenario:** Parent kan svara på äldre, fortfarande öppna enkäter  
- Given: survey X publicerades tidigare och är fortfarande öppen  
- And: användaren har inte svarat på survey X  
- When: användaren svarar på survey X  
- Then: response accepteras  
- And: aggregering uppdateras  
- And: rapportdata reflekterar den nya totalen

---

## US-07 – Visa aggregerade resultat

### TC-US07-01 (U, PR+MAIN)
**Scenario:** Feedback-mode styr återkoppling  
- Then: feedback triggas per sektion vid mode=section

### TC-US07-02 (I, MAIN)
**Scenario:** Feedback är begränsad och säker  
- Then: inga små-n-tal eller PII ingår

### TC-US07-03 (E, MAIN)
**Scenario:** UI visar feedback efter avsnitt  
- Then: feedback-komponent visas och länkar till rapportvy

---

## US-20 – Skapa kommenterad analysrapport

### TC-US20-01 (I, PR+MAIN)
**Scenario:** ReportTemplate kräver survey_id  
- Then: saknas survey_id → 400

### TC-US20-02 (U, PR+MAIN)
**Scenario:** Placeholder-interpolation  
- Then: `$kommun`, `$antal_respondenter` ersätts korrekt

### TC-US20-03 (U, PR+MAIN)
**Scenario:** Villkorstext (MVP)  
- Then: rätt textblock väljs vid tröskel

### TC-US20-04 (I, MAIN)
**Scenario:** Preview = public rendering  
- Then: samma input → identisk output (deterministiskt)

---

## US-21 – Kommunanpassad rapportvisning

### TC-US21-01 (I, MAIN)
**Scenario:** Kommun via query-param  
- Then: query-param prioriteras

### TC-US21-02 (I, MAIN)
**Scenario:** Kommun via basprofil  
- Then: basprofil används om param saknas

### TC-US21-03 (U, PR+MAIN)
**Scenario:** Small-n maskning  
- Then: `n < min_responses` → värden = “X”

### TC-US21-04 (I, MAIN)
**Scenario:** Banner vid small-n  
- Then: banner flagga returneras

### TC-US21-05 (E, MAIN)
**Scenario:** UI visar banner + “X”  
- Then: banner syns direkt och fält maskas

### TC-US21-06 (I, MAIN)
**Scenario:** Totalvärden tillåtna  
- Then: total visas om `n_total >= min_responses`

---

## US-22 – Publicera och dela rapport

### TC-US22-01 (I, PR+MAIN)
**Scenario:** Default visibility  
- Then: ny version = internal

### TC-US22-02 (I, MAIN)
**Scenario:** Publik URL skapas  
- Then: canonical_url sätts

### TC-US22-03 (I, MAIN)
**Scenario:** Ersättning → redirect  
- Then: gammal URL redirectar till ny

### TC-US22-04 (E, MAIN)
**Scenario:** Browser-redirect fungerar  
- Then: Playwright verifierar navigation

---

## US-08 – Erbjud nätverkskoppling

### TC-US08-01 (U, PR+MAIN)
**Scenario:** Erbjudande-text  
- Then: innehåller antal + grov kontext

### TC-US08-02 (I, MAIN)
**Scenario:** Matchning utan individexponering  
- Then: endast interna ids används

---

## US-09 – Opt-in till kontakt

### TC-US09-01 (I, MAIN)
**Scenario:** Endast ja-sägare inkluderas  
- Then: matchgrupp innehåller endast opt-in

### TC-US09-02 (I, MAIN)
**Scenario:** Introduktionsmail skapas  
- Then: ett outbox-mail med alla mottagare och obligatorisk motivering

### TC-US09-03 (C, MAIN)
**Scenario:** Allmänheten saknar åtkomst  
- Then: 401/403 på nätverks-endpoints

---

## US-13 – AI-fördjupning

### TC-US13-01 (I, MAIN)
**Scenario:** Endast fasta prompts  
- Then: fri prompt nekas eller normaliseras

### TC-US13-02 (I, MAIN)
**Scenario:** AI påverkar inte kvantitativ analys  
- Then: aggregat oförändrade

---

## US-15 – Administrera dataskydd

### TC-US15-01 (I, MAIN)
**Scenario:** Flaggning → redaktion loggas  
- Then: TextFlag + TextRedactionEvent skapas

### TC-US15-02 (C, MAIN)
**Scenario:** Endast kuraterad fritext publikt  
- Then: raw fritext syns aldrig publikt

### TC-US15-03 (I, MAIN)
**Scenario:** Avpublicering är reversibel  
- Then: publik vy bort, intern historik kvar

---

## US-19 – Roll- och behörighetsadmin

### TC-US19-01 (C, MAIN)
**Scenario:** RBAC enforcement  
- Parent kan inte publicera  
- Analyst kan inte ändra roller  
- Admin kan ändra roller

### TC-US19-02 (I, MAIN)
**Scenario:** Rolländring slår igenom direkt  
- Then: access ändras + audit-logg

---

## SECURITY / PRIVACY (TVÄRGÅENDE)

### TC-SEC-01 (C, MAIN)
**Scenario:** Publika endpoints utan PII  
- Then: inga identifierande fält

### TC-SEC-02 (I, MAIN)
**Scenario:** Loggpolicy i prod-mode  
- Then: inga payloads eller PII i loggar

### TC-SEC-03 (C, MAIN)
**Scenario:** Security headers  
- Then: CSP + X-Frame-Options finns

### TC-SEC-04 (I, MAIN)
**Scenario:** Rate limiting login  
- Then: max försök → spärr

### TC-SEC-05 (I, MAIN)
**Scenario:** Backup smoke  
- Then: backup-jobb kan initieras (ingen user restore)

---
