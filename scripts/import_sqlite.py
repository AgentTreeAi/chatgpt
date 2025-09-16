"""Import legacy SQLite data into Postgres."""
from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import models
from app.db.base import Base
from app.db.session import engine


LEGACY_DB_PATH = "rmht_app/rmht.db"


def ensure_schema() -> None:
    Base.metadata.create_all(bind=engine)


def import_data() -> None:
    settings = get_settings()
    ensure_schema()

    with closing(sqlite3.connect(LEGACY_DB_PATH)) as legacy_conn, Session(engine) as session:
        legacy_conn.row_factory = sqlite3.Row

        org = models.Org(name="Legacy Demo Org")
        session.add(org)
        session.flush()

        team_id_map: dict[int, models.Team] = {}
        user_id_map: dict[int, models.User] = {}

        for team_row in legacy_conn.execute("SELECT id, name, created_at FROM teams"):
            team = models.Team(
                org_id=org.id,
                name=team_row["name"],
                created_at=datetime.fromisoformat(team_row["created_at"]) if team_row["created_at"] else datetime.utcnow(),
            )
            session.add(team)
            session.flush()
            team_id_map[team_row["id"]] = team

        for member_row in legacy_conn.execute(
            "SELECT id, team_id, hashed_token, active, created_at, display_name, email FROM members"
        ):
            team = team_id_map[member_row["team_id"]]
            user = models.User(
                team_id=team.id,
                anon_token_hash=member_row["hashed_token"],
                active=bool(member_row["active"]),
                created_at=datetime.fromisoformat(member_row["created_at"]) if member_row["created_at"] else datetime.utcnow(),
                email=member_row["email"],
            )
            session.add(user)
            session.flush()
            user_id_map[member_row["id"]] = user

        for checkin_row in legacy_conn.execute(
            "SELECT id, team_id, member_id, mood, stress, comment, created_at FROM checkins"
        ):
            user = user_id_map.get(checkin_row["member_id"])
            team = team_id_map.get(checkin_row["team_id"])
            if not user or not team:
                continue
            created_at = (
                datetime.fromisoformat(checkin_row["created_at"])
                if checkin_row["created_at"]
                else datetime.utcnow()
            )
            session.add(
                models.Checkin(
                    user_id=user.id,
                    team_id=team.id,
                    submitted_at=created_at,
                    checkin_date=created_at.date(),
                    mood=checkin_row["mood"],
                    stress=checkin_row["stress"],
                    comment=checkin_row["comment"],
                )
            )

        session.commit()

        print("Imported legacy data into Postgres database", settings.database_url)


if __name__ == "__main__":
    import_data()
