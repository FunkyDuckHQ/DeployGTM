const fs = require("fs");
const path = require("path");

const root = process.cwd();
const dist = path.join(root, "dist");

const files = [
  "index.html",
  "dashboard.css",
  "dashboard.js",
  "dashboard_manifest.json",
  "clients/peregrine_space/outputs/score_snapshots.json",
  "clients/peregrine_space/outputs/route_report.md",
];

fs.rmSync(dist, { recursive: true, force: true });

for (const file of files) {
  const source = path.join(root, file);
  const target = path.join(dist, file);
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.copyFileSync(source, target);
}

console.log(`Built static dashboard in ${dist}`);
