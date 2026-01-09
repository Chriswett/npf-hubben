const newsList = document.getElementById("news-list");
const reportList = document.getElementById("report-list");
const reportFilter = document.getElementById("report-filter");

const state = {
  reports: [],
};

function createNewsItem(item) {
  const li = document.createElement("li");
  li.className = "card";
  li.innerHTML = `<strong>${item.title}</strong><p>${item.body}</p>`;
  return li;
}

function createReportItem(report) {
  const li = document.createElement("li");
  const slug = report.canonical_url.replace("/reports/", "");
  li.innerHTML = `<a class="report-link" href="/ui/report.html?slug=${encodeURIComponent(
    slug,
  )}">${slug}</a>`;
  return li;
}

function renderReports(filterText) {
  reportList.innerHTML = "";
  const normalized = filterText?.toLowerCase() || "";
  state.reports
    .filter((report) => report.canonical_url.toLowerCase().includes(normalized))
    .forEach((report) => {
      reportList.appendChild(createReportItem(report));
    });
}

async function loadNews() {
  const response = await fetch("/public/news");
  const data = await response.json();
  newsList.innerHTML = "";
  if (!data.news.length) {
    newsList.innerHTML = "<li>Inga nyheter än.</li>";
    return;
  }
  data.news.forEach((item) => newsList.appendChild(createNewsItem(item)));
}

async function loadReports() {
  const response = await fetch("/public/reports");
  const data = await response.json();
  state.reports = data.reports;
  renderReports(reportFilter.value);
}

reportFilter.addEventListener("input", (event) => {
  renderReports(event.target.value);
});

loadNews();
loadReports();
