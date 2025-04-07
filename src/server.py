import logging
import sys

from mcp.server.fastmcp import FastMCP
import json

mcp = FastMCP("Seminar Management System")
seminar_data = {
    "Python 세미나": [
        "홍길동",
        "김철수",
        "이영희"
    ],
    "AI 세미나": [
        "박지민",
        "최민수"
    ]
}


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("mcp-server")

@mcp.tool()
def get_seminar_details(party_name: str) -> str:
    logger.info(f"Fetching details for seminar: {party_name}")

    attendees = seminar_data.get(party_name, [])

    seminar_info = {
        "name": party_name,
        "total_attendees": len(attendees),
        "attendees": attendees,
    }

    return json.dumps(seminar_info, ensure_ascii=False, indent=2)

@mcp.tool()
def register_attendee(party_name: str, attendee_name: str) -> str:
    logger.info(f"Registering attendee: {attendee_name} for seminar: {party_name}")

    # 실제 구현에서는 데이터베이스에 참석자를 추가하는 로직이 있을 것입니다
    if party_name not in seminar_data:
        return f"오류: {party_name} 세미나가 존재하지 않습니다."

    if attendee_name in seminar_data[party_name]:
        return f"오류: {attendee_name}님은 이미 {party_name} 세미나에 등록되어 있습니다."

    seminar_data[party_name].append(attendee_name)

    return f"성공: {attendee_name}님이 {party_name} 세미나에 등록되었습니다."

@mcp.prompt()
def prompt(message: str) -> str:
    return f"""
당신은 세미나 관리 시스템의 AI 어시스턴트입니다.

사용 가능한 도구:
- get_seminar_details(party_name) - 특정 세미나의 상세 정보를 조회합니다.
- register_attendee(party_name, attendee_name) - 새 참석자를 등록합니다.

사용자 메시지: {message}
"""


def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()

