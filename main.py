from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
import os
from rich import print



def check_weather(location: str) -> str:
    '''지정된 위치의 날씨 예보를 반환합니다.'''
    return f"{location}는 항상 맑습니다"


model = init_chat_model("anthropic:claude-sonnet-4-5-20250929", thinking={"type": "enabled", "budget_tokens": 2000})



# response = model.invoke("Langchain에서 에이전트를 구축하는 간단한 예제 알려줘")



# for chunk in model.stream("Langchain에 대해서 간략하게 설명해줘"):
    
#     for r in chunk.content_blocks:
#         if r["type"] == "reasoning":
#             print(r['reasoning'], end="", flush=True)
    
#     print(chunk.text, end="", flush=True)
    





graph = create_agent(
    model=model,
    tools=[check_weather],
    system_prompt="당신은 유용한 도우미입니다",
)
inputs = {"messages": [{"role": "user", "content": "랭체인의 create_agent에 대해서 간략하게 설명"}]}
for chunk in graph.stream(inputs, stream_mode="updates"):
    print(chunk)