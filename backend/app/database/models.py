from sqlalchemy import Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.app.database.database import Base

class TaskModel(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, index=True)
    user_prompt = Column(Text, nullable=False)
    task_name = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    status = Column(String, default="pending", index=True)
    working_directory = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    steps = relationship("StepModel", back_populates="task", cascade="all, delete-orphan")

class StepModel(Base):
    __tablename__ = "steps"

    id = Column(String, primary_key=True, index=True)
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False)
    step_index = Column(Integer, nullable=False)
    description = Column(String, nullable=False)
    command = Column(Text, nullable=False)
    shell = Column(String, default="auto")
    working_directory = Column(String, nullable=False)
    depends_on = Column(JSON, default=list)
    risk_level = Column(String, default="low")
    requires_approval = Column(Boolean, default=True)
    status = Column(String, default="pending")
    exit_code = Column(Integer, nullable=True)
    stdout = Column(Text, default="")
    stderr = Column(Text, default="")
    duration_seconds = Column(Float, default=0.0)

    task = relationship("TaskModel", back_populates="steps")

class CommandHistoryModel(Base):
    __tablename__ = "command_history"

    id = Column(String, primary_key=True, index=True)
    user_prompt = Column(Text, nullable=False)
    command = Column(Text, nullable=False)
    task_name = Column(String, default="CLI Command")
    working_directory = Column(String, nullable=False)
    risk_level = Column(String, default="low")
    status = Column(String, default="completed")
    exit_code = Column(Integer, default=0)
    stdout = Column(Text, default="")
    stderr = Column(Text, default="")
    duration_seconds = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

class WorkflowModel(Base):
    __tablename__ = "workflows"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String, default="General")
    template_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class SettingsModel(Base):
    __tablename__ = "settings"

    key = Column(String, primary_key=True, index=True)
    value = Column(Text, nullable=False)

class UserPreferenceModel(Base):
    __tablename__ = "user_preferences"

    id = Column(String, primary_key=True, index=True)
    category = Column(String, nullable=False, index=True)
    user_key = Column(String, nullable=False, index=True)
    preference_value = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, default="default-session", index=True)
    event_type = Column(String, nullable=False, index=True)
    details = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
