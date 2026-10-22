import csv
import io
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from statistics import median

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .auth import COOKIE, current_user, hash_password, issue_session, require_roles, verify_password
from .config import settings
from .database import Base, engine, get_db
from .models import (
    AlumniProfile,
    AuditLog,
    AuthSession,
    Campaign,
    Consent,
    ProfileStatus,
    ReviewDecision,
    Role,
    User,
    ValidationReview,
)
from .schemas import CampaignWrite, Credentials, ImportedProfile, ProfileWrite, ReviewRequest


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="API Suivi Alumni EIGSI", version="2.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["Content-Type"],
)


def audit(db, user, entity, action):
    db.add(AuditLog(actor_user_id=user.id, entity_type="ALUMNI_PROFILE", entity_id=entity, action=action))


def commit(db):
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "E-mail ou matricule déjà utilisé") from exc


def has_consent(profile):
    return any(c.granted and c.revoked_at is None for c in profile.consents)


def profile_read(profile, db, private=True):
    review = db.scalar(
        select(ValidationReview)
        .where(ValidationReview.alumni_id == profile.id)
        .order_by(ValidationReview.reviewed_at.desc())
    )
    data = {
        "id": profile.id,
        "full_name": profile.full_name,
        "student_number": profile.student_number,
        "graduation_year": profile.graduation_year,
        "program": profile.program,
        "employment_status": profile.employment_status,
        "company": profile.company,
        "city": profile.city,
        "country": profile.country,
        "sector": profile.sector,
        "mentor": profile.mentor,
        "status": profile.status,
        "consent": has_consent(profile),
        "last_confirmed_at": profile.last_confirmed_at,
        "submitted_at": profile.submitted_at,
        "duplicate_checked": profile.duplicate_checked,
    }
    if private:
        data["email"] = profile.user.email
        data["review"] = (
            None
            if not review
            else {
                "decision": review.decision,
                "comment": review.comment,
                "reviewed_at": review.reviewed_at,
                "reviewer_user_id": review.reviewer_user_id,
            }
        )
    else:
        for key in ["student_number", "duplicate_checked", "submitted_at"]:
            data.pop(key)
    return data


def set_profile(profile, payload, db, user):
    for field, value in payload.model_dump(exclude={"consent", "email"}).items():
        setattr(profile, field, value)
    now = datetime.now(UTC)
    for consent in profile.consents:
        if consent.granted and consent.revoked_at is None:
            consent.granted = False
            consent.revoked_at = now
    profile.consents.append(
        Consent(
            purpose="Suivi Alumni et publication dans l’annuaire, politique v1.0",
            granted=payload.consent,
            granted_at=now if payload.consent else None,
            revoked_at=None if payload.consent else now,
        )
    )
    profile.status = ProfileStatus.PENDING if payload.consent else ProfileStatus.DRAFT
    profile.submitted_at = now if payload.consent else None
    profile.last_confirmed_at = now
    profile.duplicate_checked = False
    db.flush()
    audit(db, user, profile.id, "PROFILE_SUBMITTED" if payload.consent else "PROFILE_DRAFT")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/auth/register", status_code=201)
def register(payload: Credentials, response: Response, db: Session = Depends(get_db)):
    user = User(
        email=str(payload.email).lower(), password_hash=hash_password(payload.password), role=Role.ALUMNI
    )
    db.add(user)
    commit(db)
    issue_session(user, db, response)
    return {"id": user.id, "email": user.email, "role": user.role}


DUMMY_HASH = hash_password("dummy-password-with-no-account")


@app.post("/api/auth/login")
def login(payload: Credentials, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == str(payload.email).lower()))
    valid = verify_password(payload.password, user.password_hash if user else DUMMY_HASH)
    if not user or not valid:
        raise HTTPException(401, "Identifiants invalides")
    issue_session(user, db, response)
    return {"id": user.id, "email": user.email, "role": user.role}


@app.get("/api/auth/me")
def me(user: User = Depends(current_user)):
    return {"id": user.id, "email": user.email, "role": user.role}


@app.post("/api/auth/logout", status_code=204)
def logout(
    request: Request, response: Response, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    db.delete(db.get(AuthSession, request.state.session_id))
    db.commit()
    response.delete_cookie(COOKIE, path="/api", httponly=True, samesite="strict")


@app.get("/api/me/profile")
def own_profile(user: User = Depends(require_roles(Role.ALUMNI)), db: Session = Depends(get_db)):
    return profile_read(user.profile, db) if user.profile else None


@app.put("/api/me/profile")
def save_own_profile(
    payload: ProfileWrite, user: User = Depends(require_roles(Role.ALUMNI)), db: Session = Depends(get_db)
):
    profile = user.profile or AlumniProfile(user=user)
    db.add(profile)
    try:
        set_profile(profile, payload, db, user)
        commit(db)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "Matricule déjà utilisé") from exc
    return profile_read(profile, db)


