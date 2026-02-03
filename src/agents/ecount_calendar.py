import re
from playwright.sync_api import Playwright, sync_playwright, expect
from rich import print

from langchain.tools import tool 
from langchain.chat_models import init_chat_model
from langchain.agents import create_agent
from langchain.messages import SystemMessage, HumanMessage

from src.utils import get_today



@tool
def ecount_calendar_tool(date: str) -> list:
    """Ecount에 접속하여 특정 날짜에 등록된 일정을 크롤링하여 리스트로 반환하는 Tool 

    Args:
        date (int): 조회할 날짜(YYYY-MM-DD) 

    Returns:
        list: 크롤링된 일정 내용 리스트
    """
    
    year, month, day = date.split('-')
    day = day[1:]  # 0 제거
    with sync_playwright() as playwright:

        browser = playwright.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://login.ecount.com/Login/")


        cc = '651820'
        id = 'GHMIN'
        pw = 'ghmin12345'


        page.get_by_role("textbox", name="회사코드").fill(cc)
        page.get_by_role("textbox", name="아이디").fill(id)
        page.get_by_role("textbox", name="비밀번호").fill(pw)
        page.get_by_role("button", name="로그인").click()


        # 네트워크 유휴 상태 대기
        page.locator('table.caledar').wait_for(state='visible', timeout=10000)
        
        # 수집 할 날짜 선택
        day_cell = page.locator('td[data-role="calendar.addScheduleClick"]', has_text=day)

        day_lst = day_cell.locator('a[data-role="calendar.scheduleClick"]')


        event = []
        for i in range(day_lst.count()):
            day_lst.nth(i).click()
            page.locator('.table-form').wait_for(state='visible')
            
            content = page.locator('.table-form').inner_text()
            
            event.append(content)
            
            page.locator('.ui-dialog-titlebar-close').click()
            
        context.close()
        browser.close()
        
        return event
        
    
    
    
    
system_prompt = """너는 Ecount에 등록된 일정을 알려주는 유능한 비서야 

                오늘은 {today} 이야.

                사용자가 원하는 날짜에 어떤 일정이 등록되어있는지 알려줘.
                
                사용자가 년도와 월을 명시하지 않으면, 오늘 날짜의 년도와 월을 기준으로 일정을 찾아줘.
                  
                  만약 등록된 일정이 없으면 "등록된 일정이 없습니다."라고 답변해줘.
                  
                  제목, 날짜/시간, 참석자 정보를 포함해서 간결하게 작성해줘. 
                  
                  Example format:
                  [등록된 일정이 존재 하는 경우]
                  0000년 O월 OO일 일정을 알려드립니다.

                    - 제목: [일정 제목]
                    - 날짜/시간: [날짜/시간]
                    - 참석자: [참석자]
                                      
                  [등록된 일정이 없는 경우]
                    등록된 일정이 없습니다.
                    
                  """

system_prompt = system_prompt.format(today=get_today())


agent = create_agent(
    "openai:gpt-4o-mini",
    tools=[ecount_calendar_tool],
    system_prompt=system_prompt,
)




response = agent.invoke({"messages": [{"role": "user", "content": "2월 2일에 등록된 일정 알려줘"}]})


print(response)



# tools=[ecount_calendar_tool]

# tools[0].invoke({"date":3})   

