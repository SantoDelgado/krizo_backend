from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List
from database.database import get_db
from database.models import User, Wallet, Transaction, Payment, PaymentMethod, PaymentStatus, TransactionType
from schemas.payment import (
    Wallet as WalletSchema,
    PaymentMethod as PaymentMethodSchema,
    PaymentMethodCreate,
    PaymentMethodEnum,
    Transaction as TransactionSchema,
    TransactionCreate,
    Payment as PaymentSchema,
    PaymentCreate,
    PaymentResponse,
    BinancePayRequest,
    BinancePayResponse,
    BinancePayStatus,
    CryptoPaymentRequest,
    CryptoPaymentResponse
)
from auth.jwt import get_current_active_user
from datetime import datetime
from payment.paypal import PayPalService
from payment.binance import BinancePayService
import os

router = APIRouter(prefix="/payments", tags=["payments"])

# Inicializar servicios de pago
try:
    binance_service = BinancePayService()
except ValueError:
    print("⚠️ Binance Pay no disponible - credenciales no configuradas")
    binance_service = None

@router.post("/wallet", response_model=WalletSchema)
async def create_wallet(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Verificar si el usuario ya tiene una billetera
    existing_wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
    if existing_wallet:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario ya tiene una billetera"
        )
    
    # Crear nueva billetera
    wallet = Wallet(user_id=current_user.id)
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return wallet

@router.get("/wallet", response_model=WalletSchema)
async def get_wallet(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Billetera no encontrada"
        )
    return wallet

@router.post("/methods", response_model=PaymentMethodSchema)
async def add_payment_method(
    payment_method: PaymentMethodCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Si es el método por defecto, desactivar otros métodos por defecto
    if payment_method.is_default:
        db.query(PaymentMethod).filter(
            PaymentMethod.user_id == current_user.id,
            PaymentMethod.is_default == True
        ).update({"is_default": False})
    
    # Crear nuevo método de pago
    db_payment_method = PaymentMethod(
        user_id=current_user.id,
        type=payment_method.type,
        is_default=payment_method.is_default,
        details=payment_method.details
    )
    db.add(db_payment_method)
    db.commit()
    db.refresh(db_payment_method)
    return db_payment_method

@router.get("/methods", response_model=List[PaymentMethodSchema])
async def list_payment_methods(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return db.query(PaymentMethod).filter(PaymentMethod.user_id == current_user.id).all()

@router.put("/methods/{method_id}", response_model=PaymentMethodSchema)
async def update_payment_method(
    method_id: int,
    payment_method_update: PaymentMethodCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Verificar que el método de pago existe y pertenece al usuario
    db_payment_method = db.query(PaymentMethod).filter(
        PaymentMethod.id == method_id,
        PaymentMethod.user_id == current_user.id
    ).first()
    
    if not db_payment_method:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Método de pago no encontrado"
        )
    
    # Si se está estableciendo como predeterminado, desactivar otros
    if payment_method_update.is_default:
        db.query(PaymentMethod).filter(
            PaymentMethod.user_id == current_user.id,
            PaymentMethod.is_default == True,
            PaymentMethod.id != method_id
        ).update({"is_default": False})
    
    # Actualizar el método de pago
    db_payment_method.type = payment_method_update.type
    db_payment_method.is_default = payment_method_update.is_default
    db_payment_method.details = payment_method_update.details
    
    db.commit()
    db.refresh(db_payment_method)
    return db_payment_method

@router.delete("/methods/{method_id}")
async def delete_payment_method(
    method_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Verificar que el método de pago existe y pertenece al usuario
    db_payment_method = db.query(PaymentMethod).filter(
        PaymentMethod.id == method_id,
        PaymentMethod.user_id == current_user.id
    ).first()
    
    if not db_payment_method:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Método de pago no encontrado"
        )
    
    # Verificar que no sea el único método de pago
    total_methods = db.query(PaymentMethod).filter(
        PaymentMethod.user_id == current_user.id
    ).count()
    
    if total_methods <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar el único método de pago"
        )
    
    # Eliminar el método de pago
    db.delete(db_payment_method)
    db.commit()
    
    return {"message": "Método de pago eliminado exitosamente"}

@router.put("/methods/{method_id}/default")
async def set_default_payment_method(
    method_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Verificar que el método de pago existe y pertenece al usuario
    db_payment_method = db.query(PaymentMethod).filter(
        PaymentMethod.id == method_id,
        PaymentMethod.user_id == current_user.id
    ).first()
    
    if not db_payment_method:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Método de pago no encontrado"
        )
    
    # Desactivar todos los métodos predeterminados del usuario
    db.query(PaymentMethod).filter(
        PaymentMethod.user_id == current_user.id,
        PaymentMethod.is_default == True
    ).update({"is_default": False})
    
    # Establecer este método como predeterminado
    db_payment_method.is_default = True
    db.commit()
    db.refresh(db_payment_method)
    
    return {"message": "Método de pago establecido como predeterminado", "method": db_payment_method}

@router.post("/deposit", response_model=PaymentResponse)
async def deposit_money(
    payment: PaymentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Verificar que el usuario tenga una billetera
    wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Billetera no encontrada"
        )
    
    # Verificar el método de pago
    payment_method = db.query(PaymentMethod).filter(
        PaymentMethod.id == payment.payment_method_id,
        PaymentMethod.user_id == current_user.id
    ).first()
    if not payment_method:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Método de pago no encontrado"
        )
    
    # Crear la transacción
    transaction = Transaction(
        user_id=current_user.id,
        wallet_id=wallet.id,
        amount=payment.amount,
        type=TransactionType.DEPOSIT,
        status=PaymentStatus.PENDING,
        description="Depósito a billetera"
    )
    db.add(transaction)
    db.flush()
    
    # Crear el pago
    db_payment = Payment(
        transaction_id=transaction.id,
        payment_method_id=payment.payment_method_id,
        amount=payment.amount,
        currency=payment.currency,
        payment_provider="stripe",  # Esto debería venir de la configuración
        payment_provider_id="temp_id"  # Esto debería venir del proveedor de pagos
    )
    db.add(db_payment)
    
    # TODO: Integrar con el proveedor de pagos real
    # Por ahora, simulamos un pago exitoso
    transaction.status = PaymentStatus.COMPLETED
    db_payment.status = PaymentStatus.COMPLETED
    wallet.balance += payment.amount
    
    db.commit()
    db.refresh(transaction)
    db.refresh(db_payment)
    db.refresh(wallet)
    
    return PaymentResponse(
        transaction=transaction,
        payment=db_payment,
        wallet=wallet
    )

