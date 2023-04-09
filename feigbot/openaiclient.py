import logging
import os
from dotenv import load_dotenv
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain import LLMChain

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
fast_model = "gpt-3.5-turbo"
good_model = "text-davinci-003"

legend = open(os.path.join(os.path.dirname(__file__), '../data/legend.txt'))


async def prompt_gpt_apology(match, sinner, heroname, lang):
    llm = OpenAI(model_name=good_model)
    return llm(
        f"{default_prompt(match)} write an apologetic short speech about a bad dota 2 match. Write as a player named {sinner}, playing as {heroname}. {lang_preset(lang)}")


async def prompt_gpt_not_apology(match, sinner, heroname, lang):
    llm = OpenAI(model_name=fast_model)
    return llm(
        f"{default_prompt(match)} write an unapologetic short speech about a bad dota 2 match. Justify why the loss isn't your fault. Use dry wit and sarcasm. Write as a player named {sinner}, playing as {heroname}. {lang_preset(lang)}")


async def prompt_gpt_herotip(heroname):
    llm = OpenAI(model_name=fast_model)
    prompt = PromptTemplate(
        input_variables=["heroname"],
        template="Write me a pro-tip for improving my playstyle as {heroname} in Dota 2. Be short."
    )

    chain = LLMChain(llm=llm, prompt=prompt)
    input = {'k': 1, 'heroname': heroname}
    return chain.run(input)


async def prompt_analyse(match, lang):
    llm = OpenAI(model_name=fast_model)
    prompt = f"{default_prompt(match)} write a 2-3 paragraph witty analysis of the game. You may write about players item choices, specific lane outcomes or anything else that could be interesting. You may include some emojis from discord. {lang_preset(lang)}"
    logging.debug(f"prompt length is: {len(prompt)}")
    return llm(prompt)


async def prompt_blame(match, lang, emoji=False):
    llm = OpenAI(model_name=fast_model)
    emoji_info = ""
    if emoji:
        emoji_info = "You may include some emojis from discord."
    return llm(
        f"{default_prompt(match)} write a short and witty comment about what player is to blame for the loss. {emoji_info} {lang_preset(lang)}")


async def prompt_gpt_tips(match, hero, lang):
    llm = OpenAI(model_name=fast_model)
    return llm(
        f"{default_prompt(match)} write a two paragraph witty comment about how {hero} could improve. Include some general tips. You may include some emojis from discord. {lang_preset(lang)}")


def default_prompt(match):
    return f"Here is data collected about a Dota 2 game from the Stratz API: \n\n {match} and here is some information on how to interpret the data: \n\n{legend.read()} \n\nBased on this data and the interpretation,"


def lang_preset(lang):
    return f"Write it in the language that has language code {lang}."
