#!/usr/bin/env python3
"""
Script para limpiar usuarios y recrear la base de datos
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models_simple import User, ServiceProfile
from database.database import SessionLocal

REAL_FIRST_NAME = "Armando"
REAL_LAST_NAME = "Delgado"

def clear_users_except_real():
    db = SessionLocal()
    try:
        real_user = db.query(User).filter(
            User.first_name == REAL_FIRST_NAME,
            User.last_name == REAL_LAST_NAME
        ).first()
        if not real_user:
            print(f"❌ No se encontró el usuario real: {REAL_FIRST_NAME} {REAL_LAST_NAME}")
            return
        db.query(ServiceProfile).filter(ServiceProfile.user_id != real_user.id).delete(synchronize_session=False)
        db.query(User).filter(User.id != real_user.id).delete(synchronize_session=False)
        db.commit()
        print(f"✅ Solo queda el usuario real: {REAL_FIRST_NAME} {REAL_LAST_NAME}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    clear_users_except_real() 