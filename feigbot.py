import os
import discord
import stratz
from dotenv import load_dotenv
from discord.ext import commands
from tinydb import TinyDB, Query

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
db = TinyDB('db.json')

def get_steam_id(discord_user):
    Q = Query()
    return db.search(Q.discord_user == f'{discord_user}')[0]['steam_user_id_32']

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send("Jeg har ikke tillit til deg")

@bot.command(name="perf", help="Use this command to see hpow you did last game")
async def flink_sjekk(ctx):
    steam_id = get_steam_id(ctx.message.author)
    match = stratz.get_match(stratz.get_previous_match_id(steam_id))
    response = ""

    if match == []:
        await ctx.send("Replay is not parsed yet, try again in a minute")
        return

    for player in match.get("data").get("match").get("players"):    
        if player.get("steamAccountId") != steam_id:
            continue

        imp = player.get("imp")
        if imp <= 0:
            response = "You did bad"
        else:
            response = "You did well"

        await ctx.send(response)

@bot.command(name='blame', help="Assign blame to your worst performing teammate")
async def blame(ctx):
    steam_id = get_steam_id(ctx.message.author)
    match = stratz.get_match(stratz.get_previous_match_id(steam_id))

    lowest_imp_radiant = 100
    lowest_imp_dire = 100
    worst_player_radiant = ""
    worst_player_dire = ""

    response = ""
    worst_player_user = ""

    for player in match.get("data").get("match").get("players"):
        imp = player.get("imp")
        is_radiant = player.get('isRadiant')
        player_is_radiant = False

        if is_radiant:
            if imp < lowest_imp_radiant:
                lowest_imp_radiant = imp
                worst_player_radiant = player.get("hero").get("displayName")
        else:
            if imp < lowest_imp_dire:
                lowest_imp_dire = imp
                worst_player_dire = player.get("hero").get("displayName")

        if player.get("steamAccountId") != steam_id:
            player_is_radiant = is_radiant
        
    if player_is_radiant:
        worst_player = worst_player_radiant
    else:
        worst_player = worst_player_dire

    await ctx.send(f"{worst_player} is to blame")

@bot.command(name='reg')
async def reg(ctx, steamAcc: int):

    Q = Query()
    db.remove(Q.discord_user == f'{ctx.message.author}')
    db.insert({'discord_user':f'{ctx.message.author}', 'steam_user_id_32': steamAcc})

    await ctx.reply('You have been successfully registered')

bot.run(TOKEN)