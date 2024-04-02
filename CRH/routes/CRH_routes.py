from fastapi import APIRouter, Body, status,Request,Form
from CRH.controllers import main_controller
from fastapi.param_functions import Depends
import logging
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates


router = APIRouter()
log = logging.getLogger(__name__)
templates = Jinja2Templates(directory='/home/khaled/miro_llo_kinD/CRH/crd_templates')

# -------------------------------------------------------------------- #


@router.get("/")
def read_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.post("/create-json")
def create_json(
    cluster_name: str = Form(...),
    components: str = Form(...),
    app_name: str = Form(...),
    owner: str = Form(...),
    component_name: list = Form(...),
    image: list = Form(...),
    is_public: list = Form(...),
    is_peered: list = Form(...),
    container_port: list = Form(...),
    cluster_port: list = Form(...),
):
    # Form the "decision" field in the payload
    decision = {cluster_name: components.split(",")}

    # Form the "app" field in the payload
    app_payload = {
        "id": 72,
        "tosca": None,
        "updated_at": None,
        "cluster_id": cluster_name,
        "name": app_name,
        "owner": owner,
        "created_at": "2024-02-12T16:29:12",
        "components": [],
    }

    # Form the "components" field in the payload
    components_payload = [
        {
            "name": name,
            "image": img,
            "service": {
                "is_public": pub,
                "is_peered": peered,
                "container_port": cont_port,
                "protocol": "TCP",
                "cluster_port": clust_port,
            },
        }
        for name, img, pub, peered, cont_port, clust_port in zip(
            component_name, image, is_public, is_peered, container_port, cluster_port
        )
    ]

    # Add the components payload to the app payload
    app_payload["components"] = components_payload

    # Form the final payload
    payload = {"decision": decision, "app": app_payload}
    print(payload)
    return payload
@router.post("/apps")
async def create_app(
    decision : dict,
    app : dict,

):
    logging.info("/apps create")
    # decision = app_spec["Decision"]
    # app=app_spec["app"]
    # components=app_spec["components"]
    logging.info(decision)
    return main_controller.handle_create_msg(decision,app)


@router.delete(
    "/apps/"
)
def delete_app(
    app_name : str,
    app_id : int
):
    logging.info(f"/apps/{app_name} DELETE")
    return main_controller.handle_delete_msg(app_name=app_name,app_id=app_id)


@router.put("/apps/")
def update_app(
    decision_body : dict,
    app : dict,
    components : list
):
    logging.info(f"/apps/ UPDATE")
    return main_controller.handle_update_msg(decision_body,app,components)

