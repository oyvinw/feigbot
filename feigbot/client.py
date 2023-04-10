import asyncio
import datetime
import io
import logging
import os
import subprocess
import tempfile
from io import StringIO

import discord
import uberduck
from discord.ext import commands
from dotenv import load_dotenv
from tinydb import TinyDB, Query
from uberduck import UberDuck

from feigbot import stratz, openaiclient

logging.basicConfig(level=logging.INFO)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
KEY = os.getenv("UBERDUCK_API_KEY")
SECRET = os.getenv("UBERDUCK_API_SECRET")

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
db = TinyDB(os.path.join(os.path.dirname(__file__), '../data/db.json'))
stratz.update_items()

guild_to_voice_client = dict()
uberduck_client: UberDuck = uberduck.UberDuck(KEY, SECRET)
uberduck_voices = uberduck.get_voices(return_only_names=True)


class MatchData:
    def __init__(self, match, steam_id: int):
        self.match = match
        self.steam_id = steam_id


def get_steam_id(discord_user):
    Q = Query()
    return db.search(Q.discord_user == f'{discord_user}')[0]['steam_user_id_32']


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.reply("Jeg har ikke tillit til deg")


async def get_match(ctx, match_id):
    steam_id = get_steam_id(ctx.message.author)
    match = stratz.get_match(match_id)

    if match == []:
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
        await ctx.send(dota_hero_tips)


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
        await ctx.send(tips_text)


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
        await ctx.send(apology)


@bot.command(name="notsry", help="Use this command to justify yourself")
async def not_sorry(ctx, lang="eng", vcargs="", voice="relikk"):
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
        await ctx.send(apology)


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
    print(blame_text)
    if vcargs:
        await vc(ctx, voice, blame_text)
    else:
        await ctx.reply(blame_text)


@bot.command(name='reg')
async def reg(ctx, steam_acc: int):
    Q = Query()
    db.remove(Q.discord_user == f'{ctx.message.author}')
    db.insert({'discord_user': f'{ctx.message.author}', 'steam_user_id_32': steam_acc})

    await ctx.reply('You have been successfully registered')


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
        io.BytesIO(uberduck_voices),
        filename='voices.txt'
    )
    logging.debug(file)
    await ctx.reply(file=file)


async def vc(ctx, voice, speech):
    voice_client, _ = await get_or_create_voice_client(ctx)
    guild_to_voice_client[ctx.guild.id] = (voice_client, datetime.datetime)
    audio_data = uberduck_client.speak(speech, voice)
    logging.info("Audio data generated from Uberduck")

    with tempfile.NamedTemporaryFile(
            suffix=".wav", delete=False
    ) as wav_f, tempfile.NamedTemporaryFile(suffix=".opus", delete=False) as opus_f:
        wav_f.write(audio_data)
        wav_f.flush()

        subprocess.check_call(["ffmpeg", "-y", "-i", wav_f.name, opus_f.name])
        source = discord.FFmpegOpusAudio(opus_f.name)
        voice_client.play(source, after=None)
        while voice_client.is_playing():
            await asyncio.sleep(0.5)

        os.remove(wav_f.name)
        os.remove(opus_f.name)


bot.run(TOKEN, log_handler=handler, log_level=logging.DEBUG)
