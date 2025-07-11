import os
import hmac
import hashlib
import time
import json
import requests
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from datetime import datetime, timedelta
import qrcode
import base64
from io import BytesIO

class BinancePayService:
    def __init__(self):
        self.api_key = os.getenv("BINANCE_API_KEY")
        self.secret_key = os.getenv("BINANCE_SECRET_KEY")
        self.base_url = "https://api.binance.com"  # Para producción
        self.test_url = "https://testnet.binance.vision"  # Para testing
        self.is_testnet = os.getenv("BINANCE_TESTNET", "false").lower() == "true"
        
        if not self.api_key or not self.secret_key:
            raise ValueError("BINANCE_API_KEY y BINANCE_SECRET_KEY deben estar configurados")

    def _get_base_url(self) -> str:
        """Obtener URL base según el entorno"""
        return self.test_url if self.is_testnet else self.base_url

    def _generate_signature(self, payload: str) -> str:
        """Generar firma HMAC SHA256 para autenticación"""
        return hmac.new(
            self.secret_key.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Realizar petición autenticada a la API de Binance"""
        url = f"{self._get_base_url()}{endpoint}"
        timestamp = str(int(time.time() * 1000))
        
        headers = {
            "Content-Type": "application/json",
            "BinancePay-Timestamp": timestamp,
            "BinancePay-Nonce": timestamp,
            "BinancePay-Certificate-SN": self.api_key
        }
        
        if data:
            payload = json.dumps(data)
            headers["BinancePay-Signature"] = self._generate_signature(payload)
        
        try:
            if method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data)
            else:
                response = requests.get(url, headers=headers)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error en la comunicación con Binance: {str(e)}"
            )

    def create_payment_order(
        self,
        amount: float,
        currency: str = "USD",
        crypto_currency: str = "BNB",
        description: str = "Pago AutoAssist",
        return_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Crear orden de pago con Binance Pay"""
        
        # Obtener tasa de cambio actual
        exchange_rate = self._get_exchange_rate(currency, crypto_currency)
        crypto_amount = amount / exchange_rate
        
        data = {
            "env": {
                "terminalType": "WEB"
            },
            "merchantTradeNo": f"order_{int(time.time() * 1000)}",
            "orderAmount": amount,
            "currency": currency,
            "goods": {
                "goodsType": "01",
                "goodsCategory": "D000",
                "referenceGoodsId": "SK123456789",
                "goodsName": description,
                "goodsDetail": description
            }
        }
        
        if return_url:
            data["returnUrl"] = return_url
        
        try:
            response = self._make_request("POST", "/binancepay/openapi/v2/order", data)
            
            if response.get("status") == "SUCCESS":
                result = response.get("data", {})
                return {
                    "prepay_id": result.get("prepayId"),
                    "qr_code": result.get("qrCode"),
                    "deep_link": result.get("deeplink"),
                    "amount": amount,
                    "currency": currency,
                    "crypto_amount": crypto_amount,
                    "crypto_currency": crypto_currency,
                    "status": "PENDING",
                    "expires_at": datetime.utcnow() + timedelta(minutes=15)
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Error al crear orden de pago: {response.get('message', 'Error desconocido')}"
                )
                
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al procesar pago con Binance: {str(e)}"
            )

    def check_payment_status(self, prepay_id: str) -> Dict[str, Any]:
        """Verificar estado de un pago"""
        
        data = {
            "prepayId": prepay_id
        }
        
        try:
            response = self._make_request("POST", "/binancepay/openapi/v2/order", data)
            
            if response.get("status") == "SUCCESS":
                result = response.get("data", {})
                return {
                    "prepay_id": prepay_id,
                    "status": result.get("status"),
                    "transaction_id": result.get("transactionId"),
                    "amount": result.get("orderAmount"),
                    "currency": result.get("currency"),
                    "paid_at": datetime.utcnow() if result.get("status") == "PAID" else None
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Error al verificar estado: {response.get('message', 'Error desconocido')}"
                )
                
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al verificar estado del pago: {str(e)}"
            )

    def _get_exchange_rate(self, fiat_currency: str, crypto_currency: str) -> float:
        """Obtener tasa de cambio actual"""
        try:
            # Usar API pública de Binance para obtener precio
            symbol = f"{crypto_currency}{fiat_currency}"
            response = requests.get(f"{self._get_base_url()}/api/v3/ticker/price", params={"symbol": symbol})
            response.raise_for_status()
            
            data = response.json()
            return float(data.get("price", 0))
            
        except Exception as e:
            # Si falla, usar tasa por defecto
            default_rates = {
                "BNB": 300.0,  # BNB a USD
                "BTC": 45000.0,  # BTC a USD
                "ETH": 3000.0,  # ETH a USD
                "USDT": 1.0,  # USDT a USD
            }
            return default_rates.get(crypto_currency, 1.0)

    def create_crypto_payment(
        self,
        amount_usd: float,
        crypto_currency: str,
        wallet_address: Optional[str] = None
    ) -> Dict[str, Any]:
        """Crear pago directo con crypto (sin Binance Pay)"""
        
        # Generar dirección de wallet si no se proporciona
        if not wallet_address:
            wallet_address = self._generate_wallet_address(crypto_currency)
        
        # Obtener tasa de cambio
        exchange_rate = self._get_exchange_rate("USD", crypto_currency)
        crypto_amount = amount_usd / exchange_rate
        
        # Generar QR code
        qr_code = self._generate_qr_code(wallet_address)
        
        return {
            "payment_id": f"crypto_{int(time.time() * 1000)}",
            "amount_usd": amount_usd,
            "crypto_amount": crypto_amount,
            "crypto_currency": crypto_currency,
            "wallet_address": wallet_address,
            "qr_code": qr_code,
            "exchange_rate": exchange_rate,
            "expires_at": datetime.utcnow() + timedelta(hours=1)
        }

    def _generate_wallet_address(self, crypto_currency: str) -> str:
        """Generar dirección de wallet (simulado)"""
        # En producción, esto debería generar direcciones reales
        # o usar un servicio de wallet management
        
        addresses = {
            "BTC": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
            "ETH": "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6",
            "BNB": "bnb1jxfh2g85q3v0tdq56fnevx6xcxtcnhtsmcu64m",
            "USDT": "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6"
        }
        
        return addresses.get(crypto_currency, "0x0000000000000000000000000000000000000000")

    def _generate_qr_code(self, data: str) -> str:
        """Generar QR code en base64"""
        try:
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convertir a base64
            buffer = BytesIO()
            img.save(buffer, format="PNG")
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            # Si falla la generación del QR, devolver solo la dirección
            return data

    def get_supported_cryptocurrencies(self) -> Dict[str, Any]:
        """Obtener lista de criptomonedas soportadas"""
        return {
            "binance_pay": [
                {"symbol": "BNB", "name": "Binance Coin"},
                {"symbol": "BTC", "name": "Bitcoin"},
                {"symbol": "ETH", "name": "Ethereum"},
                {"symbol": "USDT", "name": "Tether"},
                {"symbol": "BUSD", "name": "Binance USD"}
            ],
            "direct_crypto": [
                {"symbol": "BTC", "name": "Bitcoin", "network": "Bitcoin"},
                {"symbol": "ETH", "name": "Ethereum", "network": "Ethereum"},
                {"symbol": "BNB", "name": "Binance Coin", "network": "BSC"},
                {"symbol": "USDT", "name": "Tether", "network": "Ethereum"},
                {"symbol": "USDC", "name": "USD Coin", "network": "Ethereum"}
            ]
        }

    def refund_payment(self, transaction_id: str, amount: float) -> Dict[str, Any]:
        """Procesar reembolso de un pago"""
        # Nota: Los reembolsos en Binance Pay requieren configuración especial
        # y aprobación de Binance
        
        data = {
            "refundRequestId": f"refund_{int(time.time() * 1000)}",
            "transactionId": transaction_id,
            "refundAmount": amount
        }
        
        try:
            response = self._make_request("POST", "/binancepay/openapi/v2/refund", data)
            
            if response.get("status") == "SUCCESS":
                return {
                    "refund_id": response.get("data", {}).get("refundId"),
                    "status": "PROCESSING",
                    "amount": amount
                }
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Error al procesar reembolso: {response.get('message', 'Error desconocido')}"
                )
                
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error al procesar reembolso: {str(e)}"
            ) 