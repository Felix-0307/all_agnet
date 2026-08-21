# 辅助理解代码
from conn.llm import get_llm
import json
import datetime
import re

llm = get_llm()

# =====================================================================
# 第一步：定义函数调用的"约定"（System Prompt）
# =====================================================================
# 由于本示例使用普通对话模型（非原生支持 tool_use 的模型），
# 这里通过 system prompt 让 LLM 按照约定的 JSON 格式输出函数名+参数，
# 由我们自己来"模拟" function_call 的解析与执行。
# 原生 function_call 流程通常是：
#   1) 把"可用函数 schema"作为 tools 传给模型
#   2) 模型若需要工具，会在响应中返回一个 tool_call 字段
#   3) 客户端执行工具，把结果以 tool 消息追加
#   4) 再调用模型，让其基于工具结果给出最终回答
# =====================================================================
SYSTEM_PROMPT = """
你是一个智能助手，可以调用以下函数工具：
1. 加法函数：
   - 名称：add
   - 功能：计算两个整数的和
   - 参数：
        a: 整数（第一个数字）
        b: 整数（第二个数字）
   - 调用格式：{"function": "add", "arguments": {"a": x, "b": y}}

2. 时间函数：
   - 名称：get_current_time
   - 功能：获取当前时间
   - 参数：无
   - 调用格式：{"function": "get_current_time", "arguments": {}}

调用规则：
1. 当用户问题需要数学计算时调用add
2. 当用户问题涉及当前时间时调用get_current_time
3. 其他情况直接回答问题
4. 调用函数时必须严格使用JSON格式
5. 不要解释函数调用过程，直接输出JSON或回答
"""



# =====================================================================
# 第二步：定义真正的本地函数（模拟"工具实现"）
# =====================================================================
# 这些就是 LLM 真正能调用的"工具"。
# 在原生 function_call 中，这些函数会被注册为 tools 传给模型。
def add(a, b):
    return a + b


def get_current_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# =====================================================================
# 第三步：函数注册表（function registry）
# =====================================================================
# 名字 -> 真实可调用对象的映射。
# 解析出 func_name 后，通过查表真正执行对应的 Python 函数。
function_registry = {
    "add": add,
    "get_current_time": get_current_time
}


# =====================================================================
# 第四步：解析 LLM 返回的"伪 function_call"
# =====================================================================
# 由于用的不是原生 tool_use 模型，模型只会输出 JSON 字符串。
# 我们用正则从中抠出 JSON，解析出函数名 + 参数。
# 原生 tool_use 模型这一步不需要 —— 模型直接返回结构化对象。
def parse_function_call(response):
    try:
        # 用正则贪婪匹配出第一个 {...} 块（覆盖多行 JSON）
        json_str = re.search(r'\{[\s\S]*\}', response).group()
        data = json.loads(json_str)
        # 取出函数名和参数（参数允许为空 dict）
        return data["function"], data.get("arguments", {})
    except:
        pass
    # 解析失败说明模型这次没有"调函数"，返回 None
    return None, None


def do(question):
    # --- 构建初始对话消息（system + user） ---
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question}
    ]

    print(f"User>\t {question}")

    # =================================================================
    # 第五步：第一次调用 LLM —— 让模型"决定是否调用工具"
    # =================================================================
    # 对应原生 function_call 中的：传入 tools，模型返回 tool_calls。
    # 这里我们让模型直接以 JSON 文本的形式表达"我想调哪个工具"。
    response = llm.invoke(messages)
    print(f"最初回复>\t {response.content}")

    # =================================================================
    # 第六步：解析模型回复，判断是否真的要执行函数
    # =================================================================
    # parse_function_call 返回 (func_name, func_args)；
    # 如果解析失败或函数不在注册表里，就当作"普通对话"，直接返回。
    func_name, func_args = parse_function_call(response.content)
    if func_name and func_name in function_registry:
        # --- 真正执行本地函数（这一步在客户端/服务端跑，不经过 LLM） ---
        print(f"执行函数>{func_name} 参数 {func_args}")
        if func_args:
            # 注意：**func_args 是把字典解包成关键字参数，例如 {"a":1,"b":2} -> add(a=1, b=2)
            result = function_registry[func_name](**func_args)
        else:
            result = function_registry[func_name]()

        print(f"函数返回>\t {result}")

        # =================================================================
        # 第七步：把"函数执行结果"喂回给模型，让它基于真实结果回答
        # =================================================================
        # 这是 function_call 的关键 —— 模型本身不会算加法、不会读系统时钟，
        # 我们把工具跑出来的真实结果作为新消息追加进去，让模型组织最终答案。
        # 在原生 tool_use 中，这一步对应往 messages 里追加 tool 角色的消息。
        messages.append({"role": "assistant", "content": response.content})  # 保留模型上一轮的"调用意图"
        messages.append({"role": "user", "content": f"函数执行结果: {result}\n请基于此结果回答我的原始问题"})

        # --- 第二次调用 LLM：基于工具结果生成最终回复 ---
        final_response = llm.invoke(messages)
        return final_response.content
    else:
        # 模型没有调用工具，直接返回原始回复即可
        return response.content


if __name__ == '__main__':
    # 测试不同场景
    questions = [
        "现在几点，并且告诉我123+222等于多少"
        # "123加456等于多少？",
        # "现在几点了？",
        # "你好，今天天气怎么样？"
    ]

    for q in questions:
        print("=" * 50)
        result = do(q)
        print(f"最终回复: {result}\n")







