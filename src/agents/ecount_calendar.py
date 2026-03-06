import asyncio
import os
from playwright.sync_api import Playwright, sync_playwright, expect
from playwright.async_api import async_playwright

from rich import print
from dotenv import load_dotenv

from langchain_core.runnables import RunnableConfig
from langchain.tools import tool 
from langchain.chat_models import init_chat_model

from langchain_core.messages import (
    HumanMessage,
    SystemMessage,
    ToolMessage,
    get_buffer_string
)

from langgraph.graph import START, END, StateGraph, MessagesState
from langgraph.types import Command

from src.config import Configuration
from src.prompts import ecount_agent_prompt
from src.agents.supervisor import SupervisorState

load_dotenv()


@tool
async def ecount_calendar_tool(date: str) -> list:
    
    """Ecount에 접속하여 특정 날짜에 등록된 일정을 크롤링하여 리스트로 반환하는 Tool 

    Args:
        date (int): 조회할 날짜(YYYY-MM-DD) 

    Returns:
        list: 크롤링된 일정 내용 리스트
    """
    
    year, month, day = date.split('-')
    day = day.lstrip("0")

    # with sync_playwright() as playwright:
    async with async_playwright() as playwright:

        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        await page.goto("https://login.ecount.com/Login/")
        await page.get_by_role("textbox", name="회사코드").fill(os.getenv('ECOUNT_CODE'))
        await page.get_by_role("textbox", name="아이디").fill(os.getenv('ECOUNT_ID'))
        await page.get_by_role("textbox", name="비밀번호").fill(os.getenv('ECOUNT_PW'))
        await page.get_by_role("button", name="로그인").click()

        # 네트워크 유휴 상태 대기
        await page.locator('table.caledar').wait_for(state='visible', timeout=10000)
        
        # 수집 할 날짜 선택
        # day_cell = page.locator('td[data-role="calendar.addScheduleClick"]', has_text=day)
        day_cell = page.locator(f'xpath=//span[contains(@class,"day") and normalize-space()="{day}"]/ancestor::td[1]')

        day_lst = day_cell.locator('a[data-role="calendar.scheduleClick"]')

        event = []
        for i in range(await day_lst.count()):
            await day_lst.nth(i).click()
            await page.locator('.table-form').wait_for(state='visible')

            content = await page.locator('.table-form').inner_text()
            event.append(content)
            
            await page.locator('.ui-dialog-titlebar-close').click()
            
        if not event:
            event.append("등록된 일정이 없습니다.")    
            
        await context.close()
        await browser.close()
        
        return event
        
    
"""ECount 일정 확인 에이전트"""


# ====================
# File Search Agent
# ====================
async def ecount_agent(state: SupervisorState, config: RunnableConfig):
    """ECount 일정 확인 에이전트
    
    사용자 요청을 분석하여 적절한 검색 도구를 선택하고 실행
    
    Args:
        state: EcountState - 현재 상태
        config: RunnableConfig - 구성 정보
        
    Returns:
        검색 결과를 포함한 상태 업데이트
    """
    configurable = Configuration.from_runnable_config(config)
    print(state)
    # 사용 가능한 검색 도구
    search_tools = [ecount_calendar_tool]
    
    # 모델 설정
    model_name = configurable.sub_agent_model
    ecount_model = (init_chat_model(model_name)
                         .bind_tools(search_tools))
    
    messages = state.get("messages", [])

    system_prompt = ecount_agent_prompt.format(
        messages = get_buffer_string(messages)
    )
    
    # LLM 호출
    response = await ecount_model.ainvoke([SystemMessage(content=system_prompt)])
    
    # 도구 호출이 있으면 실행
    if response.tool_calls:
        
        for tool_call in response.tool_calls:
            tool_args = tool_call["args"]
            
            try:
                result = await ecount_calendar_tool.ainvoke(tool_args)
            except Exception as e:
                result = f"일정 검색 실행 중 오류 발생: {str(e)}"
                

            # tool 결과를 LLM에 다시 전달해서 포맷팅
            tool_result = "\n\n".join(result) if isinstance(result, list) else str(result)
            
            formatted_llm = init_chat_model(model_name)
            response = await formatted_llm.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=tool_result)
            ])
            
        
        return Command(
            goto=END,
            update={
                "messages": [response]
            }
        )
    
    # 도구 호출 없으면 그냥 종료
    return Command(
        goto=END,
        update={"messages": [response]}
    )
