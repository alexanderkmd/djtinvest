import logging

from datetime import datetime, timezone
from decimal import Decimal

from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.core.exceptions import ObjectDoesNotExist

from . import tasks
from .classes import Quotation

accountLoggerLevel = settings.ACCOUNT_LOGGING_LEVEL
instrumentLoggerLevel = settings.INSTRUMENT_LOGGING_LEVEL
currencyLoggerLevel = settings.CURRENCY_LOGGING_LEVEL
centrobankRateLoggerLevel = settings.CURRENCY_LOGGING_LEVEL


##############################
#          ACCOUNT           #
##############################

class AccountManager(models.Manager):
    def by_account_id(self, accountId):
        return self.get(accountId=accountId)


class Account (models.Model):
    accountId = models.CharField(max_length=64, unique=True)
    type = models.CharField(max_length=64)
    name = models.CharField(max_length=128)
    bank = models.CharField(max_length=60)
    status = models.CharField(max_length=32)
    opened = models.DateField()
    closed = models.DateField(blank=True, null=True)
    # access_level=<AccessLevel.ACCOUNT_ACCESS_LEVEL_READ_ONLY: 2>),

    objects = AccountManager()
    account_by_id = objects.by_account_id

    class Meta:
        verbose_name = "Счет"
        verbose_name_plural = "Счета"

    def __str__(self) -> str:
        return f"{self.accountId}-{self.name} ({self.bank})"


# def account_by_accountId(accountId: str) -> Account:
#    return Account.objects.get(accountId=accountId)


def account_from_tinkoff_client(account):
    tmpAccount = Account()
    tmpAccount.accountId = account.id
    tmpAccount.type = account.type.name
    tmpAccount.name = account.name
    tmpAccount.bank = "Т-Банк"
    tmpAccount.status = account.status.name
    tmpAccount.opened = account.opened_date
    tmpAccount.closed = account.closed_date
    return tmpAccount


##############################
#       CENTROBANK RATE      #
##############################

class CentrobankRateManager(models.Manager):
    def get_rate(self, date: datetime, currency: str, **kwargs):
        """Gets rate from DB, if not exist - get trigger API call
        """
        currency = currency.upper()
        try:
            return self.get(date=date, currency=currency)
        except ObjectDoesNotExist:
            print(f"Need to get a rate for {currency} from CBRF for {date}")
        tasks.get_cb_rate(date, currency)
        return self.get(date=date, currency=currency)


class CentrobankRate(models.Model):
    date = models.DateField()
    currency = models.CharField(max_length=3)
    rate = models.DecimalField(max_digits=20, decimal_places=9)

    objects = CentrobankRateManager()
    get_rate = objects.get_rate

    class Meta:
        unique_together = ["date", "currency"]
        verbose_name = "Курс ЦБ РФ"
        verbose_name_plural = "Курсы ЦБ РФ"


##############################
#          Currency          #
##############################

class Currency (models.Model):
    code = models.CharField(max_length=3, primary_key=True)
    num = models.IntegerField()
    name = models.CharField(max_length=255, verbose_name="Название")
    name_rus = models.CharField(max_length=255, verbose_name="Название на русском")
    symbol = models.CharField(max_length=3, verbose_name="Символ")
    id = models.CharField(max_length=7, verbose_name="Код ЦБ РФ")
    auto_rate_preload = models.BooleanField(default=False, verbose_name="Подгружать курс")

    class Meta:
        verbose_name = "Валюта"
        verbose_name_plural = "Валюты"

    def __str__(self) -> str:
        return f"{self.code} ({self.name_rus})"


##############################
#         Instrument         #
##############################

instrumentLogger = logging.getLogger(__name__)
instrumentLogger.setLevel(instrumentLoggerLevel)


