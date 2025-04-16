from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import tensorflow as tf
import numpy as np
from utils import preprocess_image
from huggingface_hub import hf_hub_download

model_path = hf_hub_download(repo_id="atoxy/xray-classifier-model", filename="xray_model.h5")
model = tf.keras.models.load_model(model_path)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model = tf.keras.models.load_model("model/xray_model.h5")
class_names = ["Normal", "COVID", "Pneumonia"]

@app.get("/")
def home():
    return {"message": "X-ray Classifier is running."}

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    image_bytes = await file.read()
    img_array = preprocess_image(image_bytes)
    predictions = model.predict(img_array)
    pred_index = np.argmax(predictions[0])
    confidence = float(np.max(predictions[0]))
    return {
        "class": class_names[pred_index],
        "confidence": round(confidence, 4)
    }
