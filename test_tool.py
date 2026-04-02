import asyncio
from pydantic_ai import Agent
from pydantic import BaseModel, Field
import os
from dotenv import load_dotenv

load_dotenv()
os.environ['GOOGLE_API_KEY'] = os.environ.get('GEMINI_API_KEY')

class Dashboard(BaseModel):
    message: str
    charts: list[str]

agent = Agent(
    'gemini-2.5-flash',
    output_type=Dashboard,
    system_prompt="You must use the get_data tool to find out how many apples there are before answering. Put the answer in the message field."
)

@agent.tool_plain
def get_data(item: str) -> str:
    print(f"Tool called with item: {item}")
    if item == "apples":
        return "There are exactly 42 apples in the database."
    return "Unknown item"

async def main():
    result = await agent.run("How many apples are there?")
    print("AI Response:", result.output.message)

asyncio.run(main())
