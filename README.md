# 🪨📊 DaTa-Liyah
DaTa-Liyah is an open-source tool to help League of Legends professionnal team to reach all the potential of data to help performance and making decision for the staff !📈

Scripts and functions to export scrims and official matchs of League of Legends to JSON file containing data. And use tools to analyse its.  
It use the repo [Rofl-parser](https://github.com/Boris-s-store/rofl-parser.js?tab=readme-ov-file) from [gzordrai](https://github.com/gzordrai) to parse ROFL files.

## 🤔 How to use ?
The first thing to do is to fork this code in a **public, open-source** repo (See [License](LICENSE))
* Go to --> [Streamlit community cloud](https://streamlit.io/cloud)
* Create a new app and select your Github repo
> **Note** : Your webapp is now deployed, but you still need to enter credentials




## ⚙️ Configuration 
You have mostly 3 things to configure :
* [Deploy your personnal MongoDB database](#MongoDB) to store scrims, drafts and more
* [Deploy your personnal SQLite Cloud database](#SQLite-Cloud) to track Soloq progress of your players (Usage with Riot personnal API Key --> see [Riot Developer Portal](https://developer.riotgames.com/app-type)
* [Setup secrets and credentials](#Streamlit-secrets-and-credentials) for the streamlit webapp application

### MongoDB
Section to help you configuring a MongoDB hosted database.  
Do not hesitate to follow MongoDB [documentation](https://www.mongodb.com/docs/) if you need help.  
* Create a MongoDB account and go to Atlas --> ([Link to MongoDB](https://www.mongodb.com/))
* Create a free AWS cluster
* Create a new database (By default the name of the database in the code is : `lol_match_database`)
* Create 2 collections inside (By default : `drafts` and `scrim_matches`)

After this i recommend you to go to the *Security* section of Atlas and to configure the *Database Access* and the *Network Access*.
The goal here is to give access to the database to a limited number of users / or addresses. If you want to whitelist all IP adressess (but cannot access without the right role), add `0.0.0.0/0` to *Network Access*.

> **My personal suggestion**  
> Create at least 3 users. One who is the admin of the database. A read-only user, that will perform request from the application. And a read-&-write user. Use it if someone else wants to add data in a collection.

### SQLite Cloud
TODO

### Streamlit secrets and credentials
TODO

![{E2AEE949-74FD-414B-A525-4D23C7D76C25}](https://github.com/user-attachments/assets/12fcac20-3e0d-4332-9f61-9fa784599d82)


## NPM modules from Gzordrai
npm install rofl-parser.js
