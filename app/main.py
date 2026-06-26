from fastapi import FastAPI
from sqlalchemy import text
from app.config.auth_db import SessionLocal
from app.core.seed.admin_seed import seed_admin
from app.config import roulette_db
from app.config.auth_db import Base, engine
from app.config.admin_db import AdminBase as admin_base, admin_engine as admin_engine
from app.config.interaction_db import InteractionBase as interaction_base, interaction_engine as interaction_engine
from app.config.roulette_db import RouletteBase as roulette_base, roulette_engine as roulette_engine
from app.config.notification_db import NotificationBase as notification_base, notification_engine as notification_engine
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings

# Importar todas as rotas
from app.domain.auth.routes.auth_routes import router as auth_router
from app.domain.auth.routes.email_routes import router as email_router
from app.domain.auth.routes.password_reset_routes import router as reset_router
from app.domain.auth.routes.email_log_routes import router as email_log_router
from app.domain.auth.routes.social_routes import router as social_router
from app.domain.users.routes.profile_routes import router as profile_router
from app.domain.admin.routes.news_routes import router as news_router
from app.domain.users.routes.comment_routes import router as comment_router
from app.domain.users.routes.like_routes import router as like_router
from app.domain.admin.routes.event_routes import router as event_router
from app.domain.admin.routes.samba_school_routes import router as samba_school_router
from app.domain.admin.routes.music_lyrics_routes import router as music_lyrics_router
from app.domain.roulette.routes.roulette_routes import router as roulette_router
from app.domain.roulette.routes.prize_routes import router as prize_router
from app.domain.roulette.routes.spin_routes import router as spin_router
from app.domain.photo_ai.routes.face_routes import router as face_router
from app.domain.public.routes.public_event_routes import router as public_event_router
from app.domain.admin.routes.product_event_routes import router as product_event_router
from app.domain.admin.routes.lineup_item_routes import router as lineup_item_router
from app.domain.admin.routes.parade_lineup_item_routes import router as parade_lineup_item_router
from app.domain.admin.routes.event_stand_routes import router as event_stand_router
from app.domain.admin.routes.event_stand_session_routes import router as event_stand_session_router
from app.domain.users.routes.notification_routes import router as notification_router
from app.domain.users.routes.notification_preference_routes import router as notification_preference_router
from app.domain.users.routes.push_routes import router as push_router
from app.domain.users.routes.downloaded_photo_routes import router as downloaded_photo_router
from app.domain.admin.routes.ad_click_routes import router as ad_click_router
from app.domain.users.routes.event_stand_booking_routes import router as event_stand_booking_router
from app.domain.admin.routes.event_stand_booking_admin_routes import router as event_stand_booking_admin_router
from app.domain.admin.routes.campaign_routes import router as campaign_router
from app.domain.admin.routes.event_camping_area_routes import router as event_camping_area_router
from app.domain.admin.routes.event_camping_session_routes import router as event_camping_session_router
from app.domain.admin.routes.event_camping_booking_admin_routes import router as event_camping_booking_admin_router
from app.domain.users.routes.event_camping_booking_routes import router as event_camping_booking_router
from app.domain.admin.routes.restaurant_routes import router as restaurant_router
from app.domain.users.routes.food_order_routes import router as food_order_router
from app.domain.admin.routes.plataforma_config_routes import router as plataforma_config_router
from app.domain.admin.routes.event_camping_package_routes import router as event_camping_package_router, public_router as event_camping_package_public_router
from app.domain.admin.routes.event_parking_routes import admin_router as event_parking_admin_router, user_router as event_parking_user_router, public_router as event_parking_public_router

