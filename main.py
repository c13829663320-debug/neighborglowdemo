from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from models import (
    SessionLocal, User, Item, ServiceRequest,
    Community, Case, Diagnosis, ActionPlan, Message, Simulation, FollowUp,
    CommunityGroup, GroupMember, GroupTopic, ChatMessage, AgentSession, AuditLog,
)
from ai_engine import (
    analyze_context, generate_action_plan, generate_message,
    detect_safety, detect_emotions, classify_category,
    detect_frequency, detect_relationship,
)
from agent import (
    match_trigger, get_agent, create_agent_response, AGENT_INFO,
)
from chat_ws import manager
import uuid

# Config
SECRET_KEY = "neighborglow-demo-secret-key-2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

app = FastAPI(title="NeighborGlow API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic Models
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: Optional[str] = None
    user_id: Optional[int] = None
    username: Optional[str] = None

class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "resident"
    real_name: Optional[str] = None
    phone: Optional[str] = None
    display_name: Optional[str] = None
    community_id: Optional[int] = None
    privacy_consent: bool = True

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    real_name: Optional[str] = None
    phone: Optional[str] = None
    display_name: Optional[str] = None
    community_id: Optional[int] = None
    privacy_consent: bool = True
    is_active: bool = True
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class ItemCreate(BaseModel):
    title: str
    description: Optional[str] = None

class ServiceRequestCreate(BaseModel):
    title: str
    content: Optional[str] = None

class ServiceRequestResponse(BaseModel):
    id: int
    resident_id: int
    title: str
    content: Optional[str] = None
    status: str = "pending"
    handler_id: Optional[int] = None
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class CaseCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    frequency: Optional[str] = None
    relationship_status: Optional[str] = None
    expected_outcome: Optional[str] = None
    community_id: Optional[int] = None
    is_anonymous: bool = False

class CaseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    frequency: Optional[str] = None
    relationship_status: Optional[str] = None
    expected_outcome: Optional[str] = None
    risk_level: Optional[str] = None
    status: Optional[str] = None
    assigned_staff_id: Optional[int] = None
    is_anonymous: Optional[bool] = None

class CaseResponse(BaseModel):
    id: int
    resident_id: int
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    frequency: Optional[str] = None
    relationship_status: Optional[str] = None
    expected_outcome: Optional[str] = None
    risk_level: str = "green"
    status: str = "draft"
    assigned_staff_id: Optional[int] = None
    community_id: Optional[int] = None
    is_anonymous: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    class Config:
        from_attributes = True

class DiagnosisConfirm(BaseModel):
    facts: Optional[List[str]] = None
    assumptions: Optional[List[str]] = None
    emotions: Optional[List[str]] = None
    needs: Optional[List[str]] = None
    risk_level: Optional[str] = None

class ActionPlanCreate(BaseModel):
    pass

class MessageGenerateRequest(BaseModel):
    type: str = "wechat_friendly"
    tone: Optional[str] = None
    replacements: Optional[Dict[str, str]] = None
    user_content: Optional[str] = None

class SimulationCreate(BaseModel):
    role: str = "resident"
    counterpart_style: str = "defensive"

class SimulationMessage(BaseModel):
    content: str

class FollowUpCreate(BaseModel):
    action_taken: Optional[str] = None
    response_received: Optional[str] = None
    improvement_level: Optional[str] = None
    is_escalated: bool = False

class GroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    center_lat: Optional[float] = None
    center_lng: Optional[float] = None
    radius_km: float = 1.0
    group_type: str = "neighbor"
    tags: Optional[List[str]] = None

class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    center_lat: Optional[float] = None
    center_lng: Optional[float] = None
    radius_km: Optional[float] = None
    group_type: Optional[str] = None
    status: Optional[str] = None
    tags: Optional[List[str]] = None

class GroupTopicCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_default: bool = False

class ChatMessageCreate(BaseModel):
    content: str
    topic_id: Optional[int] = None
    message_type: str = "text"
    reply_to_id: Optional[int] = None

class AgentTriggerRequest(BaseModel):
    message: str
    group_id: Optional[int] = None
    topic_id: Optional[int] = None

class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    action: str
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    detail: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    created_at: Optional[datetime] = None
    class Config:
        from_attributes = True


# Helper Functions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = int(user_id_str)
    except (JWTError, ValueError, TypeError):
        raise credentials_exception
    user = db.query(User).filter(User.id == user_id).first()
    if user is None or not user.is_active:
        raise credentials_exception
    return user

def require_role(role: str):
    def _check(current_user: User = Depends(get_current_user)):
        if current_user.role != role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"需要 {role} 权限")
        return current_user
    return _check

def add_audit_log(db: Session, user_id: int, action: str, target_type: Optional[str] = None, target_id: Optional[int] = None, detail: Optional[Dict[str, Any]] = None, ip_address: Optional[str] = None):
    log = AuditLog(user_id=user_id, action=action, target_type=target_type, target_id=target_id, detail=detail, ip_address=ip_address)
    db.add(log)
    db.commit()

def _mask_phone(phone: Optional[str]) -> Optional[str]:
    if not phone or len(phone) < 7:
        return phone
    return phone[:3] + "****" + phone[-4:]

def _mask_name(name: Optional[str]) -> Optional[str]:
    if not name:
        return name
    if len(name) <= 1:
        return name
    return name[0] + "*" * (len(name) - 1)

