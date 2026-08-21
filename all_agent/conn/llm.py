from langchain_openai import ChatOpenAI
def get_llm():
    llm = ChatOpenAI(
        model="deepseek-ai/DeepSeek-V4-Pro",
        #model = 'Qwen/Qwen3.5-9B',
        base_url="https://api.siliconflow.cn/v1",
        api_key="sk-zaxelatyaqhvdphrxqxgznqkjvrcbwclfgskuebcvxrjuues"
    )
    return llm