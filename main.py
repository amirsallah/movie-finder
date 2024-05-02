from fastapi import FastAPI
import redis
import requests
from elasticsearch import Elasticsearch

app = FastAPI()

redis_client = redis.StrictRedis(host='redis', port=6379, db=0, decode_responses=True)

es_client = Elasticsearch('https://elasticsearch:9200')

API_URL = "https://imdb-top-100-movies.p.rapidapi.com/"

API_headers = {
    "X-RapidAPI-Key": "SIGN-UP-FOR-KEY",
    "X-RapidAPI-Host": "imdb-top-100-movies.p.rapidapi.com"
}


def redis(name):
    result = redis_client.get(name)
    if result:
        return result, True
    else:
        return None, False


def save_to_redis(name):
    res = redis_client.set(name)
    if res is not None:
        return True
    else:
        return False


def elastic(name):
    res = es_client.search(index="movies", body={"query": {"match": {"title": name}}})
    if res['hits']['total']['value'] > 0:
        return res['hits']['hits'][0]['_source'], True
    else:
        return None, False


def api_call(name):
    response = requests.get(API_URL + name)
    if response.status_code == 200:
        return response.json(), True
    else:
        return None, False


@app.get("/{name}")
async def find_movie(name: str):
    result, found = redis(name)
    if found:
        return result
    result, found = elastic(name)
    if found:
        await redis_client.set(name, result)
        await save_to_redis(name)
        return result
    result, found = api_call(name)
    if found:
        await redis_client.set(name, result)
        await save_to_redis(name)
        return result
    return {"message": "Not Found"}
