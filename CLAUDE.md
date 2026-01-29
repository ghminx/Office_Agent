# CLAUDE.md

이 문서는 Claude Code가 본 프로젝트에서 작업할 때 참고하는 가이드입니다.

## 프로젝트 컨텍스트

### 목적

업무 자동화를 위한 LLM 기반 멀티 에이전트 시스템 구축. Supervisor Agent가 사용자 요청을 분석하고, 적절한 Sub-Agent를 선택/조합하여 작업을 수행합니다.

### 핵심 기능

1. **파일 탐색**: 자연어 기반 파일 시스템 검색
2. **Ecount 일정**: RPA로 Ecount 일정 조회
3. **메일 자동화**: 템플릿 기반 메일 작성 및 발송
4. **견적 자동화**: 견적서 생성 → 유사 견적 비교 → 분석 → 메일 발송

## 아키텍처 원칙

### Supervisor 중심 구조

```
사용자 요청 → Supervisor → Agent 선택 → 도구 실행 → 응답
```

- **모든 요청**은 Supervisor를 통해 처리 (메인 플로우)
- Supervisor가 LLM으로 요청을 분석하여 적절한 Agent 선택

### Agent와 Tool의 분리

- **Agent**: LLM을 사용하여 **판단**하고 도구를 **선택/조합**
- **Tool**: 실제 **작업 수행** (파일 검색, API 호출, 메일 발송 등)

```
Agent (판단) → Tool (실행)

예시:
FileSearchAgent (검색 조건 추출) → file_system.search() (실제 검색)
MailAgent (메일 내용 생성) → mail_sender.send() (실제 발송)
```

## 코드 작성 규칙

### Python 스타일

- Python 3.13+ 문법 사용
- 비동기 함수 사용 (`async/await`)
- Type hints 필수
- Pydantic으로 데이터 검증

### 파일 배치 규칙

| 유형 | 위치 | 설명 |
|------|------|------|
| Agent 클래스 | `src/agents/` | LangGraph Agent |
| Tool 함수 | `src/tools/` | Agent가 호출하는 도구 |
| DB 모델 | `src/models/` | SQLAlchemy 모델 |
| 스키마 | `src/schemas/` | Pydantic 모델 |

### 네이밍 규칙

```python
# Agent: ~Agent 접미사
class FileSearchAgent:
    pass

# Tool 함수: 동사로 시작
def search_files():
    pass

def send_mail():
    pass

# 스키마: ~Request, ~Response 접미사
class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    result: str
```

## LangGraph 사용법

### Supervisor 구현

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import operator

class AgentState(TypedDict):
    messages: Annotated[list, operator.add]   # 이 부분은 변경될 수 있음 Messages 를 나타내는 다양한 방법이 있기 때문
    next_agent: str
    results: list

def build_supervisor():
    workflow = StateGraph(AgentState)

    # 노드 추가
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("file_search", file_search_node)
    workflow.add_node("ecount", ecount_node)
    workflow.add_node("mail", mail_node)
    workflow.add_node("quotation", quotation_node)

    # 조건부 엣지 (Supervisor → 선택된 Agent)
    workflow.add_conditional_edges(
        "supervisor",
        route_to_agent,
        {
            "file_search": "file_search",
            "ecount": "ecount",
            "mail": "mail",
            "quotation": "quotation",
            "end": END
        }
    )

    # Agent → Supervisor (추가 작업 판단)
    for agent in ["file_search", "ecount", "mail", "quotation"]:
        workflow.add_edge(agent, "supervisor")

    workflow.set_entry_point("supervisor")
    return workflow.compile()
```

### Agent State 패턴

```python
# State는 Agent 간 데이터 전달에 사용
state = {
    "messages": ["사용자 요청 내용"],
    "next_agent": "file_search",
    "results": [
        {"agent": "file_search", "data": [...], "summary": "..."},
        {"agent": "mail", "data": {...}, "summary": "..."}
    ]
}
```

## 주요 의존성

```toml
[project.dependencies]
fastapi = ">=0.115.0"
uvicorn = ">=0.30.0"
langgraph = ">=0.2.0"
langchain-anthropic = ">=0.3.0"
anthropic = ">=0.40.0"
openpyxl = ">=3.1.0"
aiosmtplib = ">=3.0.0"
selenium = ">=4.25.0"
undetected-chromedriver = ">=3.5.0"
sqlalchemy = ">=2.0.0"
asyncpg = ">=0.30.0"
redis = ">=5.0.0"
pydantic = ">=2.0.0"
pydantic-settings = ">=2.0.0"
```

## 테스트

```bash
# 전체 테스트 실행
uv run pytest

# 특정 Agent 테스트
uv run pytest tests/test_agents.py -k "file_search"

# 커버리지 포함
uv run pytest --cov=src
```

## 자주 사용하는 명령어

```bash
# 개발 서버 실행
uv run uvicorn main:app --reload

# 의존성 추가
uv add <package_name>

# 타입 체크
uv run mypy src/

# 린트
uv run ruff check src/
```

## 주의사항

### Ecount RPA

- Ecount는 API가 없어 Selenium 혹은 playwright 기반 RPA 사용
- 로그인 세션 관리 필요
- 동시 접속 제한 있을 수 있음

### Excel 처리

- `pywin32` 사용 금지 (동시성 문제)
- `openpyxl`로 Excel 파일 직접 생성/수정
- 템플릿 로드 후 값만 채우는 방식 권장

-- 위 내용은 아직 정해지지 않았음 사용자가 추후에 제공할 예정

### LLM 비용

- 모든 요청이 Supervisor를 거치므로 LLM 호출 발생
- 캐싱(Redis) 적극 활용
- 단순 반복 작업은 백업 API(`/tools/*`) 사용 권장

### 보안

- API 키는 환경 변수로 관리 (`.env`)
- Ecount 크레덴셜 암호화 저장
- 민감 정보 로깅 금지

## 확장 가이드

### 새 Agent 추가 시

1. `src/agents/`에 Agent 클래스 생성
2. `src/tools/`에 필요한 도구 함수 작성
3. `src/agents/supervisor.py`에 Agent 등록
4. LangGraph 워크플로우에 노드/엣지 추가
5. 테스트 작성

