import os
from dotenv import load_dotenv
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain import LLMChain

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

async def get_dota2_tip_gpt(heroname):
    llm = OpenAI(model_name="text-davinci-003")
    prompt = PromptTemplate(
        input_variables=["heroname"],
        template="Give me a pro-tip I can make use of when playing {heroname} in Dota 2?"
    )

    chain = LLMChain(llm=llm,prompt=prompt)
    input = {'k': 1, 'heroname': heroname}
    return chain.run(input)
