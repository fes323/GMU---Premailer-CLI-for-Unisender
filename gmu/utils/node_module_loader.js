const path = require("path");
const { execFileSync } = require("child_process");

function addUnique(values, value) {
  if (value && !values.includes(value)) {
    values.push(value);
  }
}

function getGlobalNpmRoot() {
  const commands = process.platform === "win32" ? ["npm.cmd", "npm"] : ["npm"];

  for (const command of commands) {
    try {
      const root = execFileSync(command, ["root", "-g"], {
        encoding: "utf8",
        stdio: ["ignore", "pipe", "ignore"],
      }).trim();

      if (root) {
        return root;
      }
    } catch (_) {
      // Some Node/Windows combinations cannot spawn npm.cmd from node.
    }
  }

  return null;
}

function getGlobalModuleRoots() {
  const roots = [];
  const prefixes = [];

  addUnique(roots, getGlobalNpmRoot());

  addUnique(prefixes, process.env.NPM_CONFIG_PREFIX);
  addUnique(prefixes, process.env.npm_config_prefix);

  if (process.env.APPDATA) {
    addUnique(prefixes, path.join(process.env.APPDATA, "npm"));
  }

  if (process.env.USERPROFILE) {
    addUnique(prefixes, path.join(process.env.USERPROFILE, "AppData", "Roaming", "npm"));
  }

  if (process.env.ProgramFiles) {
    addUnique(prefixes, path.join(process.env.ProgramFiles, "nodejs"));
  }

  if (process.env["ProgramFiles(x86)"]) {
    addUnique(prefixes, path.join(process.env["ProgramFiles(x86)"], "nodejs"));
  }

  addUnique(prefixes, path.dirname(process.execPath));

  for (const prefix of prefixes) {
    if (path.basename(prefix).toLowerCase() === "node_modules") {
      addUnique(roots, prefix);
    } else {
      addUnique(roots, path.join(prefix, "node_modules"));
    }
  }

  return roots;
}

function getModuleSearchRoots() {
  const roots = [
    process.cwd(),
    path.resolve(__dirname, "..", ".."),
    __dirname,
    ...((process.env.NODE_PATH || "").split(path.delimiter).filter(Boolean)),
    ...getGlobalModuleRoots(),
  ];

  return roots.filter(Boolean);
}

function resolveNodeModule(moduleName, envVarName) {
  if (process.env[envVarName]) {
    return require(process.env[envVarName]);
  }

  const attemptedRoots = [];
  for (const root of getModuleSearchRoots()) {
    try {
      const resolved = require.resolve(moduleName, { paths: [root] });
      return require(resolved);
    } catch (_) {
      attemptedRoots.push(root);
    }
  }

  throw new Error(
    `Cannot load npm package '${moduleName}'. Run \`npm install\` in the ` +
      `current project, install it globally, or set ${envVarName} to the ` +
      `installed module path. Searched in: ${attemptedRoots.join("; ")}`
  );
}

module.exports = {
  getModuleSearchRoots,
  resolveNodeModule,
};
