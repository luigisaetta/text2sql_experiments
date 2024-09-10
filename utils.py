"""
General utils
"""

import logging
from decimal import Decimal
from sqlalchemy.inspection import inspect


def get_console_logger():
    """
    To get a logger to print on console
    """
    logger = logging.getLogger("ConsoleLogger")

    # to avoid duplication of logging
    if not logger.handlers:
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)

        formatter = logging.Formatter("%(asctime)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.propagate = False

    return logger


# these 2 functions are needed to serialiaze rows returnd from query in json
def decimal_to_float(value):
    """
    convert a Decimal to float
    """
    if isinstance(value, Decimal):
        return float(value)
    return value


def to_dict(obj):
    """
    convert a row to a dict
    """
    if hasattr(obj, "__dict__"):
        # this handles an ORM object
        return {
            c.key: decimal_to_float(getattr(obj, c.key))
            for c in inspect(obj).mapper.column_attrs
        }

    # Oggetto Row tramite .mappings() (query SQL), non serve usare dict() qui
    return {key: decimal_to_float(value) for key, value in obj.items()}
