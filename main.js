// npm install rofl-parser.js

const { ROFLReader } = require('rofl-parser.js');
const fs = require('fs');
const path = require('path');

// Dossier source et cible
const sourceFolder = '../file_need_conversion_to_json';
const targetFolder = '../file_converted_to_json';

// Vérifier si le dossier cible existe, sinon le créer
if (!fs.existsSync(targetFolder)) {
    fs.mkdirSync(targetFolder, { recursive: true });
}

// Chemin complet du fichier .rofl
let filenames = fs.readdirSync(sourceFolder)
console.log("\nFilenames in directory : " )
filenames.forEach((file) => {
    // console.log(file);
    if(file.endsWith('.rofl')){
        const roflFile = path.join(sourceFolder, file);
        const jsonFile = path.join(targetFolder, `${path.basename(file, '.rofl')}.json`);
       
        try {
            // Lecture du fichier.rofl
            const reader = new ROFLReader(roflFile);
            const metadata = reader.getMetadata();
            fs.writeFileSync(jsonFile, JSON.stringify(metadata, null, 2), 'utf8');
            console.log(`Conversion réussie : ${file} -> ${jsonFile}`);
        }
        catch (error){
            console.error(`Erreur lors de la conversion du fichier ${file} :`, error.message);
        }
    }
    else {
        console.log(`Fichier ignoré (non-ROFL) : ${file}`);
    }
});

console.log(`Les métadonnées ont été converties et sauvegardées dans : ${jsonFile}`);