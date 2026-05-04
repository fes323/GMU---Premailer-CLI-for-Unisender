const fs = require("fs");
const path = require("path");
const { resolveNodeModule } = require("./node_module_loader");

function loadJuiceOptions() {
  const configPath = process.env.GMU_JUICE_CONFIG || path.join(__dirname, "juice_config.js");
  try {
    return require(configPath);
  } catch (error) {
    throw new Error(
      `Cannot load Juice config from '${configPath}'. ` +
        (error && error.message ? error.message : String(error))
    );
  }
}

try {
  const juice = resolveNodeModule("juice", "GMU_JUICE_MODULE");
  const juiceOptions = loadJuiceOptions();
  const html = fs.readFileSync(0, "utf8");
  const result = juice(html, juiceOptions);

  process.stdout.write(result);
} catch (error) {
  process.stderr.write(error && error.stack ? error.stack : String(error));
  process.exit(1);
}
