import logging
from fastapi import APIRouter, Request
from http import HTTPStatus
from controllers import app_controller

router = APIRouter()
log = logging.getLogger(__name__)



@router.get("/clusters/{cluster}/context",  status_code=HTTPStatus.OK)
async def get_context(cluster: str):
    log.info(f"/clusters/{cluster}/context GET.")
    return app_controller.get_context(cluster=cluster)

@router.get("/applications/{application_name}", status_code=HTTPStatus.OK)
async def get_app_instance(application_name: str):
    log.info(f"/applications/{application_name} GET")
    return app_controller.get_app_instance(application_name=application_name)

@router.post("/namespaces", status_code=HTTPStatus.CREATED)
async def create_namespace(request: Request):
    log.info("/namespaces POST")
    # Placeholder for the logic related to the create_namespace function (POST)
    return {"message": "create_namespace endpoint (POST)"}

@router.delete("/namespaces/{namespace_name}", status_code=HTTPStatus.NO_CONTENT)
async def delete_namespace(namespace_name: str, request: Request):
    log.info(f"/namespaces/{namespace_name} DELETE")
    # Placeholder for the logic related to the delete_namespace function (DELETE)

@router.delete("/applications/{app_name}/components/{component_name}", status_code=HTTPStatus.NO_CONTENT)
async def delete_component(app_name: str, component_name: str, request: Request):
    log.info(f"/applications/{app_name}/components/{component_name} DELETE")
    # Placeholder for the logic related to the delete_component function (DELETE)

@router.post("/deployments", status_code=HTTPStatus.CREATED)
async def install_deployment(request: Request):
    log.info("/deployments POST")
    # Placeholder for the logic related to the install_deployment function (POST)
    return {"message": "install_deployment endpoint (POST)"}

@router.post("/services", status_code=HTTPStatus.CREATED)
async def install_service(request: Request):
    log.info("/services POST")
    # Placeholder for the logic related to the install_service function (POST)
    return {"message": "install_service endpoint (POST)"}

@router.post("/servicemonitors", status_code=HTTPStatus.CREATED)
async def install_servicemonitor(request: Request):
    log.info("/servicemonitors POST")
    # Placeholder for the logic related to the install_servicemonitor function (POST)
    return {"message": "install_servicemonitor endpoint (POST)"}

@router.delete("/deployments/{component_name}", status_code=HTTPStatus.NO_CONTENT)
async def uninstall_deployment(component_name: str, request: Request):
    log.info(f"/deployments/{component_name} DELETE")
    # Placeholder for the logic related to the uninstall_deployment function (DELETE)

@router.delete("/services/{component_name}", status_code=HTTPStatus.NO_CONTENT)
async def uninstall_service(component_name: str, request: Request):
    log.info(f"/services/{component_name} DELETE")
    # Placeholder for the logic related to the uninstall_service function (DELETE)

@router.delete("/servicemonitors/{component_name}", status_code=HTTPStatus.NO_CONTENT)
async def uninstall_servicemonitor(component_name: str, request: Request):
    log.info(f"/servicemonitors/{component_name} DELETE")
    # Placeholder for the logic related to the uninstall_servicemonitor function (DELETE)
