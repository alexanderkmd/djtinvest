# Парсеры для работы с отчетами Сбербанка

import logging
import re

from bs4 import BeautifulSoup, Tag

from typing import Dict
from datetime import datetime
from decimal import Decimal

from .models import Account, Bank, Instrument, InstrumentData, Operation, Position

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


def parse_instruments_list(soup: BeautifulSoup | Tag) -> Dict[str, InstrumentData]:
    """Loads instruments for report to the DB

    Args:
        soup (BeautifulSoup | Tag): Instrument Table content
    """
    sberLogger.info("Start Sberbank HTML report instrument list parsing")

    instruments = {}

    for row in soup.find_all("tr"):
        if row.has_attr('class') and row['class'][0] in ["table-header", "rn", "summary-row"]:
            # не парсим ряды заголовков и концевые
            continue
        cells = row.find_all("td", string=True)
        if cells[0].has_attr('colspan'):
            # пропускаем ряды подзаголовков и разбивки
            continue
        name_col = 0
        ticker_col = 1
        isin_col = 2
        name = cells[name_col].string
        ticker = cells[ticker_col].string
        isin = cells[isin_col].string
        try:
            instrument = Instrument.get_instrument_by_ticker(ticker, "TQBR")
        except Exception as e:
            sberLogger.error(f"Ошибка парсинга инструмента: {e}")
        try:
            sberLogger.info(f"Пробуем найти по ISIN {isin}")
            instrument = Instrument.get_instrument_by_isin(isin)
            sberLogger.info(f"Успешно нашли {instrument}!")
        except Exception as e:
            sberLogger.error(f"Ошибка парсинга инструмента: {e}")
            continue
        instruments[name] = instrument
        instruments[ticker] = instrument
        instruments[isin] = instrument
    return instruments


def parse_buy_sell_operations(soup: BeautifulSoup, account: Account, instruments: Dict[str, InstrumentData]):
    sberLogger.info("Start Sberbank HTML buy/sell operations parsing")

    operation_number_col = 13
    date_col = 0
    time_col = 2
    instrument_code_col = 4
    currency_col = 5
    operation_type_col = 6
    qtty_col = 7
    price_col = 8
    payment_col = 9
    nkd_col = 10
    broker_comission_col = 11
    market_comission_col = 12
    operations_status_col = 15

    for row in soup.find_all("tr"):
        if row.has_attr('class') and row['class'][0] in ["table-header", "rn", "summary-row"]:
            # не парсим ряды заголовков и концевые
            continue
        cells = row.find_all("td", string=True)
        if cells[0].has_attr('colspan'):
            # пропускаем ряды подзаголовков и разбивки
            continue

        operation_number = cells[operation_number_col].string
        date = cells[date_col].string
        time = cells[time_col].string
        instrument_code = cells[instrument_code_col].string
        currency = cells[currency_col].string
        operation_type = cells[operation_type_col].string
        qtty = cells[qtty_col].string
        price = Decimal(cells[price_col].string.replace(" ", ""))
        payment = Decimal(cells[payment_col].string.replace(" ", ""))
        nkd = Decimal(cells[nkd_col].string)
        broker_comission = Decimal(cells[broker_comission_col].string.replace(" ", ""))
        market_comission = Decimal(cells[market_comission_col].string.replace(" ", ""))
        try:
            operations_status = cells[operations_status_col].string
        except:
            # если комментарий пустой...
            operations_status = cells[operations_status_col-1].string
        instrument = instruments.get(instrument_code, None)
        if instrument is None:
            sberLogger.error(f"Инструмент '{instrument_code}' не найден, но я пока не придумал, что с ним делать?!?!?!")
            continue

        # 27.12.2024 13:55:57
        operation_datetime = datetime.strptime(f"{date} {time}", "%d.%m.%Y %H:%M:%S")
        print(operation_datetime)
        try:
            operation = Operation.objects.get(operationId=operation_number)
            sberLogger.info(f"Операция '{operation_type} {instrument_code} {date}' уже существует - пропускаю")
            continue
        except:
            pass
        operation = Operation(
            operationId=operation_number,
            parentOperationId=None,
            account=account,
            currency=currency,
            payment=payment,
            price=price,
            state=operations_status,
            timestamp=operation_datetime,
            type=operation_type,
            quantity=qtty,
            instrument=instrument,
            figi=instrument.figi,
            instrument_type=instrument.instrument_type
        )
        operation.save()

        if broker_comission != 0 or market_comission != 0:
            tax_operation = Operation(
                operationId=f"{operation_number}-tax",
                parentOperationId=operation_number,
                account=account,
                currency=currency,
                payment=-(broker_comission+market_comission),
                price=0,
                state="OPERATION_STATE_EXECUTED",
                timestamp=operation_datetime,
                type="OPERATION_TYPE_BROKER_FEE",
                quantity=0,
                instrument=instrument,
                figi=instrument.figi,
                instrument_type=instrument.instrument_type
            )
            tax_operation.save()

    return


