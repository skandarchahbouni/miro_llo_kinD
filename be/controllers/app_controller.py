from kubernetes import client, config
from kubernetes.client.rest import ApiException
from kubernetes.config.config_exception import ConfigException
from jinja2 import Environment, FileSystemLoader
from fastapi import HTTPException
import yaml
import logging


# Global variables (TODO: env variables)
group = "charity-project.eu"
version = "v1"
plural = "applications"


# Functions
def get_context(cluster: str):
    # In kind we have just to add the "kind-" to the cluster name to get the context
    return {"context": "kind-" + cluster}


def get_app_instance(application_name: str) -> dict | None:
    try:
        config.load_kube_config()
        custom_objects_api = client.CustomObjectsApi()
        # Get the Custom Resource
        app_instance = custom_objects_api.get_namespaced_custom_object(
            group=group,
            version=version,
            namespace="default",
            plural=plural,
            name=application_name,
        )
        return app_instance
    except ConfigException as _:
        logging.error("Error: load_kube_config [app_controller.get_app_instance]")
        raise HTTPException(status_code=500)
    except ApiException as e:
        logging.error("Error: app_controller.get_app_instance")
        raise HTTPException(status_code=e.status)


def create_namespace(namespace_name: str, app_cluster_context: str):
    try:
        config.load_kube_config(context=app_cluster_context)
        api_instance = client.CoreV1Api()
        new_namespace = client.V1Namespace(
            metadata=client.V1ObjectMeta(name=namespace_name)
        )
        api_instance.create_namespace(body=new_namespace)
        logging.info(f"Namespace {namespace_name} created successfully!.")
    except ConfigException as _:
        logging.error(f"Error: load_kube_config [app_controller.create_namespace]")
        raise HTTPException(status_code=500)
    except ApiException as e:
        logging.error("Error: app_controller.create_namespace.")
        raise HTTPException(status_code=e.status)


def delete_namespace(namespace_name: str, app_cluster_context: str):
    try:
        config.load_kube_config(context=app_cluster_context)
        api_instance = client.CoreV1Api()
        api_instance.delete_namespace(
            name=namespace_name, body=client.V1DeleteOptions()
        )
        logging.info(f"Namespace {namespace_name} deleted successfully!")
    except ConfigException as _:
        logging.error(f"Error: load_kube_config [app_controller.delete_namespace]")
        raise HTTPException(status_code=500)
    except ApiException as e:
        logging.error("Error: app_controller.delete_namespace.")
        raise HTTPException(status_code=e.status)


TEMPLATE_DIR = "C:/Users/skand/Downloads/PFE/kopf/application/templates"


def install_deployment(component: dict, app_cluster_context: str):
    # Get the deployment template
    environment = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    deployment_template = environment.get_template("deployment_template.yaml")
    try:
        # Configure fields
        rendered_deployment = deployment_template.render(
            name=component["name"],
            image=component["image"],
            expose=component.get("expose", ""),
            env=component.get("env", ""),
            namespace=component["application"],
            # secretName=secretName,
            clusterLabel=component.get("cluster-selector", ""),
            # service_list=service_list
            service_list=[],
        )

        yaml_output = yaml.safe_load(rendered_deployment)

    except Exception as _:
        logging.error(
            "Error: <<app.controller.install_deployment>> when generating the yaml file."
        )
        raise HTTPException(status_code=500)

    # Applying the output yaml file
    try:
        config.load_kube_config(context=app_cluster_context)
        api_instance = client.AppsV1Api()
        api_instance.create_namespaced_deployment(
            body=yaml_output, namespace=component["application"], pretty="true"
        )
        logging.info("Deployment created successfully!")
    except ConfigException as _:
        logging.error(f"Error: load_kube_config [app_controller.install_deployment]")
        raise HTTPException(status_code=500)
    except ApiException as e:
        logging.error("Error: app_controller.install_deployment")
        raise HTTPException(e.status)


def uninstall_deployment(component_name: str, app_name: str, app_cluster_context: str):
    try:
        config.load_kube_config(context=app_cluster_context)
        api_instance = client.AppsV1Api()
        api_instance.delete_namespaced_deployment(
            name=component_name, namespace=app_name
        )
        logging.info("Deployment uninstalled successfully!")
    except ConfigException as _:
        logging.error("Error: load_kube_config [app_controller.uninstall_deployment]")
        raise HTTPException(status_code=500)
    except ApiException as e:
        logging.error("Error: app_controller.uninstall_deployment")
        raise HTTPException(status_code=e.status)


def install_service(
    component_name: str, app_name: str, ports_list: list, app_cluster_context: str
):
    # Get template
    environment = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    service_template = environment.get_template("service_template.yaml")
    try:
        rendered_service = service_template.render(
            name=component_name,
            expose=ports_list,
            namespace=app_name,
        )

        yaml_output = yaml.safe_load(rendered_service)
    except Exception as _:
        # TODO: handle exception
        logging.error(
            "Error: <<app_controller.install_service>> when generating the yaml file"
        )
        raise HTTPException(status_code=500)

    # Applying the output yaml_output
    try:
        config.load_kube_config(context=app_cluster_context)
        api_instance = client.CoreV1Api()
        api_instance.create_namespaced_service(
            body=yaml_output, namespace=app_name, pretty="true"
        )
        logging.info(f"Service created successfully!")
    except ConfigException as _:
        logging.error("Error: load_kube_config [app_controller.install_service]")
        raise HTTPException(status_code=500)
    except ApiException as e:
        logging.error("Error: app_controller.install_service")
        raise HTTPException(status_code=e.status)


def uninstall_service(component_name: str, app_name: str, app_cluster_context: str):
    try:
        config.load_kube_config(context=app_cluster_context)
        api_instance = client.CoreV1Api()
        api_instance.delete_namespaced_service(name=component_name, namespace=app_name)
        logging.info("Service uninstalled successfully!")
    except ConfigException as _:
        logging.error("Error: load_kube_config [app_controller.uninstall_service]")
        raise HTTPException(status_code=500)
    except ApiException as e:
        logging.error("Error: app_controller.uninstall_service")
        raise HTTPException(status_code=e.status)