# Importar modelos para garantir que SQLAlchemy os registre
from app.domain.admin.models.ad_click_model import AdClick  # noqa: F401
from app.domain.admin.models.campaign_model import Campaign  # noqa: F401
from app.domain.admin.models.ad_view_model import AdView  # noqa: F401
from app.domain.photo_ai.models.face_search_model import FaceSearch  # noqa: F401
from app.domain.admin.models.event_camping_area_model import EventCampingArea  # noqa: F401
from app.domain.admin.models.event_camping_session_model import EventCampingSession  # noqa: F401
from app.domain.admin.models.event_camping_booking_model import EventCampingBooking  # noqa: F401
from app.domain.admin.models.event_camping_entry_model import EventCampingEntry  # noqa: F401
from app.domain.admin.models.restaurant_model import Restaurant  # noqa: F401
from app.domain.admin.models.menu_item_model import MenuItem  # noqa: F401
from app.domain.admin.models.food_order_model import FoodOrder  # noqa: F401
from app.domain.admin.models.food_order_item_model import FoodOrderItem  # noqa: F401
from app.domain.admin.models.plataforma_config_model import PlataformaConfig  # noqa: F401
from app.domain.admin.models.event_camping_package_model import EventCampingPackage  # noqa: F401
from app.domain.admin.models.event_parking_spot_model import EventParkingSpot  # noqa: F401
from app.domain.admin.models.parking_booking_model import ParkingBooking  # noqa: F401

# Criar tabelas na inicialização
def init_db():
    # Criar todos os bancos
    Base.metadata.create_all(bind=engine)
    admin_base.metadata.create_all(bind=admin_engine)
    interaction_base.metadata.create_all(bind=interaction_engine)
    roulette_base.metadata.create_all(bind=roulette_engine)
    notification_base.metadata.create_all(bind=notification_engine)

app = FastAPI(
    title="Auth API",
    version="1.0.0",
)

# ===== CORS (configurado para produção e desenvolvimento local) =====
allowed_origins = [
    settings.FRONTEND_URL,  # URL de produção
    "http://localhost:3000",  # Next.js padrão
    'http://localhost:3001',
    "http://localhost:5173",  # Vite padrão
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "https://ccbrasil.app.br",
    "https://circuitosertanejo.picbrand.com.br",
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# ===== REGISTRO DE ROTAS =====
app.include_router(auth_router)
app.include_router(email_router)
app.include_router(reset_router)
app.include_router(email_log_router)
app.include_router(social_router)
app.include_router(profile_router)
app.include_router(news_router)
app.include_router(comment_router)
app.include_router(like_router)
app.include_router(event_router)
app.include_router(samba_school_router)
app.include_router(music_lyrics_router)
app.include_router(roulette_router)
app.include_router(prize_router)
app.include_router(spin_router)
app.include_router(face_router)
app.include_router(public_event_router)
app.include_router(product_event_router)
app.include_router(lineup_item_router)
app.include_router(parade_lineup_item_router)
app.include_router(event_stand_router)
app.include_router(event_stand_session_router)
app.include_router(notification_router)
app.include_router(notification_preference_router)
app.include_router(push_router)
app.include_router(downloaded_photo_router)
app.include_router(ad_click_router)
app.include_router(event_stand_booking_router)
app.include_router(event_stand_booking_admin_router)
app.include_router(campaign_router)
app.include_router(event_camping_area_router)
app.include_router(event_camping_session_router)
app.include_router(event_camping_booking_admin_router)
app.include_router(event_camping_booking_router)
app.include_router(restaurant_router)
app.include_router(food_order_router)
app.include_router(plataforma_config_router)
app.include_router(event_camping_package_router)
app.include_router(event_camping_package_public_router)
app.include_router(event_parking_admin_router)
app.include_router(event_parking_user_router)
app.include_router(event_parking_public_router)

@app.get("/")
def root():
    return {"message": "API está funcionando!"}

@app.on_event("startup")
def startup():
    init_db()

    with admin_engine.connect() as conn:
        conn.execute(text("ALTER TABLE event_camping_areas ADD COLUMN IF NOT EXISTS x_position FLOAT"))
        conn.execute(text("ALTER TABLE event_camping_areas ADD COLUMN IF NOT EXISTS y_position FLOAT"))
        conn.execute(text("ALTER TABLE events ADD COLUMN IF NOT EXISTS parking_map_image_url VARCHAR(500)"))
        conn.commit()

    db = SessionLocal()
    seed_admin(db)
    db.close()