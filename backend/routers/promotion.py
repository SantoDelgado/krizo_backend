from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database.database import get_db
from database.models import (
    User, BusinessProfile, Promotion, PromotionRedemption,
    LoyaltyProgram, LoyaltyMember, LoyaltyTransaction,
    PromotionType, PromotionStatus, TransactionType
)
from schemas.promotion import (
    Promotion as PromotionSchema,
    PromotionCreate,
    PromotionRedemption as PromotionRedemptionSchema,
    LoyaltyProgram as LoyaltyProgramSchema,
    LoyaltyProgramCreate,
    LoyaltyMember as LoyaltyMemberSchema,
    LoyaltyTransaction as LoyaltyTransactionSchema,
    PromotionResponse,
    LoyaltyPointsResponse
)
from auth.jwt import get_current_active_user
from datetime import datetime

router = APIRouter(prefix="/promotions", tags=["promotions"])

# Rutas para Promociones
@router.post("/", response_model=PromotionSchema)
async def create_promotion(
    promotion: PromotionCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Verificar que el usuario sea un negocio
    business_profile = db.query(BusinessProfile).filter(
        BusinessProfile.user_id == current_user.id
    ).first()
    
    if not business_profile:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los negocios pueden crear promociones"
        )
    
    # Crear la promoción
    db_promotion = Promotion(
        business_profile_id=business_profile.id,
        **promotion.dict()
    )
    db.add(db_promotion)
    db.commit()
    db.refresh(db_promotion)
    return db_promotion

@router.get("/", response_model=List[PromotionSchema])
async def list_promotions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Si es un negocio, mostrar sus promociones
    if current_user.user_type == "business":
        business_profile = db.query(BusinessProfile).filter(
            BusinessProfile.user_id == current_user.id
        ).first()
        if not business_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Perfil de negocio no encontrado"
            )
        return db.query(Promotion).filter(
            Promotion.business_profile_id == business_profile.id
        ).all()
    
    # Si es un usuario normal, mostrar promociones activas
    return db.query(Promotion).filter(
        Promotion.status == PromotionStatus.ACTIVE,
        Promotion.start_date <= datetime.utcnow(),
        Promotion.end_date >= datetime.utcnow()
    ).all()

@router.get("/{promotion_id}", response_model=PromotionSchema)
async def get_promotion(
    promotion_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    promotion = db.query(Promotion).filter(Promotion.id == promotion_id).first()
    if not promotion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Promoción no encontrada"
        )
    return promotion

@router.post("/validate", response_model=PromotionResponse)
async def validate_promotion(
    code: str,
    amount: float,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Buscar la promoción
    promotion = db.query(Promotion).filter(
        Promotion.code == code,
        Promotion.status == PromotionStatus.ACTIVE,
        Promotion.start_date <= datetime.utcnow(),
        Promotion.end_date >= datetime.utcnow()
    ).first()
    
    if not promotion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Código promocional inválido o expirado"
        )
    
    # Verificar límite de usos
    if promotion.usage_limit and promotion.usage_count >= promotion.usage_limit:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Límite de usos alcanzado"
        )
    
    # Verificar monto mínimo
    if promotion.min_purchase and amount < promotion.min_purchase:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Monto mínimo no alcanzado: {promotion.min_purchase}"
        )
    
    # Calcular descuento
    if promotion.type == PromotionType.PERCENTAGE:
        discount = amount * (promotion.value / 100)
        if promotion.max_discount:
            discount = min(discount, promotion.max_discount)
    elif promotion.type == PromotionType.FIXED_AMOUNT:
        discount = promotion.value
    elif promotion.type == PromotionType.FREE_DELIVERY:
        discount = 0  # Se maneja de forma diferente
    else:
        discount = 0
    
    final_amount = amount - discount
    
    return PromotionResponse(
        promotion=promotion,
        amount_saved=discount,
        final_amount=final_amount
    )

# Rutas para Programa de Fidelización
@router.post("/loyalty", response_model=LoyaltyProgramSchema)
async def create_loyalty_program(
    program: LoyaltyProgramCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Verificar que el usuario sea un negocio
    business_profile = db.query(BusinessProfile).filter(
        BusinessProfile.user_id == current_user.id
    ).first()
    
    if not business_profile:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los negocios pueden crear programas de fidelización"
        )
    
    # Crear el programa
    db_program = LoyaltyProgram(
        business_profile_id=business_profile.id,
        **program.dict()
    )
    db.add(db_program)
    db.commit()
    db.refresh(db_program)
    return db_program

@router.post("/loyalty/join/{program_id}", response_model=LoyaltyMemberSchema)
async def join_loyalty_program(
    program_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Verificar que el programa exista
    program = db.query(LoyaltyProgram).filter(LoyaltyProgram.id == program_id).first()
    if not program:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Programa de fidelización no encontrado"
        )
    
    # Verificar que el usuario no esté ya registrado
    existing_member = db.query(LoyaltyMember).filter(
        LoyaltyMember.loyalty_program_id == program_id,
        LoyaltyMember.user_id == current_user.id
    ).first()
    
    if existing_member:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya estás registrado en este programa"
        )
    
    # Crear la membresía
    member = LoyaltyMember(
        loyalty_program_id=program_id,
        user_id=current_user.id
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member

@router.get("/loyalty/points", response_model=LoyaltyPointsResponse)
async def get_loyalty_points(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Obtener todas las membresías del usuario
    memberships = db.query(LoyaltyMember).filter(
        LoyaltyMember.user_id == current_user.id
    ).all()
    
    if not memberships:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No estás registrado en ningún programa de fidelización"
        )
    
    # Calcular puntos totales
    total_points = sum(m.points_balance for m in memberships)
    
    # Determinar el nivel basado en los puntos
    tier = "basic"
    if total_points >= 1000:
        tier = "gold"
    elif total_points >= 500:
        tier = "silver"
    
    return LoyaltyPointsResponse(
        points_earned=0,  # No hay nuevos puntos en esta consulta
        new_balance=total_points,
        tier=tier
    )

@router.post("/loyalty/redeem/{program_id}", response_model=LoyaltyPointsResponse)
async def redeem_loyalty_points(
    program_id: int,
    points: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Obtener la membresía
    member = db.query(LoyaltyMember).filter(
        LoyaltyMember.loyalty_program_id == program_id,
        LoyaltyMember.user_id == current_user.id
    ).first()
    
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No estás registrado en este programa"
        )
    
    # Verificar puntos suficientes
    if member.points_balance < points:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Puntos insuficientes"
        )
    
    # Verificar mínimo de puntos
    program = member.loyalty_program
    if points < program.min_points_redemption:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Mínimo de puntos para canjear: {program.min_points_redemption}"
        )
    
    # Actualizar puntos
    member.points_balance -= points
    member.total_points_redeemed += points
    
    # Crear transacción
    transaction = LoyaltyTransaction(
        loyalty_member_id=member.id,
        points=points,
        type="redeem",
        description="Canje de puntos"
    )
    db.add(transaction)
    
    db.commit()
    db.refresh(member)
    
    return LoyaltyPointsResponse(
        points_earned=-points,
        new_balance=member.points_balance,
        tier=member.tier
    ) 