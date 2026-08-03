from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, EmailStr, ConfigDict
from sqlalchemy.engine import default


class UserRegisterSchema(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=20)
    password: str = Field(min_length=6, max_length=20)


class UserLoginSchema(BaseModel):
    login_field: str
    password: str = Field(min_length=6, max_length=20)


class UserPinSetupSchema(BaseModel):
    pincode: str = Field(max_length=4, min_length=4, pattern=r"^\d{4}$")


class UserPinLoginSchema(BaseModel):
    refresh_token: str
    pincode: str = Field(max_length=4, min_length=4, pattern=r"^\d{4}$")


class TokenResponseSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"


class TokenRefreshRequestSchema(BaseModel):
    refresh_token: str


class TransferSchema(BaseModel):
    receiver_username: str
    amount: Decimal = Field(gt=0, decimal_places=2)


class TransactionResponseSchema(BaseModel):
    id: int
    tx_type: str
    counterparty: str
    amount: Decimal
    created_at: datetime


class HistoryResponseSchema(BaseModel):
    status: str
    transactions: list[TransactionResponseSchema]


class TransferResponseSchema(BaseModel):
    status: str = "success"
    transaction: TransactionResponseSchema
    new_balance: str


class UserInfoResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: EmailStr
    joined_at: datetime
    # is_admin: bool
    # profile_picture:


class FCMTokenRequest(BaseModel):
    fcm_token: str
    locale: str = "en"
