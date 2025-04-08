import os
import logging
from dotenv import load_dotenv

load_dotenv(verbose=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Config:
    MEMBER_ID = os.getenv("MEMBER_ID")
    ACCESS_KEY = os.getenv("ACCESS_KEY")
    SECRET_KEY = os.getenv("SECRET_KEY")
    TESTNET = os.getenv("TESTNET", "False").lower() == "true"

    @classmethod
    def log_config(cls):
        logger.info(f"MEMBER_ID: {cls.MEMBER_ID}")
        logger.info(f"ACCESS_KEY: {cls.ACCESS_KEY}")
        logger.info(f"TESTNET: {cls.TESTNET}")

# Log configuration
Config.log_config()
