import logging

import requests
from aiohttp import request
import os
import pymongo
from dotenv import load_dotenv

load_dotenv()
STRATZ_TOKEN = os.getenv("STRATZ_TOKEN")
MONGODB_PW = os.getenv("MONGODB_PW")

headers = {"Authorization": f"Bearer {STRATZ_TOKEN}"}
stratz_url = "https://api.stratz.com/graphql"

client = pymongo.MongoClient(
    f"mongodb+srv://feigbot:{MONGODB_PW}@feigbot.ssqtcoy.mongodb.net/?retryWrites=true&w=majority")
itemscol = client.db.items


# Update only when needed. i.e. when a patch drops
async def update_items():
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

    async with request('POST', url=stratz_url, json={"query": item_query}, headers=headers) as response:
        r = await response.json()

    item_list = []
    for item in r.get("data").get("constants").get("items"):
        item_id = item.get("id")
        item_name = item.get("language").get("displayName")
        item_list.append({'item_id': item_id, 'item_name': item_name})

    itemscol.insert_many(item_list)
    logging.info("Items updated")


async def get_previous_match_id(steam_id):
    id_query = """
    {
        player(steamAccountId: %s) {
            matches(request: {take: 1, orderBy: DESC}) {
                id
                }
            }
    }""" % steam_id

    async with request('POST', url=stratz_url, json={"query": id_query}, headers=headers) as response:
        match_id = await response.json()

    logging.info("Got previous match ID from Stratz")
    if match_id.get("data").get("player").get("steamAccount") == "null":
        raise Exception(f"Steam account with steam id {steam_id} not found")
    return match_id.get("data").get("player").get("matches")[0].get("id")


async def get_match(match_id):
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

    async with request('POST', url=stratz_url, json={"query": match_query}, headers=headers) as response:
        match = await response.json()

    get_items_for_players(match.get("data").get("match").get("players"))
    unparsed = match.get('data').get('match').get('parsedDateTime') == 'null'
    logging.info(f"Got match {match_id} from Stratz")

    if unparsed:
        return []
    else:
        return match


async def get_live_match_initial(match_id):
    live_query = """
    {
    live {
        match(id: %s) {
            gameMinute
            gameState
            isUpdating
            league {
                displayName
                tier
                prizePool
                startDateTime
                endDateTime
                lastMatchDate
            }
            radiantTeam {
                name
            }
            direTeam {
                name
            }
            direScore
            radiantScore
            winRateValues
            insight {
                teamOneVsWinCount
                teamOneLeagueWinCount
                teamOneLeagueMatchCount
                teamTwoVsWinCount
                teamTwoLeagueWinCount
                teamTwoLeagueMatchCount
            }
            players {
                name
                isRadiant
                numKills
                numDeaths
                numLastHits
                numDenies
                networth
                goldPerMinute
                level
                itemId0
                itemId1
                itemId2
                itemId3
                itemId4
                itemId5
                steamAccount{
                    proSteamAccount{
                        name
                    }
                }
                hero {
                    displayName
                }
            }
        }
    }
    }
    """ % (
        match_id
    )

    async with request('POST', url=stratz_url, json={"query": live_query}, headers=headers) as response:
        match = (await response.json()).get('data').get('live').get('match')

    get_items_for_players(match.get("players"))
    logging.info(f"Got live match {match_id} from Stratz")
    return match


async def get_live_match_status(match_id):
    live_query = """
    {
    live {
        match(id: %s) {
            gameState
            isUpdating
            }
        }
    }
    """ % (
        match_id
    )
    async with request('POST', url=stratz_url, json={"query": live_query}, headers=headers) as response:
        return (await response.json()).get('data').get('live').get('match')


# TODO: get hero names from ids
async def get_live_draft(match_id):
    live_query = """
{
  live {
    match(id: %s) {
      playbackData{
        pickBans {
          order
          isPick
          heroId
          bannedHeroId
          isRadiant
          baseWinRate
          adjustedWinRate
          position
        }
      }
      insight {
        teamOneVsWinCount
        teamTwoVsWinCount
        teamOneLeagueWinCount
        teamOneLeagueMatchCount
        teamTwoLeagueWinCount
        teamTwoLeagueMatchCount
        lastSeries {
          teamOneWinCount
          teamTwoWinCount
        }
      }
    }
  }
}
    """ % (
        match_id
    )
    async with request('POST', url=stratz_url, json={"query": live_query}, headers=headers) as response:
        return (await response.json()).get('data').get('live').get('match')


async def get_live_match(match_id):
    live_query = """
    {
    live {
        match(id: %s) {
            gameMinute
            radiantTeam {
                name
            }
            direTeam {
                name
            }
            direScore
            radiantScore
            winRateValues
            players {
                name
                isRadiant
                numKills
                numDeaths
                numLastHits
                numDenies
                networth
                goldPerMinute
                level
                itemId0
                itemId1
                itemId2
                itemId3
                itemId4
                itemId5
                steamAccount{
                    proSteamAccount{
                        name
                    }
                }
                hero {
                    displayName
                }
            }
        }
    }
    }
    """ % (
        match_id
    )

    async with request('POST', url=stratz_url, json={"query": live_query}, headers=headers) as response:
        match = (await response.json()).get('data').get('live').get('match')
    get_items_for_players(match.get("players"))
    logging.info(f"Got live match {match_id} from Stratz")
    return match


async def get_live_games():
    live_query = """
{
  live {
    matches(request: {isCompleted: false, tiers: [MAJOR, DPC_LEAGUE, DPC_QUALIFIER, DPC_LEAGUE_FINALS, DPC_LEAGUE_QUALIFIER, MINOR, INTERNATIONAL, PROFESSIONAL]}) {
      matchId
      gameMode
      isUpdating
      radiantTeam {
        name
      }
      direTeam {
        name
      }
      league {
        displayName
        tier
      }
    }
  }
}
    """

    async with request('POST', url=stratz_url, json={"query": live_query}, headers=headers) as response:
        match = (await response.json()).get('data').get('live').get('matches')
    logging.info(f"Got list of live matches from Stratz")
    return match


async def get_team_info(team_ids: [int]):
    team_query = """
    {
	    teams(teamIds: %s){
            name
            id
            countryCode
        }
    }

    """ % (
        team_ids
    )

    async with request('POST', url=stratz_url, json={"query": team_query}, headers=headers) as response:
        return (await response.json()).get('data')


def get_items_for_players(players):
    for player in players:
        replace_id_with_item(player, "item0Id")
        replace_id_with_item(player, "item1Id")
        replace_id_with_item(player, "item2Id")
        replace_id_with_item(player, "item3Id")
        replace_id_with_item(player, "item4Id")
        replace_id_with_item(player, "item5Id")


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


def get_live_match_end(match_id):
    return None