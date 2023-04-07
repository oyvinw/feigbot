import os
from dotenv import load_dotenv
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain import LLMChain

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

async def prompt_gpt_apology(sinner, heroname):
    llm = OpenAI(model_name="text-davinci-003")
    return llm(f"Write an apologetic short speech about a bad dota 2 match. Write as a player named {sinner}, and include the hero {heroname}")

async def prompt_gpt_herotip(heroname):
    llm = OpenAI(model_name="text-davinci-003")
    prompt = PromptTemplate(
        input_variables=["heroname"],
        template="Write me a pro-tip for improving my playstyle as {heroname} in Dota 2. Be short."
    )

    chain = LLMChain(llm=llm,prompt=prompt)
    input = {'k': 1, 'heroname': heroname}
    return chain.run(input)