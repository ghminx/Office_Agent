import os 
import asyncio
import operator
from rich import print
import yaml

from typing import Annotated, Optional, TypedDict, Literal
from pydantic import BaseModel, Field

from langchain_core.runnables import RunnableConfig
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool

from langgraph.graph import MessagesState
from langgraph.graph import START, END, StateGraph
from langgraph.types import Command


from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
    ToolMessage,
    get_buffer_string
)


from src.config import Configuration
from src.prompts import mail_classify_prompt
from langchain_core.messages import MessageLikeRepresentation
    
    


# ====================
# State Definitions
# ====================
# class MailState(MessagesState):
class MailState(TypedDict):
    """메일 생성 및 발송 에이전트 상태
    
    Attributes:
        mail_content (dict): 사용자의 메일 작성 요청 내용 (메일 작성에 필요한 정보)
        send_mail_type (str): 분류된 메일 유형 (예: 일반, 보고서, 견적서 등)
    """
    mail_content: dict
    send_mail_type: str


# ====================
# Structured Output 
# ====================
class MailType(BaseModel):
    type: Literal["일반", "보고서", "견적서-신규고객", "견적서-기존고객"] = Field(description="분류된 메일 유형")
    
    

# ====================
# Mail Send Agent
# ====================

def mail_classify(state: MailState, config: RunnableConfig) -> Command[Literal["mail_generate", "mail_template"]]:
    """사용자의 요청을 분석하여 메일 유형을 분류하는 노드"""

    user_content = state['mail_content']['user_content']
    
    configurable = Configuration.from_runnable_config(config)
    
    model_name = configurable.sub_agent_model
    classify_model = init_chat_model(model_name, temperature=0).with_structured_output(MailType)
    
    system_prompt = mail_classify_prompt.format(user_content=user_content)
    response = classify_model.invoke(system_prompt)
    
    mail_type = response.type
    
    return Command(
        goto="mail_generate" if mail_type == "일반" else "mail_template",
        update={"send_mail_type": mail_type}
    )

def mail_generate(state: MailState):
    
    print(state)
    pass

def mail_template(state: MailState):
    
    print(state) 
    
    with open("src/agents/templates.yaml", encoding = 'utf-8') as f:
        templates = yaml.safe_load(f)

    template = templates[state['send_mail_type']]
    print(template)
    # template = templates["보고서"]
    # # body = template["body"].format(recipient="홍길동", ...)

    # print(template['context'].format(send_name="김우정", ext='46464646'))


    pass


builder = StateGraph(MailState, config_schema=Configuration)
builder.add_node("mail_classify", mail_classify)  # File search agent node
builder.add_node("mail_generate", mail_generate)  # File search agent node
builder.add_node("mail_template", mail_template)  # File search agent node

builder.add_edge(START, "mail_classify")  # Entry point to supervisor
agent = builder.compile()

async def run():

    state = {
            'mail_content': {
                'user_content': '클라이언트에게 보고서를 보낼거야 메일을 보내줘',
                'to_mail': 'casu106@naver.com',
                'from_mail': 'rmsghd456@daum.net',
                'app_password': 'jmjopxnhcoxfzujg',
                'send_name': '민근홍',
                'position': '주임',
                'ext': '070-0000-0000'
            }}
        
    response = await agent.ainvoke(state, config=RunnableConfig())
    
    return response

if __name__ == "__main__":
    import time 
    
    start = time.time()
    response = asyncio.run(run())
    end = time.time()
    print(f"Execution Time: {end - start} seconds")
    
    
    

    

