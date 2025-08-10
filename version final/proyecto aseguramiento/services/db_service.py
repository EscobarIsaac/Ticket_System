from pymongo import MongoClient
import certifi, os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.environ.get(
    "MONGO_URI",
    "mongodb+srv://isaac:isaac1@cluster0.uu8wq4u.mongodb.net/ticketdb?retryWrites=true&w=majority"
)
client = MongoClient(MONGO_URI, tls=True, tlsCAFile=certifi.where())
db = client['ticketdb']
users = db['users']
tickets = db['tickets']
notifications = db['notifications']
