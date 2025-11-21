import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from database import create_document, get_documents, db
from schemas import (
    Branch, Role, User, Program, BudgetItem, ProgramRequest, Approval,
    Resource, Event, Report, Evaluation, Notification
)

app = FastAPI(title="Unified Student Activities & Community Services Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Unified Platform Backend Running"}

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
            response["connection_status"] = "Connected"
            try:
                response["collections"] = db.list_collection_names()[:20]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:100]}"
    return response

# Helper: collection name from model

def coll(name: str) -> str:
    return name.lower()

# ------- Reference Data Endpoints -------
@app.post("/branches")
def create_branch(payload: Branch):
    branch_id = create_document(coll("branch"), payload)
    return {"id": branch_id, "message": "Branch created"}

@app.get("/branches")
def list_branches():
    return get_documents(coll("branch"))

@app.post("/roles")
def create_role(payload: Role):
    role_id = create_document(coll("role"), payload)
    return {"id": role_id}

@app.get("/roles")

def list_roles():
    return get_documents(coll("role"))

@app.post("/users")

def create_user(payload: User):
    user_id = create_document(coll("user"), payload)
    return {"id": user_id}

@app.get("/users")

def list_users(branch_code: Optional[str] = None):
    q = {"branch_code": branch_code} if branch_code else {}
    return get_documents(coll("user"), q)

# ------- Program Requests Lifecycle -------
@app.post("/program-requests")

def submit_program_request(payload: ProgramRequest):
    req_id = create_document(coll("programrequest"), payload)
    return {"id": req_id, "status": payload.status}

@app.get("/program-requests")

def list_program_requests(status: Optional[str] = None, branch_code: Optional[str] = None):
    q = {}
    if status:
        q["status"] = status
    if branch_code:
        q["branch_code"] = branch_code
    return get_documents(coll("programrequest"), q)

@app.post("/approvals")

def approve_request(payload: Approval):
    # minimal append of approval history
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    from bson import ObjectId
    approvals = {
        "request_id": payload.request_id,
        "approved_by": payload.approved_by,
        "decision": payload.decision,
        "notes": payload.notes,
    }
    # store approval
    approval_id = create_document(coll("approval"), approvals)
    # update request status
    db[coll("programrequest")].update_one(
        {"_id": ObjectId(payload.request_id)},
        {"$set": {"status": "approved" if payload.decision == "approved" else "rejected"}}
    )
    return {"id": approval_id}

# ------- Scheduling & Resources -------
@app.post("/resources")

def create_resource(payload: Resource):
    res_id = create_document(coll("resource"), payload)
    return {"id": res_id}

@app.get("/resources")

def list_resources(branch_code: Optional[str] = None, type: Optional[str] = None):
    q = {}
    if branch_code:
        q["branch_code"] = branch_code
    if type:
        q["type"] = type
    return get_documents(coll("resource"), q)

@app.post("/events")

def create_event(payload: Event):
    event_id = create_document(coll("event"), payload)
    return {"id": event_id}

@app.get("/events")

def list_events(branch_code: Optional[str] = None, status: Optional[str] = None):
    q = {}
    if branch_code:
        q["branch_code"] = branch_code
    if status:
        q["status"] = status
    return get_documents(coll("event"), q)

# ------- Execution, Reporting, and Evaluation -------
@app.post("/reports")

def submit_report(payload: Report):
    rep_id = create_document(coll("report"), payload)
    return {"id": rep_id}

@app.get("/reports")

def list_reports(request_id: Optional[str] = None):
    q = {"request_id": request_id} if request_id else {}
    return get_documents(coll("report"), q)

@app.post("/evaluations")

def submit_evaluation(payload: Evaluation):
    ev_id = create_document(coll("evaluation"), payload)
    return {"id": ev_id}

@app.get("/evaluations")

def list_evaluations(request_id: Optional[str] = None):
    q = {"request_id": request_id} if request_id else {}
    return get_documents(coll("evaluation"), q)

# ------- Notifications -------
@app.post("/notifications")

def create_notification(payload: Notification):
    n_id = create_document(coll("notification"), payload)
    return {"id": n_id}

@app.get("/notifications")

def list_notifications(user_email: Optional[str] = None, branch_code: Optional[str] = None):
    q = {}
    if user_email:
        q["user_email"] = user_email
    if branch_code:
        q["branch_code"] = branch_code
    return get_documents(coll("notification"), q)

# ------- Schema Introspection (for admin tooling) -------
class SchemaField(BaseModel):
    name: str
    type: str

class SchemaModel(BaseModel):
    name: str
    fields: List[SchemaField]

@app.get("/schema")

def get_schema():
    # very lightweight reflection for admin tooling
    models = [Branch, Role, User, Program, BudgetItem, ProgramRequest, Approval, Resource, Event, Report, Evaluation, Notification]
    out = []
    for m in models:
        fields = [SchemaField(name=k, type=str(v.annotation)).model_dump() for k, v in m.model_fields.items()]
        out.append(SchemaModel(name=m.__name__.lower(), fields=fields).model_dump())
    return out

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
