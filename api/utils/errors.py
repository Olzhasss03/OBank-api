from enum import Enum


class ErrorDetail(Enum):
    # User
    USER_NOT_FOUND = (404, "User not found.")
    USER_RECEIVER_NOT_FOUND = (404, "Receiver not found")
    USER_ALREADY_EXISTS = (409, "Username or Email already registered.")
    USER_PIN_NOT_SET = (400, "User PIN is not set.")
    USER_INVALID_PIN = (401, "Incorrect PIN code.")
    USER_ALREADY_ADMIN = (400, "User is already admin")
    USER_NOT_ADMIN = (400, "User is not admin")

    # Auth
    AUTH_INVALID_CREDENTIALS = (401, "Incorrect username/email or password.")
    AUTH_INSUFFICIENT_PERMISSIONS = (403, "Insufficient permissions to perform this operation.")

    # Token
    TOKEN_MISSING = (401, "Token not found in database.")
    TOKEN_INVALID_TYPE = (401, "Invalid token type.")
    TOKEN_EXPIRED = (401, "Token expired.")
    TOKEN_REFRESH_INVALID = (401, "Invalid refresh token.")
    TOKEN_REFRESH_EXPIRED = (401, "Refresh token expired.")
    TOKEN_REUSE_DETECTED = (403, "Token reuse detected. All sessions revoked.")
    SESSION_EXPIRED = (401, "Session expired. Token not found or already used.")

    # Account
    ACCOUNT_NOT_FOUND = (404, "Account not found.")
    ACCOUNT_SENDER_NOT_FOUND = (404, "Sender account not found.")
    ACCOUNT_RECEIVER_NOT_FOUND = (404, "Receiver account not found.")

    # Transaction
    TRANSACTION_INSUFFICIENT_FUNDS = (400, "Insufficient funds.")
    TRANSACTION_SELF_TRANSFER_NOT_ALLOWED = (400, "You cannot transfer money to yourself.")

    HISTORY_INVALID_DATE_RANGE = (400, "The period start date cannot be later than the end date.")
    HISTORY_PERIOD_TOO_LARGE = (400, "Maximum history period is 365 days.")


class APIException(Exception):
    def __init__(self, error: ErrorDetail, custom_message: str = None):
        self.status_code = error.value[0]
        self.error_code = error.name
        self.message = custom_message or error.value[1]
