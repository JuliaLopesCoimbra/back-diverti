# app/domain/admin/controllers/ad_click_controller.py

from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime
from typing import Optional, List
from collections import deque
import threading
import time
import logging

from app.domain.admin.models.ad_click_model import AdClick
from app.domain.admin.models.ad_view_model import AdView
from app.domain.admin.models.event_model import Event
from app.domain.admin.schemas.ad_click_schema import (
    AdClickCreateSchema,
    AdClickResponseSchema,
    AdClickStatsResponseSchema,
    AdClickStatsSchema,
    AdViewCreateSchema,
    AdViewResponseSchema,
    AdViewStatsResponseSchema,
    AdViewStatsSchema
)
from app.config.admin_db import AdminSessionLocal

logger = logging.getLogger(__name__)

class AdClickController:
    
    @staticmethod
    def create_click(
        db: Session,
        click_data: AdClickCreateSchema,
        user_id: Optional[int] = None
    ) -> AdClickResponseSchema:
        """Registra um clique em um anúncio"""
        ad_click = AdClick(
            user_id=user_id,
            event_id=click_data.event_id,
            ad_identifier=click_data.ad_identifier,
            ad_url=click_data.ad_url,
            redirect_url=click_data.redirect_url
        )
        db.add(ad_click)
        db.commit()
        db.refresh(ad_click)
        return AdClickResponseSchema.model_validate(ad_click)
    
    @staticmethod
    def get_stats(
        db: Session,
        event_id: Optional[int] = None,
        ad_identifier: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> AdClickStatsResponseSchema:
        """Obtém estatísticas de cliques"""
        query = db.query(AdClick)
        
        # Filtros
        if event_id:
            query = query.filter(AdClick.event_id == event_id)
        if ad_identifier:
            query = query.filter(AdClick.ad_identifier == ad_identifier)
        if start_date:
            query = query.filter(AdClick.clicked_at >= start_date)
        if end_date:
            query = query.filter(AdClick.clicked_at <= end_date)
        
        all_clicks = query.all()
        
        # Evento (se especificado)
        event_name = None
        if event_id:
            event = db.query(Event).filter(Event.id == event_id).first()
            event_name = event.title if event else None
        
        # Agrupa por anúncio
        clicks_by_ad: dict = {}
        clicks_by_hour: dict = {}
        
        for click in all_clicks:
            # Por anúncio
            if click.ad_identifier not in clicks_by_ad:
                clicks_by_ad[click.ad_identifier] = {
                    "clicks": 0,
                    "first_click": click.clicked_at,
                    "last_click": click.clicked_at,
                    "clicks_by_hour": {},
                    "clicks_by_event": {}
                }
            
            ad_data = clicks_by_ad[click.ad_identifier]
            ad_data["clicks"] += 1
            
            if click.clicked_at < ad_data["first_click"]:
                ad_data["first_click"] = click.clicked_at
            if click.clicked_at > ad_data["last_click"]:
                ad_data["last_click"] = click.clicked_at
            
            # Por hora
            hour = str(click.clicked_at.hour)
            ad_data["clicks_by_hour"][hour] = ad_data["clicks_by_hour"].get(hour, 0) + 1
            clicks_by_hour[hour] = clicks_by_hour.get(hour, 0) + 1
            
            # Por evento
            event_key = str(click.event_id)
            ad_data["clicks_by_event"][event_key] = ad_data["clicks_by_event"].get(event_key, 0) + 1
        
        # Converte para schema
        ad_stats_list = []
        for ad_id, ad_data in clicks_by_ad.items():
            ad_stats_list.append(AdClickStatsSchema(
                ad_identifier=ad_id,
                total_clicks=ad_data["clicks"],
                clicks_by_hour=ad_data["clicks_by_hour"],
                clicks_by_event=ad_data["clicks_by_event"],
                first_click=ad_data["first_click"],
                last_click=ad_data["last_click"]
            ))
        
        # Ordena por total de cliques
        ad_stats_list.sort(key=lambda x: x.total_clicks, reverse=True)
        
        period_start = min([c.clicked_at for c in all_clicks]) if all_clicks else None
        period_end = max([c.clicked_at for c in all_clicks]) if all_clicks else None
        
        return AdClickStatsResponseSchema(
            event_id=event_id,
            event_name=event_name,
            total_clicks=len(all_clicks),
            clicks_by_ad=ad_stats_list,
            clicks_by_hour=clicks_by_hour,
            period_start=period_start,
            period_end=period_end
        )
    
    @staticmethod
    def get_clicks_list(
        db: Session,
        event_id: Optional[int] = None,
        user_id: Optional[int] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AdClickResponseSchema]:
        """Lista cliques com paginação"""
        query = db.query(AdClick)
        
        if event_id:
            query = query.filter(AdClick.event_id == event_id)
        if user_id:
            query = query.filter(AdClick.user_id == user_id)
        
        query = query.order_by(AdClick.clicked_at.desc())
        clicks = query.limit(limit).offset(offset).all()
        
        return [AdClickResponseSchema.model_validate(click) for click in clicks]
    
    # ===== VIEWS - BATCH PROCESSING =====
    
    # Fila global para views (thread-safe)
    _view_queue = deque()
    _queue_lock = threading.Lock()
    _batch_size = 50  # Processa 50 views por vez
    _batch_timeout = 5  # Ou a cada 5 segundos
    _last_batch_time = time.time()
    _batch_thread_running = False
    
    @staticmethod
    def _process_view_batch():
        """Processa lote de views em batch (chamado periodicamente)"""
        db = AdminSessionLocal()
        try:
            with AdClickController._queue_lock:
                if len(AdClickController._view_queue) == 0:
                    return
                
                # Pega até batch_size views
                batch = []
                for _ in range(min(AdClickController._batch_size, len(AdClickController._view_queue))):
                    batch.append(AdClickController._view_queue.popleft())
            
            if batch:
                # Bulk insert usando PostgreSQL
                values = [
                    {
                        "user_id": view["user_id"],
                        "event_id": view["event_id"],
                        "ad_identifier": view["ad_identifier"],
                        "ad_url": view["ad_url"]
                    }
                    for view in batch
                ]
                
                stmt = insert(AdView).values(values)
                db.execute(stmt)
                db.commit()
                
                logger.info(f"✅ Processadas {len(batch)} views em batch")
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Erro ao processar batch de views: {e}", exc_info=True)
        finally:
            db.close()
    
    @staticmethod
    def _batch_worker():
        """Worker thread que processa batches periodicamente"""
        while AdClickController._batch_thread_running:
            try:
                current_time = time.time()
                time_since_last_batch = current_time - AdClickController._last_batch_time
                
                # Processa se passou o timeout OU se a fila está cheia
                with AdClickController._queue_lock:
                    queue_size = len(AdClickController._view_queue)
                
                if time_since_last_batch >= AdClickController._batch_timeout or queue_size >= AdClickController._batch_size:
                    AdClickController._process_view_batch()
                    AdClickController._last_batch_time = current_time
                
                # Dorme por 1 segundo antes de verificar novamente
                time.sleep(1)
            except Exception as e:
                logger.error(f"Erro no batch worker: {e}", exc_info=True)
                time.sleep(1)
    
    @staticmethod
    def _ensure_batch_worker():
        """Garante que o worker thread está rodando"""
        if not AdClickController._batch_thread_running:
            AdClickController._batch_thread_running = True
            worker_thread = threading.Thread(target=AdClickController._batch_worker, daemon=True)
            worker_thread.start()
            logger.info("🚀 Batch worker thread iniciado para processamento de views")
    
    @staticmethod
    def queue_view_for_batch(
        event_id: int,
        ad_identifier: str,
        ad_url: Optional[str],
        user_id: Optional[int] = None
    ):
        """
        Adiciona view para processamento via Celery (processo separado)
        Mais eficiente e robusto para alto volume (5000+ usuários)
        """
        view_data = {
            "user_id": user_id,
            "event_id": event_id,
            "ad_identifier": ad_identifier,
            "ad_url": ad_url
        }
        
        # Tenta usar Celery primeiro (processo separado, mais robusto)
        try:
            from app.domain.admin.tasks.ad_view_tasks import process_single_view_task
            process_single_view_task.delay(
                user_id or 0,  # Celery não aceita None, usa 0 e trata no backend
                event_id,
                ad_identifier,
                ad_url or ""
            )
            logger.debug(f"✅ View enviada para Celery: event_id={event_id}, ad={ad_identifier}")
            return
        except Exception as e:
            # Se Celery não estiver disponível, usa fallback (thread local)
            logger.warning(f"⚠️ Celery não disponível, usando fallback local: {e}")
            AdClickController._queue_view_fallback(view_data)
    
    @staticmethod
    def _queue_view_fallback(view_data: dict):
        """
        Fallback: adiciona view à fila local (thread) se Celery não estiver disponível
        """
        # Garante que o worker está rodando
        AdClickController._ensure_batch_worker()
        
        with AdClickController._queue_lock:
            AdClickController._view_queue.append(view_data)
            
            queue_size = len(AdClickController._view_queue)
            
            # Se a fila atingir o tamanho do batch, processa imediatamente
            if queue_size >= AdClickController._batch_size:
                AdClickController._process_view_batch()
                AdClickController._last_batch_time = time.time()
    
    @staticmethod
    def create_view(
        db: Session,
        view_data: AdViewCreateSchema,
        user_id: Optional[int] = None
    ) -> AdViewResponseSchema:
        """Registra uma visualização de anúncio (método direto, não usado em batch)"""
        ad_view = AdView(
            user_id=user_id,
            event_id=view_data.event_id,
            ad_identifier=view_data.ad_identifier,
            ad_url=view_data.ad_url
        )
        db.add(ad_view)
        db.commit()
        db.refresh(ad_view)
        return AdViewResponseSchema.model_validate(ad_view)
    
    @staticmethod
    def get_view_stats(
        db: Session,
        event_id: Optional[int] = None,
        ad_identifier: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> AdViewStatsResponseSchema:
        """Obtém estatísticas de visualizações"""
        query = db.query(AdView)
        
        if event_id:
            query = query.filter(AdView.event_id == event_id)
        if ad_identifier:
            query = query.filter(AdView.ad_identifier == ad_identifier)
        if start_date:
            query = query.filter(AdView.viewed_at >= start_date)
        if end_date:
            query = query.filter(AdView.viewed_at <= end_date)
        
        all_views = query.all()
        
        event_name = None
        if event_id:
            event = db.query(Event).filter(Event.id == event_id).first()
            event_name = event.title if event else None
        
        views_by_ad: dict = {}
        views_by_hour: dict = {}
        
        for view in all_views:
            if view.ad_identifier not in views_by_ad:
                views_by_ad[view.ad_identifier] = {
                    "views": 0,
                    "first_view": view.viewed_at,
                    "last_view": view.viewed_at,
                    "views_by_hour": {},
                    "views_by_event": {}
                }
            
            ad_data = views_by_ad[view.ad_identifier]
            ad_data["views"] += 1
            
            if view.viewed_at < ad_data["first_view"]:
                ad_data["first_view"] = view.viewed_at
            if view.viewed_at > ad_data["last_view"]:
                ad_data["last_view"] = view.viewed_at
            
            hour = str(view.viewed_at.hour)
            ad_data["views_by_hour"][hour] = ad_data["views_by_hour"].get(hour, 0) + 1
            views_by_hour[hour] = views_by_hour.get(hour, 0) + 1
            
            event_key = str(view.event_id)
            ad_data["views_by_event"][event_key] = ad_data["views_by_event"].get(event_key, 0) + 1
        
        ad_stats_list = []
        for ad_id, ad_data in views_by_ad.items():
            ad_stats_list.append(AdViewStatsSchema(
                ad_identifier=ad_id,
                total_views=ad_data["views"],
                views_by_hour=ad_data["views_by_hour"],
                views_by_event=ad_data["views_by_event"],
                first_view=ad_data["first_view"],
                last_view=ad_data["last_view"]
            ))
        
        ad_stats_list.sort(key=lambda x: x.total_views, reverse=True)
        
        period_start = min([v.viewed_at for v in all_views]) if all_views else None
        period_end = max([v.viewed_at for v in all_views]) if all_views else None
        
        return AdViewStatsResponseSchema(
            event_id=event_id,
            event_name=event_name,
            total_views=len(all_views),
            views_by_ad=ad_stats_list,
            views_by_hour=views_by_hour,
            period_start=period_start,
            period_end=period_end
        )

