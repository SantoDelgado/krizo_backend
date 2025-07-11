from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database.database import get_db
from schemas.report import (
    Report, ReportCreate, ReportUpdate, Analytics, AnalyticsCreate,
    Dashboard, DashboardCreate, DashboardUpdate, BusinessMetrics,
    RevenueMetrics, DeliveryMetrics, AnalyticsFilter, ReportFilter
)
from services.analytics import AnalyticsService
from auth.jwt import get_current_user
from database.models import User, UserType
from datetime import date, timedelta
from sqlalchemy import func, and_, extract
from datetime import datetime, timedelta
from typing import List, Dict, Any

from database.database import get_db
from database.models import User, Delivery, Rating, Transaction, Payment
from auth.jwt import get_current_user

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"]
)

@router.post("/reports", response_model=Report)
async def create_report(
    report_data: ReportCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear un nuevo reporte"""
    analytics_service = AnalyticsService(db)
    return analytics_service.create_report(current_user.id, report_data)

@router.get("/reports", response_model=List[Report])
async def get_reports(
    report_type: Optional[str] = Query(None),
    reason: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    business_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener reportes con filtros (solo para administradores)"""
    # Verificar permisos de administrador
    if current_user.user_type != UserType.BUSINESS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden ver todos los reportes"
        )
    
    analytics_service = AnalyticsService(db)
    filters = ReportFilter(
        report_type=report_type,
        reason=reason,
        status=status,
        business_id=business_id,
        user_id=user_id
    )
    return analytics_service.get_reports(skip=skip, limit=limit, filters=filters)

