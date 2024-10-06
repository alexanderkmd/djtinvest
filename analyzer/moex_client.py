import logging
import requests

from typing import List, Dict

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


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
