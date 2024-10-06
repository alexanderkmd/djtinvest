import logging

from datetime import datetime
from django.conf import settings
from tinkoff.invest import Client, InstrumentIdType, Account, Instrument, Operation, Share, PortfolioPosition

tlogger = logging.getLogger(__name__)
tlogger.setLevel(settings.API_CALLS_LOGGING_LEVEL)


class tinkoff_client():

    TOKEN = ""

    def __init__(self, token):
        self.TOKEN = token

    def get_accounts(self) -> list[Account]:
        """Запрашивает список счетов из Т-Банка

        Returns:
            List: Account models
        """
        tlogger.info("Getting list of accounts from Tinkoff")
        with Client(self.TOKEN) as client:
            accounts_in = client.users.get_accounts().accounts
        return accounts_in

    def get_instrument_by_figi(self, figi: str) -> Instrument:
        """Ищет инструмент по figi, но данные не полные

        Args:
            figi (str): _description_

        Returns:
            Instrument: _description_
        """
        tlogger.info(f"TClient - get instrument {figi}")
        with Client(self.TOKEN) as client:
            result = client.instruments.get_instrument_by(id=figi, id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI)

        return result.instrument

    def get_instrument_by_uid(self, uid: str) -> Instrument:
        """Ищет инструмент по figi, но данные не полные

        Args:
            uid (str): _description_

        Returns:
            Instrument: _description_
        """
        tlogger.info(f"TClient - get instrument {uid}")
        with Client(self.TOKEN) as client:
            result = client.instruments.get_instrument_by(id=uid, id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_UID)
        return result.instrument

    def get_lastprice(self, figi: list[str]):
        tlogger.info(f"TClient - get last price for {figi}")
        with Client(self.TOKEN) as client:
            result = client.market_data.get_last_prices(instrument_id=figi)
        return result.last_prices

    def get_operations(self, accountId: str,
                       startDate: datetime | None = None,
                       endDate: datetime | None = None,
                       figi: str = "") -> list[Operation]:
        tlogger.info(f"TClient - get operations list for account {accountId}")
        with Client(self.TOKEN) as client:
            operations = client.operations.get_operations(
                account_id=accountId, from_=startDate, to=endDate, figi=figi).operations
        return operations

    def get_positions(self, accountId: str) -> list[PortfolioPosition]:
        tlogger.info(f"TClient - get positions for account {accountId}")
        with Client(self.TOKEN) as client:
            positions = client.operations.get_portfolio(
                account_id=accountId).positions
        return positions

    def get_share(self, figi: str) -> Share:
        tlogger.info(f"TClient - get share data for {figi}")
        with Client(self.TOKEN) as client:
            result = client.instruments.share_by(id=figi, id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI)
        return result.instrument