@router.post("/withdraw", response_model=PaymentResponse)
async def withdraw_money(
    payment: PaymentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Verificar que el usuario tenga una billetera
    wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Billetera no encontrada"
        )
    
    # Verificar saldo suficiente
    if wallet.balance < payment.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Saldo insuficiente"
        )
    
    # Verificar el método de pago
    payment_method = db.query(PaymentMethod).filter(
        PaymentMethod.id == payment.payment_method_id,
        PaymentMethod.user_id == current_user.id
    ).first()
    if not payment_method:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Método de pago no encontrado"
        )
    
    # Crear la transacción
    transaction = Transaction(
        user_id=current_user.id,
        wallet_id=wallet.id,
        amount=payment.amount,
        type=TransactionType.WITHDRAWAL,
        status=PaymentStatus.PENDING,
        description="Retiro de billetera"
    )
    db.add(transaction)
    db.flush()
    
    # Crear el pago
    db_payment = Payment(
        transaction_id=transaction.id,
        payment_method_id=payment.payment_method_id,
        amount=payment.amount,
        currency=payment.currency,
        payment_provider="stripe",  # Esto debería venir de la configuración
        payment_provider_id="temp_id"  # Esto debería venir del proveedor de pagos
    )
    db.add(db_payment)
    
    # TODO: Integrar con el proveedor de pagos real
    # Por ahora, simulamos un pago exitoso
    transaction.status = PaymentStatus.COMPLETED
    db_payment.status = PaymentStatus.COMPLETED
    wallet.balance -= payment.amount
    
    db.commit()
    db.refresh(transaction)
    db.refresh(db_payment)
    db.refresh(wallet)
    
    return PaymentResponse(
        transaction=transaction,
        payment=db_payment,
        wallet=wallet
    )