@app.post("/api/me/consent/revoke")
def revoke_consent(user: User = Depends(require_roles(Role.ALUMNI)), db: Session = Depends(get_db)):
    if not user.profile:
        raise HTTPException(404, "Profil introuvable")
    for consent in user.profile.consents:
        if consent.granted:
            consent.granted = False
            consent.revoked_at = datetime.now(UTC)
    user.profile.status = ProfileStatus.DRAFT
    audit(db, user, user.profile.id, "CONSENT_REVOKED")
    db.commit()
    return profile_read(user.profile, db)


def profiles_query(q=None, graduation_year=None, country=None, status=None, program=None):
    statement = select(AlumniProfile).join(User)
    if q:
        statement = statement.where(
            or_(
                *[
                    field.ilike(f"%{q}%")
                    for field in [
                        AlumniProfile.full_name,
                        AlumniProfile.program,
                        AlumniProfile.employment_status,
                        AlumniProfile.company,
                        AlumniProfile.city,
                        User.email,
                    ]
                ]
            )
        )
    for field, value in [
        (AlumniProfile.graduation_year, graduation_year),
        (AlumniProfile.country, country),
        (AlumniProfile.program, program),
        (AlumniProfile.status, status),
    ]:
        if value is not None and value != "":
            statement = statement.where(field == value)
    return statement.order_by(AlumniProfile.graduation_year.desc())


@app.get("/api/profiles")
def list_profiles(
    q: str | None = Query(None, max_length=120),
    graduation_year: int | None = None,
    country: str | None = None,
    status: ProfileStatus | None = None,
    program: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(Role.SERVICE, Role.ADMIN)),
):
    return [
        profile_read(p, db) for p in db.scalars(profiles_query(q, graduation_year, country, status, program))
    ]


@app.get("/api/directory")
def directory(
    q: str | None = Query(None, max_length=120),
    graduation_year: int | None = None,
    country: str | None = None,
    program: str | None = None,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    statement = profiles_query(q, graduation_year, country, ProfileStatus.VALIDATED, program)
    return [profile_read(p, db, private=False) for p in db.scalars(statement) if has_consent(p)]


@app.post("/api/profiles", status_code=201)
def import_profile(
    payload: ImportedProfile, user: User = Depends(require_roles(Role.ADMIN)), db: Session = Depends(get_db)
):
    if payload.consent:
        raise HTTPException(422, "Un import ne peut pas accorder le consentement")
    account = User(email=str(payload.email).lower(), password_hash="INVITATION_PENDING", role=Role.ALUMNI)
    profile = AlumniProfile(user=account)
    db.add(profile)
    try:
        set_profile(profile, payload, db, user)
        commit(db)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "E-mail ou matricule déjà utilisé") from exc
    return profile_read(profile, db)


@app.post("/api/profiles/{profile_id}/duplicates/checked")
def check_duplicate(
    profile_id: str,
    user: User = Depends(require_roles(Role.SERVICE, Role.ADMIN)),
    db: Session = Depends(get_db),
):
    profile = db.get(AlumniProfile, profile_id)
    if not profile:
        raise HTTPException(404, "Profil introuvable")
    profile.duplicate_checked = True
    audit(db, user, profile.id, "DUPLICATE_CHECKED")
    db.commit()
    return profile_read(profile, db)


@app.post("/api/profiles/{profile_id}/review")
def review_profile(
    profile_id: str,
    payload: ReviewRequest,
    user: User = Depends(require_roles(Role.SERVICE, Role.ADMIN)),
    db: Session = Depends(get_db),
):
    profile = db.get(AlumniProfile, profile_id)
    if not profile:
        raise HTTPException(404, "Profil introuvable")
    if payload.decision != "APPROVED" and not payload.comment.strip():
        raise HTTPException(422, "Le motif est obligatoire")
    if payload.decision == "APPROVED":
        if not has_consent(profile) or not profile.duplicate_checked:
            raise HTTPException(422, "Consentement et examen des doublons requis")
        if not profile.full_name or not profile.submitted_at:
            raise HTTPException(422, "Le profil doit être complet et soumis")
    profile.status = {
        "APPROVED": ProfileStatus.VALIDATED,
        "CORRECTION": ProfileStatus.DRAFT,
        "REJECTED": ProfileStatus.REJECTED,
    }[payload.decision]
    db.add(
        ValidationReview(
            alumni_id=profile.id,
            reviewer_user_id=user.id,
            decision=ReviewDecision(payload.decision),
            comment=payload.comment.strip(),
        )
    )
    audit(db, user, profile.id, f"REVIEW_{payload.decision}")
    db.commit()
    return profile_read(profile, db)


