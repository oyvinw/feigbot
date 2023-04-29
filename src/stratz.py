import logging

import requests
import os
import pymongo
from dotenv import load_dotenv

load_dotenv()
STRATZ_TOKEN = os.getenv("STRATZ_TOKEN")
MONGODB_PW = os.getenv("MONGODB_PW")

headers = {"Authorization": f"Bearer {STRATZ_TOKEN}"}
stratz_url = "https://api.stratz.com/graphql"

client = pymongo.MongoClient(f"mongodb+srv://feigbot:{MONGODB_PW}@feigbot.ssqtcoy.mongodb.net/?retryWrites=true&w=majority")
itemscol = client.db.items


# Update only when needed. i.e. when a patch drops
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
    itemscol.drop()

    r = requests.post(stratz_url, json={"query": item_query}, headers=headers).json()
    item_list = []
    for item in r.get("data").get("constants").get("items"):
        item_id = item.get("id")
        item_name = item.get("language").get("displayName")
        item_list.append({'item_id': item_id, 'item_name': item_name})

    itemscol.insert_many(item_list)
    logging.info("Items updated")


def get_previous_match_id(steam_id):
    id_query = """
    {
        player(steamAccountId: %s) {
            matches(request: {take: 1, orderBy: DESC}) {
                id
                }
            }
    }""" % steam_id

    r = requests.post(stratz_url, json={"query": id_query}, headers=headers)

    resp_dict = r.json()
    logging.info("Got previous match ID from Stratz")
    if resp_dict.get("data").get("player").get("steamAccount") is "null":
        raise Exception(f"Steam account with steam id {steam_id} not found")
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
    logging.info(f"Got match {match_id} from Stratz")

    if unparsed:
        return []
    else:
        return match


def replace_id_with_item(player, item_id):
    item = player.get(item_id)
    if type(item) != int:
        return

    item_cursor = itemscol.find({'item_id': item})
    item_name = ""
    for db_item in item_cursor:
        item_name = db_item.get('item_name')

    if not item_name:
        update_items()
        return replace_id_with_item(player, item_id)

    player[item_id] = item_name
