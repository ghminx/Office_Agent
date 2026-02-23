import asyncio
from rich import print 

from langgraph.graph import START, END, StateGraph

from src.config import Configuration

from src.agents.supervisor import supervisor, supervisor_tools, SupervisorState
from src.agents.file_search import file_search_agent, FileSearchState
from src.agents.send_mail import mail_classify, MailState
from langchain_core.runnables import RunnableConfig



supervisor_builder = StateGraph(SupervisorState, config_schema=Configuration)

# Add supervisor nodes for research management
supervisor_builder.add_node("supervisor", supervisor)           # Main supervisor logic
supervisor_builder.add_node("supervisor_tools", supervisor_tools)  # Tool execution handler
supervisor_builder.add_node("file_search_agent", file_search_agent)  # File search agent node
supervisor_builder.add_node("mail_classify", mail_classify)  # File search agent node

# Define supervisor workflow edges
supervisor_builder.add_edge(START, "supervisor")  # Entry point to supervisor

# Compile supervisor subgraph for use in main workflow
agent = supervisor_builder.compile()


async def run():
    # user =  '전략기획팀 폴더에서 2025년에 작성한 디딤돌 사업에 있는 파일 어떤거 있는지 확인해줘'

    user = """{
        "from_mail": "rmsghd456@daum.net",
        "to_mail": "casu106@naver.com",
        "app_password": "jmjopxnhcoxfzujg",
        "user_content": "클라이언트에게 보고서를 보낼거야 메일을 보내줘"
    }"""
    
    
    # response = await agent.ainvoke({"messages": user}, config=RunnableConfig())
    response = await agent.ainvoke({"messages": user}, config=RunnableConfig())
    
    return response

if __name__ == "__main__":
    import time 
    
    start = time.time()
    response = asyncio.run(run())
    end = time.time()
    print(f"Execution Time: {end - start} seconds")
    
