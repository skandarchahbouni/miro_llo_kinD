import logging
from fastapi import APIRouter, Request, Body, status
from controllers import app_controller

router = APIRouter()
log = logging.getLogger(__name__)


@router.get("/clusters/{cluster}/context", status_code=status.HTTP_200_OK)
def get_context(cluster: str):
    logging.info(f"/clusters/{cluster}/context GET.")
    return app_controller.get_context(cluster=cluster)


@router.get("/applications/{application_name}", status_code=status.HTTP_200_OK)
def get_app_instance(application_name: str):
    logging.info(f"/applications/{application_name} GET")
    return app_controller.get_app_instance(application_name=application_name)


@router.post("/namespaces", status_code=status.HTTP_201_CREATED)
def create_namespace(
    namespace_name: str = Body(...),
    app_cluster_context: str = Body(
        ...,
    ),
):
    logging.info("/namespaces POST")
    return app_controller.create_namespace(
        namespace_name=namespace_name, app_cluster_context=app_cluster_context
    )


@router.delete("/namespaces/{namespace_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_namespace(
    namespace_name: str, app_cluster_context: str = Body(..., embed=True)
):
    logging.info(f"/namespaces/{namespace_name} DELETE")
    return app_controller.delete_namespace(
        namespace_name=namespace_name, app_cluster_context=app_cluster_context
    )


@router.delete(
    "/applications/{app_name}/components/{component_name}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_component(app_name: str, component_name: str, request: Request):
    logging.info(f"/applications/{app_name}/components/{component_name} DELETE")
    # Placeholder for the logic related to the delete_component function (DELETE)


@router.post("/deployments", status_code=status.HTTP_201_CREATED)
async def install_deployment(request: Request):
    logging.info("/deployments POST")
    # Change that, add examples and remove async
    body = await request.json()
    return app_controller.install_deployment(
        component=body["component"], app_cluster_context=body["app_cluster_context"]
    )


@router.post("/services", status_code=status.HTTP_201_CREATED)
def install_service(
    component_name: str = Body(...),
    app_name: str = Body(...),
    ports_list: list = Body(...),
    app_cluster_context: str = Body(...),
):
    logging.info("/services POST")
    return app_controller.install_service(
        component_name=component_name,
        app_name=app_name,
        ports_list=ports_list,
        app_cluster_context=app_cluster_context,
    )


@router.post("/servicemonitors", status_code=status.HTTP_201_CREATED)
def install_servicemonitor(request: Request):
    logging.info("/servicemonitors POST")
    # Placeholder for the logic related to the install_servicemonitor function (POST)
    return {"message": "install_servicemonitor endpoint (POST)"}


@router.delete("/deployments/{component_name}", status_code=status.HTTP_204_NO_CONTENT)
def uninstall_deployment(
    component_name: str, app_cluster_context: str = Body(...), app_name: str = Body()
):
    logging.info(f"/deployments/{component_name} DELETE")
    return app_controller.uninstall_deployment(
        component_name=component_name,
        app_cluster_context=app_cluster_context,
        app_name=app_name,
    )


@router.delete("/services/{component_name}", status_code=status.HTTP_204_NO_CONTENT)
def uninstall_service(
    component_name: str, app_name: str = Body(...), app_cluster_context: str = Body(...)
):
    logging.info(f"/services/{component_name} DELETE")
    return app_controller.uninstall_service(
        component_name=component_name,
        app_name=app_name,
        app_cluster_context=app_cluster_context,
    )


@router.delete(
    "/servicemonitors/{component_name}", status_code=status.HTTP_204_NO_CONTENT
)
def uninstall_servicemonitor(component_name: str, request: Request):
    logging.info(f"/servicemonitors/{component_name} DELETE")
    # Placeholder for the logic related to the uninstall_servicemonitor function (DELETE)
