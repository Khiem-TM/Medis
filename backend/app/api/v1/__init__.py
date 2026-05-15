from fastapi import APIRouter
from app.api.v1 import auth, users, drugs, market_drugs, activity, chatbot, recommendations, admin, reminders, onboarding, notifications

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(drugs.drug_router)
api_router.include_router(drugs.interaction_router)
api_router.include_router(market_drugs.router)
api_router.include_router(market_drugs.admin_router)
api_router.include_router(activity.router)
api_router.include_router(chatbot.router)
api_router.include_router(recommendations.router)
api_router.include_router(admin.router)
api_router.include_router(reminders.router)
api_router.include_router(onboarding.router)
api_router.include_router(notifications.router)
