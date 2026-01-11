import requests


##CONSTANTS

DDRAGON_VERSION = requests.get("https://ddragon.leagueoflegends.com/api/versions.json").json()[0]


def get_champion_image_from_id(champion_id) -> str :
    """From champion id/name (with the regex), get the image from datadragon.

    Args:
        champion_id (str): The name of the champion, without blank space or quote (Kaisa, Velkoz etc...)

    Returns:
        str: The PNG image, src link of the champion
    """
    return f"https://ddragon.leagueoflegends.com/cdn/{DDRAGON_VERSION}/img/champion/{champion_id}.png"
