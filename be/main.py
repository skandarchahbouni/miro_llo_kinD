from fastapi import FastAPI
from be.routes.app_routes import router

app = FastAPI()

app.include_router(router, prefix="/api/v1")
