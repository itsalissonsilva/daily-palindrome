import { cpSync, existsSync, lstatSync, rmSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const projectRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const source = join(projectRoot, "site");
const destination = join(projectRoot, "dist");

if (!existsSync(source) || !lstatSync(source).isDirectory()) {
  throw new Error(`Static site source is missing: ${source}`);
}

rmSync(destination, { recursive: true, force: true });
cpSync(source, destination, { recursive: true, dereference: false });

console.log(`Prepared static site at ${destination}`);
