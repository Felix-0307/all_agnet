from langchain.agents import create_agent
from conn.llm import get_llm
import datetime
from langchain.tools import tool
from pydantic import BaseModel, Field

class Args(BaseModel):
    a: int = Field(..., description="第一个数")
    b: int = Field(..., description="第二个数")

@tool(name_or_callable="add", description="两个数相加", args_schema=Args)
def add(a: int, b: int):
    return a + b

def get_current_time():
    """返回当前时间"""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

agent = create_agent(model=get_llm(),
                     tools=[get_current_time],
                     system_prompt='你是一个助理'
                     )
r = agent.invoke({'message':[{'role':'user','content':'你好'}]})
print(r)


# if __name__ == '__main__':
    # print(get_current_time())





