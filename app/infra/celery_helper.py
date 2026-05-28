"""Helper para enviar tarefas ao Celery com fallback para BackgroundTasks"""
import logging
from typing import Optional
from fastapi import BackgroundTasks

logger = logging.getLogger(__name__)

def send_notification_task(task_func, *args, background_tasks: Optional[BackgroundTasks] = None, **kwargs):
    """
    Envia tarefa para Celery, com fallback para BackgroundTasks se Celery não estiver disponível
    
    Args:
        task_func: Função da task do Celery (ex: notify_post_like_task)
        *args: Argumentos posicionais para a task
        background_tasks: BackgroundTasks do FastAPI (para fallback)
        **kwargs: Argumentos nomeados para a task
    """
    try:
        # Tentar enviar para Celery
        task_func.delay(*args, **kwargs)
        logger.debug(f"Tarefa enviada para Celery: {task_func.__name__}")
    except Exception as e:
        # Se Celery não estiver disponível, usar fallback
        logger.warning(
            f"Celery não disponível para {task_func.__name__}, usando fallback: {e}",
            exc_info=True
        )
        
        # Fallback: usar função síncrona antiga se disponível
        if background_tasks:
            try:
                # Tentar importar função de fallback
                task_name = task_func.__name__
                if 'notify_post_like' in task_name:
                    from app.domain.users.services.notification_background import notify_post_like_async
                    background_tasks.add_task(notify_post_like_async, *args)
                elif 'notify_post_comment' in task_name:
                    from app.domain.users.services.notification_background import notify_post_comment_async
                    background_tasks.add_task(notify_post_comment_async, *args)
                elif 'notify_comment_reply' in task_name:
                    from app.domain.users.services.notification_background import notify_comment_reply_async
                    background_tasks.add_task(notify_comment_reply_async, *args)
                elif 'notify_comment_like' in task_name:
                    from app.domain.users.services.notification_background import notify_comment_like_async
                    background_tasks.add_task(notify_comment_like_async, *args)
                elif 'remove_post_like_notification' in task_name:
                    from app.domain.users.services.notification_background import remove_post_like_notification_async
                    background_tasks.add_task(remove_post_like_notification_async, *args)
                elif 'remove_comment_like_notification' in task_name:
                    from app.domain.users.services.notification_background import remove_comment_like_notification_async
                    background_tasks.add_task(remove_comment_like_notification_async, *args)
                else:
                    logger.error(f"Função de fallback não encontrada para {task_name}")
            except Exception as fallback_error:
                logger.error(
                    f"Erro no fallback para {task_func.__name__}: {fallback_error}",
                    exc_info=True
                )
        else:
            logger.error(
                f"Não foi possível enviar tarefa {task_func.__name__}: "
                f"Celery indisponível e background_tasks não fornecido"
            )


