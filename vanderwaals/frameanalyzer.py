import datetime
import os

from pymongo import MongoClient

import loghandler

log_handler = loghandler.LogHandler()

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

mongo_client = MongoClient(
    host=os.getenv("MONGO_HOST"), port=int(os.getenv("MONGO_PORT"))
)[os.getenv("MONGO_DB")]


class FrameAnalyzer:
    def __init__(self, mongo_host="localhost", mongo_port=27017, mongo_db="bitmex"):
        self.logger = log_handler.create_logger("frameanalyzer")

    def count_trades(self, interval=0, get_baseline=False, lookback_periods=3):
        """interval = Lookback period in seconds"""
        if get_baseline is False:
            timestamp_delta = {
                "$gte": datetime.datetime.utcnow()
                - datetime.timedelta(seconds=interval)
            }
        else:
            timestamp_delta = {
                "$gte": (
                    datetime.datetime.utcnow() - datetime.timedelta(seconds=interval)
                )
                - (lookback_periods * datetime.timedelta(seconds=interval)),
                "$lte": datetime.datetime.utcnow()
                - datetime.timedelta(seconds=interval),
            }

        pipeline = []
        if interval > 0:
            pipeline.append({"$match": {"timestamp": timestamp_delta}})

        elif get_baseline is True:
            self.logger.warning(
                "Must use specific interval to retrieve baseline value."
            )

        # pipeline.append({"$sort": {"timestamp": -1}})
        pipeline.append({"$group": {"_id": "$side", "count": {"$sum": 1}}})
        pipeline.append(
            {"$project": {"_id": 0, "side": {"$toLower": "$_id"}, "count": "$count"}}
        )

        agg_result = mongo_client["trade"].aggregate(pipeline=pipeline)

        trade_counts = {"interval": interval}
        for result in agg_result:
            trade_counts[result["side"]] = result["count"]
        trade_counts["total"] = trade_counts["buy"] + trade_counts["sell"]

        if get_baseline is False:
            trade_counts["baseline"] = False
        else:
            trade_counts["baseline"] = True
            for key in ["buy", "sell", "total"]:
                trade_counts[key] = trade_counts[key] / lookback_periods

        return trade_counts


if __name__ == "__main__":
    from pprint import pprint

    frame_analyzer = FrameAnalyzer()
    trade_counts = frame_analyzer.count_trades(interval=300)
    trade_baseline = frame_analyzer.count_trades(interval=300, get_baseline=True)

    pprint(trade_counts)
    pprint(trade_baseline)