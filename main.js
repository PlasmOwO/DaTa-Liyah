const { ROFLReader } = require('rofl-parser.js');
const { spawn } = require("child_process");
const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);

// Dossier source et cible
const sourceFolderRofl = '../rofl_folder';
const targetFolderJson = '../json_folder';
const backupFolderRofl = '../rofl_backup';

let pythonPath = "";

args.forEach(arg => {
    if (arg.startsWith("--python_path=")) {
        pythonPath = arg.split("=")[1];
    }
});

if (pythonPath) {
    process.env.PYTHONPATH = pythonPath;
    console.log(`Ajout de ${pythonPath} à PYTHONPATH`);
}

// Vérifier si le dossier cible existe, sinon le créer
if (!fs.existsSync(targetFolderJson)) {
    fs.mkdirSync(targetFolderJson, { recursive: true });
}

// Fonction pour extraire le patch
// Fonction pour extraire le patch (format attendu : 15.0.1 ou 15.1)
function getPatch(roflPath) {
    try {
        // Lecture des premiers 300 octets du fichier (plage plus large pour trouver le patch)
        const buffer = fs.readFileSync(roflPath);
        const hexString = buffer.toString('hex');
        const utf8String = Buffer.from(hexString, 'hex').toString('ascii').replace(/\0/g, '');

        // Recherche de la version du patch (e.g., "15.0.1" ou "15.1")
        const matches = utf8String.match(/\d{1,2}\.\d{1,2}(\.\d{1,2})?/);
        if (matches && matches.length > 0) {
            return matches[0]; // Retourne le premier match trouvé
        } else {
            console.error(`Aucun patch trouvé pour le fichier : ${roflPath}`);
            return null;
        }
    } catch (error) {
        console.error(`Erreur lors de l'extraction du patch : ${error.message}`);
        return null;
    }
}

// Fonction pour mettre à jour les noms de clés
function updateJsonKeys(metadata, filename, patch) {
    // Ajouter le nom du fichier et le patch dans les métadonnées
    metadata.jsonFileName = filename;
    if (patch) metadata.patchVersion = patch;

    // Changer le nom des clés
    if (metadata.hasOwnProperty('gameLength')) {
        metadata.gameDuration = metadata.gameLength;
        delete metadata.gameLength;
    }
    if (metadata.hasOwnProperty('statsJson')) {
        metadata.participants = metadata.statsJson;
        delete metadata.statsJson;
    }
    const positions = ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"];
    metadata.participants.forEach((participant, index) => {
        participant.TRUE_POSITION = positions[index % 5];
    });

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
            // Extraire le patch
            const patch = getPatch(roflFile);

            // Lecture du fichier .rofl
            const reader = new ROFLReader(roflFile);
            const metadata = reader.getMetadata();

            // Mise à jour des clés JSON
            const updatedMetadata = updateJsonKeys(metadata, file.slice(0, -5), patch);

            // Écriture dans le fichier cible
            fs.writeFileSync(jsonFile, JSON.stringify(updatedMetadata, null, 2), 'utf8');
            console.log(`Conversion réussie : ${file} -> ${jsonFile}`);
        } catch (error) {
            console.error(`Erreur lors de la conversion du fichier ${file} :`, error.message);
        }

        fs.copyFileSync(roflFile, path.join(backupFolderRofl, file));
        console.log(`Fichier sauvegardé dans ${backupFolderRofl}`);

        fs.unlink(roflFile , (err) => {
            if (err) console.error(`Erreur lors de la suppression du fichier ${file} :`, err.message);
            else console.log(`Fichier supprimé : ${file}`);
        });
    } else {
        console.log(`Fichier ignoré (non-ROFL) : ${file}`);
    }
});

console.log(`Les métadonnées ont été converties et sauvegardées dans : ${targetFolderJson}`);

const { exec } = require('child_process');

// exec('python push_json_to_db.py', (error, stdout, stderr) => {
//     if (error) {
//         console.error(`Error executing script: ${error.message}`);
//         return;
//     }

//     if (stderr) {
//         console.error(`Error in script: ${stderr}`);
//         return;
//     }

//     console.log(`Output:\n${stdout}`);
// });


const pythonProcess = spawn("python", ["push_json_to_db.py", ...args], {
    stdio: "inherit", // Affiche la sortie du script Python dans la console  
    env: process.env
});

pythonProcess.on("close", code => {
    console.log(`Processus Python terminé avec le code ${code}`);
});