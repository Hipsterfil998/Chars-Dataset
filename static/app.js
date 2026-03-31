const COLORS = [
  "#38bdf8","#818cf8","#34d399","#fb923c","#f472b6",
  "#a78bfa","#4ade80","#fbbf24","#e879f9","#60a5fa"
];

const occLabels = charStats.map(c => c.name);
const occData   = charStats.map(c => c.occurrences);

const ctxOcc = document.getElementById("chartOccurrences").getContext("2d");
const occChart = new Chart(ctxOcc, {
  type: "bar",
  data: {
    labels: occLabels,
    datasets: [{
      label: "Occurrences",
      data: occData,
      backgroundColor: COLORS,
      borderRadius: 4,
    }]
  },
  options: {
    indexAxis: "y",
    responsive: true,
    plugins: { legend: { display: false } },
    scales: {
      x: { ticks: { color: "#94a3b8" }, grid: { color: "#1e293b" } },
      y: { ticks: { color: "#e2e8f0" }, grid: { color: "#1e293b" } }
    },
    onClick: (_evt, elements) => {
      if (!elements.length) return;
      const idx = elements[0].index;
      const name = occLabels[idx];
      showRoles(name);
    }
  }
});

const ctxRoles = document.getElementById("chartRoles").getContext("2d");
let rolesChart = null;

function showRoles(name) {
  document.getElementById("charNameLabel").textContent = name;
  const roles = rolesByChar[name] || [];
  const labels = roles.map(r => r.role);
  const data   = roles.map(r => r.count);

  if (rolesChart) {
    rolesChart.data.labels = labels;
    rolesChart.data.datasets[0].data = data;
    rolesChart.update();
  } else {
    rolesChart = new Chart(ctxRoles, {
      type: "bar",
      data: {
        labels,
        datasets: [{
          label: "Count",
          data,
          backgroundColor: "#818cf8",
          borderRadius: 4,
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { color: "#e2e8f0" }, grid: { color: "#1e293b" } },
          y: { ticks: { color: "#94a3b8" }, grid: { color: "#1e293b" } }
        }
      }
    });
  }
}

if (occLabels.length) showRoles(occLabels[0]);