def parse_money_operations(soup: BeautifulSoup, account: Account, instruments: Dict[str, InstrumentData]):
    sberLogger.info("Start Sberbank HTML money operations parsing")

    date_col = 0
    market_col = 1
    description_col = 2
    currency_col = 3
    debit_col = 4
    credit_col = 5

    for row in soup.find_all("tr"):
        if row.has_attr('class') and row['class'][0] in ["table-header", "rn", "summary-row"]:
            # не парсим ряды заголовков и концевые
            continue
        cells = row.find_all("td", string=True)
        if cells[0].has_attr('colspan'):
            # пропускаем ряды подзаголовков и разбивки
            continue

        date = cells[date_col].string
        market = cells[market_col].string
        description = cells[description_col].string
        currency = cells[currency_col].string
        debit = Decimal(cells[debit_col].string.replace(" ", ""))
        credit = Decimal(cells[credit_col].string.replace(" ", ""))

        description_split = description.split(" ")
        description_start = description_split[0]

        if description_start in ["Комиссия", "Сделка"]:
            # Комиссии и сделки обрабатываются в parse_buy_sell_operations
            # поэтому пропускаем
            sberLogger.debug("Not parsing comission/trade operations here")
            continue

        operation_id = ""
        operation_type = ""
        operation_sum = Decimal(0)
        tax = Decimal(0)
        instrument = None
        figi = ""
        instrument_type = ""

        # 27.12.2024 00:00:00+03:00
        operation_datetime = datetime.strptime(f"{date} 00:00:00+03:00", "%d.%m.%Y %H:%M:%S%z")
        operation_id = operation_datetime.strftime("%y%m%d") + account.accountId

        if description_start == "Зачисление":
            if len(description_split) == 2:
                # "Зачисление д/с"
                sberLogger.debug(f"Input operation {debit} on {date}")
                operation_id += "-input"
                operation_type = "OPERATION_TYPE_INPUT"
                operation_sum = debit
            else:
                # "Зачисление д/с (купон 7 по ОФЗ 26238)"
                sberLogger.debug(f"Coupon operation on {date}")
                operation_type = "OPERATION_TYPE_COUPON"
                operation_sum = debit
                re_match_string = r"\(купон .* по (?P<bond>.*)\)"
                out = re.search(re_match_string, description)
                bond = out.groupdict()['bond']
                instrument = instruments[bond]
                figi = instrument.figi
                instrument_type = instrument.instrument_type

                operation_id += "-coupon" + bond.replace(" ", "")
        elif description_start == "Дивиденды":
            sberLogger.debug(f"Dividend operation on {date}")
            operation_type = "OPERATION_TYPE_DIVIDEND"
            tax_operation_type = "OPERATION_TYPE_DIVIDEND_TAX"

            re_match_string = r"Дивиденды (?P<stock>.*); ISIN (?P<isin>.*); Дата Фиксации .*; Кол-во (?P<qtty>\d*); Ставка Выплаты (?P<payment>\d*); Курс конвертации (?P<rate>[\d\.]*);"
            out = re.search(re_match_string, description)
            isin = out.groupdict()['isin']
            instrument = instruments[isin]
            figi = instrument.figi
            instrument_type = instrument.instrument_type

            operation_id += "-dividend-" + isin
            operation_sum = Decimal(out.groupdict()['payment'])
            tax = debit - operation_sum

        if Operation.objects.filter(operationId=operation_id).exists():
            sberLogger.info(f"Операция '{operation_type} {date}' уже существует - пропускаю")
            continue

        operation = Operation(
            operationId=operation_id,
            parentOperationId=None,
            account=account,
            currency=currency,
            payment=operation_sum,
            price=0,
            state="OPERATION_STATE_EXECUTED",
            timestamp=operation_datetime,
            type=operation_type,
            quantity=0,
            instrument=instrument,
            figi=figi,
            instrument_type=instrument_type
        )
        operation.save()

        if tax != Decimal(0):
            tax_operation = Operation(
                operationId=f"{operation_id}-tax",
                parentOperationId=operation_id,
                account=account,
                currency=currency,
                payment=-tax,
                price=0,
                state="OPERATION_STATE_EXECUTED",
                timestamp=operation_datetime,
                type=tax_operation_type,
                quantity=0,
                instrument=instrument,
                figi=figi,
                instrument_type=instrument_type
            )
            tax_operation.save()

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
    instruments = parse_instruments_list(instruments_table_position.find_next("table"))

    buy_sell_operations_table_position = soup.find(string=re.compile("Сделки купли/продажи ценных бумаг"))
    parse_buy_sell_operations(buy_sell_operations_table_position.find_next("table"), account, instruments)

    money_operations_table_position = soup.find(string=re.compile("Движение денежных средств за период"))
    parse_money_operations(money_operations_table_position.find_next("table"), account, instruments)

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
