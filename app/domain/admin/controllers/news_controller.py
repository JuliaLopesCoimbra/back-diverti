from app.domain.admin.services.news_service import NewsService
from app.domain.admin.models.news_model import NewsPost

class NewsController:
    @staticmethod
    def list(db, limit: int, offset: int):
        return db.query(NewsPost).limit(limit).offset(offset).all()

    @staticmethod
    def update(db, news_id, title, content, image_files, user, replace_all=False):
        return NewsService.update_post(db, news_id, title, content, image_files, user, replace_all)

    # Adicionando o método de deletação
    @staticmethod
    def delete(db, news_id, user):
        return NewsService.delete_post(db, news_id, user)

    # Método de busca por ID (para obter uma única notícia)
    @staticmethod
    def get(db, id):
        return NewsService.get_post(db, id)

    @staticmethod
    def create(db, data, user, image_files=None):
        return NewsService.create_news(db, data, user, image_files=image_files)

    @staticmethod
    def list_by_event(db, event_id: int, limit: int, offset: int, include_pending: bool = False):
        return NewsService.list_by_event(db, event_id, limit, offset, include_pending)

    @staticmethod
    def approve(db, post_id, approver):
        return NewsService.approve_post(db, post_id, approver)

    @staticmethod
    def reject(db, post_id, rejector):
        return NewsService.reject_post(db, post_id, rejector)

    @staticmethod
    def list_pending(db, approver, event_id: int = None, limit: int = 10, offset: int = 0):
        return NewsService.list_posts_for_approval(db, approver, event_id, limit, offset)

    @staticmethod
    def get_with_details(admin_db, interaction_db, auth_db, news_id: int, user_id: int = None):
        return NewsService.get_news_with_details(admin_db, interaction_db, auth_db, news_id, user_id)

    @staticmethod
    def list_by_author(db, author_id: int, event_id: int = None, limit: int = 10, offset: int = 0):
        return NewsService.list_by_author(db, author_id, event_id, limit, offset)

    @staticmethod
    def list_pending_by_author(db, author_id: int, event_id: int = None, limit: int = 10, offset: int = 0):
        return NewsService.list_pending_by_author(db, author_id, event_id, limit, offset)

    @staticmethod
    def list_rejected_by_rejector(db, rejector, event_id: int = None, limit: int = 10, offset: int = 0):
        return NewsService.list_rejected_by_rejector(db, rejector, event_id, limit, offset)

    @staticmethod
    def deactivate(db, post_id, deactivator):
        return NewsService.deactivate_post(db, post_id, deactivator)