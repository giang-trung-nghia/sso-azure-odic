from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ApiIdentity(Base):
    """
    Lightweight local record for an Entra user (`oid`).

    Separate from Django's `accounts_userprofile` but keyed by the same `azure_oid`
    so both backends recognize the same person.
    """

    __tablename__ = "api_identities"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    azure_oid: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
