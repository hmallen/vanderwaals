import vanderwaals.loghandler
import os
import sys
import datetime
import json

unified_json = {
    "id": "",
    "name": "",
    "symbol": "",
    "rank": 0,
    "circulating_supply": 0,
    "total_supply": 0,
    "max_supply": 0,
    "last_updated": None,
    "market_cap": 0,
    "volume": 0,
    "ath": 0,
    "ath_date": None,
    "percent_change": {
        "5m": 0.0,
        "30m": 0.0,
        "1h": 0.0,
        "6h": 0.0,
        "12h": 0.0,
        "24h": 0.0,
        "7d": 0.0,
        "30d": 0.0,
        "1y": 0.0,
        "ath": 0.0,
        "market_cap_24h": 0.0
    },
    "price_change": {
        "24h": 0,
        "market_cap": 0
    },
    "volume_change": {
        "24h": 0
    },
    "high_24h": 0,
    "low_24h": 0,
    "image": "",
    "fully_diluted_valuation": 0,
    "roi": 0.0,
    "first_data_at": None,
    "beta_value": 0.0
}


class DataNormalizer:
    def __init__(self, return_json=True):
        self.return_json = return_json

    def unify_gecko(self, data):
        unified_data = {
            'id': data['id'],
            'name': data['name'],
            'symbol': data['symbol'],
            'rank': data['market_cap_rank'],
            'circulating_supply': data['circulating_supply'],
            'total_supply': data['total_supply'],
            'max_supply': data['max_supply'],
            'market_cap': data['market_cap'],
            'volume': data['total_volume'],
            'ath': data['ath'],
            'ath_date': data['ath_date'],
            'high_24h': data['high_24h'],
            'low_24h': data['low_24h'],
            'image': data['image'],
            'fully_diluted_valuation': data['fully_diluted_valuation'],
            'roi': data['roi'],
            'last_updated': data['last_updated'],
            'percent_change': {
                '1h': data['price_change_percentage_1h_in_currency'],
                '24h': data['price_change_percentage_24h'],
                '7d': data['price_change_percentage_7d_in_currency'],
                '30d': data['price_change_percentage_30d_in_currency'],
                'ath': data['ath_change_percentage'],
                'market_cap_24h': data['market_cap_change_percentage_24h'],
                '15m': 0.0,
                '30m': 0.0,
                '6h': 0.0,
                '12h': 0.0,
                '1y': 0.0
            },
            'price_change': {
                '24h': data['price_change_24h'],
                'market_cap_24h': data['market_cap_change_24h']
            },
            'volume_change': {
                '24h': 0.0
            },
            'first_data_at': None,
            'beta_value': 0.0
        }

        # if self.return_json is True:
        #    unified_data = json.dumps(unified_data)#, json.loads(json.dumps({})))

        return unified_data

    def unify_paprika(self, data):
        unified_data = {
            'id': data['id'],
            'name': data['name'],
            'symbol': data['symbol'],
            'rank': data['rank'],
            'circulating_supply': data['circulating_supply'],
            'total_supply': data['total_supply'],
            'max_supply': data['max_supply'],
            'market_cap': data['quotes']['USD']['market_cap'],
            'volume': data['quotes']['USD']['volume_24h'],
            'ath': data['quotes']['USD']['ath_price'],
            'ath_date': data['quotes']['USD']['ath_date'],
            'last_updated': data['last_updated'],
            'percent_change': {
                '15m': data['quotes']['USD']['percent_change_15m'],
                '30m': data['quotes']['USD']['percent_change_30m'],
                '1h': data['quotes']['USD']['percent_change_1h'],
                '6h': data['quotes']['USD']['percent_change_6h'],
                '12h': data['quotes']['USD']['percent_change_12h'],
                '24h': data['quotes']['USD']['percent_change_24h'],
                '7d': data['quotes']['USD']['percent_change_7d'],
                '30d': data['quotes']['USD']['percent_change_30d'],
                '1y': data['quotes']['USD']['percent_change_1y'],
                'ath': data['quotes']['USD']['percent_from_price_ath'],
                'market_cap_24h': 0.0
            },
            'price_change': {
                'market_cap_24h': data['quotes']['USD']['market_cap_change_24h'],
                '24h': 0.0
            },
            'volume_change': {
                '24h': data['quotes']['USD']['volume_24h_change_24h']
            },
            'first_data_at': data['first_data_at'],
            'beta_value': data['beta_value'],
            'high_24h': 0.0,
            'low_24h': 0.0,
            'image': "",
            'fully_diluted_valuation': 0.0,
            'roi': 0.0
        }

        # if self.return_json is True:
        #    unified_data = json.dumps(unified_data)#, json.loads(json.dumps({})))

        return unified_data
