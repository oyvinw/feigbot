from langchain.memory import ConversationSummaryBufferMemory
import src.stratz as stratz
from langchain import ConversationChain, PromptTemplate
from langchain import OpenAI
from src import client


class LiveMatch:
    def __init__(self, ctx, match_id: int):
        self.teams = []
        self.match_id = match_id
        md = stratz.get_live_match_initial(self.match_id)
        self.league_data = md.get('league')
        self.insight_data = md.get('insight')
        self.teams.append(md.get('radiantTeam'))
        self.teams.append(md.get('direTeam'))
        self.ctx = ctx
        self.llm = OpenAI(model_name="gpt-3.5-turbo", temperature=0.9)
        self.conv_chain = ConversationChain(
            llm=self.llm,
            verbose=True,
            memory=ConversationSummaryBufferMemory(
                llm=self.llm,
                max_token_limit=2000
            ),
        )
        self.live = True

    async def start_live(self):
        await self.ctx.send(
            f"Now following game between {self.teams[0].get('name')}({self.teams[0].get('countryCode')}) "
            f"and {self.teams[1].get('name')}({self.teams[1].get('countryCode')})")
        await self.conv_chain.arun(
            f"You are Dota 2 pro commentator, casting a live game between the following teams: {self.teams}, "
            f"updates of how the game is going will be provided in the form of "
            f"json-data from the Stratz API describing the game. Focus the "
            f"commentary on things the audience might find interesting and how the "
            f"game is progressing and has changed between the updates. Don't mention the "
            f"updates themselves, but pretend that you can tell what is happening by looking at the game.")
        await self.update_live()

    async def stop_live(self):
        self.live = False
        await self.ctx.reply("Stopping live update")

    async def update_live(self):
        while self.live:
            match_status = stratz.get_live_match_status(self.match_id)
            game_state = match_status.get('gameState')
            # Check if the game is updating
            if not match_status.get('isUpdating'):
                # Check if the game has ended
                if game_state == 'POST_GAME':
                    summary = await self.generate_game_end_summary()
                    await client.vc(self.ctx, "glados-p2", summary)
                else:
                    await self.ctx.send("The game is no longer updating. Live stream stopping")

                await self.stop_live()
                return

            # Check if we are in draft
            if game_state == 'HERO_SELECTION':
                await client.vc(self.ctx, "glados-p2", await self.generate_draft_commentary())

            if game_state == 'GAME_IN_PROGRESS':
                await client.vc(self.ctx, "glados-p2", await self.generate_commentary())

    async def generate_commentary(self):
        match = stratz.get_live_match(self.match_id)
        return await self.conv_chain.arun(f"Here is the data for the current state of the match: \n\n {match} \n\n Try not to "
                               f"repeat yourself. Stick to the data and don't invent things."
                               f"Talk about the heros using mostly the player names. Analyse the game state "
                               f"and predict how the game will progress. "
                               f"The score represents kills. winRateValues represent the radiants chance to win at "
                               f"the corresponding minute. Try not to repeat yourself too much."
                               f"Don't include a summary every time. Keep the commentary short and varied!")

    async def generate_game_end_summary(self):
        match = stratz.get_live_match(self.match_id)
        return await self.conv_chain.arun(f"The game just ended with this being the final data: \n\n {match} \n\n"
                               f"Give a summary of the game and explain why the winner won and the losers lost. Put "
                               f"it in a larger context in terms of the current tournament and the match history "
                               f"between the two teams")

    async def generate_draft_commentary(self):
        match = stratz.get_live_draft(self.match_id)
        return await self.conv_chain.arun(f"The teams are drafting their heroes. The current state of the draft is: \n\n {match} \n\n"
                               f"Provide analytical insight into which team has the highest chances of winning and why.")
