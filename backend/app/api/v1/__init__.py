from fastapi import APIRouter
from app.api.v1 import auth, users, drugs, activity, chatbot, recommendations, admin, reminders

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(drugs.drug_router)
api_router.include_router(drugs.interaction_router)
api_router.include_router(activity.router)
api_router.include_router(chatbot.router)
api_router.include_router(recommendations.router)
api_router.include_router(admin.router)
api_router.include_router(reminders.router)
