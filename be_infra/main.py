from fastapi import FastAPI
from be_infra.routers.clusters import clusters_router
from be_infra.routers.links import links_router

app = FastAPI()

app.include_router(clusters_router)
app.include_router(links_router)
