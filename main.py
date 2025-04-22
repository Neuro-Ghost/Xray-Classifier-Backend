from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from huggingface_hub import hf_hub_download
from jose import JWTError, jwt
import tensorflow as tf
import numpy as np
from database import save_prediction
from utils import preprocess_image
from auth import router as auth_router
from fastapi.staticfiles import StaticFiles


# Load Model
model_path = hf_hub_download(
    repo_id="atoxy/xray-classifier-model", filename="xray_model.h5"
)
model = tf.keras.models.load_model(model_path)
class_names = ["COVID", "Normal", "Pneumonia"]

# JWT Setup
SECRET_KEY = "supersecretkey"  # same as auth.py
ALGORITHM = "HS256"
security = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Invalid or expired token."
        )


# App Initialization
app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth_router)


@app.get("/")
def home():
    return {"message": "X-ray Classifier is running."}


@app.post("/predict")
async def predict(
    file: UploadFile = File(...),
    user_data: dict = Depends(verify_token),  # ✅ Require valid token
):
    image_bytes = await file.read()
    img_array = preprocess_image(image_bytes)
    predictions = model.predict(img_array)
    pred_index = np.argmax(predictions[0])
    confidence = float(np.max(predictions[0]))
    save_prediction(
        email=user_data.get("sub"),  # email from JWT
        predicted_class=class_names[pred_index],
        confidence=round(confidence, 4),
        filename=file.filename,
    )

    return {"class": class_names[pred_index], "confidence": round(confidence, 4)}