class InstrumentData(models.Model):
    figi = models.CharField(max_length=12)
    ticker = models.CharField(max_length=20)
    isin = models.CharField(max_length=12)
    uid = models.CharField(max_length=40, unique=True)
    position_uid = models.CharField(max_length=40)
    asset_uid = models.CharField(max_length=40)
    instrument_type = models.CharField(max_length=32)
    name = models.CharField(max_length=120)
    exchange = models.CharField(max_length=100)
    class_code = models.CharField(max_length=32)
    lot = models.IntegerField()
    currency = models.CharField(max_length=3)
    minPriceIncrement = models.DecimalField(max_digits=20, decimal_places=9)
    api_trade_available_flag = models.BooleanField()
    buyAvailableFlag = models.BooleanField()
    sellAvailableFlag = models.BooleanField()
    for_iis_flag = models.BooleanField()
    for_qual_investor_flag = models.BooleanField()
    weekend_flag = models.BooleanField()
    blocked_tca_flag = models.BooleanField()
    icon = models.CharField(max_length=32)
    logo_base_color = models.CharField(max_length=7)
    text_color = models.CharField(max_length=7)
    updated = models.DateTimeField(auto_now=True)
    # first_1min_candle_date=datetime.datetime(2018, 3, 7, 18, 33, tzinfo=datetime.timezone.utc),
    # first_1day_candle_date=datetime.datetime(2007, 5, 28, 7, 0, tzinfo=datetime.timezone.utc),
    # klong=Quotation(units=2, nano=0), kshort=Quotation(units=2, nano=0),
    # dlong=Quotation(units=0, nano=205800000),
    # dshort=Quotation(units=0, nano=225700000),
    # dlong_min=Quotation(units=0, nano=180000000),
    # dshort_min=Quotation(units=0, nano=200000000),
    # short_enabled_flag=True,
    country_of_risk = models.CharField(max_length=2)
    country_of_risk_name = models.CharField(max_length=128)
    sector = models.CharField(max_length=64)
    otc_flag = models.BooleanField()
    div_yield_flag = models.BooleanField(null=True, blank=True)
    share_type = models.CharField(max_length=120)
    real_exchange = models.CharField(max_length=120)
    liquidity_flag = models.BooleanField(null=True, blank=True)

    class Meta:
        verbose_name = "Параметры интструмента"
        verbose_name_plural = "Параметры инструментов"

    def __str__(self) -> str:
        return f"{self.ticker} ({self.figi}) - {self.name}"

    def icon_url(self) -> str:
        # https://russianinvestments.github.io/investAPI/faq_instruments/#_13
        icon = self.icon[:-4]
        url = f"https://invest-brands.cdn-tinkoff.ru/{icon}x160.png"
        return url

    def populate_share_fields(self, share_data_in):
        self.sector = share_data_in.sector
        self.share_type = share_data_in.share_type.name
        self.liquidity_flag = share_data_in.liquidity_flag
        self.div_yield_flag = share_data_in.div_yield_flag


def instrument_from_tinkoff_client(instrumentIn) -> InstrumentData:
    """Формируем инструмент для базы данных

    Args:
        instrumentIn (TBank-Instrument): [[https://russianinvestments.github.io/investAPI/instruments/#instrument]]

    Returns:
        Instrument:
    """
    instrumentLogger.debug(instrumentIn)
    tmpInstrument = InstrumentData()
    tmpInstrument.figi = instrumentIn.figi
    tmpInstrument.ticker = instrumentIn.ticker
    if instrumentIn.isin == "":
        tmpInstrument.isin = instrumentIn.ticker
    else:
        tmpInstrument.isin = instrumentIn.isin
    tmpInstrument.uid = instrumentIn.uid
    tmpInstrument.position_uid = instrumentIn.position_uid
    tmpInstrument.asset_uid = instrumentIn.asset_uid
    tmpInstrument.instrument_type = instrumentIn.instrument_type
    tmpInstrument.name = instrumentIn.name
    tmpInstrument.exchange = instrumentIn.exchange
    tmpInstrument.class_code = instrumentIn.class_code
    tmpInstrument.lot = instrumentIn.lot
    tmpInstrument.currency = instrumentIn.currency
    tmpInstrument.minPriceIncrement = Quotation(instrumentIn.min_price_increment).to_decimal()
    tmpInstrument.api_trade_available_flag = instrumentIn.api_trade_available_flag
    tmpInstrument.buyAvailableFlag = instrumentIn.buy_available_flag
    tmpInstrument.sellAvailableFlag = instrumentIn.sell_available_flag
    tmpInstrument.for_iis_flag = instrumentIn.for_iis_flag
    tmpInstrument.for_qual_investor_flag = instrumentIn.for_qual_investor_flag
    tmpInstrument.weekend_flag = instrumentIn.weekend_flag
    tmpInstrument.blocked_tca_flag = instrumentIn.blocked_tca_flag
    tmpInstrument.icon = instrumentIn.brand.logo_name
    tmpInstrument.logo_base_color = instrumentIn.brand.logo_base_color
    tmpInstrument.text_color = instrumentIn.brand.text_color
    # first_1min_candle_date=datetime.datetime(2018, 3, 7, 18, 33, tzinfo=datetime.timezone.utc)
    # first_1day_candle_date=datetime.datetime(2007, 5, 28, 7, 0, tzinfo=datetime.timezone.utc)
    # klong=Quotation(units=2, nano=0), kshort=Quotation(units=2, nano=0), dlong=Quotation(units=0, nano=205800000),
    # dshort=Quotation(units=0, nano=225700000), dlong_min=Quotation(units=0, nano=180000000),
    # dshort_min=Quotation(units=0, nano=200000000)
    # short_enabled_flag=True,
    tmpInstrument.country_of_risk = instrumentIn.country_of_risk
    tmpInstrument.country_of_risk_name = instrumentIn.country_of_risk_name
    tmpInstrument.otc_flag = instrumentIn.otc_flag
    tmpInstrument.real_exchange = instrumentIn.real_exchange
    return tmpInstrument


