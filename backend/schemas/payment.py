from pydantic import BaseModel, constr
from typing import Optional, Dict
from datetime import datetime
from database.models import PaymentStatus, TransactionType
from pydantic import Field
from enum import Enum

class WalletBase(BaseModel):
    balance: float
    currency: str = "USD"

class WalletCreate(WalletBase):
    pass

class Wallet(WalletBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class PaymentMethodEnum(str, Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    WALLET = "wallet"
    PAYPAL = "paypal"
    BINANCE_PAY = "binance_pay"
    CRYPTO = "crypto"

class PaymentMethodBase(BaseModel):
    type: PaymentMethodEnum
    is_default: bool = False

class PaymentMethodCreate(PaymentMethodBase):
    details: Dict  # Información de la tarjeta/cuenta

class PaymentMethod(PaymentMethodBase):
    id: int
    user_id: int
    details: Dict
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class TransactionBase(BaseModel):
    amount: float
    type: TransactionType
    description: str
    meta_data: Optional[Dict] = None

class TransactionCreate(TransactionBase):
    pass

class Transaction(TransactionBase):
    id: int
    user_id: int
    wallet_id: int
    status: PaymentStatus
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class PaymentBase(BaseModel):
    amount: float = Field(..., gt=0, description="Monto del pago")
    currency: str = Field(default="USD", description="Moneda del pago")
    crypto_currency: Optional[str] = Field(None, description="Moneda crypto (BTC, ETH, BNB, etc.)")
    crypto_amount: Optional[float] = Field(None, description="Cantidad en crypto")
    payment_provider: str = Field(..., description="Proveedor de pago")
    payment_provider_id: Optional[str] = Field(None, description="ID de transacción del proveedor")
    binance_prepay_id: Optional[str] = Field(None, description="ID de prepago de Binance")
    binance_qr_code: Optional[str] = Field(None, description="QR code para pagos Binance")
    binance_deep_link: Optional[str] = Field(None, description="Deep link para app Binance")

class PaymentCreate(PaymentBase):
    pass

class Payment(PaymentBase):
    id: int
    transaction_id: int
    status: PaymentStatus
    payment_provider: str
    payment_provider_id: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

class PaymentResponse(BaseModel):
    transaction: Transaction
    payment: Payment
    wallet: Wallet

class BinancePayRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Monto del pago")
    currency: str = Field(default="USD", description="Moneda fiat")
    crypto_currency: Optional[str] = Field(default="BNB", description="Moneda crypto preferida")
    description: Optional[str] = Field(None, description="Descripción del pago")
    return_url: Optional[str] = Field(None, description="URL de retorno después del pago")

class BinancePayResponse(BaseModel):
    prepay_id: str = Field(..., description="ID de prepago de Binance")
    qr_code: str = Field(..., description="QR code para el pago")
    deep_link: str = Field(..., description="Deep link para la app Binance")
    amount: float = Field(..., description="Monto del pago")
    currency: str = Field(..., description="Moneda del pago")
    crypto_amount: Optional[float] = Field(None, description="Cantidad en crypto")
    crypto_currency: Optional[str] = Field(None, description="Moneda crypto")
    status: str = Field(..., description="Estado del pago")
    expires_at: datetime = Field(..., description="Fecha de expiración")

class BinancePayStatus(BaseModel):
    prepay_id: str = Field(..., description="ID de prepago")
    status: str = Field(..., description="Estado del pago")
    transaction_id: Optional[str] = Field(None, description="ID de transacción de Binance")
    amount: float = Field(..., description="Monto pagado")
    currency: str = Field(..., description="Moneda del pago")
    crypto_amount: Optional[float] = Field(None, description="Cantidad en crypto")
    crypto_currency: Optional[str] = Field(None, description="Moneda crypto")
    paid_at: Optional[datetime] = Field(None, description="Fecha de pago")

class CryptoPaymentRequest(BaseModel):
    amount: float = Field(..., gt=0, description="Monto en USD")
    crypto_currency: str = Field(..., description="Moneda crypto (BTC, ETH, BNB, etc.)")
    wallet_address: Optional[str] = Field(None, description="Dirección de wallet para recibir")
    description: Optional[str] = Field(None, description="Descripción del pago")

class CryptoPaymentResponse(BaseModel):
    payment_id: str = Field(..., description="ID del pago")
    amount_usd: float = Field(..., description="Monto en USD")
    crypto_amount: float = Field(..., description="Cantidad en crypto")
    crypto_currency: str = Field(..., description="Moneda crypto")
    wallet_address: str = Field(..., description="Dirección de wallet para recibir")
    qr_code: str = Field(..., description="QR code con la dirección")
    exchange_rate: float = Field(..., description="Tasa de cambio")
    expires_at: datetime = Field(..., description="Fecha de expiración") 