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

# Патч HTTP/1.1 + короткий таймаут
_httpx_orig_init = httpx.Client.__init__
def _httpx_patched_init(self, *args, **kwargs):
    kwargs["http2"] = False
    kwargs.setdefault("timeout", httpx.Timeout(10.0))
    return _httpx_orig_init(self, *args, **kwargs)
httpx.Client.__init__ = _httpx_patched_init


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
    def __init__(self, max_retries: int = 3):
        url = os.environ["SUPABASE_URL"]
        key = os.environ["SUPABASE_KEY"]
        self.max_retries = max_retries
        self._url = url
        self._key = key

    def _get_client(self) -> Client:
        """Возвращает свежий клиент для каждого запроса"""
        return create_client(self._url, self._key)

    def _safe_execute(self, request_builder):
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            client = self._get_client()  # Свежий клиент = свежий TCP-сокет
            try:
                result = request_builder.execute()
                return result  # Убран client.close(), он не нужен
            except (httpx.ReadError, httpx.RemoteProtocolError, 
                    httpx.ConnectError, ConnectionResetError) as e:
                last_error = e
                wait = attempt * 1.0
                print(f"  ⚠️  Сбой сети (попытка {attempt}/{self.max_retries}): "
                      f"{type(e).__name__}. Повтор через {wait}s...")
                time.sleep(wait)
            except Exception as e:
                raise
        
        raise Exception(f"Не удалось выполнить запрос после {self.max_retries} попыток: {last_error}")

    def transfer(self, from_id: str, to_id: str, amount: float,
                 transfer_type: TransferType, description: Optional[str] = None) -> TransferResult:
        response = self._safe_execute(
            self._get_client().rpc("shop_transfer", {
                "p_from_id": from_id, "p_to_id": to_id,
                "p_amount": amount, "p_type": transfer_type.value,
                "p_description": description,
            })
        )
        
        data = response.data
        if isinstance(data, list):
            data = data[0] if data else {}
            
        status = data.get("status", "UNKNOWN")
        message = data.get("message", "Нет сообщения в ответе")
        
        if status == "SUCCESS":
            return TransferResult(success=True, message=message,
                transfer_id=data.get("transfer_id"),
                sender_balance=Decimal(str(data["sender_balance"])) if "sender_balance" in data else None,
                receiver_balance=Decimal(str(data["receiver_balance"])) if "receiver_balance" in data else None)
        return TransferResult(success=False, message=message)

    def get_participants(self) -> list[dict]:
        response = self._safe_execute(
            self._get_client().table("participants").select("*").order("role,name")
        )
        return response.data

    def get_transfers(self, limit: int = 50) -> list[dict]:
        response = self._safe_execute(
            self._get_client().table("transfers")
            .select("*, from:from_id(name,role), to:to_id(name,role)")
            .order("created_at", desc=True).limit(limit)
        )
        return response.data