##############################
#         Instrument         #
##############################

class InstrumentManager(models.Manager):

    def get_instrument(self, figi: str):
        instrumentLogger.info(f"Find instrument {figi} in DB")
        return self._get_instrument(figi, "figi")

    def get_instrument_by_ticker(self, ticker: str, class_code: str):
        # идентификация инструментов в Т-Инвестициях:
        # https://russianinvestments.github.io/investAPI/faq_identification/
        instrumentLogger.info(f"Find instrument {ticker}:{class_code} in DB")
        return self._get_instrument(ticker, "ticker", class_code)

    def get_instrument_by_uid(self, uid: str):
        # идентификация инструментов в Т-Инвестициях:
        # https://russianinvestments.github.io/investAPI/faq_identification/
        instrumentLogger.info(f"Find instrument {uid} in DB")
        return self._get_instrument(uid, "uid")

    def _get_instrument(self, id: str, idType: str, class_code: str = ""):
        instrumentLogger.info(f"Find instrument by {idType} - {id} in DB")
        try:
            search_id = id
            if class_code != "":
                search_id += ":" + class_code
            tmpInst = self.get(idValue=search_id, idType=idType)
        except ObjectDoesNotExist:
            instrumentLogger.info(f"Instrument {id} not found in DB - getting from API")
            tmpInst = None
        if tmpInst is not None:
            # Если данные из базы не устарели - то возвращаем их, чтобы лишний раз не дергать API
            # TODO: offline mode
            instrument_age = (datetime.now(timezone.utc) - tmpInst.instrumentData.updated).total_seconds()
            if instrument_age < settings.INSTRUMENT_TIMEOUT:
                return tmpInst.instrumentData
            instrumentLogger.info(f"Instrument {id} is outdated - getting from API")

        if idType == "figi":
            instrumentData = tasks.get_instrument_by_figi(id)
        elif idType == "ticker":
            instrumentData = tasks.get_instrument_by_ticker(id, class_code)
        elif idType == "uid":
            instrumentData = tasks.get_instrument_by_uid(id)
        return instrumentData


class Instrument(models.Model):
    """Хранит ID (figi, isin, uid) инструмента и возвращает его запись в данных.
    Пришлось создать потому что иногда за одним инструментом несколько figi закрепляется и они изменяются.
    """
    idValue = models.CharField(max_length=40, db_index=True)
    idType = models.CharField(max_length=4, db_index=True)
    instrumentData = models.ForeignKey(InstrumentData, on_delete=models.PROTECT)

    objects = InstrumentManager()
    get_instrument = objects.get_instrument
    get_instrument_by_ticker = objects.get_instrument_by_ticker
    get_instrument_by_uid = objects.get_instrument_by_uid

    class Meta:
        verbose_name = "Интструмент"
        verbose_name_plural = "Инструменты"


