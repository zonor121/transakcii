from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
import os

# Импортируем твой рабочий клиент
from shop_client import FlowerShopClient, TransferType, TransferResult

app = FastAPI(title="Магазин 'Ромашка'")

# Разрешаем запросы (на случай если откроешь html отдельно)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем папку static для раздачи фронтенда
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

shop = FlowerShopClient()


class TransferRequest(BaseModel):
    from_id: str
    to_id: str
    amount: float = Field(gt=0)
    transfer_type: str
    description: Optional[str] = None


@app.get("/")
async def root():
    """Отдаёт index.html при заходе на localhost:8000"""
    from fastapi.responses import FileResponse
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/api/participants")
async def get_participants():
    return shop.get_participants()


@app.get("/api/transfers")
async def get_transfers(limit: int = 50):
    return shop.get_transfers(limit=limit)


@app.post("/api/transfer")
async def create_transfer(req: TransferRequest):
    try:
        t_type = TransferType(req.transfer_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Невалидный тип: {req.transfer_type}")

    result: TransferResult = shop.transfer(
        from_id=req.from_id,
        to_id=req.to_id,
        amount=req.amount,
        transfer_type=t_type,
        description=req.description,
    )

    if not result.success:
        raise HTTPException(status_code=422, detail=result.message)

    return {
        "message": result.message,
        "transfer_id": result.transfer_id,
        "sender_balance": str(result.sender_balance),
        "receiver_balance": str(result.receiver_balance),
    }