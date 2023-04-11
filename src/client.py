import asyncio
import datetime
import io
import logging
import os
import subprocess
import tempfile

import discord
import pymongo
import uberduck
from discord.ext import commands
from dotenv import load_dotenv
from uberduck import UberDuck

from src import stratz, openaiclient

logpath = os.path.join(os.path.dirname(__file__), '../log')
os.makedirs(logpath, exist_ok=True)

date = '{date:%d-%m-%Y_%H-%M-%S}'.format(date=datetime.datetime.now())
filepath = f'{logpath}/feigbot{date}.log'
print(filepath)
logging.basicConfig(filename=filepath,
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG,
                    encoding='utf-8')

logging.info("logging initialized")

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
UBERDUCK_KEY = os.getenv("UBERDUCK_API_KEY")
UBERDUCK_SECRET = os.getenv("UBERDUCK_API_SECRET")
MONGODB_PW = os.getenv("MONGODB_PW")

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
client = pymongo.MongoClient(
    f"mongodb+srv://feigbot:{MONGODB_PW}@feigbot.ssqtcoy.mongodb.net/?retryWrites=true&w=majority")
userscol = client.db.users

guild_to_voice_client = dict()
uberduck_client: UberDuck = uberduck.UberDuck(UBERDUCK_KEY, UBERDUCK_SECRET)
uberduck_voices = uberduck.get_voices(return_only_names=True)


class MatchData:
    def __init__(self, match, steam_id: int):
        self.match = match
        self.steam_id = steam_id


def get_steam_id(discord_user):
    query = {'discord_user': f'{discord_user}'}
    user = userscol.find(query)
    for cursor in user:
        return cursor.get('steam_user_id_32')

    raise commands.errors.UserNotFound(discord_user)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.reply("Jeg har ikke tillit til deg")
    if isinstance(error, commands.errors.UserNotFound):
        await ctx.reply("You need to register using '!reg {your-steam-id-32-here}'")
    raise error


async def get_match(ctx, match_id):
    steam_id = get_steam_id(ctx.message.author)
    match = stratz.get_match(match_id)

    if not match:
        await ctx.reply("Replay is not parsed yet, try again in a minute")
        return

    return MatchData(match, steam_id)


def get_previous_match_id_from_author(author):
    steam_id = get_steam_id(author)
    return stratz.get_previous_match_id(steam_id)


async def get_previous_match(ctx):
    return await get_match(ctx, get_previous_match_id_from_author(ctx.message.author))


@bot.command(name="perf", help="Use this command to see how you did last game")
async def perf(ctx, lang="eng", vcargs="", voice="2pac"):
    md = await get_previous_match(ctx)

    for player in md.match.get("data").get("match").get("players"):
        if player.get("steamAccountId") != md.steam_id:
            continue

        hero = player.get('hero').get('displayName')
        dota_hero_tips = await openaiclient.prompt_gpt_herotip(hero)
        if vcargs:
            await vc(ctx, voice, dota_hero_tips)
        else:
            await ctx.reply(dota_hero_tips)


@bot.command(name="tips", help="get good tips")
async def tips(ctx, lang="eng", vcargs="", voice="linustt"):
    md = await get_previous_match(ctx)

    for player in md.match.get("data").get("match").get("players"):
        if player.get("steamAccountId") != md.steam_id:
            continue

        hero = player.get("hero").get("displayName")
        tips_text = await openaiclient.prompt_gpt_tips(md.match, hero, lang)

        if vcargs:
            await vc(ctx, voice, tips_text)
        else:
            await ctx.reply(tips_text)


@bot.command(name="sry", help="Use this command to apologize for your throws last match")
async def apologize(ctx, lang="eng", vcargs="", voice="dr-phil"):
    md = await get_previous_match(ctx)

    for player in md.match.get("data").get("match").get("players"):
        if player.get("steamAccountId") != md.steam_id:
            continue

        hero = player.get("hero").get("displayName")
        apology = await openaiclient.prompt_gpt_apology(md.match, ctx.message.author.name, hero, lang)

        if vcargs:
            await vc(ctx, voice, apology)
        else:
            await ctx.reply(apology)


@bot.command(name="notsry", help="Use this command to justify yourself")
async def not_sorry(ctx, lang="eng", vcargs="", voice="glados-p2"):
    md = await get_previous_match(ctx)

    for player in md.match.get("data").get("match").get("players"):
        if player.get("steamAccountId") != md.steam_id:
            continue

        hero = player.get("hero").get("displayName")
        apology = await openaiclient.prompt_gpt_not_apology(md.match, ctx.message.author.name, hero, lang)

        if vcargs:
            await vc(ctx, voice, apology)
        else:
            await ctx.reply(apology)


@bot.command(name="anal", help="Analyse the previous game")
async def analyse(ctx, lang="eng", vcargs="", voice="michael-scott"):
    md = await get_previous_match(ctx)
    analysis = await openaiclient.prompt_analyse(md.match, lang)
    if vcargs:
        await vc(ctx, voice, analysis)
    else:
        await ctx.reply(analysis)


@bot.command(name="analmatch", help="Analyse a specific game")
async def analyse(ctx, match_id, lang="eng", vcargs="", voice="michael-scott"):
    md = await get_match(ctx, match_id)
    analysis = await openaiclient.prompt_analyse(md.match, lang)
    if vcargs:
        await vc(ctx, voice, analysis)
    else:
        await ctx.reply(analysis)


