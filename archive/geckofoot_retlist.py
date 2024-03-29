import logging
import os
import sys
import time

from pycoingecko import CoinGeckoAPI
from pymongo import MongoClient

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

cg = CoinGeckoAPI()

mongo = MongoClient('mongodb://localhost:27017')['vanderwaals']['geckofoot']


class GeckoData:
    def __init__(self):
        pass

    def get_coins(self, min_cap=0):
        cm_list = []
        page = 1
        error_count = 0
        build_list = True
        while build_list:
            try:
                logger.debug(f'page: {page}')
                cm_page = cg.get_coins_markets(vs_currency='usd',
                                               per_page='250',
                                               page=str(page),
                                               order='volume_desc')  #,
                # price_change_percentage='1h,24h,7d,14d,30d')

                if len(cm_page) == 0:
                    logger.debug('No data on requested page.')
                    build_list = False

                else:
                    #[cm_list.append(cm) for cm in cm_page]
                    for cm in cm_page:
                        try:
                            if cm['market_cap'] >= min_cap:
                                cm_list.append(cm)
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

        return cm_list


if __name__ == '__main__':
    from pprint import pprint

    gecko = GeckoData()
    """
    Sorting Options:
    market_cap_asc, [market_cap_desc],
    gecko_desc, gecko_asc,
    volume_asc, volume_desc,
    id_asc, id_desc
    """

    #coins = gecko.get_coins(min_cap=100)
    #pprint(coins)
    coins = gecko.get_coins()
    pprint(coins[0])
    #pprint(coins[-1])
    print(len(coins))
