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

// Fonction pour mettre à jour les noms de clés
function updateJsonKeys(metadata) {
    if (metadata.hasOwnProperty('gameLength')) {
        metadata.gameDuration = metadata.gameLength;
        delete metadata.gameLength;
    }

    if (metadata.hasOwnProperty('statsJson')) {
        metadata.participants = metadata.statsJson;
        delete metadata.statsJson;
    }
    
    return metadata;
}

// Parcourir les fichiers dans le dossier source
let filenames = fs.readdirSync(sourceFolder);
console.log("\nFichiers dans le dossier :");
filenames.forEach((file) => {
    if (file.endsWith('.rofl')) {
        const roflFile = path.join(sourceFolder, file);
        const jsonFile = path.join(targetFolder, `${path.basename(file, '.rofl')}.json`);

        try {
            // Lecture du fichier .rofl
            const reader = new ROFLReader(roflFile);
            const metadata = reader.getMetadata();

            // Mise à jour des clés JSON
            const updatedMetadata = updateJsonKeys(metadata);

            // Écriture dans le fichier cible
            fs.writeFileSync(jsonFile, JSON.stringify(updatedMetadata, null, 2), 'utf8');
            console.log(`Conversion réussie : ${file} -> ${jsonFile}`);
        } catch (error) {
            console.error(`Erreur lors de la conversion du fichier ${file} :`, error.message);
        }
    } else {
        console.log(`Fichier ignoré (non-ROFL) : ${file}`);
    }
});

console.log(`Les métadonnées ont été converties et sauvegardées dans : ${targetFolder}`);
