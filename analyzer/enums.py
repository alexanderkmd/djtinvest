import enum


class OperationType(enum.Enum):
    """Перечисление типов операция


    см. https://russianinvestments.github.io/investAPI/operations/#operationtype
    """

    OPERATION_TYPE_UNSPECIFIED = 0, "UNSPECIFIED", "Тип операции не определён"
    OPERATION_TYPE_INPUT = 1, "INPUT", "Пополнение брокерского счёта"
    OPERATION_TYPE_BOND_TAX = 2, "BOND_TAX", "Удержание НДФЛ по купонам"
    OPERATION_TYPE_OUTPUT_SECURITIES = 3, "OUTPUT_SECURITIES", "Вывод ЦБ"
    OPERATION_TYPE_OVERNIGHT = 4, "OVERNIGHT", "Доход по сделке РЕПО овернайт"
    OPERATION_TYPE_TAX = 5, "TAX", "Удержание налога"
    OPERATION_TYPE_BOND_REPAYMENT_FULL = 6, "BOND_REPAYMENT_FULL", "Полное погашение облигаций"
    OPERATION_TYPE_SELL_CARD = 7, "SELL_CARD", "Продажа ЦБ с карты"
    OPERATION_TYPE_DIVIDEND_TAX = 8, "DIVIDEND_TAX", "Удержание налога по дивидендам"
    OPERATION_TYPE_OUTPUT = 9, "OUTPUT", "Вывод денежных средств"
    OPERATION_TYPE_BOND_REPAYMENT = 10, "BOND_REPAYMENT", "Частичное погашение облигаций"
    OPERATION_TYPE_TAX_CORRECTION = 11, "TAX_CORRECTION", "Корректировка налога"
    OPERATION_TYPE_SERVICE_FEE = 12, "SERVICE_FEE", "Удержание комиссии за обслуживание брокерского счёта"
    OPERATION_TYPE_BENEFIT_TAX = 13, "BENEFIT_TAX", "Удержание налога за материальную выгоду"
    OPERATION_TYPE_MARGIN_FEE = 14, "MARGIN_FEE", "Удержание комиссии за непокрытую позицию"
    OPERATION_TYPE_BUY = 15, "BUY", "Покупка ЦБ"
    OPERATION_TYPE_BUY_CARD = 16, "BUY_CARD", "Покупка ЦБ с карты"
    OPERATION_TYPE_INPUT_SECURITIES = 17, "INPUT_SECURITIES", "Перевод ценных бумаг из другого депозитария"
    OPERATION_TYPE_SELL_MARGIN = 18, "SELL_MARGIN", "Продажа в результате Margin-call"
    OPERATION_TYPE_BROKER_FEE = 19, "BROKER_FEE", "Удержание комиссии за операцию"
    OPERATION_TYPE_BUY_MARGIN = 20, "BUY_MARGIN", "Покупка в результате Margin-call"
    OPERATION_TYPE_DIVIDEND = 21, "DIVIDEND", "Выплата дивидендов"
    OPERATION_TYPE_SELL = 22, "SELL", "Продажа ЦБ"
    OPERATION_TYPE_COUPON = 23, "COUPON", "Выплата купонов"
    OPERATION_TYPE_SUCCESS_FEE = 24, "SUCCESS_FEE", "Удержание комиссии SuccessFee"
    OPERATION_TYPE_DIVIDEND_TRANSFER = 25, "DIVIDEND_TRANSFER", "Передача дивидендного дохода"
    OPERATION_TYPE_ACCRUING_VARMARGIN = 26, "ACCRUING_VARMARGIN", "Зачисление вариационной маржи"
    OPERATION_TYPE_WRITING_OFF_VARMARGIN = 27, "WRITING_OFF_VARMARGIN", "Списание вариационной маржи"
    OPERATION_TYPE_DELIVERY_BUY = 28, "DELIVERY_BUY", "Покупка в рамках экспирации фьючерсного контракта"
    OPERATION_TYPE_DELIVERY_SELL = 29, "DELIVERY_SELL", "Продажа в рамках экспирации фьючерсного контракта"
    OPERATION_TYPE_TRACK_MFEE = 30, "TRACK_MFEE", "Комиссия за управление по счёту автоследования"
    OPERATION_TYPE_TRACK_PFEE = 31, "TRACK_PFEE", "Комиссия за результат по счёту автоследования"
    OPERATION_TYPE_TAX_PROGRESSIVE = 32, "TAX_PROGRESSIVE", "Удержание налога по ставке 15%"
    OPERATION_TYPE_BOND_TAX_PROGRESSIVE = 33, "BOND_TAX_PROGRESSIVE", "Удержание налога по купонам по ставке 15%"
    OPERATION_TYPE_DIVIDEND_TAX_PROGRESSIVE = 34, "DIVIDEND_TAX_PROGRESSIVE", "Удержание налога по дивидендам по ставке 15%"
    OPERATION_TYPE_BENEFIT_TAX_PROGRESSIVE = 35, "BENEFIT_TAX_PROGRESSIVE", "Удержание налога за материальную выгоду по ставке 15%"
    OPERATION_TYPE_TAX_CORRECTION_PROGRESSIVE = 36, "TAX_CORRECTION_PROGRESSIVE", "Корректировка налога по ставке 15%"
    OPERATION_TYPE_TAX_REPO_PROGRESSIVE = 37, "TAX_REPO_PROGRESSIVE", "Удержание налога за возмещение по сделкам РЕПО по ставке 15%"
    OPERATION_TYPE_TAX_REPO = 38, "TAX_REPO", "Удержание налога за возмещение по сделкам РЕПО"
    OPERATION_TYPE_TAX_REPO_HOLD = 39, "TAX_REPO_HOLD", "Удержание налога по сделкам РЕПО"
    OPERATION_TYPE_TAX_REPO_REFUND = 40, "TAX_REPO_REFUND", "Возврат налога по сделкам РЕПО"
    OPERATION_TYPE_TAX_REPO_HOLD_PROGRESSIVE = 41, "TAX_REPO_HOLD_PROGRESSIVE", "Удержание налога по сделкам РЕПО по ставке 15%"
    OPERATION_TYPE_TAX_REPO_REFUND_PROGRESSIVE = 42, "TAX_REPO_REFUND_PROGRESSIVE", "Возврат налога по сделкам РЕПО по ставке 15%"
    OPERATION_TYPE_DIV_EXT = 43, "DIV_EXT", "Выплата дивидендов на карту"
    OPERATION_TYPE_TAX_CORRECTION_COUPON = 44, "TAX_CORRECTION_COUPON", "Корректировка налога по купонам"
    OPERATION_TYPE_CASH_FEE = 45, "CASH_FEE", "Комиссия за валютный остаток"
    OPERATION_TYPE_OUT_FEE = 46, "OUT_FEE", "Комиссия за вывод валюты с брокерского счёта"
    OPERATION_TYPE_OUT_STAMP_DUTY = 47, "OUT_STAMP_DUTY", "Гербовый сбор"
    OPERATION_TYPE_OUTPUT_SWIFT = 50, "OUTPUT_SWIFT", "SWIFT-перевод"
    OPERATION_TYPE_INPUT_SWIFT = 51, "INPUT_SWIFT", "SWIFT-перевод"
    OPERATION_TYPE_OUTPUT_ACQUIRING = 53, "OUTPUT_ACQUIRING", "Перевод на карту"
    OPERATION_TYPE_INPUT_ACQUIRING = 54, "INPUT_ACQUIRING", "Перевод с карты"
    OPERATION_TYPE_OUTPUT_PENALTY = 55, "OUTPUT_PENALTY", "Комиссия за вывод средств"
    OPERATION_TYPE_ADVICE_FEE = 56, "ADVICE_FEE", "Списание оплаты за сервис Советов"
    OPERATION_TYPE_TRANS_IIS_BS = 57, "TRANS_IIS_BS", "Перевод ценных бумаг с ИИС на брокерский счёт"
    OPERATION_TYPE_TRANS_BS_BS = 58, "TRANS_BS_BS", "Перевод ценных бумаг с одного брокерского счёта на другой"
    OPERATION_TYPE_OUT_MULTI = 59, "OUT_MULTI", "Вывод денежных средств со счёта"
    OPERATION_TYPE_INP_MULTI = 60, "INP_MULTI", "Пополнение денежных средств со счёта"
    OPERATION_TYPE_OVER_PLACEMENT = 61, "OVER_PLACEMENT", "Размещение биржевого овернайта"
    OPERATION_TYPE_OVER_COM = 62, "OVER_COM", "Списание комиссии"
    OPERATION_TYPE_OVER_INCOME = 63, "OVER_INCOME", "Доход от оверанайта"
    OPERATION_TYPE_OPTION_EXPIRATION = 64, "OPTION_EXPIRATION", "Экспирация опциона"
    OPERATION_TYPE_FUTURE_EXPIRATION = 65, "FUTURE_EXPIRATION", "Экспирация фьючерса"

    def __new__(cls, *args, **kwargs):
        obj = object.__new__(cls)
        obj._value_ = args[0]
        return obj

    def __init__(self, _: int, short: str, description: str):
        self._short_ = short
        self._description_ = description

    @property
    def description(self):
        return self._description_

    @property
    def short(self):
        return self._short_
