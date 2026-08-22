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
    improve_expression, build_final_version,
)
from agent import (
    match_trigger, get_agent, create_agent_response, AGENT_INFO,
)
from chat_ws import manager
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

# AI Ping (OpenAI-compatible) LLM Client
try:
    from openai import OpenAI as _OpenAI
    _ai_key = os.getenv("AI_API_KEY", "")
    _ai_base = os.getenv("AI_BASE_URL", "https://aiping.cn/api/v1")
    _ai_model = os.getenv("AI_MODEL", "deepseek-chat")
    _ai_vision = os.getenv("AI_VISION_MODEL", _ai_model)
    if _ai_key:
        llm_client = _OpenAI(api_key=_ai_key, base_url=_ai_base)
        LLM_ENABLED = True
        print(f"[AI] LLM enabled: {_ai_base} / model={_ai_model}")
    else:
        llm_client = None
        LLM_ENABLED = False
        print("[AI] No AI_API_KEY found, LLM disabled (rule-engine only)")
except Exception as _e:
    llm_client = None
    LLM_ENABLED = False
    print(f"[AI] LLM init failed: {_e}, falling back to rule-engine")


def llm_chat(system_prompt: str, user_message: str, temperature: float = 0.7, max_tokens: int = 2000) -> str:
    """通用 LLM 对话调用（AI Ping OpenAI-compatible API）"""
    if not llm_client:
        raise RuntimeError("LLM not configured")
    resp = llm_client.chat.completions.create(
        model=_ai_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content or ""


def llm_chat_messages(messages: list, temperature: float = 0.7, max_tokens: int = 2000) -> str:
    """多轮对话 LLM 调用"""
    if not llm_client:
        raise RuntimeError("LLM not configured")
    resp = llm_client.chat.completions.create(
        model=_ai_model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content or ""


def llm_vision(system_prompt: str, user_text: str, image_url: str, max_tokens: int = 1500) -> str:
    """多模态 LLM 调用（图片+文字）"""
    if not llm_client:
        raise RuntimeError("LLM not configured")
    resp = llm_client.chat.completions.create(
        model=_ai_vision,
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_text},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            },
        ],
        max_tokens=max_tokens,
    )
    return resp.choices[0].message.content or ""


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
    counterpart_reply: Optional[str] = None

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
    return {
        "status": "ok",
        "service": "NeighborGlow API",
        "timestamp": datetime.utcnow().isoformat(),
        "llm_enabled": LLM_ENABLED,
        "llm_model": _ai_model if LLM_ENABLED else None,
    }


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
        result["diagnosis"] = {"id": diagnosis.id, "facts": diagnosis.facts, "assumptions": diagnosis.assumptions, "emotions": diagnosis.emotions, "needs": diagnosis.needs, "risk_level": diagnosis.risk_level, "confidence": diagnosis.confidence, "confirmed_by_user": diagnosis.confirmed_by_user, "summary": diagnosis.summary, "insights": diagnosis.insights, "key_questions": diagnosis.key_questions, "safety_risks": diagnosis.safety_risks, "analysis_type": diagnosis.analysis_type}
    plan = db.query(ActionPlan).filter(ActionPlan.case_id == case_id).order_by(ActionPlan.created_at.desc()).first()
    if plan:
        generated = generate_action_plan(case.risk_level)
        result["action_plan"] = {"id": plan.id, "target": plan.target, "steps": plan.steps, "communication_method": plan.communication_method, "escalation_condition": plan.escalation_condition, "safety_reminder": plan.safety_reminder, "status": plan.status, "fact_record": generated.get("fact_record"), "next_step": generated.get("next_step"), "dont_do": generated.get("dont_do")}
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

    # 优先使用 LLM 诊断
    use_llm = False
    if LLM_ENABLED:
        try:
            rule_result = analyze_context(description)  # 规则引擎兜底
            system = """你是邻里纠纷调解平台的AI诊断专家。请深入分析用户描述的邻里纠纷问题。

你需要返回一个完整的JSON分析报告，格式如下：
{
  "risk_level": "green 或 yellow 或 orange 或 red",
  "summary": "一句话总结核心问题",
  "facts": ["客观事实1", "客观事实2", "客观事实3"],
  "assumptions": ["需要验证的假设1", "假设2"],
  "emotions": ["涉及的情绪1", "情绪2"],
  "needs": ["潜在需求1", "需求2"],
  "insights": ["深层洞察1", "洞察2", "洞察3"],
  "key_questions": ["需要进一步了解的问题1", "问题2"],
  "safety_risks": ["安全风险（如有）"],
  "confidence": 0.85
}

分析原则：
1. risk_level 判断标准：green=轻微摩擦可自行解决, yellow=需要沟通可能影响关系, orange=持续困扰需介入, red=严重冲突有安全隐患
2. 区分事实与假设
3. 关注情绪背后的需求
4. 只返回JSON，不要其他内容"""
            result_text = llm_chat(system, description, temperature=0.5, max_tokens=2000)
            import json as _json
            clean = result_text.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[-1] if "\n" in clean else clean[3:]
            if clean.endswith("```"):
                clean = clean[:-3]
            clean = clean.strip()
            analysis = _json.loads(clean)
            analysis["symptoms"] = rule_result.get("symptoms", {})
            if not analysis.get("safety_risks"):
                analysis["safety_risks"] = rule_result.get("safety_risks", [])
            use_llm = True
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[AI] LLM diagnosis failed, falling back to rule engine: {e}")
            analysis = analyze_context(description)
    else:
        analysis = analyze_context(description)

    diagnosis = Diagnosis(
        case_id=case_id, facts=analysis.get("facts", []), assumptions=analysis.get("assumptions", []),
        emotions=analysis.get("emotions", []), needs=analysis.get("needs", []),
        risk_level=analysis.get("risk_level", "green"), confidence=analysis.get("confidence", 0.5),
        confirmed_by_user=False,
        summary=analysis.get("summary", ""), insights=analysis.get("insights", []),
        key_questions=analysis.get("key_questions", []),
        symptoms=analysis.get("symptoms", []), safety_risks=analysis.get("safety_risks", []),
        analysis_type="llm" if use_llm else "rule",
    )
    db.add(diagnosis)
    case.risk_level = analysis.get("risk_level", case.risk_level)
    symptoms = analysis.get("symptoms", {})
    if isinstance(symptoms, dict):
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
        "analysis_type": "llm" if use_llm else "rule",
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
    return {"id": plan.id, "target": plan.target, "steps": plan.steps, "communication_method": plan.communication_method, "escalation_condition": plan.escalation_condition, "safety_reminder": plan.safety_reminder, "status": plan.status, "dont_do": plan_data.get("dont_do", []), "fact_record": plan_data.get("fact_record"), "next_step": plan_data.get("next_step")}


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
    if case.risk_level == "red":
        raise HTTPException(status_code=400, detail="该案例涉及安全风险，请先完成安全响应流程，再进行模拟训练")
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
    conversation = list(sim.conversation or [])
    uc = body.content

    # ---- PRD 11.6: [END] 结束信号 —— 不写入对话，聚合逐轮反馈并产出最终沟通版本 ----
    if uc.strip() == "[END]":
        existing = sim.feedback if isinstance(sim.feedback, dict) else {}
        history = existing.get("history", [])
        rounds = len(history)
        avg = round(sum(h.get("score", 5.0) for h in history) / rounds, 1) if rounds else 5.0
        merged: List[str] = []
        for h in history:
            for s in (h.get("suggestions") or []):
                if s not in merged:
                    merged.append(s)
        if not merged:
            merged = ["整体表达平稳，继续保持冷静和客观的语气"]
        final_version = build_final_version(case.description, case.category)
        sim.score = avg
        sim.feedback = {"history": history, "avg_score": avg, "final": True}
        db.commit()
        db.refresh(sim)
        add_audit_log(db, current_user.id, "end_simulation", "simulation", sim.id, {"score": avg, "rounds": rounds})
        return {"id": sim.id, "final": True, "conversation": sim.conversation, "score": avg,
                "feedback": merged, "final_version": final_version, "rounds": rounds}

    user_msg = {"role": "user", "content": body.content, "timestamp": datetime.utcnow().isoformat()}
    conversation.append(user_msg)
    style = sim.counterpart_style
    if body.counterpart_reply:
        # LLM 模式下前端传入真实的对方回复，保证存档对话与实际训练一致
        counterpart_reply = body.counterpart_reply
    elif style == "defensive":
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
        suggestions.append("表达平稳，继续保持冷静和客观的语气")
    score = max(0.0, min(10.0, score))
    # PRD 11.6: 每轮表达获得具体反馈和优化版本
    improved = improve_expression(uc)
    round_num = len([m for m in conversation if m["role"] == "user"])
    feedback = {"score": round(score, 1), "suggestions": suggestions, "round": round_num, "improved_version": improved}
    existing = sim.feedback if isinstance(sim.feedback, dict) else {}
    history = existing.get("history", []) if not existing.get("final") else []
    history.append(feedback)
    avg = round(sum(h.get("score", 5.0) for h in history) / len(history), 1)
    sim.conversation = list(conversation)
    sim.score = avg
    sim.feedback = {"history": list(history), "avg_score": avg}
    db.commit()
    db.refresh(sim)
    return {"id": sim.id, "conversation": sim.conversation, "score": round(score, 1), "avg_score": avg, "feedback": feedback}


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


