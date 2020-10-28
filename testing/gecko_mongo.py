import logging
#from prettyprinter import pprint O_O hehe
from pprint import pprint

from pymongo import MongoClient
from pycoingecko import CoinGeckoAPI

import sys

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# CoinGeckoAPI
cg = CoinGeckoAPI()

# Initialize MongoClient
client = MongoClient('mongodb://127.0.0.1:27017')
db = client['mydb_01']
collection = db['mycol_01']

def update_insert_coins(page_limit=0):
    coinlist = []
    page = 1
    while True:
        cm_page = cg.get_coins_markets(
            vs_currency='usd',
            per_page='250',
            page=str(page),
        )

        #[coinlist.append(cm) for cm in cm_page]

        if page == page_limit or len(cm_page) == 0:
            break

        else:
            for coin in cm_page:
                coin['_id'] = coin['id']

                logger.debug(f'coin["_id"]: {coin["_id"]}')
                updated_result = collection.update_one({'_id': coin['_id']}, {'$set': coin}, upsert=True)

                logger.debug(f'matched: {updated_result.matched_count} / modified: {updated_result.modified_count}')
                #logger.debug(f'Matched Count: {updated_result.matched_count}')
                #logger.debug(f'Updated Count: {updated_result.modified_count}')

            page += 1

        # Remain below API rate limit
        #time.sleep(0.5)
        
    #for coin in coinlist:
        #collection.update_one({"id":coin['id']}, {"$set":coin}, upsert=True)
    
    pprint("Coins Updated!")
        
    #return coinlist


if __name__ == '__main__':
    update_insert_coins()