##############################
#        LAST PRICE          #
##############################


class LastPrice(models.Model):
    figi = models.CharField(max_length=12)
    instrument_uid = models.CharField(max_length=40)
    price = models.DecimalField(max_digits=20, decimal_places=9)
    timestamp = models.DateTimeField()
    last_price_type = models.CharField(max_length=80)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Цена текущая"
        verbose_name_plural = "Цены текущие"


def last_price_from_tinkoff_client(price_info):
    tmpLP = LastPrice()
    tmpLP.figi = price_info.figi
    tmpLP.instrument_uid = price_info.instrument_uid
    tmpLP.price = Quotation(price_info.price).to_decimal()
    tmpLP.timestamp = price_info.time
    tmpLP.last_price_type = price_info.last_price_type.name
    return tmpLP


def get_last_price(figi: str) -> LastPrice:
    try:
        lp = LastPrice.objects.get(figi=figi)
    except LastPrice.DoesNotExist:
        lp = None
    # TODO: price obsoletion
    if lp is not None:
        # Если данные из базы не устарели - то возвращаем их, чтобы лишний раз не дергать API
        # TODO: offline mode
        lp_age = (datetime.now(timezone.utc) - lp.updated).total_seconds()
        if lp_age < settings.LAST_PRICE_TIMEOUT:
            return lp
    lp = tasks.get_lastprice_from_api(figi)
    return lp


##############################
#         OPERATION          #
##############################

class Operation(models.Model):
    operationId = models.CharField(max_length=20, unique=True)
    parentOperationId = models.CharField(max_length=20, null=True, blank=True)
    account = models.ForeignKey(Account, on_delete=models.PROTECT)
    currency = models.CharField(max_length=3)
    payment = models.DecimalField(max_digits=20, decimal_places=9)
    price = models.DecimalField(max_digits=20, decimal_places=9)
    state = models.CharField(max_length=20)
    timestamp = models.DateTimeField()
    type = models.CharField(max_length=64)
    quantity = models.BigIntegerField(default=0)
    quantity_rest = models.BigIntegerField(default=0)
    instrument = models.ForeignKey(InstrumentData, blank=True, null=True, on_delete=models.PROTECT)
    figi = models.CharField(max_length=16, blank=True, null=True)  # BBG00Y91R9T3
    instrument_type = models.CharField(max_length=8)

    class Meta():
        verbose_name = "Операция"
        verbose_name_plural = "Операции"

    def is_canceled(self):
        if self.state == "OPERATION_STATE_CANCELED":
            return True
        return False

    def price_rub(self):
        # Цена за штуку по курсу ЦБ РФ на дату исполнения операции
        currency = self.currency.upper()
        if currency == "RUB":
            return self.price
        cb_rate = CentrobankRate.get_rate(self.timestamp, currency)
        return self.price * cb_rate.rate

    def payment_rub(self):
        # Платеж по операции по курсу ЦБ РФ на дату исполнения операции
        currency = self.currency.upper()
        if currency == "RUB":
            return self.payment
        cb_rate = CentrobankRate.get_rate(self.timestamp, currency)
        return self.payment * cb_rate.rate

    def ticker(self) -> str:
        if self.instrument is not None:
            return self.instrument.ticker
        return ""


def operation_from_tinkoff_client(operation, accountId):
    # print(operation)
    tmpOperation = Operation()
    tmpOperation.operationId = operation.id
    tmpOperation.parentOperationId = operation.parent_operation_id
    tmpOperation.account = Account.account_by_id(accountId)
    tmpOperation.currency = operation.currency
    tmpOperation.price = Quotation(operation.price).to_decimal()
    tmpOperation.payment = Quotation(operation.payment).to_decimal()
    tmpOperation.state = operation.state.name
    tmpOperation.timestamp = operation.date
    tmpOperation.type = operation.operation_type.name
    tmpOperation.quantity = operation.quantity
    tmpOperation.quantity_rest = operation.quantity_rest
    tmpOperation.figi = operation.figi
    tmpOperation.instrument_type = operation.instrument_type
    if operation.figi != "":
        tmpOperation.instrument = Instrument.get_instrument(operation.figi)

    return tmpOperation


