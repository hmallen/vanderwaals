import datetime

from pymongo import MongoClient
import loghandler


class FrameAnalyzer:
    def __init__(self, mongo_host="localhost", mongo_port=27017, mongo_db="bitmex"):
        log_handler = loghandler.LogHandler()
        self.logger = log_handler.create_logger("frameanalyzer")

        mongo_client = MongoClient(host=mongo_host, port=mongo_port)
        self.db = mongo_client[mongo_db]

    def count_trades(self, interval=0):
        """interval = Lookback period in seconds"""
        pipeline = []
        if interval > 0:
            pipeline.append(
                {
                    "$match": {
                        "timestamp": {
                            "$gte": datetime.datetime.utcnow()
                            - datetime.timedelta(seconds=interval)
                        }
                    }
                }
            )
        # pipeline.append({"$sort": {"timestamp": -1}})
        pipeline.append({"$group": {"_id": "$side", "count": {"$sum": 1}}})
        pipeline.append(
            {"$project": {"_id": 0, "side": {"$toLower": "$_id"}, "count": "$count"}}
        )

        agg_result = self.db["trade"].aggregate(pipeline=pipeline)

        trade_counts = {"interval": interval}
        for result in agg_result:
            trade_counts[result["side"]] = result["count"]
        trade_counts["total"] = trade_counts["buy"] + trade_counts["sell"]

        return trade_counts


if __name__ == "__main__":
    from pprint import pprint

    frame_analyzer = FrameAnalyzer()
    trade_counts = frame_analyzer.count_trades(interval=3600)

    pprint(trade_counts)