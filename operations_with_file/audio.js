const fs = require("fs");
const util = require("util");
const ffmpeg = require("fluent-ffmpeg");
const path = require("path");
const wav = require("wav-decoder");
const ffprobe = require("ffprobe");
const ffprobeStatic = require("ffprobe-static");
const { spawnSync } = require("child_process");

const convertFile = util.promisify(ffmpeg);

const audioFolder = "audio";
const audioMp3Folder = "audio-mp3";
const clipsFolder = "clips";
const clipsMp3Folder = "clips-mp3";
const clipsChunkFolder = "chunk_1";

const chunkSize = 500 * 1024 * 1024; // 500 MB in bytes

ffprobe.FFmpegPath = ffprobeStatic.path;

const convertToMp3 = async (inputFolderPath, outputFolderPath) => {
  if (!fs.existsSync(outputFolderPath)) {
    fs.mkdirSync(outputFolderPath);
  }
  fs.readdir(inputFolderPath, async (err, files) => {
    if (err) {
      console.error(err);
      return;
    }

    Promise.allSettled(
      files.map(async (file) => {
        if (file.endsWith(".wav")) {
          const inputFilePath = `${inputFolderPath}/${file}`;
          const outputFilePath = `${outputFolderPath}/${file.replace(".wav", ".mp3")}`;
          try {
            await convertFile(ffmpeg(inputFilePath).save(outputFilePath));
            console.log(`${file} has been converted.`);
          } catch (err) {
            console.error(`Error converting ${file}: ${err.message}`);
          }
        }
      }),
    );
  });
};

const separateInChunks = async (sourceFolder, outputFolder, chunkSize) => {
  if (!fs.existsSync(outputFolder)) {
    fs.mkdirSync(outputFolder);
  }
  fs.readdir(sourceFolder, (err, files) => {
    if (err) throw err;
    console.log(files);
    const audioFiles = files.filter((file) => path.extname(file) === ".mp3" || path.extname(file) === ".wav");
    let currentChunk = 1;
    let currentSize = 0;
    let currentFiles = [];

    // Loop through each audio file
    audioFiles.forEach((file) => {
      const filePath = path.join(sourceFolder, file);
      const stats = fs.statSync(filePath);
      const fileSize = stats.size;

      // If adding the file to the current chunk would exceed the chunk size, create a new chunk folder and move the current files to it
      if (currentSize + fileSize > chunkSize) {
        const chunkFolder = path.join(outputFolder, `chunk_${currentChunk}`);
        fs.mkdirSync(chunkFolder);
        currentFiles.forEach((currentFile) => {
          fs.renameSync(path.join(sourceFolder, currentFile), path.join(chunkFolder, currentFile));
        });
        currentChunk++;
        currentSize = 0;
        currentFiles = [];
      }

      // Add the current file to the current chunk
      currentSize += fileSize;
      currentFiles.push(file);
    });

    if (currentFiles.length > 0) {
      const chunkFolder = path.join(outputFolder, `chunk_${currentChunk}`);
      fs.mkdirSync(chunkFolder);
      currentFiles.forEach((currentFile) => {
        fs.renameSync(path.join(sourceFolder, currentFile), path.join(chunkFolder, currentFile));
      });
    }

    console.log("Done!");
  });
};

const getWavAudioLength = async (folderPath) => {
  fs.readdir(folderPath, (err, files) => {
    if (err) {
      console.error(err);
      return;
    }

    const wavFiles = files.filter((file) => file.endsWith(".mp3"));
    let totalLength = 0;

    wavFiles.forEach((file) => {
      const filePath = `${folderPath}/${file}`;
      const buffer = fs.readFileSync(filePath);
      const decoded = wav.decode(buffer);

      if (!decoded.channelData || !decoded.channelData.length) {
        console.warn(`Skipping file ${file} - no audio data found.`);
        return;
      }

      totalLength += decoded.sampleRate * decoded.channelData[0].length;
    });

    console.log(`Total length of all WAV files: ${totalLength} samples`);
  });
};

function getMp3AudioLength(path) {
  const files = fs.readdirSync(path);
  let totalDuration = 0;

  files.forEach((file) => {
    const filePath = `${path}/${file}`;
    const stat = fs.statSync(filePath);

    if (stat.isDirectory()) {
      readFolder(filePath);
    } else if (file.endsWith(".mp3") || file.endsWith(".wav")) {
      const result = spawnSync("ffprobe", ["-i", filePath, "-show_entries", "format=duration", "-v", "quiet", "-of", "csv=p=0"]);
      if (result.error || result.status !== 0) {
        console.error(`Error while reading ${filePath}: ${result.error}`);
      } else {
        totalDuration += parseFloat(result.stdout.toString());
      }
    }
  });

  return totalDuration;
}

// separateInChunks(clipsFolder, clipsMp3Folder, chunkSize);
// convertToMp3(`${clipsMp3Folder}/${clipsChunkFolder}`, `${clipsMp3Folder}/${clipsChunkFolder}_mp3`);

// getWavAudioLength(audioMp3Folder);
// const duration = getMp3AudioLength(`${clipsMp3Folder}/${clipsChunkFolder}_mp3`);
const duration = getMp3AudioLength(audioFolder);
console.log(`Total duration of all MP3 files in folder: ${parseInt(duration) / 360} seconds`);