def _user_to_dict(user: User, mask: bool = False) -> Dict[str, Any]:
    return {
        "id": user.id, "username": user.username, "role": user.role,
        "real_name": _mask_name(user.real_name) if mask else user.real_name,
        "phone": _mask_phone(user.phone) if mask else user.phone,
        "display_name": user.display_name, "community_id": user.community_id,
        "privacy_consent": user.privacy_consent, "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }

def _case_to_dict(case: Case) -> Dict[str, Any]:
    return {
        "id": case.id, "resident_id": case.resident_id, "title": case.title,
        "description": case.description, "category": case.category,
        "frequency": case.frequency, "relationship_status": case.relationship_status,
        "expected_outcome": case.expected_outcome, "risk_level": case.risk_level,
        "status": case.status, "assigned_staff_id": case.assigned_staff_id,
        "community_id": case.community_id, "is_anonymous": case.is_anonymous,
        "created_at": case.created_at.isoformat() if case.created_at else None,
        "updated_at": case.updated_at.isoformat() if case.updated_at else None,
    }


# ================================================================================
# 1. Health
# ================================================================================
@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "NeighborGlow API", "timestamp": datetime.utcnow().isoformat()}


# ================================================================================
# 2. Auth: Register
# ================================================================================
@app.post("/api/auth/register", response_model=Token)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == user_in.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = User(
        username=user_in.username, password=get_password_hash(user_in.password),
        role=user_in.role, real_name=user_in.real_name, phone=user_in.phone,
        display_name=user_in.display_name, community_id=user_in.community_id,
        privacy_consent=user_in.privacy_consent,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"access_token": token, "token_type": "bearer", "role": user.role, "user_id": user.id, "username": user.username}


