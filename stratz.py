import requests
import os
from dotenv import load_dotenv
from tinydb import TinyDB, Query

load_dotenv()
STRATZ_TOKEN = os.getenv("STRATZ_TOKEN")
headers = {"Authorization": f"Bearer {STRATZ_TOKEN}"}
stratz_url = "https://api.stratz.com/graphql"
item_db = TinyDB('items.json')

def update_items():
    item_query = """
    {
    constants {
        items(language: ENGLISH) {
        id
        language {
                displayName
                }
            }
        }
    }
    """
    item_db.truncate()

    r = requests.post(stratz_url, json={"query": item_query}, headers=headers).json()
    for item in r.get("data").get("constants").get("items"):
        item_id = item.get("id")
        item_name = item.get("language").get("displayName")
        item_db.insert({'item_id' : item_id, 'item_name' : item_name})

    print("Items updated")

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
        parsedDateTime
        didRadiantWin
        durationSeconds
        firstBloodTime
        averageRank
        bottomLaneOutcome
        midLaneOutcome
        topLaneOutcome
        players {
            steamAccountId
            imp
            isRadiant
            kills
            deaths
            assists
            goldPerMinute
            numLastHits
            numDenies
            roleBasic
            intentionalFeeding
            lane
            heroDamage
            heroHealing
            towerDamage
            networth
            item0Id
            item1Id
            item2Id
            item3Id
            item4Id
            item5Id
            hero {
                displayName
                }
            }
        }
    }
    """ % (
        match_id
    )

    match = requests.post(stratz_url, json={"query": match_query}, headers=headers).json()  
    
    for player in match.get("data").get("match").get("players"):
        replace_id_with_item(player, "item0Id")
        replace_id_with_item(player, "item1Id")
        replace_id_with_item(player, "item2Id")
        replace_id_with_item(player, "item3Id")
        replace_id_with_item(player, "item4Id")
        replace_id_with_item(player, "item5Id")

    unparsed = match.get('data').get('match').get('parsedDateTime') == 'null'

    if unparsed:
        return []
    else:
        return match

def replace_id_with_item(player, itemId):
    item = player.get(itemId)
    if type(item) != int:
        return

    Q = Query()
    player[itemId] = item_db.search(Q.item_id == item)[0]['item_name']