@router.put("/reports/{report_id}", response_model=Report)
async def update_report(
    report_id: int,
    report_update: ReportUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualizar un reporte (solo para administradores)"""
    # Verificar permisos de administrador
    if current_user.user_type != UserType.BUSINESS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden actualizar reportes"
        )
    
    analytics_service = AnalyticsService(db)
    return analytics_service.update_report(report_id, report_update)

@router.get("/business/{business_id}/metrics", response_model=BusinessMetrics)
async def get_business_metrics(
    business_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener métricas generales de un negocio"""
    # Verificar que el usuario es propietario del negocio o administrador
    if (current_user.user_type != UserType.BUSINESS or 
        not current_user.business_profile or 
        current_user.business_profile.id != business_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver estas métricas"
        )
    
    analytics_service = AnalyticsService(db)
    metrics = analytics_service.get_business_metrics(business_id)
    return BusinessMetrics(**metrics)

@router.get("/business/{business_id}/revenue", response_model=RevenueMetrics)
async def get_revenue_metrics(
    business_id: int,
    start_date: date = Query(default_factory=lambda: date.today() - timedelta(days=30)),
    end_date: date = Query(default_factory=lambda: date.today()),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener métricas de ingresos de un negocio"""
    # Verificar permisos
    if (current_user.user_type != UserType.BUSINESS or 
        not current_user.business_profile or 
        current_user.business_profile.id != business_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver estas métricas"
        )
    
    analytics_service = AnalyticsService(db)
    metrics = analytics_service.get_revenue_metrics(business_id, start_date, end_date)
    return RevenueMetrics(**metrics)

@router.get("/business/{business_id}/deliveries", response_model=DeliveryMetrics)
async def get_delivery_metrics(
    business_id: int,
    start_date: date = Query(default_factory=lambda: date.today() - timedelta(days=30)),
    end_date: date = Query(default_factory=lambda: date.today()),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener métricas de entregas de un negocio"""
    # Verificar permisos
    if (current_user.user_type != UserType.BUSINESS or 
        not current_user.business_profile or 
        current_user.business_profile.id != business_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver estas métricas"
        )
    
    analytics_service = AnalyticsService(db)
    metrics = analytics_service.get_delivery_metrics(business_id, start_date, end_date)
    return DeliveryMetrics(**metrics)

@router.get("/business/{business_id}/weekly-report")
async def get_weekly_report(
    business_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener reporte semanal de un negocio"""
    # Verificar permisos
    if (current_user.user_type != UserType.BUSINESS or 
        not current_user.business_profile or 
        current_user.business_profile.id != business_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver este reporte"
        )
    
    analytics_service = AnalyticsService(db)
    return analytics_service.generate_weekly_report(business_id)

@router.post("/analytics", response_model=Analytics)
async def create_analytics_entry(
    analytics_data: AnalyticsCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear una entrada de analytics"""
    analytics_service = AnalyticsService(db)
    return analytics_service.create_analytics_entry(analytics_data)

@router.get("/analytics", response_model=List[Analytics])
async def get_analytics(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    metric_type: Optional[str] = Query(None),
    period: Optional[str] = Query(None),
    business_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener datos de analytics con filtros"""
    analytics_service = AnalyticsService(db)
    filters = AnalyticsFilter(
        start_date=start_date,
        end_date=end_date,
        metric_type=metric_type,
        period=period,
        business_id=business_id,
        user_id=user_id
    )
    return analytics_service.get_analytics(skip=skip, limit=limit, filters=filters)

@router.post("/dashboards", response_model=Dashboard)
async def create_dashboard(
    dashboard_data: DashboardCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear un nuevo dashboard"""
    analytics_service = AnalyticsService(db)
    return analytics_service.create_dashboard(
        current_user.id,
        dashboard_data.dict()
    )

@router.get("/dashboards", response_model=List[Dashboard])
async def get_user_dashboards(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener dashboards del usuario"""
    analytics_service = AnalyticsService(db)
    return analytics_service.get_user_dashboards(current_user.id)

@router.put("/dashboards/{dashboard_id}", response_model=Dashboard)
async def update_dashboard(
    dashboard_id: int,
    dashboard_update: DashboardUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualizar un dashboard"""
    analytics_service = AnalyticsService(db)
    return analytics_service.update_dashboard(
        dashboard_id,
        current_user.id,
        dashboard_update.dict(exclude_unset=True)
    )

@router.delete("/dashboards/{dashboard_id}")
async def delete_dashboard(
    dashboard_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar un dashboard"""
    analytics_service = AnalyticsService(db)
    analytics_service.delete_dashboard(dashboard_id, current_user.id)
    return {"message": "Dashboard eliminado exitosamente"}

@router.get("/my-business/metrics")
async def get_my_business_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener métricas del negocio del usuario actual"""
    if current_user.user_type != UserType.BUSINESS or not current_user.business_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo los negocios pueden acceder a estas métricas"
        )
    
    analytics_service = AnalyticsService(db)
    metrics = analytics_service.get_business_metrics(current_user.business_profile.id)
    return BusinessMetrics(**metrics)

@router.get("/my-business/revenue")
async def get_my_business_revenue(
    start_date: date = Query(default_factory=lambda: date.today() - timedelta(days=30)),
    end_date: date = Query(default_factory=lambda: date.today()),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener métricas de ingresos del negocio del usuario actual"""
    if current_user.user_type != UserType.BUSINESS or not current_user.business_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo los negocios pueden acceder a estas métricas"
        )
    
    analytics_service = AnalyticsService(db)
    metrics = analytics_service.get_revenue_metrics(
        current_user.business_profile.id,
        start_date,
        end_date
    )
    return RevenueMetrics(**metrics) 

@router.get("/krizoworker/stats/{user_id}")
async def get_krizoworker_stats(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener estadísticas reales de un KrizoWorker"""
    
    # Verificar que el usuario actual sea el propietario o admin
    if current_user.id != user_id and current_user.user_type != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver estas estadísticas"
        )
    
    # Verificar que el usuario sea un KrizoWorker
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.user_type != "SERVICE_PROVIDER":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario KrizoWorker no encontrado"
        )
    
    # Calcular fechas
    now = datetime.utcnow()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    start_of_year = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # 1. Ganancias totales (todas las transacciones completadas)
    total_earnings = db.query(func.sum(Transaction.amount)).filter(
        and_(
            Transaction.user_id == user_id,
            Transaction.type == "PAYMENT",
            Transaction.status == "COMPLETED"
        )
    ).scalar() or 0.0
    
    # 2. Ganancias del mes actual
    monthly_earnings = db.query(func.sum(Transaction.amount)).filter(
        and_(
            Transaction.user_id == user_id,
            Transaction.type == "PAYMENT",
            Transaction.status == "COMPLETED",
            Transaction.created_at >= start_of_month
        )
    ).scalar() or 0.0
    
    # 3. Servicios completados (deliveries completados)
    completed_services = db.query(func.count(Delivery.id)).filter(
        and_(
            Delivery.user_id == user_id,
            Delivery.status == "completed"
        )
    ).scalar() or 0
    
    # 4. Servicios pendientes (deliveries pendientes o en progreso)
    pending_services = db.query(func.count(Delivery.id)).filter(
        and_(
            Delivery.user_id == user_id,
            Delivery.status.in_(["pending", "accepted", "in_progress"])
        )
    ).scalar() or 0
    
    # 5. Calificación promedio y número de reseñas
    rating_stats = db.query(
        func.avg(Rating.rating).label('avg_rating'),
        func.count(Rating.id).label('total_reviews')
    ).filter(
        Rating.user_id == user_id
    ).first()
    
    avg_rating = float(rating_stats.avg_rating) if rating_stats.avg_rating else 0.0
    total_reviews = rating_stats.total_reviews or 0
    
    # 6. Tasa de aceptación (deliveries aceptados vs total de solicitudes)
    total_requests = db.query(func.count(Delivery.id)).filter(
        Delivery.user_id == user_id
    ).scalar() or 0
    
    accepted_requests = db.query(func.count(Delivery.id)).filter(
        and_(
            Delivery.user_id == user_id,
            Delivery.status.in_(["accepted", "in_progress", "completed"])
        )
    ).scalar() or 0
    
    acceptance_rate = (accepted_requests / total_requests * 100) if total_requests > 0 else 0
    
    # 7. Tiempo promedio de respuesta (tiempo entre creación y aceptación)
    response_times = db.query(
        func.avg(
            func.extract('epoch', Delivery.updated_at - Delivery.created_at) / 60
        ).label('avg_response_minutes')
    ).filter(
        and_(
            Delivery.user_id == user_id,
            Delivery.status.in_(["accepted", "in_progress", "completed"]),
            Delivery.updated_at != Delivery.created_at
        )
    ).scalar() or 0
    
    avg_response_minutes = int(response_times) if response_times else 0
    
    return {
        "total_earnings": round(total_earnings, 2),
        "monthly_earnings": round(monthly_earnings, 2),
        "completed_services": completed_services,
        "pending_services": pending_services,
        "average_rating": round(avg_rating, 1),
        "total_reviews": total_reviews,
        "acceptance_rate": round(acceptance_rate, 0),
        "response_time_minutes": avg_response_minutes,
        "user_id": user_id,
        "calculated_at": now.isoformat()
    }

@router.get("/krizoworker/recent-deliveries/{user_id}")
async def get_krizoworker_recent_deliveries(
    user_id: int,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener entregas recientes de un KrizoWorker"""
    
    # Verificar permisos
    if current_user.id != user_id and current_user.user_type != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver estas entregas"
        )
    
    # Obtener entregas recientes
    recent_deliveries = db.query(Delivery).filter(
        Delivery.user_id == user_id
    ).order_by(
        Delivery.created_at.desc()
    ).limit(limit).all()
    
    return [
        {
            "id": delivery.id,
            "status": delivery.status,
            "total_price": delivery.total_price,
            "created_at": delivery.created_at.isoformat(),
            "completed_at": delivery.completed_at.isoformat() if delivery.completed_at else None,
            "pickup_location": delivery.pickup_location,
            "delivery_location": delivery.delivery_location,
            "notes": delivery.notes
        }
        for delivery in recent_deliveries
    ]

@router.get("/krizoworker/earnings-chart/{user_id}")
async def get_krizoworker_earnings_chart(
    user_id: int,
    period: str = "month",  # month, week, year
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener datos para gráfico de ganancias"""
    
    # Verificar permisos
    if current_user.id != user_id and current_user.user_type != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver estos datos"
        )
    
    now = datetime.utcnow()
    
    if period == "week":
        # Últimos 7 días
        start_date = now - timedelta(days=7)
        group_by = func.date(Transaction.created_at)
    elif period == "month":
        # Últimos 30 días
        start_date = now - timedelta(days=30)
        group_by = func.date(Transaction.created_at)
    else:  # year
        # Últimos 12 meses
        start_date = now - timedelta(days=365)
        group_by = func.date_trunc('month', Transaction.created_at)
    
    earnings_data = db.query(
        group_by.label('date'),
        func.sum(Transaction.amount).label('earnings')
    ).filter(
        and_(
            Transaction.user_id == user_id,
            Transaction.type == "PAYMENT",
            Transaction.status == "COMPLETED",
            Transaction.created_at >= start_date
        )
    ).group_by(
        group_by
    ).order_by(
        group_by
    ).all()
    
    return [
        {
            "date": str(item.date),
            "earnings": float(item.earnings)
        }
        for item in earnings_data
    ] 