const routeLabels = {
  manual_sales_review_and_enrich: "Manual sales review + enrich",
  enrich_and_campaign_test: "Enrich + campaign test",
  enrich_selectively_or_monitor: "Selective enrichment or monitor",
  manual_sales_review: "Manual sales review",
  monitor_or_test_cohort: "Monitor or test cohort",
  human_review_only: "Human review only",
  hold_or_monitor: "Hold or monitor",
  exclude: "Exclude",
};

const routeClass = (route) => {
  if (route.includes("exclude")) return "exclude";
  if (route.includes("monitor") || route.includes("hold")) return "monitor";
  if (route.includes("manual")) return "manual";
  return "enrich";
};

const nextAction = (route) => {
  const actions = {
    manual_sales_review_and_enrich:
      "Assign to founder/seller, enrich contacts, and draft founder-reviewed outreach.",
    enrich_and_campaign_test:
      "Enrich likely buyers and create a controlled message-market fit test.",
    enrich_selectively_or_monitor:
      "Monitor for urgency signals and enrich only if a timing event appears.",
    manual_sales_review: "Review manually before any automation.",
    human_review_only: "Review manually before any automation.",
    monitor_or_test_cohort: "Keep in a small test cohort or monitor for stronger timing.",
    hold_or_monitor: "Hold until more evidence appears.",
    exclude: "Exclude from current motion.",
  };
  return actions[route] || "Review route before action.";
};

let allSnapshots = [];
let activeRoute = null;

const number = (value) => Number(value || 0);
const average = (items, key) =>
  items.length ? items.reduce((sum, item) => sum + number(item[key]), 0) / items.length : 0;

function renderSummary(items, generatedAt) {
  document.getElementById("accountsScored").textContent = items.length;
  document.getElementById("avgIcp").textContent = Math.round(average(items, "icp_score"));
  document.getElementById("avgUrgency").textContent = Math.round(average(items, "urgency_score"));
  document.getElementById("actionableRoutes").textContent = items.filter((item) =>
    ["manual_sales_review_and_enrich", "enrich_and_campaign_test"].includes(item.recommended_route)
  ).length;
  document.getElementById("generatedAt").textContent = `Generated ${generatedAt}`;
}

function renderFilters(items) {
  const container = document.getElementById("routeFilters");
  const counts = items.reduce((acc, item) => {
    acc[item.recommended_route] = (acc[item.recommended_route] || 0) + 1;
    return acc;
  }, {});

  container.innerHTML = "";
  Object.entries(counts).forEach(([route, count]) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `route-button ${activeRoute === route ? "active" : ""}`;
    button.innerHTML = `<span>${routeLabels[route] || route}</span><strong>${count}</strong>`;
    button.addEventListener("click", () => {
      activeRoute = activeRoute === route ? null : route;
      render();
    });
    container.appendChild(button);
  });
}

function scoreBar(label, value) {
  const safeValue = Math.max(0, Math.min(100, number(value)));
  return `
    <div class="score-block">
      <div class="score-label">${label}: ${safeValue.toFixed(safeValue % 1 ? 1 : 0)}</div>
      <div class="bar" aria-hidden="true"><span style="width:${safeValue}%"></span></div>
    </div>
  `;
}

function evidenceList(evidence) {
  if (!evidence?.length) return "<p class=\"subtle\">No evidence attached.</p>";
  return `
    <ul class="evidence">
      ${evidence
        .map(
          (item) => `
          <li>
            <strong>${item.signal_type || "signal"}</strong>: ${item.summary || ""}
            <br>
            Strength ${item.current_strength}, confidence ${item.confidence}
            ${item.source_url ? `<br><a href="${item.source_url}">Source</a>` : ""}
          </li>
        `
        )
        .join("")}
    </ul>
  `;
}

function renderAccounts(items) {
  const container = document.getElementById("accountList");
  container.innerHTML = items
    .map(
      (item) => `
        <article class="account">
          <div class="account-header">
            <div>
              <h3>${item.company_name}</h3>
              <div class="domain">${item.account_id}</div>
            </div>
            <span class="route ${routeClass(item.recommended_route)}">
              ${routeLabels[item.recommended_route] || item.recommended_route}
            </span>
          </div>

          <div class="score-row">
            ${scoreBar("ICP", item.icp_score)}
            ${scoreBar("Urgency", item.urgency_score)}
          </div>

          <p class="next-action"><strong>Next action:</strong> ${nextAction(item.recommended_route)}</p>
          ${evidenceList(item.evidence)}
        </article>
      `
    )
    .join("");
}

function render() {
  const filtered = activeRoute
    ? allSnapshots.filter((item) => item.recommended_route === activeRoute)
    : allSnapshots;
  renderFilters(allSnapshots);
  renderAccounts(filtered);
}

async function loadDashboard() {
  const response = await fetch("3_operations/outputs/peregrine_score_snapshots.json");
  if (!response.ok) throw new Error("Unable to load score snapshots");
  const data = await response.json();
  allSnapshots = data.score_snapshots || [];
  renderSummary(allSnapshots, data.generated_at || "unknown");
  render();
}

document.getElementById("resetFilters").addEventListener("click", () => {
  activeRoute = null;
  render();
});

loadDashboard().catch((error) => {
  document.getElementById("accountList").innerHTML = `
    <article class="account">
      <h3>Dashboard failed to load</h3>
      <p class="subtle">${error.message}</p>
    </article>
  `;
});