# ================================================================================
# 49. AI: Chat (LLM-powered conversation)
# ================================================================================
@app.post("/api/ai/chat")
def ai_chat(data: dict, current_user: User = Depends(get_current_user)):
    """通用 AI 对话接口（支持多轮对话）"""
    if not LLM_ENABLED:
        # 降级：无 LLM 密钥时返回友好提示而非报错
        return {
            "reply": "AI 助手暂时不在线（未配置 AI_API_KEY），您可以先提交问题描述，我们会安排人工跟进。",
            "model": None,
        }

    messages = data.get("messages", [])
    system_prompt = data.get("system", "你是邻光社区纠纷调解平台的AI助手，专业、温暖、善于倾听。品牌口号：邻里之光，让善意照进千万人家！")
    context = data.get("context", "")

    full_messages = [{"role": "system", "content": system_prompt}]

    # 添加案例上下文（如果有）
    if context:
        full_messages.append({"role": "system", "content": f"案例背景：{context}"})

    # 添加历史消息
    for msg in messages[-10:]:  # 最多保留最近10轮
        full_messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})

    try:
        reply = llm_chat_messages(full_messages, temperature=0.7, max_tokens=1500)
        return {"reply": reply, "model": _ai_model}
    except Exception as e:
        raise HTTPException(500, f"AI 调用失败: {str(e)}")


