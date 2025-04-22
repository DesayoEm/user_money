from fastapi import APIRouter, Depends, Request

from app.schemas.account import AccountCreatePayload
from app.schemas.transaction import TransactionPayload
from app.services.account import account_service
from app.dependencies import get_current_user
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

account_router = APIRouter()


@account_router.post("")
def create_account(
    account_data: AccountCreatePayload,
        current_user=Depends(get_current_user)
):
    new_account = account_service.create_account(account_data, current_user)
    return new_account


@account_router.get("")
def get_account(current_user=Depends(get_current_user)):
    account = account_service.get_account(current_user)
    return account


@account_router.post("/{account_id}/deposit")
def deposit_fund(
    account_id: str,
        payload: TransactionPayload,
        current_user=Depends(get_current_user)
):
    return account_service.deposit_fund(account_id, payload.amount)


@account_router.post("/{account_id}/withdraw")
@limiter.limit("2/minute")
def withdraw_fund(
    account_id: str, payload: TransactionPayload,
        request: Request,
        current_user=Depends(get_current_user)
):
    return account_service.withdraw_fund(
        account_id, payload.amount,
        owner_id=current_user.id
    )

