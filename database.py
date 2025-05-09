from pymongo import MongoClient
from datetime import datetime

client = MongoClient("mongodb://localhost:27017/")
db = client["xray_app"]
users = db["users"]
predictions_collection = db["predictions"]


def save_prediction(email, predicted_class, confidence, filename=None):
    predictions_collection.insert_one(
        {
            "email": email,
            "class": predicted_class,
            "confidence": confidence,
            "filename": filename,
            "timestamp": datetime.utcnow(),
        }
    )


def get_user_predictions(email):
    return list(predictions_collection.find({"email": email}).sort("timestamp", -1))
