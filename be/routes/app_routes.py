from fastapi import APIRouter, Body, status
from be.controllers import app_controller
import logging

router = APIRouter()
log = logging.getLogger(__name__)


# -------------------------------------------------------------------- #
@router.post("/apps", status_code=status.HTTP_201_CREATED, tags=["Apps"])
def create_app(
    spec: dict = Body(...),
):
    logging.info("/apps POST")
    return app_controller.create_app(spec=spec)


@router.delete(
    "/apps/{app_name}", status_code=status.HTTP_204_NO_CONTENT, tags=["Apps"]
)
def delete_app(
    app_name: str,
    spec: dict = Body(...),
):
    logging.info(f"/apps/{app_name} DELETE")
    return app_controller.delete_app(spec=spec)


@router.put("/apps/{app_name}", status_code=status.HTTP_200_OK, tags=["Apps"])
def update_app(
    app_name: str, spec: dict = Body(...), old: list = Body(...), new: list = Body(...)
):
    logging.info(f"/apps/{app_name} PUT")
    return app_controller.update_app(spec=spec, old=old, new=new)


# -------------------------------------------------------------------- #
@router.post("/comps", status_code=status.HTTP_201_CREATED, tags=["Comps"])
def create_comp(
    spec: dict = Body(...),
):
    logging.info("/comps POST")
    return app_controller.create_comp(spec=spec)


@router.delete(
    "/comps/{comp_name}", status_code=status.HTTP_204_NO_CONTENT, tags=["Comps"]
)
def delete_comp(
    comp_name: str,
    spec: dict = Body(...),
):
    logging.info(f"/comps/{comp_name} DELETE")
    return app_controller.delete_comp(spec=spec)


@router.put(
    "/comps/{comp_name}/deployment", status_code=status.HTTP_200_OK, tags=["Comps"]
)
def update_comp_deployment(comp_name: str, spec: dict = Body(...)):
    logging.info(f"/comps/{comp_name}/deployment PUT")
    return app_controller.update_comp_deployment(spec=spec)


@router.put("/comps/{comp_name}/expose", status_code=status.HTTP_200_OK, tags=["Comps"])
def update_comp_expose_field(
    comp_name: str, spec: dict = Body(...), old: list = Body(...), new: list = Body(...)
):
    logging.info(f"/comps/{comp_name}/expose PUT")
    return app_controller.update_comp_expose_field(spec=spec, old=old, new=new)