@bot.command(name="rap", help="Make a cool rap about the last game")
async def rap(ctx, lang="eng", vcargs="", voice="relikk"):
    md = await get_previous_match(ctx)
    for player in md.match.get("data").get("match").get("players"):
        if player.get("steamAccountId") != md.steam_id:
            continue

        hero = player.get('hero').get('displayName')
        result = await openaiclient.prompt_rap(md.match, hero, lang)
        if vcargs:
            await vc(ctx, voice, result)
        else:
            await ctx.reply(result)


@bot.command(name="blame", help="Find out who is to blame for your most recent game")
async def blame(ctx, lang="eng", vcargs="", voice="oblivion-guard"):
    md = await get_previous_match(ctx)
    blame_text = await openaiclient.prompt_blame(md.match, lang, vc)
    if vcargs:
        logging.info("Attempting voice chat")
        await vc(ctx, voice, blame_text)
    else:
        logging.info("Attempting to send a text reply")
        await ctx.reply(blame_text)


@bot.command(name='reg')
async def reg(ctx, steam_acc: int):
    query = {'discord_user': f'{ctx.message.author}'}
    old_user = userscol.find(query)
    for _ in old_user:
        userscol.update_one({'discord_user': f'{ctx.message.author}'}, {'$set': {'steam_user_id_32': steam_acc}})
        await ctx.reply("Your steam id has been updated")
        return

    new_user = {'discord_user': f'{ctx.message.author}', 'steam_user_id_32': steam_acc}
    user_id = userscol.insert_one(new_user)
    logging.info(
        f"Successfully registered {ctx.message.author}, with steam_id: {steam_acc} into {userscol} with "
        f"user_id: {user_id}")

    await ctx.reply('You have been successfully registered')


@bot.command(name='unreg')
async def unreg(ctx):
    query = {'discord_user': f'{ctx.message.author}'}
    old_user = userscol.find(query)
    for _ in old_user:
        userscol.delete_one({'discord_user': f'{ctx.message.author}'})
        await ctx.reply("Your steam id has been removed and forgotten")
        return

    await ctx.reply('No user to unregister')


@bot.command(name="vc-join")
async def vc_join(ctx):
    voice_client, joined = await get_or_create_voice_client(ctx)
    if voice_client is None:
        await ctx.reply(
            "You are not connected to a voice channel. Connect to the voice channel you want me to join and try the command again")
    elif ctx.author.voice and voice_client.channel.id != ctx.author.voice.channel.id:
        old_channel_name = voice_client.channel.name
        await voice_client.disconnect()
        voice_client = await ctx.author.voice.channel.connect()
        new_channel_name = voice_client.channel.name
        guild_to_voice_client[ctx.guild.id] = (voice_client, datetime.datetime)
        await ctx.reply(f'Switched from #{old_channel_name} to #{new_channel_name}!')
    else:
        await ctx.reply("Connected to voice channel!")
        guild_to_voice_client[ctx.guild.id] = (voice_client, datetime.datetime)


@bot.command(name="vc-kick")
async def vc_kick(ctx):
    if ctx.guild.id in guild_to_voice_client:
        voice_client, _ = guild_to_voice_client.pop(ctx.guild.id)
        await voice_client.disconnect()
        await ctx.reply("Disconnected from voice channel")
    else:
        await ctx.reply("I'm not in a voice channel. You can't kick me out")


def context_to_voice_channel(ctx):
    return ctx.author.voice.channel if ctx.author.voice else None


async def get_or_create_voice_client(ctx):
    joined = False
    if ctx.guild.id in guild_to_voice_client:
        voice_client, last_used = guild_to_voice_client[ctx.guild.id]
    else:
        voice_channel = context_to_voice_channel(ctx)
        if voice_channel is None:
            voice_client = None
        else:
            voice_client = await voice_channel.connect()
            joined = True
            logging.info(f"feigbot connected to {voice_channel.name}")

    return voice_client, joined


@bot.command()
async def voices(ctx):
    logging.debug("!voices")
    file = discord.File(
        io.StringIO('\n'.join(uberduck_voices)),
        filename='voices.txt'
    )
    logging.debug(file)
    await ctx.reply(file=file)


async def vc(ctx, voice, speech):
    async with ctx.typing():
        audio_data = await uberduck_client.speak_async(speech, voice, check_every=1)
        voice_client, _ = await get_or_create_voice_client(ctx)
        guild_to_voice_client[ctx.guild.id] = (voice_client, datetime.datetime)
        logging.info("Audio data generated from Uberduck")
        await asyncio.sleep(0.3)

    with tempfile.NamedTemporaryFile(
            suffix=".wav", delete=False
    ) as wav_f, tempfile.NamedTemporaryFile(suffix=".opus", delete=False) as opus_f:
        wav_f.write(audio_data)
        wav_f.flush()

        subprocess.check_call(["ffmpeg", "-y", "-i", wav_f.name, opus_f.name])
        source = discord.FFmpegOpusAudio(opus_f.name)
        voice_client.play(source, after=None)
        while voice_client.is_playing():
            await asyncio.sleep(0.2)

        os.remove(wav_f.name)
        os.remove(opus_f.name)


bot.run(DISCORD_TOKEN)
