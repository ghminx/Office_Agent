# AI Agent System

LLM 기반 멀티 에이전트 시스템으로, Supervisor가 여러 Sub-Agent를 오케스트레이션하여 업무 자동화를 수행합니다.

## 시스템 개요

### 주요 기능

| 기능 | 설명 |
|------|------|
| **파일 탐색** | 자연어로 파일 검색 요청 시 조건 기반 탐색 (파일명, 확장자, 생성일 등) |
| **Ecount 일정 확인** | Ecount에 등록된 일정 조회 및 요약 (RPA 기반) |
| **메일 자동화** | 메일 초안 생성, 템플릿 적용, 첨부파일 자동 추가 후 발송 |
| **견적 생성 자동화** | 고객 요구사항 기반 견적서 생성, 유사 견적 비교 분석, 메일 발송 연계 |

### 견적 자동화 프로세스

```
1. 고객 요구사항 기반 견적서 생성 (Excel)
2. 유사 견적서 검색 (가격, 조사모드, 표본수 기준)
3. 생성 견적서와 비교 견적서를 LLM으로 분석하여 검토 의견 생성
4. (선택) 메일 자동화 연계하여 발송
```

## 아키텍처

### 멀티 에이전트 구조

```
                         ┌─────────────────┐
                         │   사용자 요청    │
                         └────────┬────────┘
                                  ↓
                    ┌─────────────────────────┐
                    │   Supervisor Agent      │
                    │   (LangGraph 기반)       │
                    │                         │
                    │  - 요청 분석            │
                    │  - Agent 선택/조합      │
                    │  - 실행 흐름 제어       │
                    └─────────────┬───────────┘
                                  │
          ┌───────────┬───────────┼───────────┬───────────┐
          ↓           ↓           ↓           ↓           ↓
    ┌──────────┐┌──────────┐┌──────────┐┌──────────┐┌──────────┐
    │FileSearch││ Ecount   ││  Mail    ││Quotation ││  (확장)  │
    │  Agent   ││  Agent   ││  Agent   ││  Agent   ││  Agent   │
    └────┬─────┘└────┬─────┘└────┬─────┘└────┬─────┘└──────────┘
         │           │           │           │
         ↓           ↓           ↓           ↓
    ┌──────────┐┌──────────┐┌──────────┐┌──────────┐
    │FileSystem││  RPA/    ││  SMTP    ││  Excel   │
    │  Tools   ││Selenium  ││  Tools   ││  Tools   │
    └──────────┘└──────────┘└──────────┘└──────────┘
```

### 핵심 설계 원칙

1. **Supervisor 중심**: 모든 요청은 Supervisor를 거쳐 처리
2. **Agent 자율성**: 각 Agent는 독립적으로 도구를 사용하여 작업 수행
3. **동적 라우팅**: LLM이 요청을 분석하여 적절한 Agent 선택
4. **워크플로우 조합**: 복잡한 작업은 여러 Agent를 순차/병렬 실행
5. **백업 API**: Supervisor 우회 가능한 직접 Tool API 제공

## 기술 스택

### Backend

| 항목 | 기술 |
|------|------|
| Language | Python 3.13+ |
| Framework | FastAPI |
| Agent Framework | LangGraph |
| LLM | Claude(Anthropic), GPT(OpenAI), Gemini(google)|
| RPA | Selenium + undetected-chromedriver |
| Excel | openpyxl |
| Mail | aiosmtplib |
| Database | PostgreSQL + SQLAlchemy |
| Cache | Redis |

## 폴더 구조

```
agent_system/
├── main.py                     # FastAPI 앱 진입점
├── pyproject.toml              # 프로젝트 설정 및 의존성
├── README.md                   # 프로젝트 문서
├── CLAUDE.md                   # Claude Code 작업 가이드
│
├── src/
│   ├── api/                    # API 라우터
│   │   ├── agent.py           # POST /api/chat (Supervisor)
│   │   └── tools.py           # POST /tools/* (백업 API)
│   │
│   ├── agents/                 # 에이전트 구현
│   │   ├── supervisor.py      # Supervisor (LangGraph)
│   │   ├── file_search.py     # FileSearchAgent
│   │   ├── ecount.py          # EcountAgent
│   │   ├── mail.py            # MailAgent
│   │   └── quotation.py       # QuotationAgent
│   │
│   ├── tools/                  # Agent가 사용하는 도구
│   │   ├── file_system.py     # 파일 검색
│   │   ├── ecount_scraper.py  # Ecount RPA
│   │   ├── mail_sender.py     # 메일 발송
│   │   └── excel_handler.py   # 견적서 생성/분석
│   │
│   ├── models/                 # DB 모델 (SQLAlchemy)
│   └── schemas/                # Pydantic 스키마
│
└── tests/                      # 테스트 코드
```

## 설치 및 실행

### 환경 설정

```bash
# 의존성 설치
uv sync

# 환경 변수 설정
cp .env.example .env
# .env 파일 편집하여 API 키 등 설정
```

### 환경 변수

```env
# LLM
ANTHROPIC_API_KEY=your_api_key

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/agent_db

# Redis
REDIS_URL=redis://localhost:6379

# Ecount (RPA)
ECOUNT_ID=your_id
ECOUNT_PASSWORD=your_password

# Mail
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your_email
SMTP_PASSWORD=your_password
```

### 실행

```bash
# 개발 서버 실행
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API 엔드포인트

### 메인 API (Supervisor)

```
POST /api/chat
Content-Type: application/json

{
  "message": "삼성전자 견적서 만들고 메일로 보내줘"
}
```

### 백업 API (Direct Tools)

```
POST /tools/file-search      # 파일 검색
POST /tools/ecount-schedule  # 일정 조회
POST /tools/send-mail        # 메일 발송
```

## 라이선스

Private - 내부 사용 전용
