import requests
import os
from tinydb import TinyDB, Query
from dotenv import load_dotenv

STRATZ_TOKEN = os.getenv("STRATZ_TOKEN")
headers = {"Authorization": f"Bearer {STRATZ_TOKEN}"}
stratz_url = "https://api.stratz.com/graphql"

def get_previous_match_id(steam_id):
    id_query = """
    {
        player(steamAccountId: %s) {
            matches(request: {take: 1, orderBy: DESC}) {
                id
                }
            }
    }""" % (steam_id)

    r = requests.post(stratz_url, json={"query": id_query}, headers=headers)

    resp_dict = r.json()
    return resp_dict.get("data").get("player").get("matches")[0].get("id")

def get_match(match_id):
    match_query = """
    {
        match(id: %s) {
            parsedDateTime,
            players {
                steamAccountId,
                imp,
                isRadiant,
                hero {
                    displayName,
                    }
                }
            }
    }
    """ % (
        match_id
    )

    match = requests.post(stratz_url, json={"query": match_query}, headers=headers).json()  
    unparsed = match.get('data').get('match').get('parsedDateTime') == 'null'

    if unparsed:
        return []
    else:
        return match