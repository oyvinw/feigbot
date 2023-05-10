import asyncio
import datetime
import logging
import os
import subprocess
import tempfile
import discord
import numpy

import librosa
import uberduck
from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationSummaryBufferMemory
from uberduck import UberDuck

import src.stratz as stratz
from langchain import ConversationChain

import src.util
from src import client
import queue

load_dotenv()
UBERDUCK_KEY = os.getenv("UBERDUCK_API_KEY")
UBERDUCK_SECRET = os.getenv("UBERDUCK_API_SECRET")
uberduck_client: UberDuck = uberduck.UberDuck(UBERDUCK_KEY, UBERDUCK_SECRET)


class LiveMatch:
    def __init__(self, ctx, match_id: int):
        self.match_id = match_id
        self.ctx = ctx
        self.teams = None
        self.league_data = None
        self.insight_data = None
        self.llm = None
        self.conv_chain = None
        self.live = False
        self.text_buffer = queue.Queue()
        self.voice_buffer = queue.Queue()
        self.next_poll = None
        self.voice_client = None

    async def start_live(self):
        md = await stratz.get_live_match_initial(self.match_id)
        self.next_poll = datetime.datetime.now()
        self.voice_client, _ = await client.get_or_create_voice_client(self.ctx)
        self.teams = []
        self.league_data = md.get('league')
        self.insight_data = md.get('insight')
        self.teams.append(md.get('radiantTeam'))
        self.teams.append(md.get('direTeam'))
        self.llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.9)
        self.conv_chain = ConversationChain(
            llm=self.llm,
            verbose=True,
            memory=ConversationSummaryBufferMemory(
                llm=self.llm,
                max_token_limit=2000
            ),
        )
        self.live = True

        await self.ctx.send(
            f"Now following game between {self.teams[0].get('name')}({self.teams[0].get('countryCode')}) "
            f"and {self.teams[1].get('name')}({self.teams[1].get('countryCode')})")
        await self.conv_chain.arun(
            f"You are Dota 2 pro commentator, casting a live game between the following teams: {self.teams}, "
            f"updates of how the game is going will be provided in the form of "
            f"json-data from the Stratz API describing the game. Focus the "
            f"commentary on things the audience might find interesting and how the "
            f"game is progressing and has changed between the updates. Don't mention the "
            f"updates themselves, but pretend that you can tell what is happening by looking at the game. Keep all "
            f"responses to under 700 characters")

        update_task = asyncio.create_task(self.update_live())
        voice_task = asyncio.create_task(self.voice_worker())
        play_task = asyncio.create_task(self.vc_play_enqueued())

        await update_task
        await voice_task
        await play_task

    async def stop_live(self):
        self.live = False
        await self.ctx.reply("Stopping live update")

    async def update_live(self):
        while self.live:
            now = datetime.datetime.now()
            if self.next_poll > now:
                await asyncio.sleep(0.2)
                continue

            self.next_poll = datetime.datetime.max
            match_status = await stratz.get_live_match_status(self.match_id)
            game_state = match_status.get('gameState')
            text = ""
            # Check if the game is updating
            if not match_status.get('isUpdating'):
                # Check if the game has ended
                if game_state == 'POST_GAME':
                    text = await self.generate_game_end_summary()
                else:
                    await self.ctx.send("The game is no longer updating. Live stream stopping")

            # Check if we are in draft
            if game_state == 'HERO_SELECTION':
                text = await self.generate_draft_commentary()

            if game_state == 'GAME_IN_PROGRESS':
                text = await self.generate_commentary()

            # Chunking text to smaller sizes in order to keep within limits of the voice API
            sentences = src.util.split_into_sentences(text)
            parts = (len(text) / 500) + 1
            for section in numpy.array_split(sentences, parts):
                section_text = ' '.join(section)
                self.text_buffer.put((now, section_text))
                print(section_text)

            print("---GET DATA---")
            print(f"timestamp: {now}")
            print(f"text buffer length: {self.text_buffer.qsize()}")
            print(f"voice buffer length: {self.voice_buffer.qsize()}")

    async def voice_worker(self):
        while self.live:
            if self.text_buffer.empty() is True:
                await asyncio.sleep(0.2)
                continue

            print("---GET VOICE---")
            timestamp, text = self.text_buffer.get()
            print(f"timestamp: {timestamp}")
            print(f"requesting data from uberduck")
            audio_data = await uberduck_client.speak_async(text, "glados-p2", check_every=1)
            print(f"audio data recieved from uberduck")
            print(f"ffmpeg encoding started")
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as wav_f, tempfile.NamedTemporaryFile(suffix=".opus",
                                                                                                  delete=False) as opus_f:
                wav_f.write(audio_data)
                wav_f.flush()
                subprocess.check_call(["ffmpeg", "-y", "-i", wav_f.name, opus_f.name])
                self.voice_buffer.put((timestamp, opus_f))

                clip_duration = librosa.get_duration(path=opus_f.name)
                self.next_poll = timestamp + datetime.timedelta(
                    seconds=clip_duration)
                print(f"clip added to queue of length {clip_duration}")

            try:
                os.remove(wav_f.name)
            except:
                logging.warning("Could not remove temp-file")

            print(f"ffmpeg encoding finished")
            print(f"text buffer length: {self.text_buffer.qsize()}")
            print(f"voice buffer length: {self.voice_buffer.qsize()}")
            self.text_buffer.task_done()

    async def vc_play_enqueued(self):
        while self.live:
            if self.voice_buffer.empty() is True:
                await asyncio.sleep(0.2)
                continue

            print("---PLAY CLIP---")
            print("Detected audio in buffer")
            timestamp, audio = self.voice_buffer.get()
            timestamp_with_delay = timestamp + datetime.timedelta(seconds=90)
            print(f"Timestamp for clip is {timestamp}")
            print(f"clip queued to play at: {timestamp_with_delay}")
            while datetime.datetime.now() < timestamp_with_delay:
                await asyncio.sleep(0.2)

            print(f"Playing clip!")
            source = discord.FFmpegOpusAudio(audio.name)
            self.voice_client.play(source, after=None)
            while self.voice_client.is_playing():
                await asyncio.sleep(0.2)

            os.remove(audio.name)
            print(f"text buffer length: {self.text_buffer.qsize()}")
            print(f"voice buffer length: {self.voice_buffer.qsize()}")
            self.voice_buffer.task_done()

    async def generate_commentary(self):
        match = await stratz.get_live_match(self.match_id)
        return await self.conv_chain.arun(
            f"Here is the data for the current state of the match: \n\n {match} \n\n Try not to "
            f"repeat yourself. Stick to the data and don't invent things. "
            f"Talk about the heroes using mostly the player names. Analyse the game state "
            f"and predict how the game will progress. "
            f"The score represents kills. winRateValues represent the radiants chance to win at "
            f"the corresponding minute. Try not to repeat yourself too much."
            f"Don't include a summary every time. Keep the commentary short and varied!")

    async def generate_game_end_summary(self):
        match = await stratz.get_live_match(self.match_id)
        return await self.conv_chain.arun(f"The game just ended with this being the final data: \n\n {match} \n\n"
                                          f"Give a summary of the game and explain why the winner won and the losers lost. Put "
                                          f"it in a larger context in terms of the current tournament and the match history "
                                          f"between the two teams")

    async def generate_draft_commentary(self):
        match = await stratz.get_live_draft(self.match_id)
        return await self.conv_chain.arun(
            f"The teams are drafting their heroes. The current state of the draft is: \n\n {match} \n\n"
            f"Provide analytical insight into which team has the highest chances of winning and why.")
