// npm install rofl-parser.js

const { ROFLReader } = require('rofl-parser.js');
const fs = require('fs');
const path = require('path');

// Dossier source et cible
const sourceFolder = './file_need_conversion_to_json';
const targetFolder = './file_converted_to_json';

// Vérifier si le dossier cible existe, sinon le créer
if (!fs.existsSync(targetFolder)) {
    fs.mkdirSync(targetFolder, { recursive: true });
}

// Chemin complet du fichier .rofl
const roflFile = path.join(sourceFolder, 'djoko1.rofl');


// Lecture du fichier .rofl
const reader = new ROFLReader(roflFile);
const metadata = reader.getMetadata();

// Chemin complet du fichier JSON cible
const jsonFile = path.join(targetFolder, 'djoko1.json');

// Conversion et écriture dans le dossier cible
fs.writeFileSync(jsonFile, JSON.stringify(metadata, null, 2), 'utf8');

console.log(`Les métadonnées ont été converties et sauvegardées dans : ${jsonFile}`);