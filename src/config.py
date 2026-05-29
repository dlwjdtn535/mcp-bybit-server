import logging
import os

from dotenv import load_dotenv

load_dotenv(verbose=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Maximum order size in USDT (safeguard against accidentally large orders)
MAX_ORDER_SIZE_USDT = float(os.getenv("MAX_ORDER_SIZE_USDT", "100"))

# Response verbosity for token-saving trimming: "minimal" | "normal" | "full"
RESPONSE_VERBOSITY = os.getenv("RESPONSE_VERBOSITY", "normal").lower()

class Config:
    MEMBER_ID = os.getenv("MEMBER_ID")
    ACCESS_KEY = os.getenv("ACCESS_KEY")
    SECRET_KEY = os.getenv("SECRET_KEY")
    TESTNET = os.getenv("TESTNET", "false").lower() == "true"
    TRADING_ENABLED = os.getenv("TRADING_ENABLED", "false").lower() == "true"
    # Read-only mode blocks every mutating tool, regardless of TRADING_ENABLED.
    READONLY_MODE = os.getenv("READONLY_MODE", "false").lower() == "true"

    @classmethod
    def log_config(cls):
        # SECURITY: log ONLY whether a key is present, NEVER its value
        logger.info(f"ACCESS_KEY configured: {'YES' if cls.ACCESS_KEY else 'NO'}")
        logger.info(f"SECRET_KEY configured: {'YES' if cls.SECRET_KEY else 'NO'}")
        logger.info(f"TESTNET: {cls.TESTNET}")
        logger.info(f"TRADING_ENABLED: {cls.TRADING_ENABLED}")
        logger.info(f"READONLY_MODE: {cls.READONLY_MODE}")
        logger.info(f"MAX_ORDER_SIZE_USDT: {MAX_ORDER_SIZE_USDT}")
        logger.info(f"RESPONSE_VERBOSITY: {RESPONSE_VERBOSITY}")

# Log configuration
Config.log_config()
