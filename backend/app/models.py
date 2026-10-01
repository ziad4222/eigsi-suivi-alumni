import enum
import uuid
from datetime import UTC, date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Role(str, enum.Enum):
    ALUMNI = "ALUMNI"
    SERVICE = "SERVICE"
    DIRECTION = "DIRECTION"
    ADMIN = "ADMIN"


class ProfileStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"


class ReviewDecision(str, enum.Enum):
    APPROVED = "APPROVED"
    CORRECTION = "CORRECTION"
    REJECTED = "REJECTED"


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[Role] = mapped_column(Enum(Role), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    profile: Mapped["AlumniProfile | None"] = relationship(back_populates="user", uselist=False)


class AlumniProfile(Base):
    __tablename__ = "alumni_profiles"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), unique=True)
    student_number: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    graduation_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    program: Mapped[str] = mapped_column(String(120), nullable=False)
    employment_status: Mapped[str] = mapped_column(String(80), nullable=False)
    city: Mapped[str] = mapped_column(String(120), nullable=False)
    country: Mapped[str] = mapped_column(String(120), nullable=False)
    last_confirmed_at: Mapped[datetime | None] = mapped_column(DateTime)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime)
    status: Mapped[ProfileStatus] = mapped_column(Enum(ProfileStatus), default=ProfileStatus.DRAFT)
    user: Mapped[User] = relationship(back_populates="profile")
    experiences: Mapped[list["ProfessionalExperience"]] = relationship(cascade="all, delete-orphan")
    consents: Mapped[list["Consent"]] = relationship(cascade="all, delete-orphan")


class Consent(Base):
    __tablename__ = "consents"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    alumni_id: Mapped[str] = mapped_column(ForeignKey("alumni_profiles.id", ondelete="CASCADE"), index=True)
    purpose: Mapped[str] = mapped_column(String(255), nullable=False)
    granted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    granted_at: Mapped[datetime | None] = mapped_column(DateTime)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime)


class ProfessionalExperience(Base):
    __tablename__ = "professional_experiences"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    alumni_id: Mapped[str] = mapped_column(ForeignKey("alumni_profiles.id", ondelete="CASCADE"), index=True)
    company: Mapped[str] = mapped_column(String(160), nullable=False)
    job_title: Mapped[str] = mapped_column(String(160), nullable=False)
    sector: Mapped[str] = mapped_column(String(120), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ValidationReview(Base):
    __tablename__ = "validation_reviews"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    alumni_id: Mapped[str] = mapped_column(ForeignKey("alumni_profiles.id", ondelete="CASCADE"), index=True)
    reviewer_user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    decision: Mapped[ReviewDecision] = mapped_column(Enum(ReviewDecision), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    actor_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(36), nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