@router.get("/transactions", response_model=List[TransactionSchema])
async def list_transactions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    return db.query(Transaction).filter(Transaction.user_id == current_user.id).all()

@router.post("/deposit/paypal", response_model=PaymentResponse)
async def create_paypal_deposit(
    payment: PaymentCreate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Verificar que el usuario tenga una billetera
    wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Billetera no encontrada"
        )
    
    # Crear la transacción
    transaction = Transaction(
        user_id=current_user.id,
        wallet_id=wallet.id,
        amount=payment.amount,
        type=TransactionType.DEPOSIT,
        status=PaymentStatus.PENDING,
        description="Depósito a billetera vía PayPal"
    )
    db.add(transaction)
    db.flush()
    
    # Crear el pago en PayPal
    base_url = str(request.base_url)
    paypal_payment = await PayPalService.create_payment(
        amount=payment.amount,
        currency=payment.currency,
        description=f"Depósito a billetera - Usuario {current_user.id}",
        return_url=f"{base_url}payments/paypal/success?transaction_id={transaction.id}",
        cancel_url=f"{base_url}payments/paypal/cancel?transaction_id={transaction.id}"
    )
    
    # Crear el registro de pago
    db_payment = Payment(
        transaction_id=transaction.id,
        payment_method_id=payment.payment_method_id,
        amount=payment.amount,
        currency=payment.currency,
        payment_provider="paypal",
        payment_provider_id=paypal_payment["payment_id"]
    )
    db.add(db_payment)
    db.commit()
    
    return {
        "transaction": transaction,
        "payment": db_payment,
        "wallet": wallet,
        "approval_url": paypal_payment["approval_url"]
    }

@router.get("/paypal/success")
async def paypal_success(
    transaction_id: int,
    PayerID: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Obtener la transacción
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transacción no encontrada"
        )
    
    # Obtener el pago
    payment = db.query(Payment).filter(Payment.transaction_id == transaction.id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pago no encontrado"
        )
    
    # Ejecutar el pago en PayPal
    paypal_result = await PayPalService.execute_payment(
        payment_id=payment.payment_provider_id,
        payer_id=PayerID
    )
    
    # Actualizar el estado de la transacción y el pago
    transaction.status = PaymentStatus.COMPLETED
    payment.status = PaymentStatus.COMPLETED
    
    # Actualizar el saldo de la billetera
    wallet = db.query(Wallet).filter(Wallet.id == transaction.wallet_id).first()
    wallet.balance += transaction.amount
    
    db.commit()
    db.refresh(transaction)
    db.refresh(payment)
    db.refresh(wallet)
    
    return {
        "transaction": transaction,
        "payment": payment,
        "wallet": wallet
    }

@router.get("/paypal/cancel")
async def paypal_cancel(
    transaction_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Obtener la transacción
    transaction = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transacción no encontrada"
        )
    
    # Obtener el pago
    payment = db.query(Payment).filter(Payment.transaction_id == transaction.id).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pago no encontrado"
        )
    
    # Actualizar el estado de la transacción y el pago
    transaction.status = PaymentStatus.FAILED
    payment.status = PaymentStatus.FAILED
    
    db.commit()
    db.refresh(transaction)
    db.refresh(payment)
    
    return {
        "transaction": transaction,
        "payment": payment
    }

