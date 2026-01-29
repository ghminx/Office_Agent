from datetime import datetime


def get_today() -> str:
    """현재 날짜를 YYYY-MM-DD 형식으로 반환"""
    return datetime.now().strftime("%Y-%m-%d")