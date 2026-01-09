# userstories.md
**Projekt:** Samarbets- och analysplattform för NPF-föräldrar  
**Version:** v1.4  
**Datum:** 2026-01-09  
**Status:** Fastställd – funktionella krav + testspårbarhet

> Alla globala icke-funktionella krav (säkerhet, anonymitet, small-n,
> loggpolicy, tillgänglighet, drift) definieras och verifieras enligt
> `testplan.md`.  
> Detta dokument fokuserar på **beteende**, **funktion** och
> **domänspecifika acceptanskriterier**.

---

## 1. Roller

- **Allmänheten** – oinloggad läsare av publika rapporter och nyheter  
- **Parent** – registrerad förälder som svarar på enkäter  
- **Analyst** – skapar enkäter, analyser och rapporter  
- **Admin** – roller, moderation, radering, audit

---

## 2. Onboarding & grundläggande skydd

### US-01 – Snabb registrering via publik enkät
**Som** Parent  
**vill jag** kunna registrera mig via en publik enkätlänk  
**så att** tröskeln för deltagande är låg.

**AC**
- Registrering sker via e-post + verifiering
- Ingen publik profil skapas
- Användaren kan inte svara innan verifiering

**Testfall**
- TC-US01-01, TC-US01-02

---

### US-02 – Tydlig information om anonymitet
**Som** Parent  
**vill jag** få tydlig information om anonymitet och risker  
**så att** jag förstår vad som publiceras och inte.

**AC**
- Information visas vid:
  - registrering
  - start av enkät
- Informationen är kort, tydlig och icke-juridisk
- Uppmaning att inte lämna identifierande info i fritext

**Testfall**
- TC-US02-01, TC-SEC-01

---

## 3. Enkäter (insamling)

### US-03 – Skapa enkät (fri komposition)
**Som** Analyst  
**vill jag** komponera enkäter av olika frågetyper  
**så att** datan blir analysbar men lätt att svara på.

**AC**
- Stöd för:
  - skalor
  - flervalsfrågor
  - distinkta val
  - kort text
  - längre fritext
- Mjukt tak för längd
- Fördefinierade block kan återanvändas

**Testfall**
- TC-US03-01, TC-US03-02, TC-US03-03

---

### US-04 – Basblock visas bara en gång
**Som** Parent  
**vill jag** bara behöva svara på grundfrågor en gång  
**så att** senare enkäter går snabbare.

**AC**
- Basblock visas för nya användare
- Basblock hoppas över om redan besvarat
- Basblock används för:
  - skip-logik
  - default kommun i rapportvy

**Testfall**
- TC-US04-01, TC-US04-02

---

### US-05 – Enkät kan bara besvaras en gång
**Som** system  
**vill jag** förhindra dubbelsvar  
**så att** analysen inte snedvrids.

**AC**
- Samma konto kan inte svara två gånger
- Försök till dubbelsvar ger tydligt men neutralt fel

**Testfall**
- TC-US05-01

---

### US-06 – Svara på äldre enkäter
**Som** Parent  
**vill jag** kunna svara på öppna enkäter i efterhand  
**så att** mina erfarenheter fortfarande räknas.

**AC**
- Lista över öppna enkäter visas
- Status visas: svarad / ej svarad
- Nya svar påverkar aggregering och rapport

**Testfall**
- TC-US06-01

---

## 4. Återkoppling & resultat (Parent)

### US-07 – Direkt men begränsad återkoppling
**Som** Parent  
**vill jag** få viss återkoppling direkt  
**så att** mitt engagemang bibehålls.

**AC**
- Begränsad feedback efter avsnitt (default)
- Ingen exakt statistik visas vid lågt underlag
- Fördjupning sker via rapportvy

**Testfall**
- TC-US07-01, TC-US07-02, TC-US07-03

---

## 5. Analys & rapporter

### US-20 – Skapa rapportmall
**Som** Analyst  
**vill jag** skapa rapportmallar kopplade till en enkät  
**så att** analyser kan återanvändas och uppdateras.

