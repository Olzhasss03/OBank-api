from enum import Enum


class ErrorCode(str, Enum):
    ACCOUNT_NOT_FOUND = "ACCOUNT_NOT_FOUND"
    CANT_TRANSFER_YOURSELF = "CANT_TRANSFER_YOURSELF"
    RECEIVER_NOT_FOUND = "RECEIVER_NOT_FOUND"
    ACCOUNT_ERROR = "ACCOUNT_ERROR"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    USER_ALREADY_REGISTERED = "USER_ALREADY_REGISTERED"
    INCORRECT_USERNAME_OR_PASSWORD = "INCORRECT_USERNAME_OR_PASSWORD"
    INVALID_TOKEN_TYPE = "INVALID_TOKEN_TYPE"
    REFRESH_TOKEN_EXPIRED = "REFRESH_TOKEN_EXPIRED"
    INVALID_REFRESH_TOKEN = "INVALID_REFRESH_TOKEN"
    TOKEN_NOT_FOUND = "TOKEN_NOT_FOUND"
    TOKEN_REUSE_DETECTED = "TOKEN_REUSE_DETECTED"
    TOKEN_EXPIRED_IN_DATABASE = "TOKEN_EXPIRED_IN_DATABASE"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    USER_NOT_FOUND_OR_PIN_NOT_SET = "USER_NOT_FOUND_OR_PIN_NOT_SET"
    INCORRECT_PIN_CODE = "INCORRECT_PIN_CODE"
    COULD_NOT_VALIDATE_CREDENTIALS = "COULD_NOT_VALIDATE_CREDENTIALS"
    DEVICE_TOKEN_NOT_FOUND = "DEVICE_TOKEN_NOT_FOUND"


class BaseAPIException(Exception):
    def __init__(self, status_code: int, error_code: ErrorCode, message: str):
        self.status_code = status_code
        self.error_code = error_code
        self.message = message

class AccountNotFoundException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=404,
            error_code=ErrorCode.ACCOUNT_NOT_FOUND,
            message="Account not found."
        )

class CantTransferYourselfException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=400,
            error_code=ErrorCode.CANT_TRANSFER_YOURSELF,
            message="You cannot transfer money to yourself."
        )

class ReceiverNotFoundException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=404,
            error_code=ErrorCode.RECEIVER_NOT_FOUND,
            message="Receiver not found."
        )

class AccountErrorException(BaseAPIException):  # if sender_account is None or receiver_account is None:
    def __init__(self):
        super().__init__(
            status_code=400,
            error_code=ErrorCode.ACCOUNT_ERROR,
            message="Account error. Please contact support."
        )

class InsufficientFundsException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=400,
            error_code=ErrorCode.INSUFFICIENT_FUNDS,
            message="Insufficient funds."
        )

class UserAlreadyRegisteredException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=400,
            error_code=ErrorCode.USER_ALREADY_REGISTERED,
            message="Username or Email already registered."
        )

class IncorrectUsernameOrPasswordException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=401,
            error_code=ErrorCode.INCORRECT_USERNAME_OR_PASSWORD,
            message="Incorrect username/email or password."
        )

class InvalidTokenTypeException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=401,
            error_code=ErrorCode.INVALID_TOKEN_TYPE,
            message="Invalid token type."
        )

class RefreshTokenExpiredException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=401,
            error_code=ErrorCode.REFRESH_TOKEN_EXPIRED,
            message="Refresh token expired."
        )

class InvalidRefreshTokenException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=401,
            error_code=ErrorCode.INVALID_REFRESH_TOKEN,
            message="Invalid refresh token."
        )

class TokenNotFoundException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=401,
            error_code=ErrorCode.TOKEN_NOT_FOUND,
            message="Token not found in database."
        )

class TokenReuseDetectedException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=403,
            error_code=ErrorCode.TOKEN_REUSE_DETECTED,
            message="Token reuse detected. All sessions revoked."
        )

class TokenExpiredInDatabaseException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=401,
            error_code=ErrorCode.TOKEN_EXPIRED_IN_DATABASE,
            message="Token expired in database."
        )

class SessionExpiredException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=401,
            error_code=ErrorCode.SESSION_EXPIRED,
            message="Token not found or already used (Session expired)."
        )

class UserNotFoundOrPinNotSetException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=400,
            error_code=ErrorCode.USER_NOT_FOUND_OR_PIN_NOT_SET,
            message="User not found or PIN not set."
        )

class IncorrectPinCodeException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=401,
            error_code=ErrorCode.INCORRECT_PIN_CODE,
            message="Incorrect PIN code."
        )

class DeviceTokenNotFoundException(BaseAPIException):
    def __init__(self):
        super().__init__(
            status_code=404,
            error_code=ErrorCode.DEVICE_TOKEN_NOT_FOUND,
            message="User doesn't have attached devices."
        )

# class CouldNotValidateCredentials(BaseAPIException):
#     def __init__(self):
#         super().__init__(
#             status_code=401,
#             error_code=ErrorCode.COULD_NOT_VALIDATE_CREDENTIALS,
#             message="Could not validate credentials."
#         )
