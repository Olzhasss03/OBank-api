from fastapi import APIRouter, status, Depends, HTTPException, Query
from sqlalchemy import select, or_

from api.database import SessionDep
from api.models import UserModel, AccountModel, TransactionModel
from api.schemas import TransferSchema, TransactionResponseSchema, HistoryResponseSchema
from api.utils.dependencies import get_current_user

router = APIRouter(prefix="/account", tags=["account"])


@router.get("/balance", status_code=status.HTTP_200_OK)
async def get_balance(session: SessionDep, current_user: UserModel = Depends(get_current_user)):
    query = select(AccountModel).where(AccountModel.user_id == current_user.id)
    result = await session.execute(query)
    account: AccountModel | None = result.scalars().first()

    if account is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )

    return {
        "status": "success",
        "username": current_user.username,
        "balance": account.balance
    }


@router.post("/transfer", status_code=status.HTTP_200_OK)
async def transfer_money(
        data: TransferSchema,
        session: SessionDep,
        current_user: UserModel = Depends(get_current_user)
):
    receiver_username = data.receiver_username.lower()

    if current_user.username == receiver_username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot transfer money to yourself")

    receiver_query = select(UserModel).where(UserModel.username == receiver_username)
    receiver_result = await session.execute(receiver_query)
    receiver: UserModel | None = receiver_result.scalars().first()

    if receiver is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receiver not found")

    sender_account_query = select(AccountModel).where(AccountModel.user_id == current_user.id).with_for_update()
    receiver_account_query = select(AccountModel).where(AccountModel.user_id == receiver.id).with_for_update()

    sender_account = (await session.execute(sender_account_query)).scalars().first()
    receiver_account = (await session.execute(receiver_account_query)).scalars().first()

    if sender_account is None or receiver_account is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account error. Please contact support."
        )

    if sender_account.balance < data.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient funds"
        )

    sender_account.balance -= data.amount
    receiver_account.balance += data.amount

    new_transaction = TransactionModel(
        sender_account_id=sender_account.id,
        receiver_account_id=receiver_account.id,
        amount=data.amount
    )
    session.add(new_transaction)

    await session.commit()

    return {
        "status": "success",
        "detail": f"Successfully transferred {data.amount} to {receiver.username}",
        "new_balance": sender_account.balance
    }


@router.get("/history", response_model=HistoryResponseSchema, status_code=status.HTTP_200_OK)
async def get_transaction_history(
        session: SessionDep,
        current_user: UserModel = Depends(get_current_user),
        limit: int = Query(20, ge=1, le=100),
        offset: int = Query(0, ge=0)
):
    account_query = select(AccountModel).where(AccountModel.user_id == current_user.id)
    account = (await session.execute(account_query)).scalars().first()

    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")

    history_query = select(TransactionModel).where(
        or_(
            TransactionModel.sender_account_id == account.id,
            TransactionModel.receiver_account_id == account.id
        )
    ).order_by(TransactionModel.created_at.desc()).offset(offset).limit(limit)

    transactions = (await session.execute(history_query)).scalars().all()

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
        "transactions": formatted_transactions
    }
