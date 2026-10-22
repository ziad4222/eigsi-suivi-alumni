"""Create local accounts explicitly; no credentials are embedded in the repository."""

import argparse
import getpass

from sqlalchemy import select

from .api import set_profile
from .auth import hash_password
from .database import Base, SessionLocal, engine
from .models import AlumniProfile, Role, User
from .schemas import ProfileWrite


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true", help="Créer quatre comptes fictifs de démonstration")
    parser.add_argument("--email")
    parser.add_argument("--role", choices=[r.value for r in Role], default="ADMIN")
    args = parser.parse_args()
    if not args.demo and not args.email:
        parser.error("Utiliser --demo ou --email")
    password = getpass.getpass("Mot de passe des nouveaux comptes (10 caractères minimum) : ")
    if not 10 <= len(password) <= 128:
        parser.error("Le mot de passe doit contenir de 10 à 128 caractères")
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        accounts = (
            [(f"{role.value.lower()}@example.com", role) for role in Role]
            if args.demo
            else [(args.email.lower(), Role(args.role))]
        )
        for email, role in accounts:
            if db.scalar(select(User).where(User.email == email)):
                print(f"Compte existant conservé : {email}")
                continue
            user = User(email=email, role=role, password_hash=hash_password(password))
            db.add(user)
            db.flush()
            if args.demo and role == Role.ALUMNI:
                profile = AlumniProfile(user=user)
                db.add(profile)
                set_profile(
                    profile,
                    ProfileWrite(
                        full_name="Lina Benali",
                        student_number="DEMO-2022-001",
                        graduation_year=2022,
                        program="Génie numérique",
                        employment_status="Ingénieure Data",
                        company="Entreprise exemple",
                        city="La Rochelle",
                        country="France",
                        sector="Numérique",
                        mentor=True,
                        consent=True,
                    ),
                    db,
                    user,
                )
            db.commit()
            print(f"Compte créé : {email} ({role.value})")


if __name__ == "__main__":
    main()
