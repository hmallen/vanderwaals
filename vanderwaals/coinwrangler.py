import datetime
import json
import logging
import os
import sys
import time

from pycoingecko import CoinGeckoAPI
from coinpaprika import client as Coinpaprika

from pymongo import MongoClient
from dotenv import load_dotenv

from vanderwaals.utils import datanormalizer

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

load_dotenv('../.env', verbose=True)


class CoinWrangler:
    def __init__(self, return_json=True):
        self.paprika_client = Coinpaprika.Client()

        self.gecko_client = CoinGeckoAPI()

        self.db = MongoClient(
            os.getenv('MONGO_ATLAS'),
        ).os.getenv['MONGO_DB']

        self.return_json = return_json

    def get_gecko_coins(self, min_cap=0, traded_only=True):
        coins_markets = []
        page = 1
        error_count = 0
        build_list = True
        while build_list:
            try:
                logger.debug(f'page: {page}')
                cm_page = self.gecko_client.get_coins_markets(
                    vs_currency='usd',
                    per_page='250',
                    page=str(page),
                    order='volume_desc',
                    price_change_percentage='1h,24h,7d,14d,30d'
                )

                if len(cm_page) == 0:
                    logger.debug('No data on requested page.')
                    build_list = False

                else:
                    for cm in cm_page:
                        try:
                            if traded_only is True and cm['total_volume'] == 0:
                                logger.debug(
                                    f'{cm["name"]} has no trade volume.'
                                )
                                build_list = True

                            if cm['market_cap'] >= min_cap:
                                coins_markets.append(cm)
                                logger.debug(
                                    f'Appended {cm["name"]} [{cm["market_cap"]}] [{cm["total_volume"]}]'
                                )

                            else:
                                logger.debug(
                                    f'{cm["name"]} below min cap of {min_cap}.'
                                )
                                build_list = False

                        except TypeError:
                            logger.debug('Invalid volume or market cap data.')

                page += 1

                time.sleep(1)

            except Exception as e:
                error_count += 1
                logger.warning(f'Error count: {error_count}')

                logger.exception(e)

                logger.warning('Delaying for 10 seconds.')

                time.sleep(10)

            logger.debug(f'build_list: {build_list}')

        return coins_markets

    def get_paprika_coins(self):
        tickers = self.paprika_client.tickers()

        tickers = sorted(tickers, key=lambda item: item['quotes']['USD']['market_cap'], reverse=True)

        return tickers

    def get_cmc_coins(self):
        pass

    def normalize_json(self, data, api):
        # api options --> coingecko, coinpaprika
        # data --> json returned by the api's
        pass

    def store_data(self, label, data):
        dt_now = datetime.datetime.utcnow()


if __name__ == '__main__':
    from pprint import pprint

    cw = CoinWrangler()
    dn = datanormalizer.DataNormalizer()

    gecko_coins = cw.get_gecko_coins()
    pprint(gecko_coins)

    for coin in gecko_coins:
        print(dn.unify_gecko(coin))

    time.sleep(5)

    paprika_coins = cw.get_paprika_coins()
    pprint(paprika_coins)

    for coin in paprika_coins:
        print(dn.unify_paprika(coin))