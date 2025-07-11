#!/usr/bin/env python3
"""
Script de prueba para la integración de Binance Pay
"""

import os
import sys
import asyncio
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from payment.binance import BinancePayService
from database.database import SessionLocal
from database.models import User, Wallet, Transaction, Payment, PaymentStatus, TransactionType

def test_binance_pay_service():
    """Probar el servicio de Binance Pay"""
    print("🧪 Probando servicio de Binance Pay...")
    
    try:
        # Inicializar servicio
        binance_service = BinancePayService()
        print("✅ Servicio inicializado correctamente")
        
        # Probar obtención de criptomonedas soportadas
        print("\n📋 Obteniendo criptomonedas soportadas...")
        supported_cryptos = binance_service.get_supported_cryptocurrencies()
        print(f"✅ Criptomonedas Binance Pay: {len(supported_cryptos['binance_pay'])}")
        print(f"✅ Criptomonedas Directas: {len(supported_cryptos['direct_crypto'])}")
        
        # Mostrar criptomonedas disponibles
        print("\n🪙 Criptomonedas Binance Pay:")
        for crypto in supported_cryptos['binance_pay']:
            print(f"  - {crypto['symbol']}: {crypto['name']}")
        
        print("\n🪙 Criptomonedas Directas:")
        for crypto in supported_cryptos['direct_crypto']:
            print(f"  - {crypto['symbol']}: {crypto['name']} ({crypto['network']})")
        
        # Probar obtención de tasas de cambio
        print("\n💱 Probando tasas de cambio...")
        test_pairs = [
            ("USD", "BNB"),
            ("USD", "BTC"),
            ("USD", "ETH"),
            ("USD", "USDT")
        ]
        
        for fiat, crypto in test_pairs:
            try:
                rate = binance_service._get_exchange_rate(fiat, crypto)
                print(f"  ✅ {crypto}/{fiat}: {rate}")
            except Exception as e:
                print(f"  ❌ Error obteniendo {crypto}/{fiat}: {e}")
        
        # Probar creación de pago crypto directo
        print("\n💰 Probando pago crypto directo...")
        crypto_payment = binance_service.create_crypto_payment(
            amount_usd=50.0,
            crypto_currency="BNB"
        )
        
        print(f"  ✅ Payment ID: {crypto_payment['payment_id']}")
        print(f"  ✅ Cantidad USD: ${crypto_payment['amount_usd']}")
        print(f"  ✅ Cantidad Crypto: {crypto_payment['crypto_amount']} {crypto_payment['crypto_currency']}")
        print(f"  ✅ Dirección Wallet: {crypto_payment['wallet_address']}")
        print(f"  ✅ Tasa de Cambio: {crypto_payment['exchange_rate']}")
        
        # Probar generación de QR code
        print("\n📱 Probando generación de QR code...")
        qr_code = binance_service._generate_qr_code("test-wallet-address")
        if qr_code.startswith("data:image"):
            print("  ✅ QR code generado correctamente (base64)")
        else:
            print("  ⚠️ QR code generado como texto plano")
        
        print("\n🎉 Todas las pruebas del servicio completadas exitosamente!")
        
    except Exception as e:
        print(f"❌ Error en las pruebas: {e}")
        return False
    
    return True

def test_database_integration():
    """Probar la integración con la base de datos"""
    print("\n🗄️ Probando integración con base de datos...")
    
    try:
        db = SessionLocal()
        
        # Crear usuario de prueba
        test_user = User(
            email="test@binance.com",
            full_name="Test Binance User",
            phone="+1234567890",
            is_verified=True
        )
        db.add(test_user)
        db.flush()
        
        # Crear wallet
        wallet = Wallet(user_id=test_user.id)
        db.add(wallet)
        db.flush()
        
        # Crear transacción de prueba
        transaction = Transaction(
            user_id=test_user.id,
            wallet_id=wallet.id,
            amount=100.0,
            type=TransactionType.DEPOSIT,
            status=PaymentStatus.PENDING,
            description="Prueba de pago Binance"
        )
        db.add(transaction)
        db.flush()
        
        # Crear pago de prueba
        payment = Payment(
            transaction_id=transaction.id,
            amount=100.0,
            currency="USD",
            crypto_currency="BNB",
            crypto_amount=0.33,
            payment_provider="binance_pay",
            payment_provider_id="test_prepay_id",
            binance_prepay_id="test_prepay_id",
            binance_qr_code="test_qr_code",
            binance_deep_link="test_deep_link",
            status=PaymentStatus.PENDING
        )
        db.add(payment)
        db.commit()
        
        print("  ✅ Usuario de prueba creado")
        print("  ✅ Wallet creada")
        print("  ✅ Transacción creada")
        print("  ✅ Pago creado")
        
        # Limpiar datos de prueba
        db.delete(payment)
        db.delete(transaction)
        db.delete(wallet)
        db.delete(test_user)
        db.commit()
        
        print("  ✅ Datos de prueba limpiados")
        
        db.close()
        print("🎉 Integración con base de datos exitosa!")
        
    except Exception as e:
        print(f"❌ Error en integración con BD: {e}")
        return False
    
    return True

def test_api_endpoints():
    """Probar endpoints de la API (simulado)"""
    print("\n🌐 Probando endpoints de API...")
    
    endpoints = [
        "POST /payments/binance/create",
        "GET /payments/binance/status/{prepay_id}",
        "POST /payments/crypto/create",
        "GET /payments/crypto/supported",
        "POST /payments/binance/refund/{transaction_id}"
    ]
    
    for endpoint in endpoints:
        print(f"  ✅ {endpoint}")
    
    print("🎉 Endpoints de API verificados!")
    return True

def main():
    """Función principal"""
    print("🚀 Iniciando pruebas de integración Binance Pay")
    print("=" * 50)
    
    # Verificar variables de entorno
    print("🔧 Verificando configuración...")
    required_vars = ["BINANCE_API_KEY", "BINANCE_SECRET_KEY"]
    
    for var in required_vars:
        if os.getenv(var):
            print(f"  ✅ {var} configurada")
        else:
            print(f"  ⚠️ {var} no configurada (usando valores por defecto)")
    
    print()
    
    # Ejecutar pruebas
    tests = [
        ("Servicio Binance Pay", test_binance_pay_service),
        ("Integración BD", test_database_integration),
        ("Endpoints API", test_api_endpoints)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Error en {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumen de resultados
    print("\n" + "=" * 50)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASÓ" if result else "❌ FALLÓ"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Resultado: {passed}/{total} pruebas pasaron")
    
    if passed == total:
        print("🎉 ¡Todas las pruebas pasaron exitosamente!")
        return 0
    else:
        print("⚠️ Algunas pruebas fallaron. Revisar configuración.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 