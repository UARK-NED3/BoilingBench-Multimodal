const DATA = {
  archive: "data/archive.json",
  visual: "data/gpu_bubble_area.json",
  temporal: "data/gpu_temporal_heat_flux.json",
};

const visualLabels = {
  base_test: { name: "Base test", verdict: "GOOD IN-DOMAIN", tone: "good", note: "Explicit held-out split" },
  new_facility_external: { name: "New facility", verdict: "PARTIAL TRANSFER", tone: "partial", note: "External evaluation only" },
  flow_external: { name: "Flow external", verdict: "TRANSFER FAILURE", tone: "bad", note: "Baseline is safer" },
};

const temporalLabels = {
  "BB-1": { verdict: "BASELINE-LEVEL", tone: "bad", note: "No useful gain" },
  "BB-2": { verdict: "UNSTABLE", tone: "bad", note: "Severe dataset shift" },
  "BB-3": { verdict: "PROMISING", tone: "good", note: "Transferable signal" },
  "BB-4": { verdict: "PROMISING", tone: "good", note: "Strongest fold" },
};

const $ = (selector) => document.querySelector(selector);
const formatInt = (value) => new Intl.NumberFormat("en-US").format(value);
const formatMetric = (value, digits = 3) => Number(value).toLocaleString("en-US", { maximumFractionDigits: digits, minimumFractionDigits: digits });
const formatR2 = (value) => Number(value).toLocaleString("en-US", { maximumFractionDigits: 3, minimumFractionDigits: 3 });
const mean = (rows, key) => rows.reduce((sum, row) => sum + Number(row[key]), 0) / rows.length;

function visualSummary(runs, key) {
  const rows = runs.map((run) => run.evaluations[key]);
  return {
    n: rows[0].n,
    baseline: mean(rows, "baseline_mae_area_fraction"),
    model: mean(rows, "mae_area_fraction"),
    r2: mean(rows, "r2"),
  };
}

function temporalSummary(folds, dataset) {
  const rows = folds.filter((fold) => fold.test_dataset === dataset);
  return {
    n: rows[0].n_test,
    baseline: rows[0].baseline_mae_W_cm2,
    model: mean(rows, "mae_W_cm2"),
    r2: mean(rows, "r2"),
  };
}

function badge(text, tone) {
  return `<span class="read-badge read-${tone}">${text}</span>`;
}

function renderArchive(archive, visual, temporal) {
  const status = archive.status === "pass" ? "VERIFIED RELEASE" : "CHECK REQUIRED";
  $("#top-status").textContent = status;
  $("#archive-stat").textContent = archive.status === "pass" ? "PASS" : "CHECK";
  $("#archive-detail").textContent = `${formatInt(archive.bytes)} bytes accounted for`;
  $("#archive-meter").style.width = archive.status === "pass" ? "100%" : "35%";
  $("#file-stat").textContent = formatInt(archive.files);
  $("#gpu-stat").textContent = visual.gpu_name.replace("NVIDIA ", "");
  $("#archive-status").textContent = status;
  $("#revision-value").textContent = archive.revision;
  $("#manifest-link").href = archive.manifest_url;
}

function renderVisual(visual) {
  const summaryRows = Object.keys(visualLabels).map((key) => ({ key, ...visualLabels[key], ...visualSummary(visual.runs, key) }));
  const maxMae = Math.max(...summaryRows.map((row) => Math.max(row.baseline, row.model)));
  $("#visual-table tbody").innerHTML = summaryRows.map((row) => `
    <tr>
      <td>${row.name}</td><td>${formatInt(row.n)}</td><td>${formatMetric(row.baseline)}</td><td>${formatMetric(row.model)}</td><td>${formatR2(row.r2)}</td><td>${badge(row.verdict, row.tone)}</td>
    </tr>`).join("");
  $("#visual-cards").innerHTML = summaryRows.map((row) => {
    const change = ((row.baseline - row.model) / row.baseline) * 100;
    const changeText = change >= 0 ? `${formatMetric(change, 1)}% lower MAE` : `${formatMetric(Math.abs(change), 1)}% higher MAE`;
    return `<article class="domain-card ${row.tone}">
      <div class="domain-card-top"><span class="domain-name">${row.name}</span><span class="domain-verdict ${row.tone}">${row.verdict}</span></div>
      <div class="domain-number">${formatMetric(row.model)}</div><span class="domain-unit">MODEL MAE / AREA FRACTION</span>
      <div class="domain-detail"><span>${row.note}</span><strong>${changeText}</strong></div>
    </article>`;
  }).join("");
  const base = summaryRows.find((row) => row.key === "base_test");
  const lift = ((base.baseline - base.model) / base.baseline) * 100;
  $("#visual-lift").textContent = `${formatMetric(lift, 1)}%`;
  $("#visual-bars").innerHTML = [
    ["model", base.model, ""],
    ["baseline", base.baseline, "baseline"],
  ].map(([name, value, tone]) => `<div class="bar-row"><span>${name}</span><div class="bar-track"><div class="bar-fill ${tone}" style="width:${Math.max(3, (value / maxMae) * 100)}%"></div></div><strong>${formatMetric(value)}</strong></div>`).join("");
}

function renderTemporal(temporal) {
  const rows = Object.keys(temporalLabels).map((dataset) => ({ dataset, ...temporalLabels[dataset], ...temporalSummary(temporal.folds, dataset) }));
  const maxMae = Math.max(...rows.map((row) => Math.max(row.baseline, row.model)));
  $("#temporal-grid").innerHTML = rows.map((row) => `<article class="temporal-card ${row.tone}">
    <div class="temporal-card-top"><span>${row.dataset}</span><span>${formatInt(row.n)} WINDOWS</span></div>
    <h3>${row.verdict}</h3><p>${row.note}</p>
    <div class="temporal-bars">
      <div class="temporal-bar-row"><span>BASE</span><div class="temporal-track"><div class="temporal-fill" style="width:${Math.max(2, (row.baseline / maxMae) * 100)}%"></div></div><strong>${formatMetric(row.baseline, 1)}</strong></div>
      <div class="temporal-bar-row"><span>MODEL</span><div class="temporal-track"><div class="temporal-fill model" style="width:${Math.max(2, (row.model / maxMae) * 100)}%"></div></div><strong>${formatMetric(row.model, 1)}</strong></div>
    </div>
    <div class="temporal-r2">R²<strong>${formatR2(row.r2)}</strong></div>
  </article>`).join("");
  $("#temporal-table tbody").innerHTML = rows.map((row) => `<tr>
    <td>${row.dataset}</td><td>${formatInt(row.n)}</td><td>${formatMetric(row.baseline, 1)}</td><td>${formatMetric(row.model, 1)}</td><td>${formatR2(row.r2)}</td><td>${badge(row.verdict, row.tone)}</td>
  </tr>`).join("");
}

function renderError(error) {
  console.error(error);
  $("#top-status").textContent = "DATA LOAD ERROR";
  $("#archive-stat").textContent = "ERROR";
  $("#archive-detail").textContent = "Could not load result files";
  document.querySelectorAll(".loading-row").forEach((row) => { row.textContent = "Result file unavailable. See the working record below."; });
}

async function start() {
  try {
    const [archive, visual, temporal] = await Promise.all(Object.values(DATA).map((path) => fetch(path).then((response) => {
      if (!response.ok) throw new Error(`Could not load ${path}`);
      return response.json();
    })));
    renderArchive(archive, visual, temporal);
    renderVisual(visual);
    renderTemporal(temporal);
  } catch (error) {
    renderError(error);
  }
}

start();
