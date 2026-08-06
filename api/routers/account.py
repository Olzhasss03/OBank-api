from datetime import datetime, UTC, timedelta

from fastapi import APIRouter, status, Depends, Query
from sqlalchemy import select, or_

from api.database import SessionDep
from api.models import UserModel, AccountModel, TransactionModel
from api.schemas import TransferSchema, HistoryResponseSchema, TransferResponseSchema, UserPushRequestSchema
from api.utils.dependencies import get_current_user
from api.utils.errors import APIException, ErrorDetail
from api.utils.push_service import send_push_to_user

router = APIRouter(prefix="/account", tags=["account"])


@router.get("/balance", status_code=status.HTTP_200_OK)
async def get_balance(session: SessionDep, current_user: UserModel = Depends(get_current_user)):
    query = select(AccountModel).where(AccountModel.user_id == current_user.id)
    result = await session.execute(query)
    account: AccountModel | None = result.scalars().first()

    if account is None:
        raise APIException(ErrorDetail.ACCOUNT_NOT_FOUND)

    return {
        "status": "success",
        "username": current_user.username,
        "balance": account.balance
    }


@router.post("/transfer", response_model=TransferResponseSchema, status_code=status.HTTP_200_OK)
async def transfer_money(
        data: TransferSchema,
        session: SessionDep,
        current_user: UserModel = Depends(get_current_user)
):
    receiver_username = data.receiver_username.lower()

    if current_user.username == receiver_username:
        raise APIException(ErrorDetail.TRANSACTION_SELF_TRANSFER_NOT_ALLOWED)

    receiver_query = select(UserModel).where(UserModel.username == receiver_username)
    receiver_result = await session.execute(receiver_query)
    receiver: UserModel | None = receiver_result.scalars().first()

    if receiver is None:
        raise APIException(ErrorDetail.USER_RECEIVER_NOT_FOUND)

    sender_account_query = select(AccountModel).where(AccountModel.user_id == current_user.id).with_for_update()
    receiver_account_query = select(AccountModel).where(AccountModel.user_id == receiver.id).with_for_update()

    sender_account = (await session.execute(sender_account_query)).scalars().first()
    receiver_account = (await session.execute(receiver_account_query)).scalars().first()

    if sender_account is None:
        raise APIException(ErrorDetail.ACCOUNT_SENDER_NOT_FOUND)
    if receiver_account is None:
        raise APIException(ErrorDetail.ACCOUNT_RECEIVER_NOT_FOUND)

    if sender_account.balance < data.amount:
        raise APIException(ErrorDetail.TRANSACTION_INSUFFICIENT_FUNDS)

    sender_account.balance -= data.amount
    receiver_account.balance += data.amount

    new_transaction = TransactionModel(
        sender_account_id=sender_account.id,
        receiver_account_id=receiver_account.id,
        amount=data.amount
    )
    session.add(new_transaction)
    await session.commit()

    await session.refresh(new_transaction)

    push_request = UserPushRequestSchema(
        user_id=receiver_account.user_id,
        title_key="transfer_title",
        body_key="transfer_body"
    )

    await send_push_to_user(
        request=push_request,
        session=session,
        amount=data.amount,
        sender=current_user.username
    )

    return {
        "status": "success",
        "transaction": {
            "id": new_transaction.id,
            "tx_type": "outgoing",
            "counterparty": receiver.username,
            "amount": data.amount,
            "created_at": new_transaction.created_at
        },
        "new_balance": str(sender_account.balance)
    }


@router.get("/history", response_model=HistoryResponseSchema, status_code=status.HTTP_200_OK)
async def get_transaction_history(
        session: SessionDep,
        current_user: UserModel = Depends(get_current_user),
        limit: int = Query(30, ge=1, le=100),
        offset: int = Query(0, ge=0),
        date_from: datetime | None = Query(None),
        date_to: datetime | None = Query(None)
):
    account_query = select(AccountModel).where(AccountModel.user_id == current_user.id)
    account = (await session.execute(account_query)).scalars().first()

    if account is None:
        raise APIException(ErrorDetail.ACCOUNT_NOT_FOUND)

    if date_to is None:
        date_to = datetime.now(UTC)
    if date_from is None:
        date_from = date_to - timedelta(days=31)

    if date_from > date_to:
        raise APIException(ErrorDetail.HISTORY_INVALID_DATE_RANGE)
    if (date_to - date_from).days > 365:
        raise APIException(ErrorDetail.HISTORY_PERIOD_TOO_LARGE)

    history_query = (
        select(TransactionModel)
        .where(
            or_(
                TransactionModel.sender_account_id == account.id,
                TransactionModel.receiver_account_id == account.id,
            ),
            TransactionModel.created_at >= date_from,
            TransactionModel.created_at < (date_to + timedelta(days=1)),
        )
        .order_by(TransactionModel.created_at.desc())
        .offset(offset)
        .limit(limit + 1)
    )

    transactions = (await session.execute(history_query)).scalars().all()

    has_more = len(transactions) > limit

    if has_more:
        transactions = transactions[:-1]

    other_account_ids = set()
    for tx in transactions:
        if tx.sender_account_id == account.id:
            other_account_ids.add(tx.receiver_account_id)
        else:
            other_account_ids.add(tx.sender_account_id)

    users_query = select(AccountModel.id, UserModel.username).join(
        UserModel, AccountModel.user_id == UserModel.id
    ).where(AccountModel.id.in_(other_account_ids))

    users_result = await session.execute(users_query)

    account_to_username = {row.id: row.username for row in users_result}

    formatted_transactions = []
    for tx in transactions:
        if tx.sender_account_id == account.id:
            tx_type = "outgoing"
            counterparty_id = tx.receiver_account_id
        else:
            tx_type = "incoming"
            counterparty_id = tx.sender_account_id

        formatted_transactions.append({
            "id": tx.id,
            "tx_type": tx_type,
            "counterparty": account_to_username.get(counterparty_id, "Unknown"),
            "amount": tx.amount,
            "created_at": tx.created_at
        })

    return {
        "status": "success",
        "period": {
            "from": date_from,
            "to": date_to
        },
        "pagination": {
            "limit": limit,
            "offset": offset,
            "has_more": has_more
        },
        "transactions": formatted_transactions
    }


@router.get("/search")
async def search_users(
        session: SessionDep,
        query: str = Query(..., min_length=1),
        current_user: UserModel = Depends(get_current_user)
):
    clean_query = query.lstrip("@").lower()

    db_query = select(UserModel.username).where(
        UserModel.username.startswith(clean_query),
        UserModel.id != current_user.id
    ).limit(5)

    result = await session.execute(db_query)
    usernames = result.scalars().all()

    return {
        "status": "success",
        "matches": usernames
    }
