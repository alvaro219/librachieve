from datetime import datetime

from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import UserRole, pg_enum


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(255))
    steam_id: Mapped[str | None] = mapped_column(String(32), unique=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512))
    role: Mapped[UserRole] = mapped_column(
        pg_enum(UserRole, "user_role"), default=UserRole.USER, server_default=UserRole.USER.value
    )
    is_public: Mapped[bool] = mapped_column(default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    # Last sign-in or session refresh: daily Steam syncs only run for recently active users
    last_seen_at: Mapped[datetime | None]

    library_entries = relationship(
        "LibraryEntry", back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def has_password(self) -> bool:
        return self.password_hash is not None
