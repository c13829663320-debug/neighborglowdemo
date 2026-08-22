from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./demo.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False)
    real_name = Column(String)
    phone = Column(String)
    display_name = Column(String)
    community_id = Column(Integer, ForeignKey("communities.id"), nullable=True)
    privacy_consent = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    community = relationship("Community")


class Community(Base):
    __tablename__ = "communities"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    address = Column(String)
    center_lat = Column(Float)
    center_lng = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)


class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, index=True)


class ServiceRequest(Base):
    __tablename__ = "service_requests"
    id = Column(Integer, primary_key=True, index=True)
    resident_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=False)
    content = Column(Text)
    status = Column(String, default="pending")
    handler_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    resident = relationship("User", foreign_keys=[resident_id])
    handler = relationship("User", foreign_keys=[handler_id])


class Case(Base):
    __tablename__ = "cases"
    id = Column(Integer, primary_key=True, index=True)
    resident_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=False)
    description = Column(Text)
    category = Column(String)
    frequency = Column(String)
    relationship_status = Column(String)
    expected_outcome = Column(String)
    risk_level = Column(String, default="green")
    status = Column(String, default="draft")
    assigned_staff_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    community_id = Column(Integer, ForeignKey("communities.id"), nullable=True)
    is_anonymous = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resident = relationship("User", foreign_keys=[resident_id])
    assigned_staff = relationship("User", foreign_keys=[assigned_staff_id])
    community = relationship("Community", foreign_keys=[community_id])


class Diagnosis(Base):
    __tablename__ = "diagnoses"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    facts = Column(JSON)
    assumptions = Column(JSON)
    emotions = Column(JSON)
    needs = Column(JSON)
    risk_level = Column(String)
    confidence = Column(Float, default=0.5)
    confirmed_by_user = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    case = relationship("Case")


class ActionPlan(Base):
    __tablename__ = "action_plans"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    target = Column(String)
    steps = Column(JSON)
    communication_method = Column(String)
    escalation_condition = Column(String)
    safety_reminder = Column(Text)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    case = relationship("Case")


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    type = Column(String)
    tone = Column(String)
    content = Column(Text)
    is_sent = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    case = relationship("Case")


class Simulation(Base):
    __tablename__ = "simulations"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    role = Column(String)
    counterpart_style = Column(String)
    conversation = Column(JSON)
    score = Column(Float)
    feedback = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    case = relationship("Case")


class FollowUp(Base):
    __tablename__ = "follow_ups"
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"))
    action_taken = Column(String)
    response_received = Column(String)
    improvement_level = Column(String)
    is_escalated = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    case = relationship("Case")


class CommunityGroup(Base):
    __tablename__ = "community_groups"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    center_lat = Column(Float)
    center_lng = Column(Float)
    radius_km = Column(Float, default=1.0)
    owner_id = Column(Integer, ForeignKey("users.id"))
    group_type = Column(String, default="neighbor")
    status = Column(String, default="active")
    member_count = Column(Integer, default=1)
    tags = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    owner = relationship("User")


class GroupMember(Base):
    __tablename__ = "group_members"
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("community_groups.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String, default="member")
    nickname = Column(String)
    joined_at = Column(DateTime, default=datetime.utcnow)
    last_read_at = Column(DateTime)
    group = relationship("CommunityGroup")
    user = relationship("User")


class GroupTopic(Base):
    __tablename__ = "group_topics"
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("community_groups.id"))
    name = Column(String, nullable=False)
    description = Column(Text)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    group = relationship("CommunityGroup")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("community_groups.id"))
    topic_id = Column(Integer, ForeignKey("group_topics.id"), nullable=True)
    sender_id = Column(Integer, ForeignKey("users.id"))
    message_type = Column(String, default="text")
    content = Column(Text)
    reply_to_id = Column(Integer, nullable=True)
    is_agent = Column(Boolean, default=False)
    agent_name = Column(String, nullable=True)
    agent_session_id = Column(String, nullable=True)
    read_by = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    group = relationship("CommunityGroup")
    sender = relationship("User")


class AgentSession(Base):
    __tablename__ = "agent_sessions"
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("community_groups.id"))
    topic_id = Column(Integer, ForeignKey("group_topics.id"), nullable=True)
    agent_name = Column(String, nullable=False)
    trigger_type = Column(String)
    context = Column(JSON)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    group = relationship("CommunityGroup")
    topic = relationship("GroupTopic")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String, nullable=False)
    target_type = Column(String)
    target_id = Column(Integer)
    detail = Column(JSON)
    ip_address = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User")


Base.metadata.create_all(bind=engine)
