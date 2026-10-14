
from pymongo import MongoClient
from pymongo.errors import PyMongoError

def test_connection():
    client = None

    try:
        client = MongoClient(
            "mongodb://localhost:27017/",
            serverSelectionTimeoutMS=5000
        )

        # Verify that MongoDB responds
        client.admin.command("ping")

        print("MongoDB connection successful!")
        print("Server:", client.address)

    except PyMongoError as error:
        print("MongoDB connection failed.")
        print("Error:", error)

    finally:
        if client is not None:
            client.close()

if __name__ == "__main__":
    test_connection()
