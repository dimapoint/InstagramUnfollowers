import { file } from "bun";

const indexPath = Bun.argv[2];
const minifiedCodePath = Bun.argv[3];

const CODE_BLOCK_START = 'const instagramScript = "';
const CODE_BLOCK_END = '";//__END_OF_SCRIPT__';

const indexFile = file(indexPath);
const minifiedCodeFile = file(minifiedCodePath);

let indexData = await indexFile.text();
let minifiedCode = await minifiedCodeFile.text();

const replaceStartIndex = indexData.indexOf(CODE_BLOCK_START) + CODE_BLOCK_START.length;
const replaceEndIndex = indexData.lastIndexOf(CODE_BLOCK_END);

if (replaceStartIndex === CODE_BLOCK_START.length - 1) {
  console.error("Could not find CODE_BLOCK_START in index.html");
  process.exit(1);
}

if (replaceEndIndex === -1) {
  console.error("Could not find CODE_BLOCK_END in index.html");
  process.exit(1);
}

// Properly escape all special characters
minifiedCode = minifiedCode
  .replace(/\\/g, '\\\\')    // Escape backslashes first
  .replace(/"/g, '\\"')      // Escape quotes
  .replace(/\n/g, '\\n')     // Escape newlines
  .replace(/\r/g, '\\r')     // Escape carriage returns
  .replace(/\t/g, '\\t')     // Escape tabs
  .replace(/\f/g, '\\f');    // Escape form feeds

const updatedIndexData = 
  indexData.substring(0, replaceStartIndex) + 
  minifiedCode + 
  indexData.substring(replaceEndIndex);

await Bun.write(indexPath, updatedIndexData);
console.log("Successfully updated index.html with minified code.");