@router.post("/refund/{payment_id}")
async def refund_payment(
    payment_id: int,
    amount: float = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Obtener el pago
    payment = db.query(Payment).filter(
        Payment.id == payment_id,
        Payment.transaction.has(user_id=current_user.id)
    ).first()
    
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pago no encontrado"
        )
    
    # Verificar que el pago esté completado
    if payment.status != PaymentStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El pago debe estar completado para poder reembolsarlo"
        )
    
    # Procesar el reembolso en PayPal
    refund_result = await PayPalService.refund_payment(
        payment_id=payment.payment_provider_id,
        amount=amount
    )
    
    # Crear la transacción de reembolso
    transaction = Transaction(
        user_id=current_user.id,
        wallet_id=payment.transaction.wallet_id,
        amount=float(refund_result["amount"]),
        type=TransactionType.REFUND,
        status=PaymentStatus.COMPLETED,
        description=f"Reembolso del pago {payment.id}",
        meta_data={"original_payment_id": payment.id}
    )
    db.add(transaction)
    
    # Actualizar el saldo de la billetera
    wallet = db.query(Wallet).filter(Wallet.id == transaction.wallet_id).first()
    wallet.balance -= float(refund_result["amount"])
    
    # Actualizar el estado del pago original
    payment.status = PaymentStatus.REFUNDED
    
    db.commit()
    db.refresh(transaction)
    db.refresh(payment)
    db.refresh(wallet)
    
    return {
        "transaction": transaction,
        "payment": payment,
        "wallet": wallet,
        "refund_details": refund_result
    }

@router.post("/binance/create", response_model=BinancePayResponse)
async def create_binance_payment(
    payment_request: BinancePayRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Crear pago con Binance Pay"""
    if not binance_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio de Binance Pay no disponible"
        )
    
    try:
        # Crear orden de pago con Binance
        binance_order = binance_service.create_payment_order(
            amount=payment_request.amount,
            currency=payment_request.currency,
            crypto_currency=payment_request.crypto_currency,
            description=payment_request.description or f"Pago Krizo - Usuario {current_user.id}",
            return_url=payment_request.return_url
        )
        
        # Crear transacción en la base de datos
        wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
        if not wallet:
            # Crear wallet si no existe
            wallet = Wallet(user_id=current_user.id)
            db.add(wallet)
            db.flush()
        
        transaction = Transaction(
            user_id=current_user.id,
            wallet_id=wallet.id,
            amount=payment_request.amount,
            type=TransactionType.DEPOSIT,
            status=PaymentStatus.PENDING,
            description=payment_request.description or "Depósito con Binance Pay"
        )
        db.add(transaction)
        db.flush()
        
        # Crear registro de pago
        payment = Payment(
            transaction_id=transaction.id,
            amount=payment_request.amount,
            currency=payment_request.currency,
            crypto_currency=payment_request.crypto_currency,
            crypto_amount=binance_order.get("crypto_amount"),
            payment_provider="binance_pay",
            payment_provider_id=binance_order["prepay_id"],
            binance_prepay_id=binance_order["prepay_id"],
            binance_qr_code=binance_order["qr_code"],
            binance_deep_link=binance_order["deep_link"],
            status=PaymentStatus.PENDING
        )
        db.add(payment)
        db.commit()
        
        return BinancePayResponse(
            prepay_id=binance_order["prepay_id"],
            qr_code=binance_order["qr_code"],
            deep_link=binance_order["deep_link"],
            amount=binance_order["amount"],
            currency=binance_order["currency"],
            crypto_amount=binance_order.get("crypto_amount"),
            crypto_currency=binance_order.get("crypto_currency"),
            status=binance_order["status"],
            expires_at=binance_order["expires_at"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear pago con Binance: {str(e)}"
        )

@router.get("/binance/status/{prepay_id}", response_model=BinancePayStatus)
async def check_binance_payment_status(
    prepay_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Verificar estado de un pago de Binance Pay"""
    if not binance_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio de Binance Pay no disponible"
        )
    
    try:
        # Verificar estado con Binance
        binance_status = binance_service.check_payment_status(prepay_id)
        
        # Si el pago fue completado, actualizar la base de datos
        if binance_status["status"] == "PAID":
            payment = db.query(Payment).filter(
                Payment.binance_prepay_id == prepay_id
            ).first()
            
            if payment:
                payment.status = PaymentStatus.COMPLETED
                payment.payment_provider_id = binance_status.get("transaction_id")
                
                # Actualizar transacción
                transaction = db.query(Transaction).filter(
                    Transaction.id == payment.transaction_id
                ).first()
                
                if transaction:
                    transaction.status = PaymentStatus.COMPLETED
                    
                    # Actualizar saldo de la wallet
                    wallet = db.query(Wallet).filter(Wallet.id == transaction.wallet_id).first()
                    if wallet:
                        wallet.balance += transaction.amount
                
                db.commit()
        
        return BinancePayStatus(
            prepay_id=prepay_id,
            status=binance_status["status"],
            transaction_id=binance_status.get("transaction_id"),
            amount=binance_status["amount"],
            currency=binance_status["currency"],
            crypto_amount=binance_status.get("crypto_amount"),
            crypto_currency=binance_status.get("crypto_currency"),
            paid_at=binance_status.get("paid_at")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al verificar estado del pago: {str(e)}"
        )

