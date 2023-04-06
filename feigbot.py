import os

import discord
import requests

from dotenv import load_dotenv
from discord.ext import commands
from tinydb import TinyDB, Query

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
STRATZ_TOKEN = os.getenv("STRATZ_TOKEN")
headers = {"Authorization": f"Bearer {STRATZ_TOKEN}"}
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
db = TinyDB('db.json')
stratz_url = "https://api.stratz.com/graphql"

def get_steam_id(discord_user):
    Q = Query()
    return db.search(Q.discord_user == f'{discord_user}')[0]['steam_user_id_32']

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

    print(unparsed)
    if unparsed:
        return []
    else:
        return match

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send("Jeg har ikke tillit til deg")

@bot.command(name="perf")
async def flink_sjekk(ctx):
    steam_id = get_steam_id(ctx.message.author)
    match = get_match(get_previous_match_id(steam_id))

    if match == []:
        await ctx.send("Replay is not parsed yet, try again in a minute")
        return

    for player in match.get("data").get("match").get("players"):    
        if player.get("steamAccountId") != steam_id:
            continue

        imp = player.get("imp")
        response = ""
        if imp <= 0:
            response = "You did well"
        else:
            response = "You did bad"

        await ctx.send(response)

@bot.command(name='blame')
async def blame(ctx):
    steam_id = get_steam_id(ctx.message.author)
    match = get_match(get_previous_match_id(steam_id))

    lowest_imp = 100
    worst_player = ""

    for player in match.get("data").get("match").get("players"):

        imp = player.get("imp")
        if imp < lowest_imp:
            lowest_imp = imp
            worst_player = player.get("hero").get("displayName")

    await ctx.send(f"{worst_player} is to blame")

@bot.command(name='reg')
async def reg(ctx, steamAcc: int):

    Q = Query()
    db.remove(Q.discord_user == f'{ctx.message.author}')
    db.insert({'discord_user':f'{ctx.message.author}', 'steam_user_id_32': steamAcc})

    await ctx.reply('you have been successfully added')

bot.run(TOKEN)