import os
import discord
import stratz
import openaiclient
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
        await ctx.reply("Jeg har ikke tillit til deg")

@bot.command(name="perf", help="Use this command to see how you did last game")
async def flink_sjekk(ctx):
    steam_id = get_steam_id(ctx.message.author)
    match = stratz.get_match(stratz.get_previous_match_id(steam_id))
    response = ""

    if match == []:
        await ctx.reply("Replay is not parsed yet, try again in a minute")
        return

    for player in match.get("data").get("match").get("players"):    
        if player.get("steamAccountId") != steam_id:
            continue

        imp = player.get("imp")
        hero = player.get('hero').get('displayName')
        
        if imp <= 0:
            response = f"You did bad - here's a tip for your next game with {hero}:"
            
        else:
            response = f"You did well - here's a tip for your next game with {hero}:"

        dota_hero_tips = await openaiclient.prompt_gpt_herotip(hero)
        await ctx.reply(response + dota_hero_tips)

@bot.command(name="tips", help="Use this command to apologize for your throws last match")
async def tips(ctx):
    steam_id = get_steam_id(ctx.message.author)
    match = stratz.get_match(stratz.get_previous_match_id(steam_id))

    if match == []:
        await ctx.send("Replay is not parsed yet, try again in a minute")
        return

    for player in match.get("data").get("match").get("players"):    
        if player.get("steamAccountId") != steam_id:
            continue

        hero = player.get("hero").get("displayName")
        tips = await openaiclient.prompt_gpt_tips(match, hero)

        await ctx.send(tips)


@bot.command(name="sry", help="Use this command to apologize for your throws last match")
async def apologize(ctx):
    steam_id = get_steam_id(ctx.message.author)
    match = stratz.get_match(stratz.get_previous_match_id(steam_id))

    if match == []:
        await ctx.send("Replay is not parsed yet, try again in a minute")
        return

    for player in match.get("data").get("match").get("players"):    
        if player.get("steamAccountId") != steam_id:
            continue

        hero = player.get("hero").get("displayName")
        apology = await openaiclient.prompt_gpt_apology(ctx.message.author.name, hero)

        await ctx.send(apology)

def get_previous_match_from_author(author):
    steam_id = get_steam_id(author)
    match = stratz.get_match(stratz.get_previous_match_id(steam_id))


@bot.command(name="anal", help="Analyse the previous game")
async def analyse(ctx):
    steam_id = get_steam_id(ctx.message.author)
    match = stratz.get_match(stratz.get_previous_match_id(steam_id))

    if match == []:
        await ctx.reply("Replay is not parsed yet, try again in a minute")
        return

    analysis = await openaiclient.prompt_analyse(match)
    await ctx.reply(analysis)

@bot.command(name="analmatch", help="Analyse a specific game")
async def analyse(ctx, match_id):
    match = stratz.get_match(match_id)
    if match == []:
        await ctx.reply("Replay is not parsed yet, try again in a minute")
        return

    analysis = await openaiclient.prompt_analyse(match)
    await ctx.reply(analysis)

@bot.command(name="blame", help="Find out who is to blame for your most recent loss")
async def blame(ctx, lang = "eng"):
    steam_id = get_steam_id(ctx.message.author)
    match = stratz.get_match(stratz.get_previous_match_id(steam_id))

    if match == []:
        await ctx.reply("Replay is not parsed yet, try again in a minute")
        return

    blame = await openaiclient.prompt_blame(match, lang)
    await ctx.reply(blame)

@bot.command(name='reg')
async def reg(ctx, steamAcc: int):

    Q = Query()
    db.remove(Q.discord_user == f'{ctx.message.author}')
    db.insert({'discord_user':f'{ctx.message.author}', 'steam_user_id_32': steamAcc})

    await ctx.reply('You have been successfully registered')

bot.run(TOKEN)