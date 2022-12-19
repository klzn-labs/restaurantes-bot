from urllib.parse import urljoin

import requests
from geopy import Point
import os
import googlemaps
import tweepy
import random
from shapely.geometry import Polygon, Point
from dotenv import load_dotenv

load_dotenv()

CONSUMER_KEY = os.environ.get("CONSUMER_KEY", "")
CONSUMER_SECRET = os.environ.get("CONSUMER_SECRET", "")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN", "")
ACCESS_TOKEN_SECRET = os.environ.get("ACCESS_TOKEN_SECRET", "")

GOOGLE_APIKEY = os.environ.get("GOOGLE_APIKEY", "")

GOOGLE_API_URL = "https://maps.googleapis.com/maps/api/place/"

client = googlemaps.Client(key=GOOGLE_APIKEY)

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)
poly = Polygon(
    [
        (-27.563509939334267, -48.61403937842272),
        (-27.605198664774598, -48.62124915625475),
        (-27.610370612842175, -48.60545630957506),
        (-27.61584652701801, -48.596873240727405),
        (-27.617975975264585, -48.58674521948717),
        (-27.59546257085664, -48.569407420414905),
        (-27.585040949668812, -48.5774755051317),
        (-27.579183107341944, -48.57593055273912),
        (-27.5870529208321, -48.563011163173485),
        (-27.58396797619373, -48.54803183708441),
        (-27.574754629714327, -48.54073248666407),
        (-27.57071988621876, -48.51602397721888),
        (-27.561815345727954, -48.52427445214869),
        (-27.54765694699429, -48.51056299966456),
        (-27.540646032953322, -48.53120528024317),
        (-27.525405026812617, -48.52717123788477),
        (-27.51866862791634, -48.51704321664454),
        (-27.50702167684197, -48.52219305795313),
        (-27.483724076117596, -48.53798590463282),
        (-27.434676424765538, -48.51669989389063),
        (-27.436676076161596, -48.492452724396),
        (-27.42648699822563, -48.473698718963874),
        (-27.425001409246768, -48.44855032724024),
        (-27.413496941063087, -48.42915259164454),
        (-27.394142351429554, -48.43430243295313),
        (-27.38408272251584, -48.41644964975001),
        (-27.437418794595235, -48.38898382943751),
        (-27.447473567581223, -48.366324527679694),
        (-27.524301351307493, -48.415720088897956),
        (-27.557216563189954, -48.428744895874274),
        (-27.588277189839914, -48.416717870651496),
        (-27.60594339485688, -48.43352995675684),
        (-27.647692012070085, -48.46301279824854),
        (-27.692464709796138, -48.482882602630866),
        (-27.7032940572783, -48.494920356689704),
        (-27.709772153168792, -48.499651773391975),
        (-27.71685772369609, -48.50283823770167),
        (-27.730115811911492, -48.50680790704371),
        (-27.743979995658787, -48.507344348846686),
        (-27.755070072339567, -48.500907047210944),
        (-27.75347067659778, -48.51318083566309),
        (-27.716661289937885, -48.51202212136866),
        (-27.709878575579136, -48.53641949456812),
        (-27.693672050810417, -48.57025824350001),
        (-27.64524928289253, -48.545946990706895),
        (-27.649924609022943, -48.52349168169316),
        (-27.61606728257414, -48.53114677865114),
        (-27.61282536885287, -48.53875087742309),
        (-27.61323402528313, -48.55047484924192),
        (-27.603952833313777, -48.550604174710415),
        (-27.595125079737535, -48.56322244478799),
        (-27.587518131192827, -48.56322244478799),
        (-27.57557290229694, -48.59266095507344),
        (-27.571920981860792, -48.60021405565938),
        (-27.569963565044784, -48.60553020813817),
        (-27.567162509111263, -48.60937340647608),
        (-27.565881307366503, -48.61163732224149),
    ]
)


def polygon_random_points(polygon) -> tuple:
    min_x, min_y, max_x, max_y = polygon.bounds
    random_point = Point([random.uniform(min_x, max_x), random.uniform(min_y, max_y)])
    return random_point.x, random_point.y


def get_nearest_place_id(latitude, longitude) -> list:
    url = urljoin(
        GOOGLE_API_URL,
        f"nearbysearch/json?location={latitude}%2C{longitude}&radius=8000&type=restaurant&key={GOOGLE_APIKEY}",
    )

    nearby_places = requests.request("GET", url, headers={}, data={}).json()

    filtered_places = [
        place
        for place in nearby_places["results"]
        if not ("lodging" in place["types"] or "gas_station" in place["types"])
    ]
    return random.choice(filtered_places)["place_id"]


def get_place_details(place_id) -> dict:
    url = urljoin(
        GOOGLE_API_URL,
        f"details/json?place_id={place_id}&fields=name%2Crating%2Caddress_component%2Cphoto%2Curl&key={GOOGLE_APIKEY}",
    )
    place_details = requests.request("GET", url).json()

    photo_ids = []
    try:
        photos = place_details["result"]["photos"]
        if len(photos) > 4:
            photos = photos[:4]

        for photo in photos:
            photo_url = urljoin(
                GOOGLE_API_URL,
                f"photo?photoreference={photo['photo_reference']}&sensor=false&maxheight={640}&maxwidth={640}&key={GOOGLE_APIKEY}",
            )
            photo_req = requests.request("GET", photo_url)
            with open(f"images/image{photos.index(photo)}.jpg", "wb") as f:
                f.write(photo_req.content)
                upload = api.media_upload(f"images/image{photos.index(photo)}.jpg")
                photo_ids.append(upload.media_id)
    except:
        # No idea if the upload can fail, but probably it will fail sometime
        pass
    place_details["result"]["media_ids"] = photo_ids
    return place_details["result"]


def draw_stars(rating) -> str:
    return f"{'★'*int(rating)}{'☆'*(5-int(rating))}"

def tweet(place_details):
    address_components = place_details['address_components']
    number = address_components[0]["long_name"]
    street = address_components[1]["long_name"]
    district = address_components[2]["long_name"]
    short_address = f"{street}, {number}, {district}"
    tweet_text = f"{place_details['name']} - {short_address} - {draw_stars(place_details['rating'])}\n{place_details['url']}"
    return api.update_status(status=tweet_text, media_ids=place_details["media_ids"])


def main():
    latitude, longitude = polygon_random_points(poly)
    place_id = get_nearest_place_id(latitude, longitude)
    place_details = get_place_details(place_id)
    tweet(place_details)


if __name__ == "__main__":
    main()