# ================================================================================
# 49.5. AI: Chat-Submit (引导对话 + 意图检测 + 案例创建准备)
# ================================================================================
def _chat_submit_fallback(messages: list, user_input: str) -> dict:
    """规则引擎智能兜底：根据已收集的信息给出针对性回复，避免千篇一律的模板话术。"""
    uc = user_input or ""
    analysis = analyze_context(uc)
    symptoms = analysis.get("symptoms", {}) if isinstance(analysis, dict) else {}
    category = symptoms.get("category") or classify_category(uc)
    freq = symptoms.get("frequency") or detect_frequency(uc)
    emotions = detect_emotions(uc)
    _has_safety, safety = detect_safety(uc)
    if not isinstance(safety, list):
        safety = []

    cat_labels = {"noise": "噪音", "parking": "停车", "pet": "宠物", "renovation": "装修施工",
                  "leak": "漏水", "garbage": "卫生", "public_space": "公共区域", "wechat": "微信群"}
    freq_labels = {"daily": "几乎每天", "weekly": "每周几次", "occasional": "偶尔发生", "once": "只发生过一次"}
    user_turns = len([m for m in messages if m.get("role") == "user"])

    # 安全风险最高优先级
    if safety:
        return {
            "reply": "🚨 你描述的情况可能涉及人身安全，请优先保护好自己和家人，必要时直接拨打 110。在不冲突的前提下，先用手机记录时间、声音或现场情况作为证据。需要我帮你把这个情况建档跟进吗？",
            "ready_to_create": user_turns >= 1,
            "case_title": uc[:20] or "安全风险事件",
            "case_summary": "、".join(safety[:2]),
            "category": category if category != "other" else "other",
            "action_suggestions": ["确保人身安全", "拨打 110 / 12345", "录音录像留证"],
        }

    info_bits = []
    if category and category != "other":
        info_bits.append(cat_labels.get(category, "相关"))
    if freq and freq != "unknown":
        info_bits.append(freq_labels.get(freq, ""))
    enough = bool(info_bits) and len(uc) >= 12 and user_turns >= 2

    if enough:
        summary = f"{'、'.join([b for b in info_bits if b])}的邻里困扰，已影响到你的日常生活"
        return {
            "reply": "✅ 好的，情况我基本记下了。我帮你整理了一份案例摘要，确认无误就可以建档，之后我会给你一份 AI 诊断和行动建议 📋",
            "ready_to_create": True,
            "case_title": (cat_labels.get(category, "邻里") + "困扰")[:20],
            "case_summary": summary,
            "category": category,
            "action_suggestions": ["确认创建案例", "补充更多细节"],
        }

    # 信息不足：针对缺失项提问，且避免与历史回复重复
    prev_ai_texts = [m.get("content", "") for m in messages if m.get("role") == "assistant"]
    questions = []
    if not (category and category != "other"):
        questions.append("具体是发生了什么事呢？比如噪音、漏水、停车还是宠物问题 🤔")
    if not (freq and freq != "unknown"):
        questions.append("这种情况大概持续多久了？是每天都发生，还是偶尔出现？")
    if not emotions:
        questions.append("这件事对你的休息或生活造成了什么影响？")
    if not questions:
        questions.append("你之前有没有和对方或物业沟通过？效果怎么样？")
    q = questions[0]
    if any(q[:10] in t for t in prev_ai_texts) and len(questions) > 1:
        q = questions[1]
    empathy = "谢谢你告诉我这些 🤝" if user_turns >= 2 else "收到 🤝"
    return {
        "reply": f"{empathy} 为了帮你把情况梳理清楚，{q}",
        "ready_to_create": False,
        "case_title": None,
        "case_summary": None,
        "category": category if category != "other" else "other",
        "action_suggestions": ["📷 拍照留证", "📝 记录发生时间", "💬 尝试友善沟通"],
    }


