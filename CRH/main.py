from fastapi import FastAPI
from CRH.routes.CRH_routes import router

app = FastAPI()

app.include_router(router)