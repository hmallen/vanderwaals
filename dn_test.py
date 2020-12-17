from pprint import pprint

from vanderwaals import coinwrangler
from vanderwaals.utils import datanormalizer


if __name__ == '__main__':
    cw = coinwrangler.CoinWrangler()
    dn = datanormalizer.DataNormalizer()

    gecko_coins = cw.get_gecko_coins()
    #paprika_coins = cw.get_paprika_coins()

    for coin in gecko_coins:
        pprint(dn.unify_gecko(coin))

    #for coin in paprika_coins:
    #    pprint(dn.unify_paprika(coin))

    #pprint(gc_norm)
    #print()
    #pprint(pc_norm)