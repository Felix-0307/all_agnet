from pydantic import BaseModel, Field
from langchain.agents import create_agent
from conn.llm import get_llm
from langchain.messages import AIMessageChunk


class ContactInfo(BaseModel):
    """一个人的联系信息。"""
    name: str = Field(description="该人的姓名")
    email: str = Field(description="该人的电子邮件地址")
    phone: str = Field(description="该人的电话号码")


agent = create_agent(
    model=get_llm(),
    tools=[],
    response_format=ContactInfo  # 自动选择 ProviderStrategy
)

result = agent.stream({
    "messages": [{"role": "user", "content": "从如下文本中提取信息: John Doe, john@example.com, (555) 123-4567"}]
}, stream_mode=['messages','updates'])

for chunk in result:
    print(chunk)
    if chunk[0] == 'messages':
        if type(chunk[1][0]) == AIMessageChunk:
            print(chunk[1][0].content,end='\n')
    else:
        print(chunk)


# print('_'*100)


#
# print(result["structured_response"])
# # name='John Doe' email='john@example.com' phone='(555) 123-4567'
# print(type(result["structured_response"]))
# # <class '__main__.ContactInfo'>
# print(result["structured_response"].name)
# # John Doe