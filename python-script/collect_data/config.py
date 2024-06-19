import hashlib
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os

uri = os.getenv("MONGO_URI")

client = MongoClient(uri, server_api=ServerApi("1"))

db = client["waterloo_ai"]


def get_document_name(title, year, authorID):
    base_string = f"{title}_{year}_{authorID}"
    return hashlib.md5(base_string.encode()).hexdigest()
