from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr
from pymongo import MongoClient
import bcrypt
import jwt
import datetime
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Request

# === CONFIG ===
SECRET_KEY = "supersecretkey"  # Replace with a strong, secure key in production
ALGORITHM = "HS256"

# === DATABASE ===
client = MongoClient("mongodb://localhost:27017/")
db = client["xray_app"]
users = db["users"]

# === ROUTER ===
router = APIRouter()


# === Pydantic Models ===
class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


# === Hashing Password ===
def hash_password(password: str) -> bytes:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())


# === Token Generation ===
def create_token(user_id: str, email: str):
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# === Token Verification ===
security = HTTPBearer()


# def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
#     try:
#         payload = jwt.decode(
#             credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM]
#         )
#         user = users.find_one({"_id": payload["user_id"]})
#         if not user:
#             raise HTTPException(status_code=401, detail="User not found")
#         return str(user["_id"])
#     except jwt.ExpiredSignatureError:
#         raise HTTPException(status_code=401, detail="Token expired")
#     except jwt.InvalidTokenError:
#         raise HTTPException(status_code=401, detail="Invalid token")


# # === ROUTES ===


@router.post("/signup")
def signup(user: SignupRequest):
    if users.find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_pw = hash_password(user.password).decode("utf-8")
    users.insert_one(
        {
            "email": user.email,
            "password": hashed_pw,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }
    )

    return {"message": "User created successfully"}


@router.post("/login")
async def login(request: Request):
    data = await request.json()
    email = data.get("email")
    password = data.get("password")

    db_user = users.find_one({"email": email})
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not bcrypt.checkpw(password.encode("utf-8"), db_user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_token(str(db_user["_id"]), db_user["email"])
    return {"token": token, "message": "Login successful"}
