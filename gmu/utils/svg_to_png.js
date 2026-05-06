const fs = require("fs");
const { resolveNodeModule } = require("./node_module_loader");

function parseArgs(argv) {
  const options = {};

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--width") {
      const value = Number.parseInt(argv[i + 1], 10);
      if (!Number.isFinite(value) || value <= 0) {
        throw new Error("--width must be a positive integer");
      }
      options.width = value;
      i += 1;
    }
  }

  return options;
}

try {
  const { Resvg } = resolveNodeModule("@resvg/resvg-js", "GMU_RESVG_MODULE");
  const args = parseArgs(process.argv.slice(2));
  const svg = fs.readFileSync(0);
  const renderOptions = {};

  if (args.width) {
    renderOptions.fitTo = {
      mode: "width",
      value: args.width,
    };
  }

  const resvg = new Resvg(svg, renderOptions);
  const pngBuffer = resvg.render().asPng();
  process.stdout.write(pngBuffer);
} catch (error) {
  process.stderr.write(error && error.stack ? error.stack : String(error));
  process.exit(1);
}