**AC**
- Blockbaserad rapport:
  - text
  - diagram
  - tabeller
- Placeholders (t.ex. `$kommun`, `$antal_respondenter`)
- Enkla villkorstexter (MVP)
- WYSIWYG-preview
- Deterministisk rendering för given dataversion

**Testfall**
- TC-US20-01 – TC-US20-04

---

### US-21 – Kommunanpassad rapportvy
**Som** användare  
**vill jag** se rapporten för min kommun  
**så att** situationen blir lokal och relevant.

**AC**
- Kommun väljs via:
  1. URL-parameter
  2. basprofil
  3. manuellt val
- Small-n:
  - banner visas direkt
  - värden maskas med “X”
- Jämförelsevärden visas endast om tillräckligt underlag finns

**Testfall**
- TC-US21-01 – TC-US21-06

---

## 6. Publicering

### US-22 – Publicera rapport
**Som** Analyst  
**vill jag** publicera rapporter kontrollerat  
**så att** rätt innehåll blir publikt.

**AC**
- Default: intern
- Kan publiceras för:
  - inloggade
  - allmänheten
- Stabil canonical URL skapas
- Publicering är reversibel
- Ersättning skapar redirect
- Publicering med kuraterad fritext kräver extra bekräftelse

**Testfall**
- TC-US22-01 – TC-US22-04

---

## 7. Fritext & moderation

### US-15 – Moderera fritext
**Som** Admin/Analyst  
**vill jag** kunna granska och kuratera fritext  
**så att** publikt material inte blir identifierande.

**AC**
- Parent kan flagga fritext
- Redaktionella åtgärder:
  - redigera
  - kuratera
  - utesluta
- Endast kuraterad fritext får visas publikt
- Alla åtgärder audit-loggas

**Testfall**
- TC-US15-01 – TC-US15-03

---

## 8. Nätverk mellan föräldrar

### US-08 – Identifiera liknande situationer
**Som** system  
**vill jag** identifiera föräldrar i liknande situation  
**så att** nätverk kan erbjudas.

**AC**
- Matchning sker på grov nivå
- Ingen individinformation exponeras

**Testfall**
- TC-US08-01, TC-US08-02

---

### US-09 – Opt-in till kontakt
**Som** Parent  
**vill jag** själv välja om jag vill få kontakt  
**så att** jag behåller kontrollen.

**AC**
- Endast ja-sägare kopplas ihop
- Introduktion sker via e-post
- Mailet innehåller tydlig motivering
- Plattformens ansvar upphör efter introduktion

**Testfall**
- TC-US09-01 – TC-US09-03

---

## 9. AI-fördjupning

### US-13 – AI-baserad kontextanalys
**Som** Analyst  
**vill jag** kunna lägga till AI-genererad analys  
**så att** rapporten får djupare kontext.

**AC**
- Endast fasta prompts används
- AI-innehåll märks tydligt
- Påverkar inte kvantitativ analys

**Testfall**
- TC-US13-01, TC-US13-02

---

## 10. Administration

### US-19 – Roll- och behörighetsadministration
**Som** Admin  
**vill jag** hantera roller  
**så att** rätt personer gör rätt saker.

**AC**
- Roller:
  - Allmänheten
  - Parent
  - Analyst
  - Admin
- Ändringar slår igenom direkt
- Alla ändringar audit-loggas

**Testfall**
- TC-US19-01, TC-US19-02

---

## 11. Allmänheten

### US-30 – Läsa publika rapporter
**Som** medlem av allmänheten  
**vill jag** läsa publicerade rapporter utan inloggning  
**så att** kunskap sprids öppet.

**AC**
- Ingen inloggning krävs
- Endast publika rapporter visas
- Kuraterad fritext kan ingå
- Inga skyddade endpoints är åtkomliga

**Testfall**
- TC-SEC-01, TC-US22-04

---
