const fs = require("fs");
const path = require("path");

const rootDir = "./MII_LIEPA_REC_V1";
const fileToDelete = ".DS_Store";

function deleteFileRecursively(dir) {
  fs.readdir(dir, (err, files) => {
    if (err) {
      console.error(`Error reading directory ${dir}:`, err);
      return;
    }

    files.forEach((file) => {
      const filePath = path.join(dir, file);
      fs.stat(filePath, (err, stats) => {
        if (err) {
          console.error(`Error getting stats for ${filePath}:`, err);
          return;
        }

        if (stats.isDirectory()) {
          deleteFileRecursively(filePath);
        } else if (stats.isFile() && file === fileToDelete) {
          fs.unlink(filePath, (err) => {
            if (err) {
              console.error(`Error deleting file ${filePath}:`, err);
              return;
            }

            console.log(`Deleted file: ${filePath}`);
          });
        }
      });
    });
  });
}

deleteFileRecursively(rootDir);
