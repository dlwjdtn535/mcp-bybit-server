import logging
import sys

from mcp.server.fastmcp import FastMCP
mcp = FastMCP("Seminar Management System")


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("mcp-server")

@mcp.tool()
def data_example() -> str:
    return "data_example"

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