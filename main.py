from urllib.parse import urljoin

import requests
from geopy import Point
import os
import googlemaps
import tweepy
import random
from shapely.geometry import Polygon, Point
from dotenv import load_dotenv

from errors import NoPhotosFoundError

load_dotenv(override=False)

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
        (-27.43906003590224, -48.51664066145628),
        (-27.412243228124584, -48.40952396223753),
        (-27.45246599682376, -48.37381839583128),
        (-27.712948031025505, -48.501534460284404),
        (-27.691062177356784, -48.559212682940654),
        (-27.597389849852792, -48.583931921221904),
        (-27.579966888602065, -48.5862079177254),
    ]
)


def polygon_random_points(polygon) -> tuple:
    min_x, min_y, max_x, max_y = polygon.bounds
    while True:
        random_point = Point([random.uniform(min_x, max_x), random.uniform(min_y, max_y)])
        if random_point.within(polygon):
            return random_point.x, random_point.y


def get_nearest_place_id(latitude, longitude) -> list:
    url = urljoin(
        GOOGLE_API_URL,
        f"nearbysearch/json?location={latitude}%2C{longitude}&rankby=distance&type=restaurant&key={GOOGLE_APIKEY}",
    )

    nearby_places = requests.request("GET", url, headers={}, data={}).json()

    filtered_places = [
        place
        for place in nearby_places["results"]
        if not ("lodging" in place["types"] or "gas_station" in place["types"])
        and place.get("user_ratings_total", 0) > 25
    ]
    return random.choice(filtered_places)


def get_place_details(near_place) -> dict:
    place_id = near_place["place_id"]

    url = urljoin(
        GOOGLE_API_URL,
        f"details/json?place_id={place_id}&fields=name%2Crating%2Caddress_component%2Cphoto%2Curl&key={GOOGLE_APIKEY}",
    )
    place_details = requests.request("GET", url).json()

    if not place_details["result"].get("photos"):
        raise NoPhotosFoundError("Could not find any photo for this place")

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
    place_details = place_details["result"]
    place_details["media_ids"] = photo_ids
    place_details["user_ratings_total"] = near_place["user_ratings_total"]

    return place_details


def draw_stars(rating) -> str:
    rating = int(rating)
    full_stars = "★" * rating
    clear_stars = "☆" * (5 - rating)
    return f"{full_stars}{clear_stars}"


def tweet(place_details):
    address_components = place_details['address_components']
    number = address_components[0]["long_name"]
    street = address_components[1]["long_name"]
    district = address_components[2]["long_name"]
    short_address = f"{street}, {number}, {district}"
    rating = place_details["rating"]
    tweet_text = (
        f"{place_details['name']} - {short_address}\n"
        f"{rating} {draw_stars(rating)} ({place_details['user_ratings_total']})\n"
        f"{place_details['url']}"
    )
    return api.update_status(status=tweet_text, media_ids=place_details["media_ids"])


def main():
    latitude, longitude = polygon_random_points(poly)
    near_place = get_nearest_place_id(latitude, longitude)
    place_details = get_place_details(near_place)
    tweet(place_details)


if __name__ == "__main__":
    main()
