import logging
import requests

from typing import List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_index_positions(index_code: str, date: datetime = datetime.now(), secondary=False) -> List[Dict]:
    """Запрашивает состав индекса с сайта МосБиржи на указанную дату

    Args:
        index_code (str): Кодовое название индекса, например IMOEX, MOEXBC...
        date (datetime, optional): Интересующая дата. По умолчанию сегодня, либо последняя дата обновления индекса.
        secondary (bool, optional): Если это повторный запрос по последней дате обноваления индекса.

    Returns:
        List[Dict]: Состав индекса с долями в долях процентов
    """

    url = "https://iss.moex.com/iss/statistics/engines/stock/markets/index/analytics/"
    url += index_code
    url += ".json?limit=300"  # Переключаем в json и чтобы все прогрузилось
    url += "&iss.json=extended&iss.meta=off"  # переводим в словарь из массива и отключаем метаданные
    url += date.strftime("&date=%Y-%m-%d")

    logger.debug(url)

    try:
        response = requests.get(url, verify=False)
        data = response.json()
    except Exception as e:
        logger.error(f"Error during MOEX-index-positions request: {e}")
        return []

    logger.debug(data)

    try:
        if len(data[1]["analytics"]) > 0:
            return data[1]["analytics"]

        if secondary:
            # Если это повторный запрос, а данных так и нет - то что-то странное творится
            raise Exception("Secondary request failed")

        # Если запрос вернулся пустой, но есть предыдущая дата - вернуть его
        prev_date_val = data[1]["analytics.cursor"][0]["PREV_DATE"]
        if prev_date_val is None:
            # Если предыдущая дата пустая - вероятно неправильный или несуществующий индекс запрошен
            raise Exception("Unknown index requested")
        prev_date = datetime.strptime(prev_date_val, "%Y-%m-%d")
        return get_index_positions(index_code, date=prev_date, secondary=True)
    except Exception as e:
        logger.error(f"Error parsing MOEX-index-positions response: {e}")

    return []


def get_security_data_from_moex(security: str):
    """Получает данные о бумаге из MOEX API

    Args:
        security (str): _description_
    """
    # url = "https://iss.moex.com/iss/securities/VTBR.json?iss.json=extended&iss.meta=off&primary_board=1"
    pass


def get_security_data_by_isin_from_moex(isin: str = "RU000A105PU9"):
    # https://iss.moex.com/iss/securities.json?q=RU000A105PU9&iss.json=extended&iss.meta=off

    url = "https://iss.moex.com/iss/securities.json?q="
    url += isin
    url += "&iss.json=extended&iss.meta=off"  # переводим в словарь из массива и отключаем метаданные

    logger.debug(url)

    try:
        response = requests.get(url, verify=False)
        data = response.json()
    except Exception as e:
        logger.error(f"Error during MOEX-index-positions request: {e}")
        return []

    logger.debug(data)
    secs = data[1]['securities']

    if len(secs) == 0:
        return None, None

    return secs[0]["secid"], secs[0]["primary_boardid"]


def get_splits_list_from_moex() -> List[Dict]:
    """Получает список прошедших сплитов/консолидаций из MOEX API

    Returns:
        List[Dict]: список сплитов и их параметров
    """
    splits_url = "https://iss.moex.com/iss/statistics/engines/stock/splits.json?iss.json=extended&iss.meta=off"

    try:
        response = requests.get(splits_url, verify=False)
        data = response.json()
    except Exception as e:
        logger.error(f"Error during MOEX-splits request: {e}")
        return []

    try:
        return data[1]["splits"]
    except Exception as e:
        logger.error(f"Error parsing MOEX-splits response: {e}")

    return []
