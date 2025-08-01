//Run this script with the following command: node main.js --python_path=your_python_path

const { ROFLReader } = require('rofl-parser.js');
const { spawn } = require("child_process");
const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);

// Dossier source et cible
const sourceFolderRofl = './rofl_folder';
const targetFolderJson = './json_folder';
const backupFolderRofl = './rofl_backup';

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
        const buffer = fs.readFileSync(roflPath);
        const hexString = buffer.toString('hex');
        const utf8String = Buffer.from(hexString, 'hex').toString('ascii').replace(/\0/g, '');

        const matches = utf8String.match(/\d{1,2}\.\d{1,2}(\.\d{1,2})?/);
        if (matches && matches.length > 0) {
            return matches[0]; 
        } else {
            console.error(`Aucun patch trouvé pour le fichier : ${roflPath}`);
            return null;
        }
    } catch (error) {
        console.error(`Erreur lors de l'extraction du patch : ${error.message}`);
        return null;
    }
}

function isOfficialMatch(filename){
    // Vérifie si c'est un match officiel
    // Retourne N pour la Nieme etape (1 pour la GA, 2 pour la deuxieme etape etc...)
    const GA_regex = /^(1904|2004)/;
    if (GA_regex.test(filename)) {
        return 1;
    }
    const NT_2_regex = /^(1005|1105|1705|1805)/;
    if (NT_2_regex.test(filename)) {
        return 2;
    }
    const NT_3_regex = /^(0706|0806|1406|1506)/;
    if (NT_3_regex.test(filename)) {
        return 3;
    }
    const NT_4_regex = /^(1207|1307|1907|2007)/;
    if (NT_4_regex.test(filename)) {
        return 4;
    }

    return 0;
}

// Fonction pour mettre à jour les noms de clés
function updateJsonKeys(metadata, filename, patch) {
    // Ajouter le nom du fichier et le patch dans les métadonnées
    metadata.jsonFileName = filename;
    if (patch) metadata.patchVersion = patch;
    
    metadata.officialMatch = isOfficialMatch(filename);

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

const pythonProcess = spawn("C:/Users/Utilisateur/python_envs/lol_webapp/Scripts/python.exe", ["push_json_to_db.py", ...args], {
    stdio: "inherit", // Affiche la sortie du script Python dans la console  
    env: process.env
});

pythonProcess.on("close", code => {
    console.log(`Processus Python terminé avec le code ${code}`);
});
