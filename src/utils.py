from datetime import datetime
import smtplib
import imaplib
import time
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.utils import formatdate, make_msgid


def get_today() -> str:
    """현재 날짜를 YYYY-MM-DD 형식으로 반환"""
    return datetime.now().strftime("%Y-%m-%d")


def send_smtp(state: dict) -> dict:
    """SMTP를 사용하여 이메일을 보내고, 보낸편지함에 기록하는 함수"""
    
    from_mail = state["from_mail"]
    to_mail = state["to_mail"]
    app_password = state["app_password"]
    title = state["title"]
    context = state["context"]
    files = state["files"]

    # 제목 및 본문
    smtp = MIMEMultipart()
    smtp["Subject"] = title  # 제목
    smtp["From"] = from_mail # 발신자
    smtp["To"] = to_mail     # 수신자
    smtp["Message-ID"] = make_msgid()
    smtp.attach(MIMEText(context, _charset="utf-8")) # 본문 내용

    # 첨부파일
    if files:
        file_path = Path(files)
        with file_path.open("rb") as f:
            part = MIMEApplication(f.read(), _subtype="octet-stream")   # _subtype="octet-stream" : 일반 바이너리 파일로 취급
            part.add_header("Content-Disposition", "attachment", filename=file_path.name)
            smtp.attach(part)

    # SMTP 전송
    with smtplib.SMTP_SSL("smtp.daum.net", 465) as server:
        server.login(from_mail, app_password)
        server.send_message(smtp)

    # 보낸편지함 기록
    raw_bytes = smtp.as_bytes()
    with imaplib.IMAP4_SSL("imap.daum.net", 993) as imap:
        imap.login(from_mail, app_password)
        imap.append(
            "Sent",
            None,
            imaplib.Time2Internaldate(time.time()),
            raw_bytes,
        )
        
        