##############################
#         POSITION           #
##############################


class Position(models.Model):
    # https://russianinvestments.github.io/investAPI/operations/#portfolioposition
    account = models.ForeignKey(Account, on_delete=models.PROTECT)
    instrument = models.ForeignKey(InstrumentData, blank=True, null=True, on_delete=models.PROTECT)
    figi = models.CharField(max_length=12)
    quantity = models.IntegerField()
    # average_position_price	MoneyValue	Средневзвешенная цена позиции. Для пересчёта возможна задержка до одной секунды.
    # current_nkd	MoneyValue	Текущий НКД.
    # current_price	MoneyValue	Текущая цена за 1 инструмент.
    # average_position_price_fifo	MoneyValue	Средняя цена позиции по методу FIFO.
    blocked = models.BooleanField()  # Заблокировано на бирже.
    # blocked_lots	Quotation	Количество бумаг, заблокированных выставленными заявками.
    position_uid = models.CharField(max_length=40)
    instrument_uid = models.CharField(max_length=40)
    # var_margin	MoneyValue	Вариационная маржа.
    # expected_yield	Quotation	Текущая рассчитанная доходность позиции.
    # expected_yield_fifo	Quotation	Текущая рассчитанная доходность позиции.
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["account", "instrument", "blocked"]
        verbose_name = "Позиция"
        verbose_name_plural = "Позиции"


def position_from_tinkoff_client(position, accountId: str) -> Position:
    tmpPosition = Position()
    tmpPosition.account = Account.account_by_id(accountId)
    tmpPosition.figi = position.figi
    tmpPosition.instrument = Instrument.get_instrument_by_uid(position.instrument_uid)
    tmpPosition.quantity = Quotation(position.quantity).to_integer()
    tmpPosition.blocked = position.blocked
    tmpPosition.position_uid = position.position_uid
    tmpPosition.instrument_uid = position.instrument_uid
    return tmpPosition


##############################
#    PORTFOLIO   POSITION    #
##############################


class PortfolioPosition():
    """accounts: list[str] | None
    figi: str
    instrument: Instrument
    history: list[Operation]
    quantity: int = 0
    lastPrice: Decimal
    marketValue: Decimal"""

    def __init__(self, figi: str, accounts: list[str] = []):
        self.accounts = accounts
        self.figi = figi
        self.instrument = Instrument.get_instrument(figi)

        tmpPositions = Position.objects.filter(instrument=self.instrument)
        tmpHistory = Operation.objects.filter(instrument=self.instrument).order_by("-timestamp")
        if len(accounts) > 0:
            tmpPositions.filter(accountId__in=accounts)
            tmpHistory.filter(accountId__in=accounts)

        self.quantity = 0
        for tmpPosition in tmpPositions:
            self.quantity += tmpPosition.quantity

        self.history = []
        for record in tmpHistory:
            self.history.append(record)

        lp = get_last_price(figi)
        self.lastPrice = lp.price
        self.marketValue = self.lastPrice*self.quantity

        cb_rate_today = CentrobankRate.get_rate(datetime.now(), self.instrument.currency)
        self.market_value_rub_cb = self.marketValue * cb_rate_today.rate

    def icon_url(self) -> str:
        return self.instrument.icon_url()

    def ticker(self) -> str:
        return self.instrument.ticker


##############################
#           SPLITS           #
##############################

class Split(models.Model):
    date = models.DateField()
    ticker = models.CharField(max_length=12)
    before = models.IntegerField()
    after = models.IntegerField()

    class Meta:
        unique_together = ["date", "ticker"]
        verbose_name = "Сплит"
        verbose_name_plural = "Сплиты"


##############################
#          TARGETS           #
##############################

