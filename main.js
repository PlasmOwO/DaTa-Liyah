// npm install rofl-parser.js
// npm install express mongodb fs

const { ROFLReader } = require('rofl-parser.js');
const fs = require('fs');
const path = require('path');

// Dossier source et cible
const sourceFolderRofl = './rofl_folder';
const targetFolderJson = './json_folder';



// Vérifier si le dossier cible existe, sinon le créer
if (!fs.existsSync(targetFolderJson)) {
    fs.mkdirSync(targetFolderJson, { recursive: true });
}

// Fonction pour mettre à jour les noms de clés
function updateJsonKeys(metadata, filename) {
    // add du file name en première ligne
    metadata.jsonFileName = filename
    // changement du nom gameLength en gameDuration
    if (metadata.hasOwnProperty('gameLength')) {
        metadata.gameDuration = metadata.gameLength;
        delete metadata.gameLength;
    }
    // changement du nom statsJson en participants
    if (metadata.hasOwnProperty('statsJson')) {
        metadata.participants = metadata.statsJson;
        delete metadata.statsJson;
    }

    return metadata;
}

// Parcourir les fichiers dans le dossier source
let filenames = fs.readdirSync(sourceFolderRofl);
console.log("\nFichiers dans le dossier :");
filenames.forEach((file) => {
    if (file.endsWith('.rofl')) {
        const roflFile = path.join(sourceFolderRofl, file);
        const jsonFile = path.join(targetFolderJson, `${path.basename(file, '.rofl')}.json`);

        try {
            // Lecture du fichier .rofl
            const reader = new ROFLReader(roflFile);
            const metadata = reader.getMetadata();

            // Mise à jour des clés JSON
            const updatedMetadata = updateJsonKeys(metadata, file.slice(0, -5));

            // Écriture dans le fichier cible
            fs.writeFileSync(jsonFile, JSON.stringify(updatedMetadata, null, 2), 'utf8');
            console.log(`Conversion réussie : ${file} -> ${jsonFile}`);
        } catch (error) {
            console.error(`Erreur lors de la conversion du fichier ${file} :`, error.message);
        }

        // fs.unlink(roflFile , (err) => {
        //     if (err) console.error(`Erreur lors de la suppression du fichier ${file} :`, err.message);
        //     else console.log(`Fichier supprimé : ${file}`);
        // });

    } else {
        console.log(`Fichier ignoré (non-ROFL) : ${file}`);
    }
});

console.log(`Les métadonnées ont été converties et sauvegardées dans : ${targetFolderJson}`);

const { exec } = require('child_process');

exec('python push_json_to_db.py', (error, stdout, stderr) => {
    if (error) {
        console.error(`Error executing script: ${error.message}`);
        return;
    }

    if (stderr) {
        console.error(`Error in script: ${stderr}`);
        return;
    }

    console.log(`Output:\n${stdout}`);
});