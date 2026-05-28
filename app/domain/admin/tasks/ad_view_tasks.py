"""Tasks do Celery para processamento assíncrono de views de anúncios"""
from app.infra.celery_app import celery_app
from app.config.admin_db import AdminSessionLocal
from sqlalchemy.dialects.postgresql import insert
import logging

# IMPORTANTE: Importar todos os modelos necessários
from app.domain.admin.models.ad_view_model import AdView  # noqa: F401
from app.domain.admin.models.event_model import Event  # noqa: F401

logger = logging.getLogger(__name__)


@celery_app.task(name='ads.process_view_batch', bind=True, max_retries=3)
def process_view_batch_task(self, views_batch: list):
    """
    Task Celery para processar lote de views em batch (bulk insert)
    
    Args:
        views_batch: Lista de dicionários com views para processar
        [
            {
                "user_id": 123,
                "event_id": 1,
                "ad_identifier": "1",
                "ad_url": "/ads/1.png"
            },
            ...
        ]
    """
    if not views_batch or len(views_batch) == 0:
        return {"processed": 0, "message": "Empty batch"}
    
    db = AdminSessionLocal()
    try:
        # Prepara dados para bulk insert
        values = [
            {
                "user_id": view.get("user_id"),
                "event_id": view["event_id"],
                "ad_identifier": view["ad_identifier"],
                "ad_url": view.get("ad_url")
            }
            for view in views_batch
        ]
        
        # Bulk insert usando PostgreSQL
        stmt = insert(AdView).values(values)
        db.execute(stmt)
        db.commit()
        
        logger.info(f"✅ Processadas {len(views_batch)} views em batch via Celery")
        return {"processed": len(views_batch), "status": "success"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erro ao processar batch de views via Celery: {e}", exc_info=True)
        # Retry automático em caso de erro
        raise self.retry(exc=e, countdown=30)  # Tenta novamente em 30 segundos
    finally:
        db.close()


@celery_app.task(name='ads.process_single_view', bind=True, max_retries=3, ignore_result=True)
def process_single_view_task(self, user_id: int, event_id: int, ad_identifier: str, ad_url: str):
    """
    Task Celery para processar uma única view
    Usa ignore_result=True para não armazenar resultados (economiza memória Redis)
    
    Args:
        user_id: ID do usuário (0 se não autenticado, será convertido para None)
        event_id: ID do evento
        ad_identifier: Identificador do anúncio
        ad_url: URL do anúncio
    """
    db = AdminSessionLocal()
    try:
        ad_view = AdView(
            user_id=user_id if user_id > 0 else None,  # Converte 0 para None
            event_id=event_id,
            ad_identifier=ad_identifier,
            ad_url=ad_url if ad_url else None
        )
        db.add(ad_view)
        db.commit()
        db.refresh(ad_view)
        
        logger.debug(f"✅ View processada via Celery: event_id={event_id}, ad={ad_identifier}")
        return {"id": ad_view.id, "status": "success"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Erro ao processar view via Celery: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=30)
    finally:
        db.close()