class TargetPortfolio(models.Model):
    """Портфель целей и его название
    """
    name = models.CharField(max_length=64, verbose_name="Название")
    targetPrice = models.IntegerField(default=1000, verbose_name="Цель (капитал)")
    accounts = models.ManyToManyField(Account, verbose_name="Включенные счета")

    def my_total_weight(self):
        """Сумма скорректированных на коэффициент весов входящих в портфель"""
        total_weight = tasks.target_portfolio_total_weight(self.pk)
        return total_weight

    def total_value(self):
        """Стоимость всех активов в портфеле"""
        total_value = tasks.target_portfolio_total_value(self.pk)
        return total_value

    def completed(self):
        if self.targetPrice == 0:
            return 0
        return self.total_value() / self.targetPrice * 100


class TargetPortfolioValues(models.Model):
    """Список целевых значений и весов для данного портфеля
    """
    # name = models.CharField(max_length=64)
    targetPortfolio = models.ForeignKey(TargetPortfolio, on_delete=models.PROTECT)
    order_number = models.IntegerField()
    instrument = models.ForeignKey(InstrumentData, on_delete=models.PROTECT)
    indexTarget = models.DecimalField(max_digits=9, decimal_places=7, verbose_name="Вес в индексе")
    coefficient = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Мой коэффициент",
                                      default=Decimal(1.0))

    # TODO: индекс по уникальности - портфель/инструмент

    BOUGHT_QTTY_CACHE_TIMEOUT = 300  # Обновлять количество купленных бумаг раз в 5 минут
    BOUGHT_PRICE_CACHE_TIMEOUT = 60  # Обновлять стоимость купленных бумаг раз в 1 минуту

    def corrected_weight(self):
        """Вес, скорректированный на коэффициент

        Returns:
            Decimal: десятичное число
        """
        if self.indexTarget == 0:
            return self.coefficient
        return self.indexTarget*self.coefficient

    def my_weight(self) -> Decimal:
        # тут должен быть скорректированный вес деленный
        # на общий скорректированный вес
        return Decimal(round(self.corrected_weight() / self.targetPortfolio.my_total_weight()*100, 2))

    def index_correlation(self):
        if self.indexTarget == 0:
            return 0
        return self.my_weight()/self.indexTarget

    def current_price(self):
        """Текущая стоимость данной позиции

        Returns:
            Decimal: стоимость позиции
        """
        cache_key = f"last_price_{self.instrument.figi}"
        value = cache.get(cache_key)
        if value is not None:
            return value
        return get_last_price(self.instrument.figi).price

    def to_buy_qtty(self) -> int:
        """Количество для закупки

        Returns:
            : количество бумаг, которое надо купить
        """
        # https://www.tutorialkart.com/python/python-round/python-round-to-nearest-10/
        current_price = self.current_price()
        if current_price == 0:
            return 0
        lots = self.instrument.lot
        qtty = self.targetPortfolio.targetPrice * self.my_weight() / 100 / current_price
        return round(qtty/lots)*lots

    def to_buy_price(self):
        """Стоимость для закупки

        Returns:
            : стоимость бумаг, которые надо купить
        """
        return self.to_buy_qtty() * self.current_price()

    def bought_qtty(self) -> int:
        """Количество купленного

        Returns:
            : количество уже купленных бумаг
        """
        cache_key = f"bought_qtty_{self.pk}"
        cached_value = cache.get(cache_key)
        if cached_value is not None:
            return cached_value
        qtty = Position.objects.filter(
            account__in=self.targetPortfolio.accounts.all()).filter(
                instrument=self.instrument).aggregate(models.Sum("quantity"))
        instrumentLogger.info(qtty)
        out = qtty['quantity__sum']
        if out is None:
            out = 0
        cache.set(cache_key, out, self.BOUGHT_QTTY_CACHE_TIMEOUT)
        return out

    def bought_price(self):
        """Стоимость купленных бумаг

        Returns:
            : Стоимость уже купленных бумаг
        """
        cache_key = f"bought_price_{self.pk}"
        cached_value = cache.get(cache_key)
        if cached_value is not None:
            return cached_value
        out = self.bought_qtty() * self.current_price()
        cache.set(cache_key, out, self.BOUGHT_PRICE_CACHE_TIMEOUT)
        return out

    def percent_complete(self) -> int:
        if self.to_buy_qtty() == 0:
            return 100
        result = round(self.bought_qtty() / self.to_buy_qtty() * 100)
        return result
