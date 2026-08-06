from sqlalchemy import ForeignKey, DateTime, Numeric, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, timezone
from decimal import Decimal
from api.database import Base


class UserModel(Base):
    __tablename__ = "Users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True, index=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column()
    hashed_pin: Mapped[str | None] = mapped_column(String(255), nullable=True)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True
    )
    account: Mapped["AccountModel"] = relationship(back_populates="user", uselist=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    avatar_key: Mapped[str | None] = mapped_column(String(255), nullable=True)


class AccountModel(Base):
    __tablename__ = "Accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("Users.id"), unique=True, index=True)
    balance: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0.00"))
    user: Mapped["UserModel"] = relationship(back_populates="account")


class TransactionModel(Base):
    __tablename__ = "Transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    sender_account_id: Mapped[int] = mapped_column(ForeignKey("Accounts.id"), index=True)
    receiver_account_id: Mapped[int] = mapped_column(ForeignKey("Accounts.id"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True
    )


class RefreshTokenModel(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("Users.id", ondelete="CASCADE"), index=True)
    is_used: Mapped[bool] = mapped_column(default=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(index=True)


class DeviceTokenModel(Base):
    __tablename__ = "device_tokens"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("Users.id", ondelete="CASCADE"), index=True)
    fcm_token: Mapped[str] = mapped_column(String, unique=True)
    locale: Mapped[str] = mapped_column(String, server_default="en")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
