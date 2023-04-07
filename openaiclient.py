import os
from dotenv import load_dotenv
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain import LLMChain

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
legend = open("legend.txt")

async def prompt_gpt_apology(match, sinner, heroname, lang):
    llm = OpenAI(model_name="text-davinci-003")
    return llm(f"{default_prompt(match)} write an apologetic short speech about a bad dota 2 match. Write as a player named {sinner}, playing as {heroname}. {lang_preset(lang)}")

async def prompt_gpt_herotip(heroname):
    llm = OpenAI(model_name="text-davinci-003")
    prompt = PromptTemplate(
        input_variables=["heroname"],
        template="Write me a pro-tip for improving my playstyle as {heroname} in Dota 2. Be short."
    )

    chain = LLMChain(llm=llm,prompt=prompt)
    input = {'k': 1, 'heroname': heroname}
    return chain.run(input)

async def prompt_analyse(match, lang):
    llm = OpenAI(model_name="text-davinci-003")
    return llm(f"{default_prompt(match)} write a short and witty analysis of the game. You may include some emojis from discord. {lang_preset(lang)}")

async def prompt_blame(match, lang):
    llm = OpenAI(model_name="text-davinci-003")
    return llm(f"{default_prompt(match)} write a short witty comment about what player is to blame for the loss. You may include some emojis from discord. {lang_preset(lang)}")

async def prompt_gpt_tips(match, hero, lang):
    llm = OpenAI(model_name="text-davinci-003")
    return llm(f"{default_prompt(match)} write a short witty comment about how {hero} could improve. Include some general tips. You may include some emojis from discord. {lang_preset(lang)}")

def default_prompt(match):
    return f"Here is data collected about a Dota 2 game from the Stratz API: \n\n {match} and here is some information on how to interpret the data: \n\n{legend.read()} \n\nBased on this data and the interpretation,"

def lang_preset(lang):
    return f"Write it in the language that has language code {lang}."