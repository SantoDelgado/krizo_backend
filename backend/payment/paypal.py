from paypalrestsdk import Payment as PayPalPayment, configure
from fastapi import HTTPException, status
from typing import Dict, Optional
import os
from dotenv import load_dotenv

load_dotenv()

# Configurar PayPal
configure({
    "mode": os.getenv("PAYPAL_MODE", "sandbox"),  # sandbox o live
    "client_id": os.getenv("PAYPAL_CLIENT_ID"),
    "client_secret": os.getenv("PAYPAL_CLIENT_SECRET")
})

class PayPalService:
    @staticmethod
    async def create_payment(
        amount: float,
        currency: str,
        description: str,
        return_url: str,
        cancel_url: str
    ) -> Dict:
        try:
            payment = PayPalPayment({
                "intent": "sale",
                "payer": {
                    "payment_method": "paypal"
                },
                "redirect_urls": {
                    "return_url": return_url,
                    "cancel_url": cancel_url
                },
                "transactions": [{
                    "amount": {
                        "total": str(amount),
                        "currency": currency
                    },
                    "description": description
                }]
            })

            if payment.create():
                return {
                    "payment_id": payment.id,
                    "approval_url": next(
                        (link.href for link in payment.links if link.rel == "approval_url"),
                        None
                    )
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Error al crear el pago en PayPal: {payment.error}"
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error en la integración con PayPal: {str(e)}"
            )

    @staticmethod
    async def execute_payment(payment_id: str, payer_id: str) -> Dict:
        try:
            payment = PayPalPayment.find(payment_id)
            if payment.execute({"payer_id": payer_id}):
                return {
                    "payment_id": payment.id,
                    "status": payment.state,
                    "amount": payment.transactions[0].amount.total,
                    "currency": payment.transactions[0].amount.currency
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Error al ejecutar el pago en PayPal: {payment.error}"
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error en la integración con PayPal: {str(e)}"
            )

    @staticmethod
    async def get_payment_details(payment_id: str) -> Dict:
        try:
            payment = PayPalPayment.find(payment_id)
            return {
                "payment_id": payment.id,
                "status": payment.state,
                "amount": payment.transactions[0].amount.total,
                "currency": payment.transactions[0].amount.currency,
                "create_time": payment.create_time,
                "update_time": payment.update_time
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al obtener detalles del pago: {str(e)}"
            )

    @staticmethod
    async def refund_payment(payment_id: str, amount: Optional[float] = None) -> Dict:
        try:
            payment = PayPalPayment.find(payment_id)
            refund = payment.refund({
                "amount": {
                    "total": str(amount) if amount else payment.transactions[0].amount.total,
                    "currency": payment.transactions[0].amount.currency
                }
            })

            if refund.success():
                return {
                    "refund_id": refund.id,
                    "status": refund.state,
                    "amount": refund.amount.total,
                    "currency": refund.amount.currency
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Error al procesar el reembolso: {refund.error}"
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error en la integración con PayPal: {str(e)}"
            ) 