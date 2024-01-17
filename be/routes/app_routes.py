from fastapi import APIRouter, Body, status
from controllers import app_controller
import logging

router = APIRouter()
log = logging.getLogger(__name__)


# TODO: remove unnecessary routes
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
    app_cluster: str = Body(...),
):
    logging.info("/namespaces POST")
    return app_controller.create_namespace(
        namespace_name=namespace_name, app_cluster=app_cluster
    )


@router.delete("/namespaces/{namespace_name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_namespace(namespace_name: str, app_cluster: str = Body(..., embed=True)):
    logging.info(f"/namespaces/{namespace_name} DELETE")
    return app_controller.delete_namespace(
        namespace_name=namespace_name, app_cluster=app_cluster
    )


@router.delete(
    "/applications/{app_name}/components/{component_name}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_component(app_name: str, component_name: str):
    logging.info(f"/applications/{app_name}/components/{component_name} DELETE")
    return app_controller.delete_component(
        app_name=app_name, component_name=component_name
    )


@router.post("/deployments", status_code=status.HTTP_200_OK)
def install_deployment(
    app_name: str = Body(...),
    component: dict = Body(...),
    update: bool = Body(...),
):
    logging.info("/deployments POST")
    return app_controller.install_deployment(
        component=component, app_name=app_name, update=update
    )


@router.post("/services", status_code=status.HTTP_200_OK)
def install_service(
    component_name: str = Body(...),
    app_name: str = Body(...),
    ports_list: list = Body(...),
    update: bool = Body(...),
):
    logging.info("/services POST")
    return app_controller.install_service(
        component_name=component_name,
        app_name=app_name,
        ports_list=ports_list,
        update=update,
    )


@router.post("/servicemonitors", status_code=status.HTTP_200_OK)
def install_servicemonitor(
    app_name: str = Body(...),
    component_name: str = Body(...),
    ports_list: list = Body(...),
    update: bool = Body(...),
):
    logging.info("/servicemonitors POST")
    return app_controller.install_servicemonitor(
        app_name=app_name,
        component_name=component_name,
        ports_list=ports_list,
        update=update,
    )


@router.delete("/deployments/{component_name}", status_code=status.HTTP_204_NO_CONTENT)
def uninstall_deployment(
    component_name: str,
    app_name: str = Body(..., embed=True),
):
    logging.info(f"/deployments/{component_name} DELETE")
    return app_controller.uninstall_deployment(
        component_name=component_name,
        app_name=app_name,
    )


@router.delete("/services/{component_name}", status_code=status.HTTP_204_NO_CONTENT)
def uninstall_service(component_name: str, app_name: str = Body(..., embed=True)):
    logging.info(f"/services/{component_name} DELETE")
    return app_controller.uninstall_service(
        component_name=component_name, app_name=app_name
    )


@router.delete(
    "/servicemonitors/{component_name}", status_code=status.HTTP_204_NO_CONTENT
)
def uninstall_servicemonitor(
    component_name: str,
    app_name: str = Body(..., embed=True),
):
    logging.info(f"/servicemonitors/{component_name} DELETE")
    app_controller.uninstall_servicemonitor(
        app_name=app_name,
    )


@router.post(
    "/ingress/{app_name}/hosts/{component_name}", status_code=status.HTTP_200_OK
)
def add_host_to_ingress(
    app_name: str,
    component_name: str,
    port: int = Body(..., embed=True),
):
    logging.info(f"/ingress/{app_name}/hosts/{component_name} POST")
    return app_controller.add_host_to_ingress(
        component_name=component_name,
        app_name=app_name,
        port=port,
    )


@router.delete(
    "/ingress/{app_name}/hosts/{component_name}", status_code=status.HTTP_200_OK
)
def remove_host_from_ingress(
    app_name: str,
    component_name: str,
):
    logging.info(f"/ingress/{app_name}/hosts/{component_name} DELETE")
    return app_controller.remove_host_from_ingress(
        component_name=component_name, app_name=app_name
    )


@router.put(
    "/ingress/{app_name}/hosts/{component_name}", status_code=status.HTTP_200_OK
)
def update_host_in_ingress(
    app_name: str,
    component_name: str,
    new_port: int = Body(...),
):
    logging.info(f"/ingress/{app_name}/hosts/{component_name} PUT")
    return app_controller.update_host_in_ingress(
        component_name=component_name,
        app_name=app_name,
        new_port=new_port,
    )
