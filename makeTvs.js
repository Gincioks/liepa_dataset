const fs = require("fs");
const path = require("path");

const dirPath = "./MII_LIEPA_REC_V1";
const folderPrefix = "S";
const outputFileName = "liepa_dataset/train.tsv";
const audioFolder = "liepa_dataset/clips";

// Default values
const up_votes = 0;
const down_votes = 0;
const accents = "";
const locale = "lt";
const segment = "";

const writeStream = fs.createWriteStream(outputFileName);
writeStream.write("client_id\tpath\taudio\tsentence\tup_votes\tdown_votes\tage\tgender\taccent\tlocale\tsegment\n");

const prepareInfoFromFile = (filePath) => {
  const pathWithoutExt = filePath.split(".")[0];
  const separatedFilePath = filePath.split("/");
  const fileNameWithExt = separatedFilePath[separatedFilePath.length - 1];
  const fileName = fileNameWithExt.split(".")[0];
  const regex = /(\d+|[a-zA-Z]+)/g;
  const result = fileName.match(regex);
  const client_id = result[1];
  let audioFileName = result[1];
  const userInfo = result[2].split("");
  const genger = userInfo[0] === "M" ? "female" : "male";
  audioFileName = `${audioFileName}${userInfo[0] === "M" ? 0 : 1}`;
  let age = "";

  const teensPattern = /[cdefghijk]/g;
  const twentiesPattern = /[lm]/g;
  const thirtiesPattern = /[nopqr]/g;

  if (userInfo[1].match(teensPattern)) {
    age = "teens";
    audioFileName = `${audioFileName}1`;
  } else if (userInfo[1].match(twentiesPattern)) {
    age = "twenties";
    audioFileName = `${audioFileName}2`;
  } else if (userInfo[1].match(thirtiesPattern)) {
    age = "thirties";
    audioFileName = `${audioFileName}3`;
  }
  audioFileName = `${audioFileName}${result[3]}${result[4]}`;

  return { client_id, genger, age, pathWithoutExt, audioFileName };
};

const readyAudioFile = (fileDir, newFileName) => {
  const sourcePath = `${fileDir}.wav`;
  const destFolder = audioFolder;
  const newFileNameWithExt = `liepa_${newFileName}.wav`;
  let isFileValid = true;

  if (!fs.existsSync(destFolder)) {
    fs.mkdirSync(destFolder, { recursive: true });
  }

  const destPath = path.join(destFolder, newFileNameWithExt);

  fs.copyFile(sourcePath, destPath, (err) => {
    if (err) {
      isFileValid = false;
      console.log(`File error in: ${sourcePath}`);
    }
  });

  return { path: destPath, isFileValid };
};

function traverseDir(dirPath) {
  fs.readdirSync(dirPath).forEach((file) => {
    const filePath = path.join(dirPath, file);
    const stats = fs.statSync(filePath);

    if (stats.isDirectory()) {
      traverseDir(filePath);
    } else if (path.extname(filePath) === ".txt") {
      const fileContent = fs.readFileSync(filePath, "utf-8");
      const folderName = path.basename(path.dirname(filePath));

      // Check if folder name starts with prefix
      if (folderName.startsWith(folderPrefix)) {
        const { client_id, genger, age, pathWithoutExt, audioFileName } = prepareInfoFromFile(filePath);
        const { path, isFileValid } = readyAudioFile(pathWithoutExt, audioFileName);
        if (!isFileValid) return;
        const sentences = fileContent.split(/[\.\?\!]/).filter(Boolean);
        sentences.forEach((sentence) => {
          writeStream.write(
            `${client_id}\t${path}\t${path}\t${sentence.trim()}\t${up_votes}\t${down_votes}\t${age}\t${genger}\t${accents}\t${locale}\t${segment}\n`,
          );
        });
      }
    }
  });
}

traverseDir(dirPath);
writeStream.end(() => console.log("Task completed!"));
