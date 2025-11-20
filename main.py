import os
import secrets
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, create_document, get_documents

app = FastAPI(title="IT Provisioning Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ====== Schemas for requests ======
class LoginRequest(BaseModel):
    nik: str
    password: str

class LoginResponse(BaseModel):
    token: str
    nik: str
    name: Optional[str] = None
    division: Optional[str] = None

class PackageRequest(BaseModel):
    division: str

class TaskCreateRequest(BaseModel):
    type: str
    payload: Optional[Dict[str, Any]] = None

class TaskResponse(BaseModel):
    id: str
    status: str

# ====== Helpers ======

def get_collection(name: str):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    return db[name]


def auth_dependency(token: str) -> str:
    # Simple token auth via header: Authorization: Bearer <token>
    # This is a minimal demo, not production grade
    if not token:
        raise HTTPException(status_code=401, detail="Token required")
    coll = get_collection("session")
    doc = coll.find_one({"token": token})
    if not doc:
        raise HTTPException(status_code=401, detail="Invalid token")
    return doc["nik"]


# ====== Seed demo employees if not exists ======
@app.on_event("startup")
def seed_employee():
    if db is None:
        return
    coll = get_collection("employee")
    # Seed original demo user
    if not coll.find_one({"nik": "EMP001"}):
        coll.insert_one({
            "nik": "EMP001",
            "name": "Demo User",
            "division": "IT",
            "password": "12345",
            "is_active": True,
        })
    # Seed requested employee 555501254121
    if not coll.find_one({"nik": "555501254121"}):
        coll.insert_one({
            "nik": "555501254121",
            "name": "User 555501254121",
            "division": "IT",
            "password": "12345",
            "is_active": True,
        })


@app.get("/")
def read_root():
    return {"message": "IT Provisioning Dashboard API"}


@app.post("/api/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    coll = get_collection("employee")
    user = coll.find_one({"nik": payload.nik})
    if not user:
        raise HTTPException(status_code=401, detail="NIK tidak ditemukan")
    if user.get("password") != payload.password:
        raise HTTPException(status_code=401, detail="Password salah")
    # create simple token
    token = secrets.token_hex(16)
    sess = get_collection("session")
    sess.insert_one({"token": token, "nik": user["nik"]})
    return LoginResponse(token=token, nik=user["nik"], name=user.get("name"), division=user.get("division"))


@app.get("/api/divisions", response_model=List[str])
def list_divisions():
    # Static divisions for now
    return [
        "IT",
        "Finance",
        "HR",
        "Marketing",
        "Operations",
    ]


@app.post("/api/tasks", response_model=TaskResponse)
def create_task(payload: TaskCreateRequest, authorization: Optional[str] = None):
    # authorization should be like: Bearer <token>
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    nik = auth_dependency(token)

    if payload.type not in ["install_packages", "activate_windows", "activate_office"]:
        raise HTTPException(status_code=400, detail="Invalid task type")

    # create task document
    task_doc = {
        "nik": nik,
        "type": payload.type,
        "status": "pending",
        "payload": payload.payload or {},
    }
    task_id = create_document("task", task_doc)
    return TaskResponse(id=task_id, status="pending")


@app.get("/api/tasks")
def list_my_tasks(authorization: Optional[str] = None):
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    nik = auth_dependency(token)
    tasks = get_documents("task", {"nik": nik}, limit=50)
    # convert ObjectId to str if present
    for t in tasks:
        if "_id" in t:
            t["id"] = str(t.pop("_id"))
    return tasks


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
