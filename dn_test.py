from pprint import pprint
import os
import time

from pymongo import MongoClient
from vanderwaals import coinwrangler
from vanderwaals.utils import datanormalizer

from dotenv import load_dotenv
load_dotenv(verbose=True)


if __name__ == '__main__':
    cw = coinwrangler.CoinWrangler()
    dn = datanormalizer.DataNormalizer()

    mongo_client = MongoClient(f"mongodb://{os.getenv('MONGODB_HOST')}:{os.getenv('MONGODB_PORT')}")
    mongo_db = mongo_client[os.getenv('MONGODB_DB')]
    mongo_coll = mongo_db['coinwrangler']
    
    recording_active = True
    while recording_active is True:
        try:
            gecko_coins = cw.get_gecko_coins()
            paprika_coins = cw.get_paprika_coins()

            for idx, coin in enumerate(gecko_coins):
                #pprint(dn.unify_gecko(coin))
                gecko_coins[idx] = dn.unify_gecko(coin)
            
            insert_result = mongo_coll.insert_many(gecko_coins)
            print(f'Gecko Coins Inserted: {len(insert_result.inserted_ids)}')

            for idx, coin in enumerate(paprika_coins):
                #pprint(dn.unify_paprika(coin))
                paprika_coins[idx] = dn.unify_paprika(coin)
            
            insert_result = mongo_coll.insert_many(paprika_coins)
            print(f'Paprika Coins Inserted: {len(insert_result.inserted_ids)}')

            delay_start = time.time()
            update_last = 0
            while (time.time() - delay_start) < 300:
                if (time.time() - update_last) >= 30:
                    print(f'{int(300 - (time.time() - delay_start))} seconds remaining until coin data update.')
                    update_last = time.time()
                time.sleep(1)
    
        except KeyboardInterrupt:
            print('Exit signal received.')
            recording_active = False
        
        except Exception as e:
            print(e)
            time.sleep(10)
    
    print('Done.')
