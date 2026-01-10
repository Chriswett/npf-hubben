# security.md
**Projekt:** Samarbets- och analysplattform för NPF-föräldrar  
**Version:** v1.2  
**Datum:** 2026-01-08  
**Status:** Fastställd – Security & Privacy by Design

---

## 1. Syfte och tillämpning

Detta dokument beskriver hur plattformen:

- skyddar användare och data mot oavsiktlig och otillåten exponering
- behandlar personuppgifter lagligt, proportionerligt och transparent
- operationaliserar “privacy by design” och “security by design”

Dokumentet gäller för hela systemet och är bindande för:
- arkitektur
- implementation
- testning
- drift

---

## 2. Säkerhetsklassning och hotmodell

### 2.1 Säkerhetsklassning
Plattformen klassas som **hög skyddsnivå**.

Motivering:
- uppgifter kan indirekt röra barns hälsa/diagnoser
- fritext kan oavsiktligt bli identifierande
- användare kan göra misstag trots tydlig information

### 2.2 Hotmodell (MVP)
Primära risker:
- oavsiktlig överdelning
- felpublicering
- små-n-exponering
- felaktig åtkomst internt

Sekundära risker:
- opportunistiskt missbruk (spam, brute force)

Riktade attacker bedöms som låg sannolikhet i MVP.

---

## 3. Grundprinciper

### 3.1 Privacy by Design
- Dataminimering
- Aggregering som standard
- Samtycke som rättslig grund
- Återkallelse alltid möjlig
- Tydlig information innan risk uppstår

### 3.2 Security by Design
- Secure-by-default
- Least privilege
- Rollbaserad åtkomst
- Guardrails före hårda spärrar (MVP)
- Spårbarhet före automatisering

---

## 4. Rättslig grund och samtycke

### 4.1 Rättslig grund
- **Samtycke** (GDPR art. 6.1 a och 9.2 a)

Samtycke är:
- aktivt
- informerat
- frivilligt
- alltid återkalleligt

### 4.2 Stegvis samtycke
- **Grundsamtycke vid registrering**
  - konto
  - deltagande
  - publicering av anonymiserade, aggregerade resultat
- **Specifika samtycken vid behov**
  - fritext
  - nätverkskontakt
  - särskilda analyser

Alla samtycken:
- versionshanteras
- tidsstämplas
- kan återkallas

---

## 5. Datakategorier och behandling

### 5.1 Kontodata (PII)
Exempel:
- e-post
- roller
- samtycken
- basblock (kommun, grov kategorisering)

Policy:
- lagras isolerat
- används endast för funktion som kräver identitet
- raderas/anonymiseras vid kontoborttagning

---

### 5.2 Strukturerade enkätsvar
- används endast aggregerat
- anonymiseras irreversibelt efter ingestion
- betraktas därefter som anonym statistik (utanför GDPR)
- kan inte raderas i efterhand

Detta kommuniceras tydligt till användaren.

---

### 5.3 Fritext (förhöjd risk)
- användaren uppmanas tydligt att inte lämna identifierande uppgifter
- kan flaggas av andra användare
- kan redigeras eller uteslutas av analyst/admin via reviewstatus

Vid:
- återkallat samtycke
- kontoborttagning  
→ fritext tas bort eller anonymiseras

Fritext i publika rapporter styrs av reviewstatus (endast **unreviewed**, **reviewed** och **highlight** får visas).

---

## 6. Kontoradering och rättigheter

- Självservice för kontoradering
- Manuell begäran som fallback

Vid radering:
- PII raderas
- basblock raderas
- fritext tas bort
- anonymiserade aggregat kvarstår

Alla åtgärder audit-loggas.

---

## 7. Roller och åtkomst

### 7.1 Roller

**Allmänheten (oinloggad)**
- läsa publika rapporter och nyheter
- läsa publicerad fritext enligt tillåtna reviewstatusar
- ingen åtkomst till rådata eller nätverksfunktioner

**Parent**
- svara på enkäter
- läsa rapporter
- flagga fritext
- opt-in till nätverkskontakt

**Analyst**
- skapa enkäter
- skapa rapportmallar
- preview och publicera
- redigera och reviewa fritext

**Admin**
- hantera roller
- kontoradering
- audit
- avpublicering

Åtkomst styrs via enkel RBAC.

---

## 8. Autentisering och sessioner

### 8.1 Autentisering (MVP)
- e-postbaserad inloggning (magic link/kod)
- e-postverifiering krävs
- ingen MFA i MVP

### 8.2 Sessionshantering
- Parent: längre sessioner, “kom ihåg mig”
- Analyst/Admin: kortare sessioner, striktare timeout

---

## 9. Kryptering och transport

- TLS för all trafik
- Kryptering i vila för databaser
- Kryptering av backups/object storage ej krav i MVP

---

## 10. Klientsäkerhet (Webb)

- HTTPS
- Säkra cookies (HttpOnly, Secure, SameSite)
- CSRF-skydd
- Content Security Policy (CSP)
- X-Frame-Options
- Grundläggande XSS-skydd

---

## 11. Loggning och felsökning

### 11.1 Produktion
- Inga personuppgifter eller enkätpayloads i loggar
- Generiska felmeddelanden

### 11.2 Test/utveckling
- Rådata kan förekomma
- Endast syntetiska/testdata

---

## 12. Skydd mot missbruk

- Begränsat antal inloggningsförsök
- Enkel rate limiting på publika endpoints
- Ingen avancerad bot-detektion eller WAF i MVP

---

## 13. Incidenthantering

- Incidenthantering sker manuellt utanför plattformen
- Plattformen stödjer:
  - spårbarhet
  - versionshistorik
  - audit-loggar
- Bedömning och eventuell anmälan hanteras av ansvarig (DPO)

---

## 14. Backup och återställning

- Grundläggande driftbackup för tillgänglighet
- Ingen användarstyrd återställning
- Återställning hanteras manuellt vid behov

---

## 15. Testbarhet och verifiering

- Säkerhets- och integritetskrav verifieras via automatiserade tester
- Maskning, RBAC, loggpolicy och headers testas i CI
- `testplan.md` är source of truth för NFR

---

## 16. Sammanfattning

Plattformens säkerhet bygger på att:
- minimera insamlad data
- aggregera tidigt
- ge tydlig information till användare
- använda enkla men robusta skydd
- kombinera mänsklig kontroll med tekniska räcken

Security och privacy är integrerade i arkitektur, process och test – inte tillägg.
