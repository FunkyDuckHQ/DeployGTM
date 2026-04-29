const fs = require("fs");
const path = require("path");

const root = process.cwd();
const dist = path.join(root, "dist");

const files = [
  "index.html",
  "dashboard.css",
  "dashboard.js",
  "3_operations/outputs/peregrine_score_snapshots.json",
  "3_operations/outputs/peregrine_route_report.md",
];

fs.rmSync(dist, { recursive: true, force: true });

for (const file of files) {
  const source = path.join(root, file);
  const target = path.join(dist, file);
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.copyFileSync(source, target);
}

console.log(`Built static dashboard in ${dist}`);
