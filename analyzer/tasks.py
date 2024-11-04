import logging

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from django.conf import settings
from django.core.cache import cache
from django.db.utils import IntegrityError
from . import models  # import Account, Instrument, Operation
from . import tclient, cbrf_client, moex_client
from .classes import Quotation


tinkoff_client = tclient.tinkoff_client(settings.TINKOFF_API_KEY)

taskLogger = logging.getLogger(__name__)
taskLogger.setLevel(settings.TASKS_LOGGING_LEVEL)


def update_tinkoff_accounts():
    accounts_in = tinkoff_client.get_accounts()
    for account in accounts_in:
        models.Account.objects.get_or_create(
            accountId=account.id,
            defaults={"accountId": account.id,
                      "type": account.type.name,
                      "name": account.name,
                      "bank": "Т-Банк",
                      "status": account.status.name,
                      "opened": account.opened_date,
                      "closed": account.closed_date,
                      })


def get_cb_rate(date: datetime, currency: str):
    taskLogger.info(f"Get cb_rate from API for '{currency}' on {date}.")
    currency = currency.upper()
    rates = cbrf_client.get_rates_for_date_from_cbrf(date)
    outRate = None

    currencies = models.Currency.objects.all()
    for tmpCurrency in currencies:
        rate = rates[tmpCurrency.code]
        if rate is None:
            continue
        taskLogger.info(f"Parsing rate of '{tmpCurrency}' from API.")
        tmpRate = models.CentrobankRate.objects.get_or_create(
            date=date,
            currency=rate.currency.code,
            defaults={"rate": rate.value}
        )[0]
        if rate.currency.code.__str__() == currency:
            outRate = models.CentrobankRate.objects.get(pk=tmpRate.pk)
    # чтобы в базе были курсы для рубля, а не ошибку каждый раз обрабатывать
    tmpRate = models.CentrobankRate.objects.get_or_create(
            date=date,
            currency="RUB",
            defaults={"rate": Decimal(1)}
        )[0]
    if currency == "RUB":
        outRate = models.CentrobankRate.objects.get(pk=tmpRate.pk)
    return outRate


def get_cb_rate_dynamics(currency: str, start_date: datetime, end_date: datetime = datetime.now()):
    rates = cbrf_client.get_rate_dynamics_from_cbrf(currency, start_date, end_date)
    count = 0
    for date, rate in rates.items():
        _, created = models.CentrobankRate.objects.get_or_create(
            date=date,
            currency=rate.currency.code,
            defaults={"rate": rate.value}
        )
        if created:
            # Добавляем рубль, чтобы не создавать исключений по запросам в базу данных
            models.CentrobankRate.objects.get_or_create(date=date, currency="RUB",
                                                        defaults={"rate": Decimal(1)})
            count += 1
    return count


def get_instrument_by_figi(figi: str):
    taskLogger.debug(f"Get instrument by figi {figi}")
    instrument_in = tinkoff_client.get_instrument_by_figi(figi)
    return _process_instrument(instrument_in)


def get_instrument_by_ticker(ticker: str, class_code: str):
    taskLogger.debug(f"Get instrument by ticker {ticker}")
    instrument_in = tinkoff_client.get_instrument_by_ticker(ticker, class_code)
    return _process_instrument(instrument_in)


def get_instrument_by_uid(uid: str):
    taskLogger.debug(f"Get instrument by uid {uid}")
    instrument_in = tinkoff_client.get_instrument_by_uid(uid)
    return _process_instrument(instrument_in)


def _process_instrument(instrument_in):
    instrument = models.instrument_from_tinkoff_client(instrument_in)
    try:
        tmp = models.InstrumentData.objects.get(isin=instrument.isin)
        instrument.pk = tmp.pk
        instrument.save()
    except models.InstrumentData.DoesNotExist:
        instrument.save()

    _put_instrument_ids(instrument)

    if instrument.instrument_type == "share":
        share = tinkoff_client.get_share(instrument.figi)
        instrument.populate_share_fields(share)
        instrument.save()

    return instrument


def _put_instrument_ids(instrument):
    taskLogger.debug(f"Updating ids for {instrument}")
    taskLogger.debug(f"Putting figi {instrument.figi}")
    models.Instrument.objects.update_or_create(
        idType="figi",
        idValue=instrument.figi,
        defaults={"instrumentData": instrument}
    )
    taskLogger.debug(f"Putting isin {instrument.isin}")
    models.Instrument.objects.update_or_create(
        idType="isin",
        idValue=instrument.isin,
        defaults={"instrumentData": instrument}
    )
    taskLogger.debug(f"Putting ticker {instrument.ticker}")
    models.Instrument.objects.update_or_create(
        idType="ticker",
        idValue=instrument.ticker + ":" + instrument.class_code,
        defaults={"instrumentData": instrument}
    )
    taskLogger.debug(f"Putting uid {instrument.uid}")
    models.Instrument.objects.update_or_create(
        idType="uid",
        idValue=instrument.uid,
        defaults={"instrumentData": instrument}
    )


def get_lastprice_from_api(figi_in: str | list[str]):
    if type(figi_in) is str:
        figi = [figi_in, ]
    else:
        figi = list(figi_in)
    prices = tinkoff_client.get_lastprice(figi)
    for price in prices:
        tmpLp = models.last_price_from_tinkoff_client(price)

        try:
            lp = models.LastPrice.objects.get(figi=tmpLp.figi)
            tmpLp.pk = lp.pk
            tmpLp.save()
        except models.LastPrice.DoesNotExist:
            tmpLp.save()
    return tmpLp


def get_share_by_figi(figi: str):
    figi = "BBG004730ZJ9"
    tinkoff_client.get_share(figi)


