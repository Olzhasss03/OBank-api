from decimal import Decimal
from pydantic import BaseModel, Field, EmailStr


class UserRegisterSchema(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=20)
    password: str = Field(min_length=6, max_length=20)


class UserLoginSchema(BaseModel):
    login_field: str
    password: str = Field(min_length=6, max_length=20)


class UserPinLoginSchema(BaseModel):
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
