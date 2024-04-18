from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os

# Set up MongoDB connection
load_dotenv()
uri = f"mongodb+srv://{os.environ.get('TEST_MONGODB_USERNAME')}:{os.environ.get('TEST_MONGODB_PASSWORD')}@playground0.ktzvb2d.mongodb.net/?retryWrites=true&w=majority&appName=Playground0"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

def verify():
    try:
        client.admin.command('ping')
        print("---------------------------")
        print("Pinged your deployment. You successfully connected to MongoDB!")
        print("---------------------------")
        return True
    except Exception as e:
        print(e)
        return False

