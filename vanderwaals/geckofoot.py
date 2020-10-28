import datetime
import itertools
import logging
import os
import sys
import time

from pycoingecko import CoinGeckoAPI
from pymongo import MongoClient

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class GeckoData:
    def __init__(self):
        self.cg = CoinGeckoAPI()

        db = MongoClient("mongodb://localhost:27017")["vanderwaals-dev"]
        self.coll_data = db["geckofoot-data"]
        self.coll_summary = db["geckofoot-summary"]

    def update_available(self):
        coins_list = self.cg.get_coins_list()
        coins_list_last = self.coll_data.find_one({"_id": "coins_list"})

        new_coins = list(
            itertools.filterfalse(lambda i: i in coins_list, coins_list_last)
        ) + list(itertools.filterfalse(lambda i: i in coins_list_last, coins_list))

        new_coins_update = []
        for coin in new_coins:
            new_coins_update.append({"coin": coin, "time": datetime.datetime.utcnow()})

        coins_list_update = {
            "_id": "coins_list",
            "coins": coins_list,
            "new": new_coins_update,
        }

        update_result = self.coll_data.update_one(
            {"_id": "coins_list"}, coins_list_update, upsert=True
        )

    def update_coins(self, min_cap=0):
        request_status = True
        page = 1
        error_count = 0
        continue_requests = True
        while continue_requests:
            try:
                logger.debug(f"page: {page}")
                cm_page = self.cg.get_coins_markets(
                    vs_currency="usd",
                    per_page="250",
                    page=str(page),
                    order="volume_desc"  # ,
                    # price_change_percentage='1h,24h,7d,14d,30d')
                )

                if len(cm_page) == 0:
                    logger.debug("No data on requested page.")
                    continue_requests = False

                else:
                    for cm in cm_page:
                        try:
                            if cm["market_cap"] >= min_cap:
                                if cm["ath_date"]:
                                    cm["ath_date"] = datetime.datetime.fromisoformat(
                                        cm["ath_date"].rstrip("Z")
                                    )
                                if cm["atl_date"]:
                                    cm["atl_date"] = datetime.datetime.fromisoformat(
                                        cm["atl_date"].rstrip("Z")
                                    )
                                if cm["last_updated"]:
                                    cm[
                                        "last_updated"
                                    ] = datetime.datetime.fromisoformat(
                                        cm["last_updated"].rstrip("Z")
                                    )

                                inserted_id = self.coll_data.insert_one(cm).inserted_id
                                logger.debug(f"inserted_id: {inserted_id}")

                            else:
                                logger.debug(
                                    f'{cm["name"]} below min cap of {min_cap}.'
                                )
                                continue_requests = False

                        except TypeError:
                            logger.debug("Invalid volume or market cap data.")

                page += 1

                time.sleep(1)

            except KeyboardInterrupt:
                logger.info("Exit signal received.")

                break

            except Exception as e:
                request_status = False

                error_count += 1
                logger.warning(f"Error count: {error_count}")

                logger.exception(e)

                logger.warning("Delaying for 10 seconds.")

                time.sleep(10)

            logger.debug(f"continue_requests: {continue_requests}")

        return (request_status, error_count)


if __name__ == "__main__":
    from pprint import pprint

    gecko = GeckoData()

    while True:
        res, err = gecko.update_coins()
        logger.debug(f"res: {res}, err: {err}")
        last_loop = time.time()

        try:
            while (time.time() - last_loop) < 600:
                time.sleep(1)

        except KeyboardInterrupt:
            logger.info("Exit signal received.")

            break

        except Exception as e:
            logger.exception(e)
