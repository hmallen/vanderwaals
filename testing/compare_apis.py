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

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

load_dotenv('../.env', verbose=True)


class CoinWrangler:
    def __init__(self):
        self.paprika_client = Coinpaprika.Client()

        self.gecko_client = CoinGeckoAPI()

        self.db = MongoClient(
            os.getenv('MONGO_ATLAS'),
        )[os.getenv['MONGO_DB']]

    def get_gecko_coins(self, min_cap=0):
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
                    order='volume_desc'
                )# price_change_percentage='1h,24h,7d,14d,30d')

                if len(cm_page) == 0:
                    logger.debug('No data on requested page.')
                    build_list = False

                else:
                    for cm in cm_page:
                        try:
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
        pass

    def get_cmc_coins(self):
        pass

    def store_data(self, label):
        dt_now = datetime.datetime.utcnow()


if __name__ == '__main__':
    db = MongoClient(os.getenv('MONGO_ATLAS'))[os.getenv('MONGO_DB')]