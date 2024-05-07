import json

from fastapi import FastAPI
import redis
import requests
from elasticsearch import Elasticsearch

app = FastAPI()

redis_client = redis.StrictRedis(host='redis', port=6379, db=0, decode_responses=True)

es_client = Elasticsearch('http://elasticsearch:9200', http_auth=('elastic', 'elasticpass'))

API_URL = "https://imdb188.p.rapidapi.com/api/v1/searchIMDB"

API_headers = {
    "X-RapidAPI-Key": "90daada7acmshf985d8bc7b14882p1efb7ajsn5af69d3c274f",
    "X-RapidAPI-Host": "imdb188.p.rapidapi.com"
}


def redis(name):
    result = redis_client.get(name)
    if result:
        return result, True
    else:
        return "not found in redis", False


def save_to_redis(name, data):
    res = redis_client.set(name, json.dumps(data))
    if res is not None:
        return True
    else:
        return False


def elastic(name):
    res = es_client.search(index="your_index_name", body={"query": {"match": {"Series_Title": name}}})
    if res['hits']['total']['value'] > 0:
        return res['hits']['hits'][0]['_source'], True
    else:
        return "not found in elastic", False


def api_call(name):
    querystring = {"query": name}
    response = requests.get(API_URL, headers=API_headers, params=querystring)
    if response.status_code == 200:
        return response.json(), True
    else:
        print(response.json())
        print(response.status_code)
        return "not found in api-call", False


@app.get("/{name}")
async def find_movie(name: str):
    print("SEARCH REDIS")
    result, found = redis(name)
    if found:
        print("in redis")
        return result
    print(result)
    print("SEARCH-ELASTICS")
    result, found = elastic(name)
    if found:
        print("in elastic")
        save_to_redis(name, result)
        return result
    print(result)
    print("SEARCH-API-CALL")
    result, found = api_call(name)
    if found:
        print("in api-call")
        save_to_redis(name, result)
        return result
    print(result)
    return {"message": "Not Found"}
