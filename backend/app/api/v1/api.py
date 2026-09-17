from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    users,
    classes,
    polls,
    dashboards,
    students
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(classes.router, prefix="/classes", tags=["Classes"])
api_router.include_router(polls.router, prefix="/polls", tags=["Polls"])
# Also include /classes/{id}/polls directly
api_router.include_router(polls.router, tags=["Class Polls"])
api_router.include_router(dashboards.router, prefix="/dashboards", tags=["Dashboards"])
api_router.include_router(students.router, prefix="/students", tags=["Students"])
