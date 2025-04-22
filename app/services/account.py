from datetime import datetime
from decimal import Decimal
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from app.schemas.account import AccountCreatePayload, Account
from app.database import accounts_collection, transactions_collection
from app.schemas.transaction import TransactionType
from app.schemas.user import User
from app.serializers import account_serializer, transaction_serializer
from bson.objectid import ObjectId


class AccountService:

    @staticmethod
    def create_account(account_data: AccountCreatePayload, user: User) -> Account:
        account_data = account_data.model_dump()
        account_with_defaults = Account(
            **account_data,
            user_id=user.id,
            balance=0.0,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        account_id = accounts_collection.insert_one(
            jsonable_encoder(account_with_defaults)
        ).inserted_id
        account = accounts_collection.find_one({"_id": account_id})
        return account_serializer(account)


    @staticmethod
    def get_account(user: User):
        account = accounts_collection.find_one({"user_id": user.id})
        if not account:
            raise HTTPException(status_code=400, detail="User does not have an account")
        return account_serializer(account)


    @staticmethod
    def get_account_by_id(account_id: str):
        account = accounts_collection.find_one({"_id": ObjectId(account_id)})
        if not account:
            return None
        return account_serializer(account)


    @staticmethod
    def record_transaction(
        account_id: str, amount: Decimal, transaction_type: TransactionType
    ):
        transaction = {
            "account_id": account_id,
            "amount": float(amount),
            "transaction_type": transaction_type.value,
            "date": datetime.now(),
        }
        result = transactions_collection.insert_one(transaction)
        return transactions_collection.find_one({"_id": result.inserted_id})


    @staticmethod
    def deposit_fund(account_id: str, amount: Decimal):
        account = AccountService.get_account_by_id(account_id)
        if not account:
            raise HTTPException(status_code=404, detail="Account not found")
        account=account.model_dump()

        old_balance = Decimal(str(account.get("balance", 0.0)))
        new_balance = old_balance + amount

        account = accounts_collection.find_one_and_update(
            {"_id": ObjectId(account_id)},
            {"$set": {"balance": float(new_balance), "updated_at": datetime.now()}},
        )
        transaction = AccountService.record_transaction(
            account_id, amount, TransactionType.credit
        )
        return transaction_serializer(transaction)


    @staticmethod
    def withdraw_fund(account_id: str, amount: Decimal, owner_id):
        account = AccountService.get_account_by_id(account_id)
        if account.user_id != owner_id:
            raise HTTPException(status_code=403,
                                detail="Unauthorized to withdraw from account"
                                )
        account=account.model_dump()
        if not account:
            raise HTTPException(status_code=404,
                                detail="Account not found"
                                )
        old_balance = Decimal(str(account.get("balance", 0.0)))
        if old_balance<amount:
            raise HTTPException(status_code=402,
                                detail="Insufficient balance"
                                )

        new_balance = old_balance - amount

        account = accounts_collection.find_one_and_update(
            {"_id": ObjectId(account_id)},
            {"$set": {"balance": float(new_balance), "updated_at": datetime.now()}},
        )
        transaction = AccountService.record_transaction(
            account_id, amount, TransactionType.debit
        )
        return transaction_serializer(transaction)



account_service = AccountService()
