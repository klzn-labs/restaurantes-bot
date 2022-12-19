from urllib.parse import urljoin

import requests
from geopy import Point
import os
import googlemaps
from geopy.geocoders import Nominatim
import tweepy
import random
from shapely.geometry import Polygon, Point
from dotenv import load_dotenv

load_dotenv()

CONSUMER_KEY = os.environ.get("CONSUMER_KEY", "")
CONSUMER_SECRET = os.environ.get(
    "CONSUMER_SECRET", ""
)
ACCESS_TOKEN = os.environ.get(
    "ACCESS_TOKEN", ""
)
ACCESS_TOKEN_SECRET = os.environ.get(
    "ACCESS_TOKEN_SECRET", ""
)

GOOGLE_APIKEY = os.environ.get(
    "GOOGLE_APIKEY", ""
)

GOOGLE_API_URL = "https://maps.googleapis.com/maps/api/place/"

client = googlemaps.Client(key=GOOGLE_APIKEY)

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)

poly = Polygon(
    [
        (-27.44180229680025, -48.36638447158204),
        (-27.37810332932587, -48.414106334375006),
        (-27.433880023830316, -48.519506419824225),
        (-27.59363455441509, -48.557958568261725),
        (-27.760423230181726, -48.57766573449177),
        (-27.83227287029294, -48.56166733431555),
        (-27.79221841898422, -48.477072167597235),
    ]
)


def polygon_random_points(polygon) -> tuple:
    min_x, min_y, max_x, max_y = polygon.bounds
    random_point = Point([random.uniform(min_x, max_x), random.uniform(min_y, max_y)])
    return random_point.x, random_point.y


def get_nearest_place_id(latitude, longitude) -> list:
    url = urljoin(
        GOOGLE_API_URL,
        f"nearbysearch/json?location={latitude}%2C{longitude}&radius=50000&type=restaurant&key={GOOGLE_APIKEY}",
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

address_map = {"NUMBER": 0, "STREET": 1, "DISTRICT": 2}

def tweet(place_details):
    short_address = f"{place_details['address_components'][address_map['STREET']]['long_name']}, {place_details['address_components'][address_map['NUMBER']]['long_name']} - {place_details['address_components'][address_map['DISTRICT']]['long_name']}"
    tweet_text = f"{place_details['name']} - {short_address} - {draw_stars(place_details['rating'])}\n{place_details['url']}"
    return api.update_status(status=tweet_text, media_ids=place_details["media_ids"])


if __name__ == "__main__":
    latitude, longitude = polygon_random_points(poly)
    place_id = get_nearest_place_id(latitude, longitude)
    place_details = get_place_details(place_id)
    tweet(place_details)
