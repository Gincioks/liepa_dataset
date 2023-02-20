const fs = require("fs");
const readline = require("readline");

const fileNames = ["output.tsv"]; // array of file names to process

const rows = [];
const sentences = new Set(); // declare a Set to store the unique sentences

fileNames.forEach((filePath) => {
  // process each file in the array
  const rl = readline.createInterface({
    input: fs.createReadStream(filePath),
    crlfDelay: Infinity,
  });

  let columnNames = [];

  rl.on("line", (line) => {
    const values = line.split("\t");

    if (columnNames.length === 0) {
      columnNames = values;
    } else {
      const row = {};
      values.forEach((value, index) => {
        row[columnNames[index]] = value;
        if (columnNames[index] === "Sentence") {
          if (sentences.has(value)) {
            console.log(`Duplicate sentence found in ${filePath}: "${value}"`);
          } else {
            sentences.add(value);
          }
        }
      });
      rows.push(row);
    }
  });

  rl.on("close", () => {
    console.log(`Finished processing ${filePath}`);
  });
});
