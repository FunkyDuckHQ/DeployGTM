const http = require("http");
const fs = require("fs");
const path = require("path");

const root = path.join(process.cwd(), "dist");
const port = Number(process.env.PORT || 4173);

const types = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
};

function resolveRequest(url = "/") {
  const clean = decodeURIComponent(url.split("?")[0]);
  const file = clean === "/" ? "/index.html" : clean;
  const resolved = path.resolve(root, `.${file}`);
  return resolved.startsWith(root) ? resolved : null;
}

http
  .createServer((request, response) => {
    const filePath = resolveRequest(request.url);
    if (!filePath || !fs.existsSync(filePath) || fs.statSync(filePath).isDirectory()) {
      response.writeHead(404, { "content-type": "text/plain; charset=utf-8" });
      response.end("Not found");
      return;
    }

    response.writeHead(200, { "content-type": types[path.extname(filePath)] || "application/octet-stream" });
    fs.createReadStream(filePath).pipe(response);
  })
  .listen(port, () => {
    console.log(`DeployGTM web dashboard running at http://127.0.0.1:${port}`);
  });
