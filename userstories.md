# userstories.md
**Projekt:** Samarbets- och analysplattform för NPF-föräldrar  
**Version:** v1.3  
**Datum:** 2026-01-08  
**Status:** Fastställd (funktionella krav + testspårbarhet)

> Icke-funktionella krav (säkerhet, anonymitet, small-n-maskning,
> loggpolicy, åtkomst, drift m.m.) definieras och verifieras enligt `testplan.md`.
> User stories fokuserar på funktionellt beteende och domänspecifika krav.

---

## ONBOARDING & ANONYMITET

### US-01 – Snabb registrering via publik enkät
**Som** förälder  
**vill jag** kunna registrera mig snabbt via en publik enkätlänk  
**så att** jag kan svara utan krångel.

**AC**
- Registrering via e-post med verifiering
- Ingen publik profil skapas
- Användaren kan börja svara efter verifiering

**Tests**
- TC-US01-01, TC-US01-02

---

### US-02 – Anonymitet som default
**Som** förälder  
**vill jag** att mina svar är anonyma  
**så att** jag kan dela känsliga erfarenheter tryggt.

**AC**
- Identitet och svar hålls strikt åtskilda
- Endast aggregerad och/eller kuraterad data exponeras publikt
- Tydlig information om anonymitet visas i enkätflödet

**Tests**
- TC-US02-01, TC-US02-02, TC-SEC-01

---

## ENKÄTER

### US-03 – Skapa enkät
**Som** analytiker  
**vill jag** kunna skapa enkäter med olika frågetyper  
**så att** jag kan samla in både snabba svar och analysbar data.

**AC**
- Fri komposition av frågor
- Stöd för flera frågetyper (skala, flerval, kort/lång text m.fl.)
- Basblock visas för nya användare och hoppas över för återkommande
- Mjukt tak för längd

**Tests**
- TC-US03-01, TC-US03-02, TC-US03-03

---

### US-04 – Svara på enkät (en gång)
**Som** förälder  
**vill jag** bara kunna svara en gång per enkät  
**så att** resultaten inte snedvrids.

**AC**
- Systemet förhindrar dubbelsvar
- Bekräftelse visas efter inskick

**Tests**
- TC-US04-01, TC-US04-02

---

### US-05 – Svara på äldre enkäter
**Som** förälder  
**vill jag** kunna svara på öppna enkäter i efterhand  
**så att** mina svar fortfarande bidrar till analysen.

**AC**
- Lista över öppna enkäter visas
- Status: svarad / ej svarad
- Nya svar påverkar analys och rapport

**Tests**
- TC-US05-01

---

## RESULTAT & INSYN (FÖRÄLDER)

### US-07 – Visa aggregerade resultat
**Som** förälder  
**vill jag** få trygg och begriplig återkoppling  
**så att** jag förstår hur andra i liknande situation svarat.

**AC**
- Ingen separat resultatvy; återkoppling sker i flöde och via rapport
- Omedelbar feedback efter avsnitt (default; konfigurerbar)
- Fördjupning via rapportvy
- Presentation prioriterar begriplighet före precision vid låg tillförlitlighet

**Tests**
- TC-US07-01, TC-US07-02, TC-US07-03

---

## ANALYS & INFOGRAPHICS

### US-20 – Skapa kommenterad analysrapport
**Som** analytiker  
**vill jag** skapa rapporter med text och kommenterade diagram  
**så att** analysen blir begriplig och återanvändbar.

**AC**
- Blockbaserad rapport (text, diagram, tabeller, AI-block)
- Placeholders (t.ex. `$kommun`, `$antal_respondenter`)
- Enkla villkorstexter (MVP)
- WYSIWYG-preview
- Rapportmall kopplad till specifik enkät
- Rapportrendering ska vara reproducerbar för givet dataversionstillstånd

**Tests**
- TC-US20-01, TC-US20-02, TC-US20-03, TC-US20-04

---

### US-21 – Kommunanpassad rapportvisning
**Som** användare  
**vill jag** kunna läsa rapporten för min kommun  
**så att** jag ser lokal situation.

**AC**
- Kommunval via: query-param → basprofil → manuellt val
- Banner visas direkt vid öppning om underlag är för litet
- Kommunvärden maskas enligt policy
- Total/jämförelsevärden visas endast om underlag räcker

**Tests**
- TC-US21-01, TC-US21-02, TC-US21-03, TC-US21-04, TC-US21-05, TC-US21-06

---

## PUBLICERING

### US-22 – Publicera och dela rapport
**Som** analytiker  
**vill jag** kunna publicera rapporter kontrollerat  
**så att** rätt innehåll når rätt målgrupp.

**AC**
- Default-synlighet är intern
- Publicering är reversibel
- Stabil URL skapas vid publicering
- Ersättning skapar redirect till senaste version
- Publicering av rapport med kuraterad fritext kräver uttrycklig bekräftelse

**Tests**
- TC-US22-01, TC-US22-02, TC-US22-03, TC-US22-04

---

## NÄTVERK & SAMVERKAN

### US-08 – Erbjud nätverkskoppling
**Som** system  
**vill jag** identifiera liknande situationer  
**så att** samverkan kan erbjudas.

**AC**
- Erbjudande visar antal + grov kontext (ingen individexponering)

**Tests**
- TC-US08-01, TC-US08-02

---

### US-09 – Opt-in till kontakt
**Som** förälder  
**vill jag** själv välja om jag vill ha kontakt  
**så att** jag behåller kontrollen.

**AC**
- Endast ja-sägare kopplas ihop
- Introduktion sker via gemensamt e-postmeddelande
- Meddelandet innehåller motivering till varför det skickas
- Plattformens ansvar upphör efter introduktionen

**Tests**
- TC-US09-01, TC-US09-02, TC-US09-03

---

## AI-FÖRDJUPNING

### US-13 – Initiera AI-analys
**Som** analytiker  
**vill jag** köra AI-baserad fördjupning  
**så att** rapporten får kontext.

**AC**
- Endast fasta prompts används
- AI-innehåll märks tydligt
- Påverkar inte kvantitativ analys

**Tests**
- TC-US13-01, TC-US13-02

---

## ADMINISTRATION & SKYDD

### US-15 – Administrera dataskydd
**Som** admin  
**vill jag** styra åtkomst och moderation  
**så att** integritet efterlevs.

**AC**
- RBAC tillämpas
- Redaktionella ingrepp skapar audit-händelser
- Avpublicering är möjlig utan att radera historik

**Tests**
- TC-US15-01, TC-US15-02, TC-US15-03, TC-SEC-02

---

### US-19 – Roll- och behörighetsadmin
**Som** admin  
**vill jag** kunna tilldela roller  
**så att** rätt personer gör rätt saker.

**AC**
- Roller: Allmänheten / Parent / Analyst / Admin
- Alla ändringar loggas och slår igenom omedelbart

**Tests**
- TC-US19-01, TC-US19-02, TC-SEC-03, TC-SEC-04, TC-SEC-05

---