def get_tinkoff_operations(accountId: str,
                           startDate: datetime | None = None,
                           endDate: datetime | None = None,
                           figi: str = "") -> int:
    operations = tinkoff_client.get_operations(accountId, startDate, endDate, figi)
    op_count = 0
    for operation in operations:
        op_out = models.operation_from_tinkoff_client(operation, accountId)
        try:
            models.Operation.objects.get(operationId=op_out.operationId)
        except models.Operation.DoesNotExist:
            op_count += 1
            op_out.save()
    return op_count


def get_tinkoff_positions(accountId: str):
    positions = tinkoff_client.get_positions(accountId)
    account = models.Account.account_by_id(accountId)

    # TODO: temporary workaround for soldout items
    models.Position.objects.filter(account=account).update(quantity=0)

    for tmpPosition in positions:
        position = models.position_from_tinkoff_client(tmpPosition, accountId)
        try:
            position.save()
        except IntegrityError:
            taskLogger.debug(f"Position {position.figi} already exists - updating")
            tmpPositions = models.Position.objects.filter(
                instrument=position.instrument,
                account=account
            )
            if tmpPositions.count() > 1:
                tmpPosition = tmpPositions.get(figi=position.figi)
            else:
                tmpPosition = tmpPositions[0]

            position.pk = tmpPosition.pk
            position.save()


def preload_currencies_to_db():
    """Загружает список валют с Центробанка, дополняя необходимые данные в базу данных
    """
    yesterday = datetime.now() - timedelta(days=1)
    rates_en = cbrf_client.get_rates_for_date_from_cbrf(yesterday, locale_en=True)
    for rate_en in rates_en.rates:
        taskLogger.debug(rate_en)
        taskLogger.info(f"Checking record for {rate_en.code} - {rate_en.name_eng}")
        if rate_en is not None and not models.Currency.objects.filter(code=rate_en.code).exists():
            taskLogger.info(f"Adding record for {rate_en.code} - {rate_en.name_eng}")
            name_en = rate_en.name_eng
            name_ru = rate_en.name_ru
            currency = models.Currency(code=rate_en.code,
                                       name=name_en, name_rus=name_ru,
                                       symbol=rate_en.code, id=rate_en.id,
                                       num=rate_en.num)
            currency.save()


def preload_splits_list_to_db():
    splits = moex_client.get_splits_list_from_moex()

    for split in splits:
        models.Split.objects.get_or_create(
            date=split["tradedate"], ticker=split['secid'],
            defaults={"before": split["before"], "after": split["after"]})


def total_weight_for_target_portfolio(targetPortfolioId: int, use_cache=True):
    """Расчет общего веса позиций в портфолио.
    Учитывает вес в индексе, помноженный на коэффициент.
    Если в индексе 0 - берет коэффициент как нужный вес.

    Args:
        targetPortfolioId (int): pk портфолио
        use_cache (bool, optional): Использовать ли кэширования при пересчетах.

    Returns:
        _type_: _description_
    """
    cache_key = f"total_weight_for_portfolio_{targetPortfolioId}"
    cached_value = cache.get(cache_key)
    if use_cache and cached_value is not None:
        taskLogger.debug("Used cache for total_weight")
        return cached_value
    portfolioValues = models.TargetPortfolioValues.objects.filter(targetPortfolio__pk=targetPortfolioId)
    total_weight = 0
    for portfolioValue in portfolioValues:
        if portfolioValue.indexTarget == 0:
            total_weight += portfolioValue.coefficient
        else:
            weight = portfolioValue.indexTarget * portfolioValue.coefficient
            total_weight += weight
    cache.set(cache_key, total_weight, 5)
    return total_weight


def update_all_accounts():
    """Запрашивает информацию по последним сделкам всех счетов, обновляет портфолио
    """
    taskLogger.info("Splits list update")
    preload_splits_list_to_db()

    taskLogger.info("Updating tinkoff accounts list")
    update_tinkoff_accounts()

    accounts = models.Account.objects.all()
    total_ops = 0
    first_new_op_date = datetime.now(tz=timezone.utc)
    for account in accounts:
        taskLogger.info(f"Starting parsing of account {account.name} ({account.accountId})")
        last_op = models.Operation.objects.filter(account=account).order_by("-timestamp").first()
        if last_op is not None:
            last_op_date = last_op.timestamp
        else:
            last_op_date = datetime.fromtimestamp(0, tz=timezone.utc)
        taskLogger.info(f"Last operation date for {account.name} - {last_op_date}")
        op_count = get_tinkoff_operations(accountId=account.accountId, startDate=last_op_date)
        taskLogger.info(f"Loaded {op_count} operations")
        if op_count > 0:
            new_operations = models.Operation.objects.filter(
                account=account, timestamp__gte=last_op_date).order_by("timestamp")
            taskLogger.debug(f"New operations count: {new_operations.count()}")

            if new_operations[0].timestamp < first_new_op_date:
                # дата для загрузки динамики курса валют
                first_new_op_date = new_operations[0].timestamp

            taskLogger.info(f"Loading positions for {account.name}")
            get_tinkoff_positions(accountId=account.accountId)
        total_ops += op_count
    if total_ops > 0:
        taskLogger.info("Preloasding CBRF rates for new operations")
        currencies = models.Currency.objects.filter(auto_rate_preload=True)
        for currency in currencies:
            c = get_cb_rate_dynamics(currency.code, first_new_op_date)
            taskLogger.info(f"Added {c} rates for '{currency.code}'")
    taskLogger.info(f"Total operations parsed: {total_ops}")
    return total_ops
