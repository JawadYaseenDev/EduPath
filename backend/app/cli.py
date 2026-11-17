"""Command-line tools.

Create a staff account (password is asked for, never passed on the command line):
    uv run python -m app.cli create-staff someone@example.com data_editor
"""

import argparse
import getpass
import sys

from sqlalchemy import select

from . import models as m
from .db import Base, SessionLocal, engine
from .security import hash_password, password_problem

STAFF_ROLES = ("super_admin", "data_editor", "data_verifier", "support")


def create_staff(email: str, role: str) -> None:
    password = getpass.getpass("Password for the new staff account: ")
    problem = password_problem(password)
    if problem:
        sys.exit(problem)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        user = db.scalar(select(m.User).where(m.User.email == email.lower()))
        if user is None:
            user = m.User(email=email.lower(), password_hash=hash_password(password))
            db.add(user)
        user.role = role
        user.email_verified = True
        db.commit()
    print(f"Staff account ready: {email} ({role})")


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    staff = sub.add_parser("create-staff", help="Create or update a staff account")
    staff.add_argument("email")
    staff.add_argument("role", choices=STAFF_ROLES)
    args = parser.parse_args()
    if args.command == "create-staff":
        create_staff(args.email, args.role)


if __name__ == "__main__":
    main()
