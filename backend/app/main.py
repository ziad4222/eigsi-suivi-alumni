from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .config import settings
from .database import Base, engine, get_db
from .models import AlumniProfile, AuditLog, Consent, ProfileStatus, Role, User
from .schemas import DashboardRead, ProfileCreate, ProfileRead, ReviewRequest


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="API Suivi Alumni EIGSI", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def require_roles(*allowed: Role):
    def dependency(x_role: str | None = Header(default=None)) -> Role:
        if x_role is None:
            raise HTTPException(status_code=401, detail="Authentification requise")
        try:
            role = Role(x_role.upper())
        except ValueError as exc:
            raise HTTPException(status_code=401, detail="Rôle invalide") from exc
        if role not in allowed:
            raise HTTPException(status_code=403, detail="Accès refusé")
        return role

    return dependency


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/profiles", response_model=list[ProfileRead])
def list_profiles(
    q: str | None = Query(default=None, max_length=120),
    graduation_year: int | None = None,
    country: str | None = None,
    db: Session = Depends(get_db),
    _role: Role = Depends(require_roles(Role.SERVICE, Role.DIRECTION, Role.ADMIN)),
):
    statement = select(AlumniProfile)
    if q:
        statement = statement.where(
            or_(AlumniProfile.program.ilike(f"%{q}%"), AlumniProfile.employment_status.ilike(f"%{q}%"))
        )
    if graduation_year:
        statement = statement.where(AlumniProfile.graduation_year == graduation_year)
    if country:
        statement = statement.where(AlumniProfile.country == country)
    return list(db.scalars(statement.order_by(AlumniProfile.graduation_year.desc())))


@app.post("/api/profiles", response_model=ProfileRead, status_code=status.HTTP_201_CREATED)
def create_profile(payload: ProfileCreate, db: Session = Depends(get_db)):
    if not payload.consent:
        raise HTTPException(status_code=422, detail="Le consentement est obligatoire")
    user = User(email=payload.email, password_hash="INVITATION_PENDING", role=Role.ALUMNI)
    profile = AlumniProfile(
        user=user,
        student_number=payload.student_number,
        graduation_year=payload.graduation_year,
        program=payload.program,
        employment_status=payload.employment_status,
        city=payload.city,
        country=payload.country,
        status=ProfileStatus.PENDING,
        submitted_at=datetime.now(UTC),
        last_confirmed_at=datetime.now(UTC),
    )
    profile.consents.append(
        Consent(purpose="Suivi Alumni et publication annuaire", granted=True, granted_at=datetime.now(UTC))
    )
    db.add(profile)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="E-mail ou matricule déjà utilisé") from exc
    db.refresh(profile)
    return profile


@app.post("/api/profiles/{profile_id}/review", response_model=ProfileRead)
def review_profile(
    profile_id: str,
    payload: ReviewRequest,
    db: Session = Depends(get_db),
    _role: Role = Depends(require_roles(Role.SERVICE, Role.ADMIN)),
):
    profile = db.get(AlumniProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profil introuvable")
    mapping = {
        "APPROVED": ProfileStatus.VALIDATED,
        "CORRECTION": ProfileStatus.PENDING,
        "REJECTED": ProfileStatus.REJECTED,
    }
    decision = payload.decision.upper()
    if decision not in mapping:
        raise HTTPException(status_code=422, detail="Décision invalide")
    profile.status = mapping[decision]
    db.add(AuditLog(entity_type="ALUMNI_PROFILE", entity_id=profile.id, action=f"REVIEW_{decision}"))
    db.commit()
    db.refresh(profile)
    return profile


@app.get("/api/dashboard", response_model=DashboardRead)
def dashboard(
    db: Session = Depends(get_db),
    _role: Role = Depends(require_roles(Role.SERVICE, Role.DIRECTION, Role.ADMIN)),
):
    cutoff = datetime.now(UTC) - timedelta(days=365)
    total = db.scalar(select(func.count()).select_from(AlumniProfile)) or 0
    validated = (
        db.scalar(
            select(func.count())
            .select_from(AlumniProfile)
            .where(AlumniProfile.status == ProfileStatus.VALIDATED)
        )
        or 0
    )
    pending = (
        db.scalar(
            select(func.count())
            .select_from(AlumniProfile)
            .where(AlumniProfile.status == ProfileStatus.PENDING)
        )
        or 0
    )
    fresh = (
        db.scalar(
            select(func.count()).select_from(AlumniProfile).where(AlumniProfile.last_confirmed_at >= cutoff)
        )
        or 0
    )
    return DashboardRead(
        alumni_count=total,
        validated_count=validated,
        pending_count=pending,
        fresh_count=fresh,
        updated_at=datetime.now(UTC),
    )