@app.get("/api/dashboard")
def dashboard(
    user: User = Depends(require_roles(Role.SERVICE, Role.DIRECTION, Role.ADMIN)),
    db: Session = Depends(get_db),
):
    profiles = list(db.scalars(select(AlumniProfile)))
    validated = [p for p in profiles if p.status == ProfileStatus.VALIDATED and has_consent(p)]
    cutoff = (datetime.now(UTC) - timedelta(days=365)).replace(tzinfo=None)
    fresh = sum(bool(p.last_confirmed_at and p.last_confirmed_at >= cutoff) for p in validated)
    delays = []
    for profile in validated:
        review = db.scalar(
            select(ValidationReview)
            .where(
                ValidationReview.alumni_id == profile.id, ValidationReview.decision == ReviewDecision.APPROVED
            )
            .order_by(ValidationReview.reviewed_at.desc())
        )
        if review and profile.submitted_at and review.reviewed_at >= profile.submitted_at:
            delays.append((review.reviewed_at - profile.submitted_at).total_seconds() / 86400)
    return {
        "alumni_count": len(profiles),
        "validated_count": len(validated),
        "pending_count": sum(p.status == ProfileStatus.PENDING for p in profiles),
        "fresh_count": fresh,
        "complete_count": sum(bool(p.full_name and p.student_number) for p in validated),
        "median_days": median(delays) if delays else None,
        "updated_at": datetime.now(UTC),
        "promotions": {
            str(year): sum(p.graduation_year == year for p in profiles)
            for year in sorted({p.graduation_year for p in profiles}, reverse=True)
        },
    }


@app.get("/api/audit")
def audit_log(user: User = Depends(require_roles(Role.SERVICE, Role.ADMIN)), db: Session = Depends(get_db)):
    return [
        {
            "action": row.action,
            "entity_id": row.entity_id,
            "actor_user_id": row.actor_user_id,
            "created_at": row.created_at,
        }
        for row in db.scalars(select(AuditLog).order_by(AuditLog.id.desc()))
    ]


@app.post("/api/campaigns", status_code=201)
def prepare_campaign(
    payload: CampaignWrite,
    user: User = Depends(require_roles(Role.SERVICE, Role.ADMIN)),
    db: Session = Depends(get_db),
):
    cutoff = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=365)
    recipients = list(
        db.scalars(
            select(AlumniProfile.id).where(
                or_(AlumniProfile.last_confirmed_at < cutoff, AlumniProfile.last_confirmed_at.is_(None))
            )
        )
    )
    campaign = Campaign(
        name=payload.name, message=payload.message, created_by=user.id, recipient_ids=recipients
    )
    db.add(campaign)
    db.flush()
    audit(db, user, campaign.id, "CAMPAIGN_PREPARED")
    db.commit()
    return {"id": campaign.id, "recipient_count": len(recipients), "status": "PREPARED"}


@app.get("/api/campaigns")
def campaigns(user: User = Depends(require_roles(Role.SERVICE, Role.ADMIN)), db: Session = Depends(get_db)):
    result = []
    for campaign in db.scalars(select(Campaign).order_by(Campaign.created_at.desc())):
        responses = sum(
            bool(p.last_confirmed_at and p.last_confirmed_at >= campaign.created_at)
            for p in db.scalars(select(AlumniProfile).where(AlumniProfile.id.in_(campaign.recipient_ids)))
        )
        result.append(
            {
                "id": campaign.id,
                "name": campaign.name,
                "message": campaign.message,
                "created_at": campaign.created_at,
                "recipient_count": len(campaign.recipient_ids),
                "responses": responses,
                "status": "PREPARED",
            }
        )
    return result


@app.get("/api/export")
def export_profiles(
    q: str | None = None,
    graduation_year: int | None = None,
    country: str | None = None,
    status: ProfileStatus | None = None,
    program: str | None = None,
    user: User = Depends(require_roles(Role.ADMIN)),
    db: Session = Depends(get_db),
):
    stream = io.StringIO()
    fields = [
        "full_name",
        "email",
        "student_number",
        "graduation_year",
        "program",
        "employment_status",
        "company",
        "city",
        "country",
        "sector",
    ]
    writer = csv.DictWriter(stream, fieldnames=fields, delimiter=";", extrasaction="ignore")
    writer.writeheader()
    for profile in db.scalars(profiles_query(q, graduation_year, country, status, program)):
        row = profile_read(profile, db)
        writer.writerow(
            {k: "'" + str(row[k]) if str(row[k]).startswith(("=", "+", "-", "@")) else row[k] for k in fields}
        )
    audit(db, user, "export", "CSV_EXPORTED")
    db.commit()
    return Response(
        "\ufeff" + stream.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="alumni-eigsi.csv"'},
    )
