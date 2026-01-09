# spec.md
**Projekt:** Samarbets- och analysplattform för NPF-föräldrar  
**Version:** v1.1  
**Datum:** 2026-01-08  
**Status:** Fastställd systemspecifikation (scope & syfte)

---

## 1. Syfte

Syftet med plattformen är att möjliggöra trygg, anonym och strukturerad
insamling av erfarenheter från föräldrar till barn med NPF, samt att
bearbeta dessa erfarenheter till analyser, rapporter och underlag som:

- ger föräldrar bättre insyn och sammanhang
- stärker kollektiv röst och kunskap
- möjliggör lokal och nationell analys
- kan publiceras öppet utan att exponera individer

Plattformen ska även möjliggöra frivillig samverkan mellan föräldrar
i liknande situationer, utan att skapa social exponering eller beroenden.

---

## 2. Problem som ska lösas

- Enskilda föräldrar sitter ofta isolerade med erfarenheter som inte
  synliggörs systematiskt.
- Befintliga enkättyg saknar:
  - inbyggd anonymisering
  - small-n-skydd
  - koppling till offentlig statistik och analys
- Publicerade berättelser riskerar att bli identifierande eller
  missvisande utan redaktionell hantering.
- Föräldrar saknar enkla sätt att hitta andra i liknande situation
  utan att exponera sig.

---

## 3. Målgrupper och roller

### 3.1 Roller

- **Allmänheten**  
  Oidentifierade användare som tar del av publikt publicerade rapporter
  och nyheter.

- **Parent (förälder)**  
  Registrerad användare som:
  - svarar på enkäter
  - tar del av rapporter
  - frivilligt kan välja nätverkskontakt
  - kan flagga olämplig fritext

- **Analyst (analytiker)**  
  Användare som:
  - skapar enkäter
  - analyserar och sammanställer resultat
  - producerar rapporter och infographics
  - publicerar material

- **Admin**  
  Ansvarar för:
  - roller och behörigheter
  - kontoradering
  - moderation och audit
  - avpublicering vid behov

---

## 4. Övergripande funktionalitet

### 4.1 Enkäter
- Webbaserade enkäter (ingen app krävs)
- Flera frågetyper (skalor, flerval, fritext m.m.)
- Basblock med grunduppgifter som:
  - visas för nya användare
  - hoppas över för återkommande
- Enkäter kan besvaras löpande över tid
- Förälder kan inte svara mer än en gång per enkät

---

### 4.2 Insamling och anonymitet
- Föräldrar uppmanas tydligt att inte lämna identifierande uppgifter i fritext
- Identitet och svar hålls strikt åtskilda
- Analys och publicering sker endast på aggregerad nivå
- Small-n-maskning tillämpas konsekvent

---

### 4.3 Analys och rapporter
- Aggregering per enkät
- Rapportmallar kopplas till specifika enkäter
- Rapporter kan:
  - innehålla text, diagram och tabeller
  - använda placeholders (t.ex. kommunnamn, antal svar)
  - innehålla enkla villkorstexter (MVP)
- Kommunanpassad vy via:
  - URL-parameter
  - användarens basprofil
- Tydlig markering när underlag är för litet

---

### 4.4 Publicering
- Rapporter kan publiceras med olika synlighet:
  - intern
  - inloggade
  - publik
- Publika rapporter:
  - har stabila URL:er
  - är sökmotorindexerbara
- Publicering är reversibel
- Äldre versioner ersätts via redirect

---

### 4.5 Fritext och moderation
- Fritextsvar samlas in men exponeras aldrig rått publikt
- Andra användare kan flagga olämplig fritext
- Analytiker/admin kan:
  - redigera
  - kuratera
  - utesluta fritext
- Endast kuraterad fritext får förekomma i publika rapporter

---

### 4.6 Nätverk mellan föräldrar
- Systemet kan identifiera liknande situationer på grov nivå
- Föräldrar får erbjudande om kontakt (opt-in)
- Endast ja-sägare kopplas ihop
- Introduktion sker via gemensamt e-postmeddelande
- Plattformens ansvar upphör efter introduktionen

---

### 4.7 Publik webb
- Startsida med nyheter
- Rapportbibliotek med sök och filter
- Kommun- och enkätrapporter
- Ingen inloggning krävs för publikt material

---

## 5. Icke-funktionella principer (översikt)

Detaljerade krav definieras i `testplan.md`.

På hög nivå ska systemet:
- vara lättanvänt även för användare med kognitiva svårigheter
- minimera textmängd och använda tydlig struktur
- skydda användare genom design, inte genom juridiska förbehåll
- vara möjligt att drifta enkelt (PaaS-miljö)
- vara testbart och automatiserbart

---

## 6. Säkerhet och integritet (översikt)

Detaljerad hantering finns i `security.md`.

Principer:
- Samtycke som rättslig grund
- Samtycke är alltid återkalleligt
- Kontoradering ska vara möjlig
- Aggregerade data betraktas som anonym statistik
- Incidenthantering sker manuellt utanför systemet

---

## 7. Avgränsningar

Plattformen:
- är inte en kommunikationsplattform efter introduktion
- ersätter inte formella klagomålssystem
- erbjuder inte individuell juridisk rådgivning
- innehåller ingen mobilapp i MVP
- innehåller ingen realtidschatt

---

## 8. Framtida utökningar (ej del av denna spec)

- Fler användargrupper (t.ex. skolpersonal)
- Mer avancerade rapportvillkor
- Utökade jämförelser och visualiseringar
- Fördjupad prestanda- och tillgänglighetsoptimering
- Formell DPIA-dokumentation

---

## 9. Sammanfattning

Denna specifikation beskriver ett system som:
- ger röst åt många utan att exponera individer
- kombinerar kvalitativa och kvantitativa perspektiv
- möjliggör analys, publicering och samverkan
- sätter integritet och användartrygghet främst

Specen definierar **vad** systemet ska vara.
Hur det byggs, säkras och verifieras styrs av övriga dokument.
