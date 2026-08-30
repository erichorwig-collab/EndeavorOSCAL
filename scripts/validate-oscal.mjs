import { readFile } from "node:fs/promises";
import Ajv from "ajv";

const [schemaPath, documentPath] = process.argv.slice(2);
if (!schemaPath || !documentPath) {
  console.error("usage: validate-oscal.mjs SCHEMA.json DOCUMENT.json");
  process.exit(2);
}

const [schema, document] = await Promise.all([
  readFile(schemaPath, "utf8").then(JSON.parse),
  readFile(documentPath, "utf8").then(JSON.parse),
]);
const ajv = new Ajv({ allErrors: true, strict: false, validateFormats: false });
const validate = ajv.compile(schema);
if (!validate(document)) {
  for (const error of validate.errors ?? []) {
    console.error(`${error.instancePath || "/"}: ${error.message}`);
  }
  process.exit(1);
}
