from datetime import datetime
from pycbrf import ExchangeRate, ExchangeRates, ExchangeRateDynamics


def get_rates_for_date_from_cbrf(date: datetime, locale_en=False) -> ExchangeRates:
    rates = ExchangeRates(date, locale_en=locale_en)
    return rates


def get_rate_dynamics_from_cbrf(currency: str,
                                start_date: datetime,
                                end_date: datetime = datetime.now()) -> dict[datetime, ExchangeRate]:
    dynamics = ExchangeRateDynamics(since=start_date, till=end_date, currency=currency)
    return dynamics.rates
