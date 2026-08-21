from langchain.agents import create_agent
from conn.llm import get_llm
import datetime
from langchain.tools import tool

def add(a: int, b: int):
    """
    两个数相加
    :param a: 第一个数
    :param b: 第二个数
    :return: 两个数的和
    """
    return a + b

@tool(name_or_callable="get_current_time", description="返回当前时间")
def get_current_time():
    """返回当前时间"""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

agent = create_agent(model=get_llm(),
                     tools=[get_current_time, add],
                     system_prompt='你是一个助理'
                     )
r = agent.invoke({'message':[{'role':'user','content':'你好'}]})
print(r)


# if __name__ == '__main__':
    # print(get_current_time())

















