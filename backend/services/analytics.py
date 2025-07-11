from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from database.models import (
    Report, Analytics, Dashboard, User, BusinessProfile, 
    Delivery, Transaction, Rating, Promotion, LoyaltyMember
)
from schemas.report import ReportCreate, ReportUpdate, AnalyticsCreate, AnalyticsFilter, ReportFilter
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
import json

class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def create_report(
        self,
        user_id: int,
        report_data: ReportCreate
    ) -> Report:
        """Crear un nuevo reporte"""
        # Verificar que el usuario existe
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuario no encontrado"
            )

        # Crear el reporte
        report = Report(
            user_id=user_id,
            **report_data.dict()
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def get_reports(
        self,
        skip: int = 0,
        limit: int = 20,
        filters: Optional[ReportFilter] = None
    ) -> List[Report]:
        """Obtener reportes con filtros"""
        query = self.db.query(Report)

        if filters:
            if filters.report_type:
                query = query.filter(Report.report_type == filters.report_type)
            if filters.reason:
                query = query.filter(Report.reason == filters.reason)
            if filters.status:
                query = query.filter(Report.status == filters.status)
            if filters.business_id:
                query = query.filter(Report.business_id == filters.business_id)
            if filters.user_id:
                query = query.filter(Report.user_id == filters.user_id)
            if filters.start_date:
                query = query.filter(Report.created_at >= filters.start_date)
            if filters.end_date:
                query = query.filter(Report.created_at <= filters.end_date)

        return query.order_by(desc(Report.created_at)).offset(skip).limit(limit).all()

    def update_report(
        self,
        report_id: int,
        report_update: ReportUpdate
    ) -> Report:
        """Actualizar un reporte (solo para administradores)"""
        report = self.db.query(Report).filter(Report.id == report_id).first()
        
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reporte no encontrado"
            )

        for key, value in report_update.dict(exclude_unset=True).items():
            setattr(report, key, value)

        report.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(report)
        return report

    def get_business_metrics(self, business_id: int) -> Dict[str, Any]:
        """Obtener métricas generales de un negocio"""
        # Total de ingresos
        total_revenue = self.db.query(func.sum(Transaction.amount)).filter(
            Transaction.meta_data.contains({"business_id": business_id}),
            Transaction.status == "completed"
        ).scalar() or 0.0

        # Total de entregas
        total_deliveries = self.db.query(func.count(Delivery.id)).filter(
            Delivery.service.has(business_profile_id=business_id)
        ).scalar() or 0

        # Promedio de calificaciones
        avg_rating = self.db.query(func.avg(Rating.rating)).filter(
            Rating.business_id == business_id
        ).scalar() or 0.0

        # Promociones activas
        active_promotions = self.db.query(func.count(Promotion.id)).filter(
            Promotion.business_profile_id == business_id,
            Promotion.status == "active"
        ).scalar() or 0

        # Miembros de lealtad
        loyalty_members = self.db.query(func.count(LoyaltyMember.id)).filter(
            LoyaltyMember.loyalty_program.has(business_profile_id=business_id)
        ).scalar() or 0

        return {
            "total_revenue": total_revenue,
            "total_deliveries": total_deliveries,
            "average_rating": round(avg_rating, 2),
            "active_promotions": active_promotions,
            "loyalty_members": loyalty_members
        }

    def get_revenue_metrics(
        self,
        business_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """Obtener métricas de ingresos"""
        # Ingresos diarios
        daily_revenue = self.db.query(
            func.date(Transaction.created_at).label('date'),
            func.sum(Transaction.amount).label('revenue')
        ).filter(
            Transaction.meta_data.contains({"business_id": business_id}),
            Transaction.status == "completed",
            func.date(Transaction.created_at) >= start_date,
            func.date(Transaction.created_at) <= end_date
        ).group_by(func.date(Transaction.created_at)).all()

        # Calcular crecimiento
        current_period_revenue = sum([r.revenue for r in daily_revenue])
        previous_period_start = start_date - timedelta(days=(end_date - start_date).days)
        previous_period_revenue = self.db.query(func.sum(Transaction.amount)).filter(
            Transaction.meta_data.contains({"business_id": business_id}),
            Transaction.status == "completed",
            func.date(Transaction.created_at) >= previous_period_start,
            func.date(Transaction.created_at) < start_date
        ).scalar() or 0.0

        growth_rate = 0.0
        if previous_period_revenue > 0:
            growth_rate = ((current_period_revenue - previous_period_revenue) / previous_period_revenue) * 100

        return {
            "daily_revenue": [{"date": str(r.date), "revenue": r.revenue} for r in daily_revenue],
            "total_revenue": current_period_revenue,
            "growth_rate": round(growth_rate, 2)
        }

    def get_delivery_metrics(
        self,
        business_id: int,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """Obtener métricas de entregas"""
        # Total de entregas
        total_deliveries = self.db.query(func.count(Delivery.id)).filter(
            Delivery.service.has(business_profile_id=business_id),
            func.date(Delivery.created_at) >= start_date,
            func.date(Delivery.created_at) <= end_date
        ).scalar() or 0

        # Entregas completadas
        completed_deliveries = self.db.query(func.count(Delivery.id)).filter(
            Delivery.service.has(business_profile_id=business_id),
            Delivery.status == "completed",
            func.date(Delivery.created_at) >= start_date,
            func.date(Delivery.created_at) <= end_date
        ).scalar() or 0

        # Tiempo promedio de entrega
        avg_delivery_time = self.db.query(
            func.avg(func.extract('epoch', Delivery.completed_at - Delivery.created_at) / 3600)
        ).filter(
            Delivery.service.has(business_profile_id=business_id),
            Delivery.status == "completed",
            Delivery.completed_at.isnot(None),
            func.date(Delivery.created_at) >= start_date,
            func.date(Delivery.created_at) <= end_date
        ).scalar() or 0.0

        # Tasa de éxito
        success_rate = 0.0
        if total_deliveries > 0:
            success_rate = (completed_deliveries / total_deliveries) * 100

        return {
            "total_deliveries": total_deliveries,
            "completed_deliveries": completed_deliveries,
            "average_delivery_time": round(avg_delivery_time, 2),
            "delivery_success_rate": round(success_rate, 2)
        }

    def create_analytics_entry(
        self,
        analytics_data: AnalyticsCreate
    ) -> Analytics:
        """Crear una entrada de analytics"""
        analytics = Analytics(**analytics_data.dict())
        self.db.add(analytics)
        self.db.commit()
        self.db.refresh(analytics)
        return analytics

    def get_analytics(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[AnalyticsFilter] = None
    ) -> List[Analytics]:
        """Obtener datos de analytics con filtros"""
        query = self.db.query(Analytics)

        if filters:
            if filters.start_date:
                query = query.filter(Analytics.date >= filters.start_date)
            if filters.end_date:
                query = query.filter(Analytics.date <= filters.end_date)
            if filters.metric_type:
                query = query.filter(Analytics.metric_type == filters.metric_type)
            if filters.period:
                query = query.filter(Analytics.period == filters.period)
            if filters.business_id:
                query = query.filter(Analytics.business_id == filters.business_id)
            if filters.user_id:
                query = query.filter(Analytics.user_id == filters.user_id)

        return query.order_by(desc(Analytics.date)).offset(skip).limit(limit).all()

    def create_dashboard(
        self,
        user_id: int,
        dashboard_data: dict
    ) -> Dashboard:
        """Crear un nuevo dashboard"""
        dashboard = Dashboard(
            user_id=user_id,
            **dashboard_data
        )
        self.db.add(dashboard)
        self.db.commit()
        self.db.refresh(dashboard)
        return dashboard

    def get_user_dashboards(self, user_id: int) -> List[Dashboard]:
        """Obtener dashboards de un usuario"""
        return self.db.query(Dashboard).filter(
            Dashboard.user_id == user_id
        ).order_by(desc(Dashboard.created_at)).all()

    def update_dashboard(
        self,
        dashboard_id: int,
        user_id: int,
        dashboard_update: dict
    ) -> Dashboard:
        """Actualizar un dashboard"""
        dashboard = self.db.query(Dashboard).filter(
            Dashboard.id == dashboard_id,
            Dashboard.user_id == user_id
        ).first()

        if not dashboard:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dashboard no encontrado"
            )

        for key, value in dashboard_update.items():
            setattr(dashboard, key, value)

        dashboard.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(dashboard)
        return dashboard

    def delete_dashboard(self, dashboard_id: int, user_id: int) -> bool:
        """Eliminar un dashboard"""
        dashboard = self.db.query(Dashboard).filter(
            Dashboard.id == dashboard_id,
            Dashboard.user_id == user_id
        ).first()

        if not dashboard:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dashboard no encontrado"
            )

        self.db.delete(dashboard)
        self.db.commit()
        return True

    def generate_weekly_report(self, business_id: int) -> Dict[str, Any]:
        """Generar reporte semanal para un negocio"""
        end_date = date.today()
        start_date = end_date - timedelta(days=7)

        revenue_metrics = self.get_revenue_metrics(business_id, start_date, end_date)
        delivery_metrics = self.get_delivery_metrics(business_id, start_date, end_date)
        business_metrics = self.get_business_metrics(business_id)

        return {
            "period": {
                "start_date": str(start_date),
                "end_date": str(end_date)
            },
            "revenue": revenue_metrics,
            "deliveries": delivery_metrics,
            "overview": business_metrics
        } 