# ================================================================================
# 3. Auth: Login
# ================================================================================
@app.post("/api/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="账户已禁用")
    token = create_access_token({"sub": str(user.id), "role": user.role})
    return {"access_token": token, "token_type": "bearer", "role": user.role, "user_id": user.id, "username": user.username}


# ================================================================================
# 4. Auth: Get Current User
# ================================================================================
@app.get("/api/auth/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user


# ================================================================================
# 5. Auth: Update Current User
# ================================================================================
@app.put("/api/auth/me", response_model=UserResponse)
def update_current_user(update: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if update.real_name is not None:
        current_user.real_name = update.real_name
    if update.phone is not None:
        current_user.phone = update.phone
    if update.display_name is not None:
        current_user.display_name = update.display_name
    if update.community_id is not None:
        current_user.community_id = update.community_id
    if update.privacy_consent is not None:
        current_user.privacy_consent = update.privacy_consent
    if update.password:
        current_user.password = get_password_hash(update.password)
    db.commit()
    db.refresh(current_user)
    return current_user


# ================================================================================
# 6. Communities: List
# ================================================================================
@app.get("/api/communities")
def list_communities(db: Session = Depends(get_db)):
    communities = db.query(Community).all()
    return [{"id": c.id, "name": c.name, "address": c.address, "center_lat": c.center_lat, "center_lng": c.center_lng, "created_at": c.created_at.isoformat() if c.created_at else None} for c in communities]


# ================================================================================
# 7. Communities: Create (staff only)
# ================================================================================
@app.post("/api/communities")
def create_community(name: str, address: Optional[str] = None, center_lat: Optional[float] = None, center_lng: Optional[float] = None, db: Session = Depends(get_db), _: User = Depends(require_role("staff"))):
    community = Community(name=name, address=address, center_lat=center_lat, center_lng=center_lng)
    db.add(community)
    db.commit()
    db.refresh(community)
    return {"id": community.id, "name": community.name, "address": community.address, "center_lat": community.center_lat, "center_lng": community.center_lng}


# ================================================================================
# 8. Items: List
# ================================================================================
@app.get("/api/items")
def list_items(db: Session = Depends(get_db)):
    items = db.query(Item).all()
    return [{"id": i.id, "title": i.title, "description": i.description} for i in items]


# ================================================================================
# 9. Items: Create (staff only)
# ================================================================================
@app.post("/api/items")
def create_item(item_in: ItemCreate, db: Session = Depends(get_db), _: User = Depends(require_role("staff"))):
    item = Item(title=item_in.title, description=item_in.description)
    db.add(item)
    db.commit()
    db.refresh(item)
    return {"id": item.id, "title": item.title, "description": item.description}


# ================================================================================
# 10. Items: Delete (staff only)
# ================================================================================
@app.delete("/api/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db), _: User = Depends(require_role("staff"))):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="物品不存在")
    db.delete(item)
    db.commit()
    return {"detail": "已删除"}


# ================================================================================
# 11. Service Requests: Create (resident only)
# ================================================================================
@app.post("/api/service-requests", response_model=ServiceRequestResponse)
def create_service_request(sr_in: ServiceRequestCreate, db: Session = Depends(get_db), current_user: User = Depends(require_role("resident"))):
    sr = ServiceRequest(resident_id=current_user.id, title=sr_in.title, content=sr_in.content)
    db.add(sr)
    db.commit()
    db.refresh(sr)
    add_audit_log(db, current_user.id, "create_service_request", "service_request", sr.id)
    return sr


# ================================================================================
# 12. Service Requests: List
# ================================================================================
@app.get("/api/service-requests", response_model=List[ServiceRequestResponse])
def list_service_requests(db: Session = Depends(get_db), current_user: User = Depends(get_current_user), status_filter: Optional[str] = Query(None, alias="status")):
    query = db.query(ServiceRequest)
    if current_user.role == "resident":
        query = query.filter(ServiceRequest.resident_id == current_user.id)
    if status_filter:
        query = query.filter(ServiceRequest.status == status_filter)
    return query.order_by(ServiceRequest.created_at.desc()).all()


# ================================================================================
# 13. Service Requests: Handle (staff)
# ================================================================================
@app.put("/api/service-requests/{sr_id}/handle", response_model=ServiceRequestResponse)
def handle_service_request(sr_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("staff"))):
    sr = db.query(ServiceRequest).filter(ServiceRequest.id == sr_id).first()
    if not sr:
        raise HTTPException(status_code=404, detail="服务请求不存在")
    sr.handler_id = current_user.id
    sr.status = "handling"
    db.commit()
    db.refresh(sr)
    add_audit_log(db, current_user.id, "handle_service_request", "service_request", sr.id)
    return sr


# ================================================================================
# 14. Service Requests: Complete (staff)
# ================================================================================
@app.put("/api/service-requests/{sr_id}/complete", response_model=ServiceRequestResponse)
def complete_service_request(sr_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role("staff"))):
    sr = db.query(ServiceRequest).filter(ServiceRequest.id == sr_id).first()
    if not sr:
        raise HTTPException(status_code=404, detail="服务请求不存在")
    sr.status = "completed"
    db.commit()
    db.refresh(sr)
    add_audit_log(db, current_user.id, "complete_service_request", "service_request", sr.id)
    return sr


# ================================================================================
# 15. Cases: Create (resident, runs analyze_context on description)
# ================================================================================
@app.post("/api/cases", response_model=CaseResponse)
def create_case(case_in: CaseCreate, db: Session = Depends(get_db), current_user: User = Depends(require_role("resident"))):
    category = case_in.category
    frequency = case_in.frequency
    relationship_status = case_in.relationship_status
    risk_level = "green"
    if case_in.description:
        analysis = analyze_context(case_in.description)
        if not category:
            category = analysis["symptoms"].get("category")
        if not frequency:
            frequency = analysis["symptoms"].get("frequency")
        if not relationship_status:
            relationship_status = analysis["symptoms"].get("relationship")
        risk_level = analysis.get("risk_level", "green")
    case = Case(
        resident_id=current_user.id, title=case_in.title, description=case_in.description,
        category=category, frequency=frequency, relationship_status=relationship_status,
        expected_outcome=case_in.expected_outcome, risk_level=risk_level,
        community_id=case_in.community_id or current_user.community_id, is_anonymous=case_in.is_anonymous,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    add_audit_log(db, current_user.id, "create_case", "case", case.id, {"title": case.title})
    return case


# ================================================================================
# 16. Cases: List (filtered by role)
# ================================================================================
@app.get("/api/cases", response_model=List[CaseResponse])
def list_cases(db: Session = Depends(get_db), current_user: User = Depends(get_current_user), status_filter: Optional[str] = Query(None, alias="status"), risk_level: Optional[str] = Query(None), community_id: Optional[int] = Query(None)):
    query = db.query(Case)
    if current_user.role == "resident":
        query = query.filter(Case.resident_id == current_user.id)
    if status_filter:
        query = query.filter(Case.status == status_filter)
    if risk_level:
        query = query.filter(Case.risk_level == risk_level)
    if community_id:
        query = query.filter(Case.community_id == community_id)
    return query.order_by(Case.created_at.desc()).all()


# ================================================================================
# 17. Cases: Detail with diagnosis data
# ================================================================================
@app.get("/api/cases/{case_id}")
def get_case_detail(case_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")
    if current_user.role == "resident" and case.resident_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此案件")
    result = _case_to_dict(case)
    diagnosis = db.query(Diagnosis).filter(Diagnosis.case_id == case_id).order_by(Diagnosis.created_at.desc()).first()
    if diagnosis:
        result["diagnosis"] = {"id": diagnosis.id, "facts": diagnosis.facts, "assumptions": diagnosis.assumptions, "emotions": diagnosis.emotions, "needs": diagnosis.needs, "risk_level": diagnosis.risk_level, "confidence": diagnosis.confidence, "confirmed_by_user": diagnosis.confirmed_by_user}
    plan = db.query(ActionPlan).filter(ActionPlan.case_id == case_id).order_by(ActionPlan.created_at.desc()).first()
    if plan:
        result["action_plan"] = {"id": plan.id, "target": plan.target, "steps": plan.steps, "communication_method": plan.communication_method, "escalation_condition": plan.escalation_condition, "safety_reminder": plan.safety_reminder, "status": plan.status}
    result["messages_count"] = db.query(Message).filter(Message.case_id == case_id).count()
    result["followups_count"] = db.query(FollowUp).filter(FollowUp.case_id == case_id).count()
    return result


# ================================================================================
# 18. Cases: Update
# ================================================================================
@app.put("/api/cases/{case_id}", response_model=CaseResponse)
def update_case(case_id: int, case_in: CaseUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")
    if current_user.role == "resident" and case.resident_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权修改此案件")
    update_data = case_in.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(case, key, value)
    case.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(case)
    add_audit_log(db, current_user.id, "update_case", "case", case.id, update_data)
    return case


# ================================================================================
# 19. Cases: Delete
# ================================================================================
@app.delete("/api/cases/{case_id}")
def delete_case(case_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")
    if current_user.role == "resident" and case.resident_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权删除此案件")
    add_audit_log(db, current_user.id, "delete_case", "case", case.id)
    db.delete(case)
    db.commit()
    return {"detail": "已删除"}


# ================================================================================
# 20. Cases: Diagnose (AI)
# ================================================================================
@app.post("/api/cases/{case_id}/diagnose")
def diagnose_case(case_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")
    if current_user.role == "resident" and case.resident_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此案件")
    description = case.description or case.title or ""
    analysis = analyze_context(description)
    diagnosis = Diagnosis(
        case_id=case_id, facts=analysis.get("facts", []), assumptions=analysis.get("assumptions", []),
        emotions=analysis.get("emotions", []), needs=analysis.get("needs", []),
        risk_level=analysis.get("risk_level", "green"), confidence=analysis.get("confidence", 0.5),
        confirmed_by_user=False,
    )
    db.add(diagnosis)
    case.risk_level = analysis.get("risk_level", case.risk_level)
    symptoms = analysis.get("symptoms", {})
    if symptoms.get("category") and symptoms["category"] != "other":
        case.category = symptoms["category"]
    if symptoms.get("frequency") and symptoms["frequency"] != "unknown":
        case.frequency = symptoms["frequency"]
    if symptoms.get("relationship") and symptoms["relationship"] != "unknown":
        case.relationship_status = symptoms["relationship"]
    case.status = "diagnosed"
    case.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(diagnosis)
    add_audit_log(db, current_user.id, "diagnose_case", "case", case_id, {"risk_level": diagnosis.risk_level, "confidence": diagnosis.confidence})
    return {
        "id": diagnosis.id, "facts": diagnosis.facts, "assumptions": diagnosis.assumptions,
        "emotions": diagnosis.emotions, "needs": diagnosis.needs, "risk_level": diagnosis.risk_level,
        "confidence": diagnosis.confidence, "confirmed_by_user": diagnosis.confirmed_by_user,
        "summary": analysis.get("summary", ""), "insights": analysis.get("insights", []),
        "key_questions": analysis.get("key_questions", []),
    }


# ================================================================================
# 21. Cases: Confirm / Edit Diagnosis
# ================================================================================
@app.post("/api/cases/{case_id}/diagnose/confirm")
def confirm_diagnosis(case_id: int, body: DiagnosisConfirm, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")
    if current_user.role == "resident" and case.resident_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此案件")
    diagnosis = db.query(Diagnosis).filter(Diagnosis.case_id == case_id).order_by(Diagnosis.created_at.desc()).first()
    if not diagnosis:
        raise HTTPException(status_code=404, detail="尚未进行诊断")
    if body.facts is not None:
        diagnosis.facts = body.facts
    if body.assumptions is not None:
        diagnosis.assumptions = body.assumptions
    if body.emotions is not None:
        diagnosis.emotions = body.emotions
    if body.needs is not None:
        diagnosis.needs = body.needs
    if body.risk_level is not None:
        diagnosis.risk_level = body.risk_level
        if body.risk_level != case.risk_level:
            case.risk_level = body.risk_level
    diagnosis.confirmed_by_user = True
    case.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(diagnosis)
    add_audit_log(db, current_user.id, "confirm_diagnosis", "case", case_id)
    return {"id": diagnosis.id, "facts": diagnosis.facts, "assumptions": diagnosis.assumptions, "emotions": diagnosis.emotions, "needs": diagnosis.needs, "risk_level": diagnosis.risk_level, "confidence": diagnosis.confidence, "confirmed_by_user": diagnosis.confirmed_by_user}


# ================================================================================
# 22. Cases: Generate Action Plan
# ================================================================================
@app.post("/api/cases/{case_id}/plan")
def create_action_plan(case_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")
    if current_user.role == "resident" and case.resident_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此案件")
    plan_data = generate_action_plan(case.risk_level)
    plan = ActionPlan(
        case_id=case_id, target=plan_data.get("target", ""), steps=plan_data.get("steps", []),
        communication_method=plan_data.get("communication_method", ""),
        escalation_condition=plan_data.get("escalation", ""),
        safety_reminder=plan_data.get("safety_reminder"), status="pending",
    )
    db.add(plan)
    case.status = "in_progress"
    case.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(plan)
    add_audit_log(db, current_user.id, "create_action_plan", "case", case_id)
    return {"id": plan.id, "target": plan.target, "steps": plan.steps, "communication_method": plan.communication_method, "escalation_condition": plan.escalation_condition, "safety_reminder": plan.safety_reminder, "status": plan.status, "dont_do": plan_data.get("don't_do", [])}


# ================================================================================
# 23. Cases: List Action Plans
# ================================================================================
@app.get("/api/cases/{case_id}/plans")
def list_action_plans(case_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")
    if current_user.role == "resident" and case.resident_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此案件")
    plans = db.query(ActionPlan).filter(ActionPlan.case_id == case_id).order_by(ActionPlan.created_at.desc()).all()
    return [{"id": p.id, "target": p.target, "steps": p.steps, "communication_method": p.communication_method, "escalation_condition": p.escalation_condition, "safety_reminder": p.safety_reminder, "status": p.status, "created_at": p.created_at.isoformat() if p.created_at else None} for p in plans]


# ================================================================================
# 24. Cases: Generate Communication Message
# ================================================================================
@app.post("/api/cases/{case_id}/messages/generate")
def generate_case_message(case_id: int, body: MessageGenerateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")
    if current_user.role == "resident" and case.resident_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此案件")
    if body.user_content:
        content = body.user_content
    else:
        default_replacements = {"direction": "楼上/隔壁", "time": "最近", "fact": case.description[:50] if case.description else "描述的问题", "impact": "对生活的影响", "request": "希望改善", "previous_attempt": "曾尝试口头沟通"}
        if body.replacements:
            default_replacements.update(body.replacements)
        content = generate_message(body.type, default_replacements)
    msg = Message(case_id=case_id, type=body.type, tone=body.tone or "neutral", content=content, is_sent=False)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    add_audit_log(db, current_user.id, "generate_message", "case", case_id, {"type": body.type})
    return {"id": msg.id, "type": msg.type, "tone": msg.tone, "content": msg.content, "is_sent": msg.is_sent, "created_at": msg.created_at.isoformat() if msg.created_at else None}


# ================================================================================
# 25. Cases: List Messages
# ================================================================================
@app.get("/api/cases/{case_id}/messages")
def list_case_messages(case_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")
    if current_user.role == "resident" and case.resident_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此案件")
    messages = db.query(Message).filter(Message.case_id == case_id).order_by(Message.created_at.desc()).all()
    return [{"id": m.id, "type": m.type, "tone": m.tone, "content": m.content, "is_sent": m.is_sent, "created_at": m.created_at.isoformat() if m.created_at else None} for m in messages]


# ================================================================================
# 26. Cases: Start Simulation
# ================================================================================
@app.post("/api/cases/{case_id}/simulations")
def start_simulation(case_id: int, body: SimulationCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")
    if current_user.role == "resident" and case.resident_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此案件")
    style = body.counterpart_style
    if style == "defensive":
        initial_response = "你谁啊？找我什么事？我什么都没做啊，你是不是搞错了？"
    elif style == "cooperative":
        initial_response = "哦，你好你好。有什么事吗？咱们可以好好聊聊。"
    elif style == "avoidant":
        initial_response = "嗯……我现在有点忙，有什么事能不能改天再说？"
    else:
        initial_response = "你好，有什么事？"
    conversation = [{"role": "counterpart", "content": initial_response, "timestamp": datetime.utcnow().isoformat()}]
    sim = Simulation(case_id=case_id, role=body.role, counterpart_style=body.counterpart_style, conversation=conversation, score=None, feedback=None)
    db.add(sim)
    db.commit()
    db.refresh(sim)
    add_audit_log(db, current_user.id, "start_simulation", "simulation", sim.id)
    return {"id": sim.id, "case_id": sim.case_id, "role": sim.role, "counterpart_style": sim.counterpart_style, "conversation": sim.conversation, "score": sim.score, "feedback": sim.feedback, "created_at": sim.created_at.isoformat() if sim.created_at else None}


# ================================================================================
# 27. Cases: Send Simulation Message
# ================================================================================
@app.post("/api/cases/{case_id}/simulations/{sim_id}/messages")
def send_simulation_message(case_id: int, sim_id: int, body: SimulationMessage, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")
    sim = db.query(Simulation).filter(Simulation.id == sim_id, Simulation.case_id == case_id).first()
    if not sim:
        raise HTTPException(status_code=404, detail="模拟记录不存在")
    conversation = sim.conversation or []
    user_msg = {"role": "user", "content": body.content, "timestamp": datetime.utcnow().isoformat()}
    conversation.append(user_msg)
    style = sim.counterpart_style
    uc = body.content
    if style == "defensive":
        if any(w in uc for w in ["请", "谢谢", "理解", "商量"]):
            counterpart_reply = "嗯……你说的也不是完全没道理，但是我觉得这事也不能全怪我吧？让我想想。"
        elif any(w in uc for w in ["总是", "每次", "一直"]):
            counterpart_reply = "什么总是？哪有每次？你说话能不能别这么夸张？"
        else:
            counterpart_reply = "行吧，我听到了。但是这也不是我故意的啊，你也不能光说我吧？"
    elif style == "cooperative":
        if any(w in uc for w in ["请", "谢谢", "希望", "商量"]):
            counterpart_reply = "好的，我理解了。确实是我没注意到，我会注意改进的。咱们一起想想办法？"
        else:
            counterpart_reply = "嗯，我听到了你的想法。谢谢你告诉我，咱们可以一起商量一个解决方案。"
    elif style == "avoidant":
        if any(w in uc for w in ["重要", "影响很大", "必须"]):
            counterpart_reply = "哎呀，我知道了知道了。但是我现在真的很忙，回头再说好不好？"
        else:
            counterpart_reply = "嗯……好吧。这个……我再考虑考虑吧。"
    else:
        counterpart_reply = "好的，我听到了，我会考虑的。"
    counterpart_msg = {"role": "counterpart", "content": counterpart_reply, "timestamp": datetime.utcnow().isoformat()}
    conversation.append(counterpart_msg)
    score = 5.0
    suggestions: List[str] = []
    if any(w in uc for w in ["请", "谢谢", "理解", "商量", "希望"]):
        score += 2.0
        suggestions.append("使用了礼貌用语，态度友善")
    if any(w in uc for w in ["总是", "每次", "一直", "从不"]):
        score -= 1.5
        suggestions.append("避免使用绝对化表述（如'总是''每次'），这容易引发对方防御")
    if len(uc) > 20:
        score += 0.5
    if "我" in uc and ("觉得" in uc or "感受" in uc or "希望" in uc):
        score += 1.5
        suggestions.append("使用了'我'开头的表达方式，很好")
    if "你" in uc and any(w in uc for w in ["不对", "错", "问题"]):
        score -= 1.0
        suggestions.append("尝试减少指责性语言，改用描述事实的方式")
    if not suggestions:
        suggestions.append("继续保持冷静和客观的表达")
    suggestions.append("可以尝试提出一个具体的、可操作的小请求")
    score = max(0.0, min(10.0, score))
    feedback = {"score": round(score, 1), "suggestions": suggestions, "round": len([m for m in conversation if m["role"] == "user"])}
    sim.conversation = conversation
    sim.score = round(score, 1)
    sim.feedback = feedback
    db.commit()
    db.refresh(sim)
    return {"id": sim.id, "conversation": sim.conversation, "score": sim.score, "feedback": sim.feedback}


# ================================================================================
# 28. Cases: Create Follow-up
# ================================================================================
@app.post("/api/cases/{case_id}/followups")
def create_followup(case_id: int, body: FollowUpCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")
    if current_user.role == "resident" and case.resident_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此案件")
    followup = FollowUp(case_id=case_id, action_taken=body.action_taken, response_received=body.response_received, improvement_level=body.improvement_level, is_escalated=body.is_escalated)
    db.add(followup)
    if body.is_escalated:
        case.status = "escalated"
    case.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(followup)
    add_audit_log(db, current_user.id, "create_followup", "case", case_id, {"improvement_level": body.improvement_level, "is_escalated": body.is_escalated})
    return {"id": followup.id, "case_id": followup.case_id, "action_taken": followup.action_taken, "response_received": followup.response_received, "improvement_level": followup.improvement_level, "is_escalated": followup.is_escalated, "created_at": followup.created_at.isoformat() if followup.created_at else None}


# ================================================================================
# 29. Cases: List Follow-ups
# ================================================================================
@app.get("/api/cases/{case_id}/followups")
def list_followups(case_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")
    if current_user.role == "resident" and case.resident_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此案件")
    followups = db.query(FollowUp).filter(FollowUp.case_id == case_id).order_by(FollowUp.created_at.desc()).all()
    return [{"id": f.id, "case_id": f.case_id, "action_taken": f.action_taken, "response_received": f.response_received, "improvement_level": f.improvement_level, "is_escalated": f.is_escalated, "created_at": f.created_at.isoformat() if f.created_at else None} for f in followups]


# ================================================================================
# 30. Cases: Escalate
# ================================================================================
@app.post("/api/cases/{case_id}/escalate")
def escalate_case(case_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="案件不存在")
    if current_user.role == "resident" and case.resident_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权操作此案件")
    old_status = case.status
    case.status = "escalated"
    if case.risk_level in ("green", "yellow"):
        case.risk_level = "orange"
    case.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(case)
    add_audit_log(db, current_user.id, "escalate_case", "case", case_id, {"old_status": old_status, "new_status": "escalated"})
    return {"detail": "案件已升级", "case_id": case.id, "status": case.status, "risk_level": case.risk_level}


# ================================================================================
# 31. Groups: List (nearby)
# ================================================================================
@app.get("/api/groups")
def list_groups(db: Session = Depends(get_db), current_user: User = Depends(get_current_user), lat: Optional[float] = Query(None), lng: Optional[float] = Query(None), radius_km: Optional[float] = Query(None)):
    import math
    query = db.query(CommunityGroup).filter(CommunityGroup.status == "active")
    groups = query.all()
    if lat is not None and lng is not None:
        filtered = []
        max_radius = radius_km or 10.0
        for g in groups:
            if g.center_lat is not None and g.center_lng is not None:
                dist = math.sqrt((g.center_lat - lat) ** 2 + (g.center_lng - lng) ** 2) * 111.0
                if dist <= max_radius:
                    filtered.append(g)
            else:
                filtered.append(g)
        groups = filtered
    return [{"id": g.id, "name": g.name, "description": g.description, "center_lat": g.center_lat, "center_lng": g.center_lng, "radius_km": g.radius_km, "owner_id": g.owner_id, "group_type": g.group_type, "status": g.status, "member_count": g.member_count, "tags": g.tags, "created_at": g.created_at.isoformat() if g.created_at else None} for g in groups]


# ================================================================================
# 32. Groups: My Groups
# ================================================================================
@app.get("/api/groups/my")
def my_groups(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    memberships = db.query(GroupMember).filter(GroupMember.user_id == current_user.id).all()
    group_ids = [m.group_id for m in memberships]
    groups = db.query(CommunityGroup).filter(CommunityGroup.id.in_(group_ids)).all() if group_ids else []
    result = []
    for g in groups:
        member = next((m for m in memberships if m.group_id == g.id), None)
        result.append({"id": g.id, "name": g.name, "description": g.description, "group_type": g.group_type, "status": g.status, "member_count": g.member_count, "tags": g.tags, "my_role": member.role if member else "member", "my_nickname": member.nickname if member else None, "joined_at": member.joined_at.isoformat() if member and member.joined_at else None})
    return result


# ================================================================================
# 33. Groups: Detail
# ================================================================================
@app.get("/api/groups/{group_id}")
def get_group_detail(group_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    group = db.query(CommunityGroup).filter(CommunityGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="群组不存在")
    is_member = db.query(GroupMember).filter(GroupMember.group_id == group_id, GroupMember.user_id == current_user.id).first() is not None
    topics = db.query(GroupTopic).filter(GroupTopic.group_id == group_id).all()
    members_count = db.query(GroupMember).filter(GroupMember.group_id == group_id).count()
    return {"id": group.id, "name": group.name, "description": group.description, "center_lat": group.center_lat, "center_lng": group.center_lng, "radius_km": group.radius_km, "owner_id": group.owner_id, "group_type": group.group_type, "status": group.status, "member_count": members_count, "tags": group.tags, "is_member": is_member, "topics": [{"id": t.id, "name": t.name, "description": t.description, "is_default": t.is_default} for t in topics], "created_at": group.created_at.isoformat() if group.created_at else None}


# ================================================================================
# 34. Groups: Create
# ================================================================================
@app.post("/api/groups")
def create_group(body: GroupCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    group = CommunityGroup(name=body.name, description=body.description, center_lat=body.center_lat, center_lng=body.center_lng, radius_km=body.radius_km, owner_id=current_user.id, group_type=body.group_type, tags=body.tags, member_count=1)
    db.add(group)
    db.flush()
    member = GroupMember(group_id=group.id, user_id=current_user.id, role="owner", nickname=current_user.display_name or current_user.username)
    db.add(member)
    db.commit()
    db.refresh(group)
    add_audit_log(db, current_user.id, "create_group", "group", group.id, {"name": group.name})
    return {"id": group.id, "name": group.name, "description": group.description, "owner_id": group.owner_id, "group_type": group.group_type, "member_count": group.member_count, "tags": group.tags, "created_at": group.created_at.isoformat() if group.created_at else None}


# ================================================================================
# 35. Groups: Update
# ================================================================================
@app.put("/api/groups/{group_id}")
def update_group(group_id: int, body: GroupUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    group = db.query(CommunityGroup).filter(CommunityGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="群组不存在")
    if group.owner_id != current_user.id and current_user.role != "staff":
        raise HTTPException(status_code=403, detail="无权修改此群组")
    update_data = body.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(group, key, value)
    db.commit()
    db.refresh(group)
    add_audit_log(db, current_user.id, "update_group", "group", group_id, update_data)
    return {"id": group.id, "name": group.name, "description": group.description, "group_type": group.group_type, "status": group.status, "tags": group.tags}


# ================================================================================
# 36. Groups: Join
# ================================================================================
@app.post("/api/groups/{group_id}/join")
def join_group(group_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user), nickname: Optional[str] = None):
    group = db.query(CommunityGroup).filter(CommunityGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="群组不存在")
    existing = db.query(GroupMember).filter(GroupMember.group_id == group_id, GroupMember.user_id == current_user.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="已是群组成员")
    member = GroupMember(group_id=group_id, user_id=current_user.id, role="member", nickname=nickname or current_user.display_name or current_user.username)
    db.add(member)
    group.member_count = (group.member_count or 0) + 1
    db.commit()
    add_audit_log(db, current_user.id, "join_group", "group", group_id)
    return {"detail": "已加入群组", "group_id": group_id}


# ================================================================================
# 37. Groups: Leave
# ================================================================================
@app.post("/api/groups/{group_id}/leave")
def leave_group(group_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    group = db.query(CommunityGroup).filter(CommunityGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="群组不存在")
    member = db.query(GroupMember).filter(GroupMember.group_id == group_id, GroupMember.user_id == current_user.id).first()
    if not member:
        raise HTTPException(status_code=400, detail="不是群组成员")
    db.delete(member)
    group.member_count = max(0, (group.member_count or 1) - 1)
    db.commit()
    add_audit_log(db, current_user.id, "leave_group", "group", group_id)
    return {"detail": "已离开群组", "group_id": group_id}


# ================================================================================
# 38. Groups: Members
# ================================================================================
@app.get("/api/groups/{group_id}/members")
def list_group_members(group_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    group = db.query(CommunityGroup).filter(CommunityGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="群组不存在")
    members = db.query(GroupMember).filter(GroupMember.group_id == group_id).all()
    result = []
    for m in members:
        user = db.query(User).filter(User.id == m.user_id).first()
        result.append({"id": m.id, "user_id": m.user_id, "role": m.role, "nickname": m.nickname, "display_name": user.display_name if user else None, "joined_at": m.joined_at.isoformat() if m.joined_at else None})
    return result


# ================================================================================
# 39. Groups: Topics
# ================================================================================
@app.get("/api/groups/{group_id}/topics")
def list_group_topics(group_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    group = db.query(CommunityGroup).filter(CommunityGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="群组不存在")
    topics = db.query(GroupTopic).filter(GroupTopic.group_id == group_id).order_by(GroupTopic.created_at.desc()).all()
    return [{"id": t.id, "name": t.name, "description": t.description, "is_default": t.is_default, "created_at": t.created_at.isoformat() if t.created_at else None} for t in topics]


# ================================================================================
# 40. Groups: Create Topic
# ================================================================================
@app.post("/api/groups/{group_id}/topics")
def create_group_topic(group_id: int, body: GroupTopicCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    group = db.query(CommunityGroup).filter(CommunityGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="群组不存在")
    member = db.query(GroupMember).filter(GroupMember.group_id == group_id, GroupMember.user_id == current_user.id).first()
    if not member:
        raise HTTPException(status_code=403, detail="非群组成员不能创建话题")
    topic = GroupTopic(group_id=group_id, name=body.name, description=body.description, is_default=body.is_default)
    db.add(topic)
    db.commit()
    db.refresh(topic)
    add_audit_log(db, current_user.id, "create_topic", "topic", topic.id, {"group_id": group_id})
    return {"id": topic.id, "name": topic.name, "description": topic.description, "is_default": topic.is_default, "group_id": topic.group_id, "created_at": topic.created_at.isoformat() if topic.created_at else None}


# ================================================================================
# 41. Groups: Chat History
# ================================================================================
@app.get("/api/groups/{group_id}/chat/history")
def get_chat_history(group_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user), topic_id: Optional[int] = Query(None), limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    group = db.query(CommunityGroup).filter(CommunityGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="群组不存在")
    query = db.query(ChatMessage).filter(ChatMessage.group_id == group_id)
    if topic_id is not None:
        query = query.filter(ChatMessage.topic_id == topic_id)
    messages = query.order_by(ChatMessage.created_at.desc()).offset(offset).limit(limit).all()
    messages = list(reversed(messages))
    result = []
    for m in messages:
        sender = db.query(User).filter(User.id == m.sender_id).first()
        result.append({"id": m.id, "group_id": m.group_id, "topic_id": m.topic_id, "sender_id": m.sender_id, "sender_name": (sender.display_name or sender.username) if sender else "未知", "message_type": m.message_type, "content": m.content, "reply_to_id": m.reply_to_id, "is_agent": m.is_agent, "agent_name": m.agent_name, "agent_session_id": m.agent_session_id, "created_at": m.created_at.isoformat() if m.created_at else None})
    return result


# ================================================================================
# 42. Groups: Send Chat Message (with agent trigger)
# ================================================================================
@app.post("/api/groups/{group_id}/chat/messages")
def send_chat_message(group_id: int, body: ChatMessageCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    group = db.query(CommunityGroup).filter(CommunityGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="群组不存在")
    member = db.query(GroupMember).filter(GroupMember.group_id == group_id, GroupMember.user_id == current_user.id).first()
    if not member:
        raise HTTPException(status_code=403, detail="非群组成员不能发送消息")
    chat_msg = ChatMessage(group_id=group_id, topic_id=body.topic_id, sender_id=current_user.id, message_type=body.message_type, content=body.content, reply_to_id=body.reply_to_id, is_agent=False)
    db.add(chat_msg)
    db.commit()
    db.refresh(chat_msg)
    result = {"id": chat_msg.id, "group_id": chat_msg.group_id, "topic_id": chat_msg.topic_id, "sender_id": chat_msg.sender_id, "sender_name": current_user.display_name or current_user.username, "message_type": chat_msg.message_type, "content": chat_msg.content, "reply_to_id": chat_msg.reply_to_id, "is_agent": False, "created_at": chat_msg.created_at.isoformat() if chat_msg.created_at else None}
    # Check for agent trigger
    recent_messages = db.query(ChatMessage).filter(ChatMessage.group_id == group_id, ChatMessage.topic_id == body.topic_id).order_by(ChatMessage.created_at.desc()).limit(20).all()
    recent_contents = [{"content": m.content} for m in recent_messages]
    trigger_result = match_trigger(body.content)
    if trigger_result:
        agent_name = trigger_result["agent"]
        agent = get_agent(agent_name, db)
        agent_response = agent.respond(body.content, {"recent_messages": recent_contents})
        if agent_response:
            agent_session = db.query(AgentSession).filter(AgentSession.group_id == group_id, AgentSession.topic_id == body.topic_id, AgentSession.agent_name == agent_name, AgentSession.status == "active").first()
            if not agent_session:
                agent_session = AgentSession(group_id=group_id, topic_id=body.topic_id, agent_name=agent_name, trigger_type="explicit" if trigger_result.get("explicit") else "implicit", context={"trigger_keyword": trigger_result.get("matched_keyword")}, status="active")
                db.add(agent_session)
                db.flush()
            agent_msg = ChatMessage(group_id=group_id, topic_id=body.topic_id, sender_id=current_user.id, message_type="agent", content=agent_response, is_agent=True, agent_name=agent_name, agent_session_id=str(agent_session.id))
            db.add(agent_msg)
            db.commit()
            db.refresh(agent_msg)
            result["agent_response"] = {"id": agent_msg.id, "content": agent_msg.content, "agent_name": agent_name, "agent_session_id": agent_msg.agent_session_id, "created_at": agent_msg.created_at.isoformat() if agent_msg.created_at else None}
    return result


# ================================================================================
# 43. Groups: Audit Logs
# ================================================================================
@app.get("/api/groups/{group_id}/audit")
def get_group_audit_logs(group_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user), limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    group = db.query(CommunityGroup).filter(CommunityGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="群组不存在")
    if current_user.role != "staff" and group.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权查看审计日志")
    logs = db.query(AuditLog).filter(AuditLog.target_type.in_(["group", "topic", "chat_message"]), AuditLog.target_id == group_id).order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
    topic_ids = [t.id for t in db.query(GroupTopic).filter(GroupTopic.group_id == group_id).all()]
    if topic_ids:
        topic_logs = db.query(AuditLog).filter(AuditLog.target_id.in_(topic_ids)).order_by(AuditLog.created_at.desc()).limit(limit).all()
        logs = sorted(list(logs) + list(topic_logs), key=lambda x: x.created_at or datetime.min, reverse=True)[:limit]
    return [{"id": log.id, "user_id": log.user_id, "action": log.action, "target_type": log.target_type, "target_id": log.target_id, "detail": log.detail, "ip_address": log.ip_address, "created_at": log.created_at.isoformat() if log.created_at else None} for log in logs]


# ================================================================================
# 44. Agents: List
# ================================================================================
@app.get("/api/agents")
def list_agents():
    return [{"name": key, "display_name": info["name"], "emoji": info["emoji"], "description": info["description"]} for key, info in AGENT_INFO.items()]


# ================================================================================
# 45. Agent: Trigger
# ================================================================================
@app.post("/api/agent/trigger")
def trigger_agent(body: AgentTriggerRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    context = {}
    if body.group_id:
        recent = db.query(ChatMessage).filter(ChatMessage.group_id == body.group_id, ChatMessage.topic_id == body.topic_id).order_by(ChatMessage.created_at.desc()).limit(20).all()
        context["recent_messages"] = [{"content": m.content} for m in recent]
    trigger_result = match_trigger(body.message)
    if not trigger_result:
        return {"triggered": False, "message": "未触发任何智能体", "matched_keyword": None}
    agent_name = trigger_result["agent"]
    agent = get_agent(agent_name, db)
    response = agent.respond(body.message, context)
    return {"triggered": True, "agent_name": agent_name, "agent_display_name": AGENT_INFO.get(agent_name, {}).get("name", agent_name), "explicit": trigger_result.get("explicit", False), "matched_keyword": trigger_result.get("matched_keyword"), "response": response}


# ================================================================================
# 46. Community: Overview (staff)
# ================================================================================
@app.get("/api/community/overview")
def community_overview(db: Session = Depends(get_db), _: User = Depends(require_role("staff")), community_id: Optional[int] = Query(None)):
    query = db.query(Case)
    if community_id:
        query = query.filter(Case.community_id == community_id)
    total = query.count()
    by_risk = {}
    for level in ["green", "yellow", "orange", "red"]:
        by_risk[level] = query.filter(Case.risk_level == level).count()
    by_status = {}
    for s in ["draft", "diagnosed", "in_progress", "resolved", "escalated"]:
        by_status[s] = query.filter(Case.status == s).count()
    by_category = {}
    cases_list = query.all()
    for c in cases_list:
        cat = c.category or "other"
        by_category[cat] = by_category.get(cat, 0) + 1
    return {"total_cases": total, "by_risk_level": by_risk, "by_status": by_status, "by_category": by_category}


# ================================================================================
# 47. Community: Trends (staff)
# ================================================================================
@app.get("/api/community/trends")
def community_trends(db: Session = Depends(get_db), _: User = Depends(require_role("staff")), days: int = Query(30, ge=1, le=365), community_id: Optional[int] = Query(None)):
    from datetime import timedelta as td
    since = datetime.utcnow() - td(days=days)
    query = db.query(Case).filter(Case.created_at >= since)
    if community_id:
        query = query.filter(Case.community_id == community_id)
    cases_list = query.all()
    # Daily counts
    daily = {}
    for c in cases_list:
        day_key = c.created_at.strftime("%Y-%m-%d") if c.created_at else "unknown"
        daily[day_key] = daily.get(day_key, 0) + 1
    # Category trends
    cat_trend = {}
    for c in cases_list:
        cat = c.category or "other"
        cat_trend[cat] = cat_trend.get(cat, 0) + 1
    # Risk escalation count
    escalated = sum(1 for c in cases_list if c.status == "escalated")
    # Average resolution (simple count of resolved)
    resolved = sum(1 for c in cases_list if c.status == "resolved")
    return {"period_days": days, "total_new_cases": len(cases_list), "daily_counts": daily, "category_distribution": cat_trend, "escalated_count": escalated, "resolved_count": resolved}


# ================================================================================
# 48. WebSocket: Real-time Chat
# ================================================================================
@app.websocket("/ws/groups/{group_id}")
async def websocket_endpoint(websocket: WebSocket, group_id: str, token: str = Query(None)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except Exception:
        await websocket.close(code=4001)
        return
    await manager.connect(websocket, group_id, user_id)
    try:
        while True:
            data = await websocket.receive_json()
            data["sender_id"] = user_id
            data["timestamp"] = datetime.utcnow().isoformat()
            await manager.send_to_group(group_id, data)
    except WebSocketDisconnect:
        manager.disconnect(websocket, group_id, user_id)
