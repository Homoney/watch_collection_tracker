"""Administrative commands.

Create (or promote) an account without opening public registration:

    python -m app.cli create-user EMAIL [--admin] [--name "Full Name"]

The password is read from the WATCH_USER_PASSWORD environment variable if
set, otherwise prompted for (twice). With --admin an existing account is
promoted to admin and its password is left unchanged.
"""

import argparse
import getpass
import os
import sys
from typing import Optional

from sqlalchemy.orm import Session

from app.core.passwords import password_problem
from app.core.security import get_password_hash
from app.models.user import User, UserRole


def _read_password() -> str:
    password = os.environ.get("WATCH_USER_PASSWORD")
    if password:
        return password
    first = getpass.getpass("Password: ")
    if first != getpass.getpass("Repeat password: "):
        raise SystemExit("Passwords do not match")
    return first


def create_user(
    db: Session,
    email: str,
    password: Optional[str],
    admin: bool = False,
    full_name: Optional[str] = None,
) -> tuple:
    """Create a user, or promote an existing one when admin=True.

    Returns (user, created). Raises ValueError on bad input.
    """
    email = email.strip()
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        if not admin:
            raise ValueError(f"{email} already exists")
        existing.role = UserRole.admin
        db.commit()
        db.refresh(existing)
        return existing, False
    problem = password_problem(password or "")
    if problem:
        raise ValueError(problem)
    user = User(
        email=email,
        full_name=full_name,
        hashed_password=get_password_hash(password),
        role=UserRole.admin if admin else UserRole.user,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, True


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    sub = parser.add_subparsers(dest="command", required=True)
    cu = sub.add_parser("create-user", help="create an account or promote one")
    cu.add_argument("email")
    cu.add_argument("--admin", action="store_true", help="make the account admin")
    cu.add_argument("--name", default=None, help="full name")
    args = parser.parse_args(argv)

    from app.database import SessionLocal

    db = SessionLocal()
    try:
        exists = db.query(User).filter(User.email == args.email.strip()).first()
        password = None if (exists and args.admin) else _read_password()
        user, created = create_user(db, args.email, password, args.admin, args.name)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()
    action = "Created" if created else "Promoted"
    print(f"{action} {user.email} ({user.role.value})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
