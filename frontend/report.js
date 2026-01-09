const params = new URLSearchParams(window.location.search);
const slug = params.get("slug");
const initialKommun = params.get("kommun") || "";

const titleEl = document.getElementById("report-title");
const subtitleEl = document.getElementById("report-subtitle");
const kommunInput = document.getElementById("kommun-input");
const kommunSubmit = document.getElementById("kommun-submit");
const banner = document.getElementById("small-n-banner");
const blocks = document.getElementById("report-blocks");
const totalEl = document.getElementById("report-total");
const curatedList = document.getElementById("curated-texts");

kommunInput.value = initialKommun;

function setTitle(text) {
  document.title = text;
  titleEl.textContent = text;
}

function setSubtitle(text) {
  subtitleEl.textContent = text;
}

function renderBlocks(blockItems) {
  blocks.innerHTML = "";
  blockItems.forEach((block) => {
    const div = document.createElement("div");
    div.className = "card";
    div.textContent = block.content || "";
    blocks.appendChild(div);
  });
}

function renderCurated(texts) {
  curatedList.innerHTML = "";
  texts.forEach((text) => {
    const li = document.createElement("li");
    li.textContent = text;
    curatedList.appendChild(li);
  });
}

async function loadReport(kommun) {
  if (!slug || !kommun) {
    setTitle("Rapport saknas");
    setSubtitle("Ange rapport-id och kommun för att läsa rapporten.");
    return;
  }

  const response = await fetch(`/reports/${encodeURIComponent(slug)}?kommun=${encodeURIComponent(kommun)}`);
  const data = await response.json();
  const payload = data.payload;

  setTitle(`Rapport ${slug}`);
  setSubtitle(`Kommun: ${payload.kommun}`);

  banner.classList.toggle("hidden", !payload.small_n_banner);
  totalEl.textContent = `Antal respondenter: ${payload.metrics.total}`;

  renderBlocks(payload.blocks);
  renderCurated(payload.curated_texts || []);
}

kommunSubmit.addEventListener("click", () => {
  const kommun = kommunInput.value.trim();
  loadReport(kommun);
});

loadReport(initialKommun);
