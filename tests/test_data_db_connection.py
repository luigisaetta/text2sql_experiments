"""
Test Data DB connection
"""

import oracledb
from config import CONNECT_ARGS
from utils import get_console_logger

logger = get_console_logger()

connection = oracledb.connect(**CONNECT_ARGS)

logger.info("Connection OK")