@router.post("/crypto/create", response_model=CryptoPaymentResponse)
async def create_crypto_payment(
    payment_request: CryptoPaymentRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Crear pago directo con crypto (sin Binance Pay)"""
    if not binance_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio de Binance Pay no disponible"
        )
    
    try:
        # Crear pago crypto
        crypto_payment = binance_service.create_crypto_payment(
            amount_usd=payment_request.amount,
            crypto_currency=payment_request.crypto_currency,
            wallet_address=payment_request.wallet_address
        )
        
        # Crear transacción en la base de datos
        wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
        if not wallet:
            wallet = Wallet(user_id=current_user.id)
            db.add(wallet)
            db.flush()
        
        transaction = Transaction(
            user_id=current_user.id,
            wallet_id=wallet.id,
            amount=payment_request.amount,
            type=TransactionType.DEPOSIT,
            status=PaymentStatus.PENDING,
            description=f"Depósito con {payment_request.crypto_currency}"
        )
        db.add(transaction)
        db.flush()
        
        # Crear registro de pago
        payment = Payment(
            transaction_id=transaction.id,
            amount=payment_request.amount,
            currency="USD",
            crypto_currency=payment_request.crypto_currency,
            crypto_amount=crypto_payment["crypto_amount"],
            payment_provider="crypto_direct",
            payment_provider_id=crypto_payment["payment_id"],
            status=PaymentStatus.PENDING
        )
        db.add(payment)
        db.commit()
        
        return CryptoPaymentResponse(
            payment_id=crypto_payment["payment_id"],
            amount_usd=crypto_payment["amount_usd"],
            crypto_amount=crypto_payment["crypto_amount"],
            crypto_currency=crypto_payment["crypto_currency"],
            wallet_address=crypto_payment["wallet_address"],
            qr_code=crypto_payment["qr_code"],
            exchange_rate=crypto_payment["exchange_rate"],
            expires_at=crypto_payment["expires_at"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear pago crypto: {str(e)}"
        )

@router.get("/crypto/supported")
async def get_supported_cryptocurrencies():
    """Obtener lista de criptomonedas soportadas"""
    if not binance_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Servicio de Binance Pay no disponible"
        )
    
    try:
        return binance_service.get_supported_cryptocurrencies()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener criptomonedas soportadas: {str(e)}"
        )

@router.post("/binance/refund/{transaction_id}")
async def refund_binance_payment(
    transaction_id: str,
    amount: float,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Procesar reembolso de un pago de Binance Pay"""
    try:
        # Verificar que el usuario sea el propietario del pago
        payment = db.query(Payment).filter(
            Payment.payment_provider_id == transaction_id,
            Payment.transaction.has(user_id=current_user.id)
        ).first()
        
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pago no encontrado"
            )
        
        # Procesar reembolso con Binance
        refund_result = binance_service.refund_payment(transaction_id, amount)
        
        # Crear transacción de reembolso
        wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
        
        refund_transaction = Transaction(
            user_id=current_user.id,
            wallet_id=wallet.id,
            amount=amount,
            type=TransactionType.REFUND,
            status=PaymentStatus.COMPLETED,
            description=f"Reembolso de pago Binance {transaction_id}",
            meta_data={"original_payment_id": payment.id}
        )
        db.add(refund_transaction)
        
        # Actualizar saldo de la wallet
        wallet.balance += amount
        
        db.commit()
        
        return {
            "refund_id": refund_result["refund_id"],
            "status": refund_result["status"],
            "amount": refund_result["amount"],
            "message": "Reembolso procesado exitosamente"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar reembolso: {str(e)}"
        ) 