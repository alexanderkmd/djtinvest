# Парсеры для работы с отчетами Сбербанка

import logging
import re

from bs4 import BeautifulSoup, Tag

from datetime import datetime

from .models import Account, Bank, Instrument, InstrumentData, Position

sberLogger = logging.getLogger(__name__)
sberLogger.setLevel(logging.DEBUG)  # lsettings.TASKS_LOGGING_LEVEL)



def parse_account(soup: BeautifulSoup) -> Account | None:
    sberLogger.info("Getting account data from Sberbank HTML report")
    strings = soup.find_all(string=re.compile("Договор"))
    if len(strings) != 1:
        return None
    account_string_data = strings[0].split(" ")
    account_number = account_string_data[1]
    account_open_date_str = account_string_data[3][:10]
    sberLogger.debug(f"Найден счет в отчете: {account_number}, открытый '{account_open_date_str}'")

    account = Account.account_by_id(account_number)
    if account is not None:
        # если счет нашелся - его и возвращаем
        sberLogger.debug(f"Счет '{account}' найден - возвращаю")
        return account

    account_open_date = datetime.strptime(account_open_date_str, "%d.%m.%Y")

    sberLogger.debug("Создаем новую запись счета...")
    sberbank = Bank.get_sberbank()
    if sberbank is None:
        logging.critical("Cannot find sberbank record in Banks to create Account!")
        return None
    tmpAccount = Account()
    tmpAccount.accountId = account_number
    tmpAccount.type = "ACCOUNT_TYPE_BROKER"
    tmpAccount.name = account_number
    tmpAccount.bankId = sberbank
    tmpAccount.status = "ACCOUNT_STATUS_OPEN"
    tmpAccount.opened = account_open_date

    try:
        tmpAccount.save()
        return tmpAccount
    except Exception as e:
        sberLogger.error(e)
        return None


def parse_instruments_list(soup: BeautifulSoup | Tag):
    """Loads instruments for report to the DB

    Args:
        soup (BeautifulSoup | Tag): Instrument Table content
    """
    sberLogger.info("Start Sberbank HTML report instrument list parsing")

    for row in soup.find_all("tr"):
        if row.has_attr('class') and row['class'][0] in ["table-header", "rn", "summary-row"]:
            # не парсим ряды заголовков и концевые
            continue
        cells = row.find_all("td", string=True)
        if cells[0].has_attr('colspan'):
            # пропускаем ряды подзаголовков и разбивки
            continue
        ticker_col = 1
        isin_col = 2
        ticker = cells[ticker_col].string
        isin = cells[isin_col].string
        try:
            Instrument.get_instrument_by_ticker(ticker, "TQBR")
            continue
        except Exception as e:
            sberLogger.error(f"Ошибка парсинга инструмента: {e}")
        try:
            sberLogger.info(f"Пробуем найти по ISIN {isin}")
            instrument = Instrument.get_instrument_by_isin(isin)
            sberLogger.info(f"Успешно нашли {instrument}!")
        except Exception as e:
            sberLogger.error(f"Ошибка парсинга инструмента: {e}")
    pass


def parse_portfolio(soup: BeautifulSoup, account: Account):
    sberLogger.info("Start Sberbank HTML report portfolio parsing")

    for row in soup.find_all("tr"):
        if row.has_attr('class') and row['class'][0] in ["table-header", "rn", "summary-row"]:
            # не парсим ряды заголовков и концевые
            continue
        cells = row.find_all("td", string=True)
        if cells[0].has_attr('colspan'):
            # пропускаем ряды подзаголовков и разбивки
            continue
        name_col = 0
        isin_col = 1
        end_date_qtty_col = 8
        name = cells[name_col].string
        isin = cells[isin_col].string
        end_date_qtty = cells[end_date_qtty_col].string.replace(" ", "")
        sberLogger.debug(f"'{name}', isin: {isin} количество в конце периода: {end_date_qtty}")
        try:
            instrument = Instrument.get_instrument_by_isin(isin)
            sberLogger.debug(instrument)
        except Exception as e:
            sberLogger.warning(f"Ошибка вненсения инструмента {name}")
            sberLogger.error(f"Ошибка поиска инструмента для {isin}:\n{e}")
            continue
        _put_sberbank_position(account, instrument, end_date_qtty)
    pass


def parse_html_report(file_name):
    sberLogger.info("Start Sberbank HTML report parsing")
    with open(file_name) as fp:
        soup = BeautifulSoup(fp, "html.parser")

    account = parse_account(soup)
    if account is None:
        sberLogger.error("Ошибка парсинга отчета - невозможно сопоставить со счетом в базе")
        return

    instruments_table_position = soup.find(string=re.compile("Справочник Ценных Бумаг"))
    parse_instruments_list(instruments_table_position.find_next("table"))

    portfolio_table_position = soup.find(string=re.compile("Портфель Ценных Бумаг"))
    parse_portfolio(portfolio_table_position.find_next("table"), account)


def _put_sberbank_position(account: Account, instrument: InstrumentData, qtty: int):
    Position.objects.update_or_create(
        account=account,
        instrument=instrument,
        defaults={"qtty": qtty},
        create_defaults={
            "account": account,
            "instrument": instrument,
            "figi": instrument.figi,
            "instrument_uid": instrument.uid,
            "quantity": qtty,
            "blocked": False,
        }
    )