@app.post("/api/ai/chat-submit")
def ai_chat_submit(data: dict, current_user: User = Depends(get_current_user)):
    """
    提交案例前的引导对话接口。
    分析用户输入意图，判断是否已收集足够信息来创建案例。
    返回：
      - reply: AI 的对话回复
      - ready_to_create: 是否已收集足够信息可以创建案例
      - case_summary: 如果 ready_to_create 为 true，返回案例摘要
    """
    messages = data.get("messages", [])
    # 当前用户最新输入
    user_input = data.get("user_input", "")

    # 如果 LLM 不可用，降级到规则引擎做智能意图判断
    if not LLM_ENABLED:
        return _chat_submit_fallback(messages, user_input)

    # LLM 模式：使用 LLM 分析对话意图
    system = """你是邻光社区纠纷调解平台的AI助手「邻光」。品牌口号：邻里之光，让善意照进千万人家！你的任务是引导居民描述他们遇到的邻里纠纷问题，并在收集到足够信息后准备创建案例。

你需要分析对话并判断当前状态：

1. **问候/闲聊**：用户只是打招呼、寒暄，没有描述具体问题
2. **正在描述问题但信息不足**：用户开始描述问题，但缺少关键信息（如时间、频率、影响等）
3. **信息足够**：用户已经提供了足够的纠纷描述

关键信息包括：
- 发生了什么问题（噪音、漏水、宠物、装修等）
- 什么时候发生的、频率如何
- 对用户造成了什么影响
- 用户的情绪状态

判断规则：
- 如果用户只是打招呼或问无关问题 → stage="greeting"
- 如果用户描述了问题但信息不完整 → stage="collecting"
- 如果用户提供了足够的问题描述（至少包含问题类型和影响）→ stage="ready"

输出格式（只返回JSON，不要任何多余文字）：
{
  "stage": "greeting" | "collecting" | "ready",
  "reply": "你对用户的回复内容（温暖、专业、引导性）",
  "case_title": "如果stage是ready，生成一个简短的案例标题（15字以内），否则为null",
  "case_summary": "如果stage是ready，生成案例摘要（30字以内），否则为null",
  "category": "推测的问题分类（noise/parking/pet/renovation/leak/garbage/public_space/wechat/other）",
  "action_suggestions": ["给用户的1-3条行动建议（每条10字以内，可含1个表情）"]
}

回复风格要求：
1. 温暖、专业、善于倾听，用「你」称呼用户，不要说教
2. 回复中自然地使用1-2个表情符号（如 😊🤝💡✅），让对话更亲切，但不要堆砌
3. 每一轮回复必须有实质内容：先共情确认用户说的具体细节，再提出一个最关键的追问，禁止重复之前说过的话
4. 如果用户的内容涉及敏感或隐私话题（如私密噪音），保持中立专业，聚焦于「声音干扰生活」这一事实层面，给出可操作的记录与沟通建议
5. action_suggestions 给出当前阶段用户立刻可以做的小事（如：记录发生时间、手机录音留证、先友善沟通一次、联系物业）"""

    full_messages = [{"role": "system", "content": system}]
    for msg in messages[-15:]:
        full_messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})

    try:
        result_text = llm_chat_messages(full_messages, temperature=0.7, max_tokens=1000)
        import json as _json
        import re as _re
        clean = result_text.strip()
        # 去掉 markdown 代码围栏
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[-1] if "\n" in clean else clean[3:]
        if clean.endswith("```"):
            clean = clean[:-3]
        clean = clean.strip()
        # 容错：从文本中提取第一个 JSON 对象（防止 LLM 输出多余前后缀）
        try:
            result = _json.loads(clean)
        except _json.JSONDecodeError:
            m = _re.search(r"\{[\s\S]*\}", clean)
            if not m:
                raise ValueError("LLM 输出中未找到 JSON")
            result = _json.loads(m.group(0))

        reply = result.get("reply") or ""
        if not reply:
            raise ValueError("LLM 输出缺少 reply 字段")
        suggestions = result.get("action_suggestions") or []
        if not isinstance(suggestions, list):
            suggestions = []
        return {
            "reply": reply,
            "ready_to_create": result.get("stage") == "ready",
            "case_title": result.get("case_title"),
            "case_summary": result.get("case_summary"),
            "category": result.get("category", "other"),
            "action_suggestions": suggestions[:3],
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[AI] chat-submit LLM failed, using smart fallback: {e}")
        # 降级：规则引擎智能兜底（针对性回复 + 表情 + 行动建议）
        return _chat_submit_fallback(messages, user_input)


# ================================================================================
# 50. AI: Image Analysis (multimodal vision)
# ================================================================================
@app.post("/api/cases/{case_id}/analyze-image")
def analyze_case_image(case_id: int, data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """分析案例相关图片（多模态AI）"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(404, "案例不存在")
    if current_user.role == "resident" and case.resident_id != current_user.id:
        raise HTTPException(403, "无权访问")

    image_data = data.get("image")  # base64 data URL: data:image/jpeg;base64,...
    user_text = data.get("text", "")

    if not image_data:
        raise HTTPException(400, "缺少图片数据")

    if not LLM_ENABLED:
        return {"analysis": "AI 功能未启用，图片已保存。", "model": None}

    system = """你是邻里纠纷调解平台的AI图片分析助手。用户上传了一张与邻里纠纷相关的照片。
请仔细观察照片内容，分析与纠纷相关的事实信息，返回JSON格式：
{
  "image_description": "照片内容的简要描述",
  "image_facts": ["从照片中观察到的事实1", "事实2"],
  "evidence_relevance": "高/中/低",
  "suggestions": ["基于照片的建议1", "建议2"]
}
只返回JSON，不要其他内容。"""

    try:
        result = llm_vision(system, user_text or "请分析这张照片", image_data)
        import json
        clean = result.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[-1] if "\n" in clean else clean[3:]
        if clean.endswith("```"):
            clean = clean[:-3]
        clean = clean.strip()
        try:
            parsed = json.loads(clean)
            return {"analysis": parsed, "raw": result, "model": _ai_vision}
        except json.JSONDecodeError:
            return {"analysis": result, "model": _ai_vision}
    except Exception as e:
        raise HTTPException(500, f"图片分析失败: {str(e)}")


# ================================================================================
# 51. AI: LLM-enhanced Diagnosis
# ================================================================================
@app.post("/api/cases/{case_id}/diagnose/llm")
def diagnose_case_llm(case_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """LLM 增强的AI诊断（替代纯规则引擎）"""
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(404, "案例不存在")
    if current_user.role == "resident" and case.resident_id != current_user.id:
        raise HTTPException(403, "无权访问")

    if not LLM_ENABLED:
        raise HTTPException(400, "AI 功能未启用")

    # 规则引擎兜底
    rule_result = analyze_context(case.description or "")

    system = """你是邻里纠纷调解平台的AI诊断专家。请深入分析用户描述的邻里纠纷问题。

你需要返回一个完整的JSON分析报告，格式如下：
{
  "risk_level": "green 或 yellow 或 orange 或 red",
  "summary": "一句话总结核心问题",
  "facts": ["客观事实1", "客观事实2", "客观事实3"],
  "assumptions": ["需要验证的假设1", "假设2"],
  "emotions": ["涉及的情绪1", "情绪2"],
  "needs": ["潜在需求1", "需求2"],
  "insights": ["深层洞察1", "洞察2", "洞察3"],
  "key_questions": ["需要进一步了解的问题1", "问题2"],
  "safety_risks": ["安全风险（如有）"],
  "confidence": 0.85,
  "recommendation": "初步建议方向"
}

分析原则：
1. risk_level 判断标准：
   - green：轻微摩擦，可自行解决
   - yellow：需要沟通，可能影响关系
   - orange：持续困扰，影响生活，需介入
   - red：严重冲突，有安全隐患，需紧急介入
2. 要区分事实与假设，标注需要验证的假设
3. 关注情绪背后的需求，而非表面冲突
4. 提出温暖且实用的建议

只返回JSON，不要其他内容。"""

    try:
        result = llm_chat(system, case.description or "", temperature=0.5, max_tokens=2000)
        import json
        clean = result.strip()
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[-1] if "\n" in clean else clean[3:]
        if clean.endswith("```"):
            clean = clean[:-3]
        clean = clean.strip()
        parsed = json.loads(clean)

        # 合并规则引擎的安全风险检测
        if "safety_risks" not in parsed or not parsed["safety_risks"]:
            parsed["safety_risks"] = rule_result.get("safety_risks", [])
        # 补充症状标签
        parsed["symptoms"] = rule_result.get("symptoms", [])

        # 保存诊断结果
        diagnosis = Diagnosis(
            case_id=case.id,
            risk_level=parsed.get("risk_level", "yellow"),
            summary=parsed.get("summary", ""),
            facts=parsed.get("facts", []),
            assumptions=parsed.get("assumptions", []),
            emotions=parsed.get("emotions", []),
            needs=parsed.get("needs", []),
            insights=parsed.get("insights", []),
            key_questions=parsed.get("key_questions", []),
            symptoms=parsed.get("symptoms", []),
            safety_risks=parsed.get("safety_risks", []),
            confidence=parsed.get("confidence", 0.8),
            analysis_type="llm",
        )
        db.add(diagnosis)
        db.commit()
        db.refresh(diagnosis)

        return {
            "id": diagnosis.id,
            "case_id": case.id,
            "risk_level": diagnosis.risk_level,
            "summary": diagnosis.summary,
            "facts": diagnosis.facts,
            "assumptions": diagnosis.assumptions,
            "emotions": diagnosis.emotions,
            "needs": diagnosis.needs,
            "insights": diagnosis.insights,
            "key_questions": diagnosis.key_questions,
            "safety_risks": diagnosis.safety_risks,
            "confidence": diagnosis.confidence,
            "analysis_type": "llm",
            "model": _ai_model,
        }
    except Exception as e:
        # LLM 失败时降级到规则引擎
        import traceback
        traceback.print_exc()
        return {
            "fallback": True,
            "error": str(e),
            "rule_result": rule_result,
        }
