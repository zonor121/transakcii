import os
import time
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from dotenv import load_dotenv
from supabase import create_client, Client
import httpx

load_dotenv()


class TransferType(str, Enum):
    SALARY = "SALARY"
    PAYMENT = "PAYMENT"


@dataclass
class TransferResult:
    success: bool
    message: str
    transfer_id: Optional[int] = None
    sender_balance: Optional[Decimal] = None
    receiver_balance: Optional[Decimal] = None


class FlowerShopClient:
    """Клиент для магазина цветов 'Ромашка'"""

    def __init__(self, max_retries: int = 3):
        url = os.environ["SUPABASE_URL"]
        key = os.environ["SUPABASE_KEY"]
        self.max_retries = max_retries
        
        # 🔑 Принудительно HTTP/1.1 — обходит WinError 10054 на Windows
        http_client = httpx.Client(
            http2=False,
            timeout=httpx.Timeout(30.0),
        )
        self.supabase: Client = create_client(url, key, http_client=http_client)

    def _call_rpc_with_retry(self, func_name: str, params: dict) -> dict:
        """Вызов RPC с автоматическим повтором при сетевых сбоях"""
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = self.supabase.rpc(func_name, params).execute()
                data = response.data
                if isinstance(data, list):
                    data = data[0] if data else {}
                return data
            except (httpx.ReadError, httpx.RemoteProtocolError, httpx.ConnectError) as e:
                last_error = e
                wait = attempt * 0.5  # 0.5s, 1.0s, 1.5s
                print(f"  ⚠️  Попытка {attempt}/{self.max_retries} не удалась ({type(e).__name__}), повтор через {wait}s...")
                time.sleep(wait)
            except Exception as e:
                return {"status": "FAILED", "message": f"Неожиданная ошибка: {e}"}
        
        return {"status": "FAILED", "message": f"Сетевая ошибка после {self.max_retries} попыток: {last_error}"}

    def transfer(
        self,
        from_id: str,
        to_id: str,
        amount: float,
        transfer_type: TransferType,
        description: Optional[str] = None,
    ) -> TransferResult:
        data = self._call_rpc_with_retry("shop_transfer", {
            "p_from_id": from_id,
            "p_to_id": to_id,
            "p_amount": amount,
            "p_type": transfer_type.value,
            "p_description": description,
        })

        status = data.get("status", "UNKNOWN")
        message = data.get("message", "Нет сообщения в ответе")

        if status == "SUCCESS":
            return TransferResult(
                success=True,
                message=message,
                transfer_id=data.get("transfer_id"),
                sender_balance=Decimal(str(data["sender_balance"])) if "sender_balance" in data else None,
                receiver_balance=Decimal(str(data["receiver_balance"])) if "receiver_balance" in data else None,
            )
        return TransferResult(success=False, message=message)

    def get_participants(self) -> list[dict]:
        response = self.supabase.table("participants").select("*").order("role,name").execute()
        return response.data

    def get_transfers(self, limit: int = 50) -> list[dict]:
        response = (
            self.supabase.table("transfers")
            .select("*, from:from_id(name,role), to:to_id(name,role)")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data