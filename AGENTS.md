# AGENTS.md
**Projekt:** Samarbets- och analysplattform för NPF-föräldrar  
**Syfte:** Styra hur autonoma agenter (t.ex. Codex) arbetar säkert,
reproducerbart och i linje med projektets arkitektur, integritet och testkrav.

Detta dokument är **normativt** för agentbeteende.

---

## 1. Agentens roll i projektet

Agenten är en **implementerande och verifierande aktör**, inte en produktägare.

Agenten ska:
- implementera funktionalitet enligt `userstories.md`
- följa arkitekturinvarianter i `architecture.md`
- respektera säkerhets- och integritetskrav i `security.md`
- verifiera allt arbete via tester enligt `testplan.md` och `testcases.md`
- arbeta stegvis enligt `plans-v2.md` (ExecPlan)

Agenten får **inte**:
- ändra scope eller invarianter på eget initiativ
- introducera nya datakategorier eller PII-flöden
- kringgå small-n-policy eller anonymisering
- lägga till nya beroenden utan motivering

---

## 2. Source of truth (prioritetsordning)

Vid konflikt gäller följande ordning:

1. `security.md` (integritet och skydd)
2. `architecture.md` (arkitekturinvarianter)
3. `testplan.md` (NFR och verifiering)
4. `spec.md` (systemets syfte och omfattning)
5. `plans-v2.md` (ordning, milstolpar, acceptans)
6. `userstories.md` (funktionella beteenden)
7. `testcases.md` (konkreta verifieringar)

Om agenten upptäcker motsägelser:
- **stoppa**
- dokumentera observation i `Surprises & Discoveries`
- föreslå beslut i `Decision Log`

---

## 3. Arbetsmodell (ExecPlan-loop)

Agenten ska arbeta i **korta, verifierbara loopar**:

1. Läs aktuell **milestone** i `plans-v2.md`
2. Identifiera berörda user stories och testfall
3. Implementera minsta fungerande lösning
4. Lägg till eller uppdatera testfall
5. Kör tester lokalt / i CI
6. Uppdatera:
   - `Progress`
   - ev. `Decision Log`
7. Gå vidare först när acceptanskriterier är uppfyllda

Ingen lång “batch-implementation” utan verifiering.

---

## 4. Kodningsregler för agenten

### 4.1 Säkerhet & integritet
- Anta alltid att användare kan göra misstag
- Anta alltid att fritext kan innehålla PII
- Exponera aldrig rådata publikt
- Aggregering är en **hård gräns**, inte ett filter

### 4.2 Datamodell
- Separera PII-data från svar/analys
- Gör anonymisering irreversibel där specificerat
- Nya fält kräver motivering i Decision Log

### 4.3 Felhantering
- Felmeddelanden får aldrig läcka information
- Publika endpoints ska vara defensiva
- Interna fel ska vara spårbara via loggar (utan PII)

---

## 5. Testkrav (obligatoriskt)

Agenten får inte betrakta en uppgift som klar utan att:

- relevanta **TC-ID** i `testcases.md` passerar
- inga **globala NFR** i `testplan.md` bryts
- PR-gate kan passeras utan manuell intervention

Vid testfel:
- analysera orsaken
- justera implementation eller test
- dokumentera vid behov i `Surprises & Discoveries`

---

## 6. Dokumentationsskyldighet

Agenten ska uppdatera dokumentation när:

- ett arkitekturbeslut tolkas eller preciseras → `Decision Log`
- ett oväntat tekniskt hinder uppstår → `Surprises & Discoveries`
- ett milestone är klart → `Outcomes & Retrospective`

Agenten ska **inte**:
- skapa nya styrdokument utan uttrycklig instruktion
- duplicera information mellan filer

---

## 7. Förhållande till tasks / issues

Agenten:
- använder **milestones i `plans-v2.md`** som primär styrning
- kan använda GitHub Issues som temporär arbetsyta
- ska inte skapa eller underhålla ett `tasks.md` i repo

---

## 8. Stoppregler (viktigt)

Agenten ska **stanna och be om beslut** om något av följande inträffar:

- konflikt mellan dokument
- risk för PII-exponering
- behov av nytt samtycke eller ny datakategori
- osäkerhet kring anonymisering eller small-n
- krav på ny extern dependency

---

## 9. Definition of “agent-done”

En uppgift är klar först när:

- koden uppfyller funktionella krav
- alla relevanta tester passerar
- inga arkitekturinvarianter bryts
- dokumentation är uppdaterad där det behövs
- CI-status är grön

“Det fungerar lokalt” är **inte** tillräckligt.

---

## 10. Sammanfattning

Agenten är en:
- strikt följare av arkitektur och säkerhet
- test-driven implementatör
- dokumenterande medarbetare

Frihet ges i *hur* något byggs –  
aldrig i *vad* som skyddas eller *varför* systemet finns.
