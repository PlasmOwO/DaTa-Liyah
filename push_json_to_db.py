import pymongo
import json
import os  # Import os to work with directories
from dotenv import load_dotenv
load_dotenv()

sourceJsonFolder = "./json_folder"

myclient = pymongo.MongoClient(host=os.getenv("ATLAS_CONNEXION_STRING"))
db = myclient["lol_match_database"]
collection = db["scrim_matches"]

try:
    for file_name in os.listdir(sourceJsonFolder):
        file_path = os.path.join(sourceJsonFolder, file_name)
        
        if os.path.isfile(file_path) and file_name.endswith('.json'):
            with open(file_path, 'rb') as f:
                file_data = json.load(f)

            if isinstance(file_data, dict):
                file_data = [file_data] 

            if isinstance(file_data, list) and file_data:  
                collection.insert_many(file_data)
            else:
                print(f"Skipping file {file_name}: Not a valid list of documents.")

    myclient.close()
    print("Data pushed successfully, and connection closed.")
except Exception as e:
    print(f"Error: {e}")
