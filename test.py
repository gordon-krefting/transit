from google.transit import gtfs_realtime_pb2
import requests

feed = gtfs_realtime_pb2.FeedMessage()
response = requests.get('http://datamine.mta.info/mta_esi.php?key=bf19e1713f8b4c05913690c66518e7d2&feed_id=21')
feed.ParseFromString(response.content)
for entity in feed.entity:
    if entity.HasField('trip_update'):
        print(entity.trip_update)
