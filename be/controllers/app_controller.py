from kubernetes import client, config
from kubernetes.client.rest import ApiException
from kubernetes.config.config_exception import ConfigException
from jinja2 import Environment, FileSystemLoader
from fastapi import HTTPException
import yaml
import os
import logging


group = os.environ.get("CRD_GROUP")
version = os.environ.get("CRD_VERSION")
TEMPLATE_DIR = os.environ.get("TEMPLATE_DIR")


def get_context(cluster: str):
    # In kind we have just to add the "kind-" to the cluster name to get the context
    # TODO
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
            plural="applications",
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


def install_deployment(component: dict, app_cluster_context: str, update: bool):
    # Get the deployment template
    try:
        environment = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
        deployment_template = environment.get_template("deployment_template.yaml")
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
        if update == False:
            api_instance.create_namespaced_deployment(
                body=yaml_output, namespace=component["application"], pretty="true"
            )
            logging.info("Deployment created successfully!")
        else:
            api_instance.replace_namespaced_deployment(
                body=yaml_output,
                namespace=component["application"],
                name=component["name"],
                pretty="true",
            )
            logging.info("Deployment updated successfully!")

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
    component_name: str,
    app_name: str,
    ports_list: list,
    app_cluster_context: str,
    update: bool,
):
    try:
        # Get template
        environment = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
        service_template = environment.get_template("service_template.yaml")
        rendered_service = service_template.render(
            name=component_name,
            expose=ports_list,
            namespace=app_name,
        )

        yaml_output = yaml.safe_load(rendered_service)
    except Exception as _:
        logging.error(
            "Error: <<app_controller.install_service>> when generating the yaml file"
        )
        raise HTTPException(status_code=500)

    # Applying the output yaml_output
    try:
        config.load_kube_config(context=app_cluster_context)
        api_instance = client.CoreV1Api()
        if update == False:
            api_instance.create_namespaced_service(
                body=yaml_output, namespace=app_name, pretty="true"
            )
            logging.info("Service created successfully!")
        else:
            api_instance.replace_namespaced_service(
                body=yaml_output, namespace=app_name, name=component_name, pretty="true"
            )
            logging.info("Service updated successfully!")
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


# Still other apps to be implemented
def install_servicemonitor(
    app_name: str,
    component_name: str,
    ports_list: list,
    app_cluster_context: str,
    update: bool,
):
    # Get the ServiceMonitor template
    try:
        environment = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
        service_monitor_template = environment.get_template(
            "ServiceMonitor_template.yaml"
        )
        rendered_service_monitor = service_monitor_template.render(
            namespace=app_name,
            component_name=component_name,
            expose=ports_list,
        )

        yaml_output = yaml.safe_load(rendered_service_monitor)
    except Exception as _:
        logging.error(
            "Error: <<app_controller.install_servicemonitor>> when generating the yaml file"
        )
        raise HTTPException(status_code=500)

    try:
        # Apply the CRD using the Kubernetes Python client library
        config.load_kube_config(context=app_cluster_context)
        api_instance = client.CustomObjectsApi()
        api_version = yaml_output["apiVersion"]
        if update == False:
            api_instance.create_namespaced_custom_object(
                group=api_version.split("/")[0],
                version=api_version.split("/")[1],
                namespace=app_name,
                plural="servicemonitors",
                body=yaml_output,
            )
            logging.info("ServiceMonitor created successfully!")
        else:
            api_instance.replace_namespaced_custom_object(
                group=api_version.split("/")[0],
                version=api_version.split("/")[1],
                namespace=app_name,
                name=component_name,
                plural="servicemonitors",
                body=yaml_output,
            )
            logging.info("ServiceMonitor updated successfully!")
    except ConfigException as _:
        logging.error("Error: load_kube_config [app_controller.install_servicemonitor]")
        raise HTTPException(status_code=500)
    except ApiException as e:
        logging.error("Error: app_controller.install_servicemonitor")
        raise HTTPException(status_code=e.status)


def uninstall_servicemonitor(
    component_name: str, app_name: str, app_cluster_context: str
):
    try:
        config.load_kube_config(context=app_cluster_context)
        api_instance = client.CustomObjectsApi()
        api_instance.delete_namespaced_custom_object(
            group="monitoring.coreos.com",
            version="v1",
            namespace=app_name,
            name=component_name,
            plural="servicemonitors",
            body=client.V1DeleteOptions(),
        )
    except ConfigException as _:
        logging.error("Error: load_kube_config [app_controller.install_servicemonitor]")
        raise HTTPException(status_code=500)
    except ApiException as e:
        logging.error("Error: app_controller.install_servicemonitor")
        raise HTTPException(status_code=e.status)


def delete_component(component_name: str, app_name: str):
    try:
        # default context : Management cluster
        config.load_kube_config()
        api_instance = client.CustomObjectsApi()
        api_instance.delete_namespaced_custom_object(
            group=group,
            version=version,
            namespace="default",  # TODO: change to app_name or change in the metadata
            name=component_name,
            plural="components",
            body=client.V1DeleteOptions(),
        )
    except ConfigException as _:
        logging.error("Error: load_kube_config [app_controller.delete_component]")
        raise HTTPException(status_code=500)
    except ApiException as e:
        logging.error("Error: app_controller.delete_component")
        raise HTTPException(status_code=e.status)


def add_host_to_ingress(
    app_name: str, component_name: str, app_cluster_context: str, port: int
):
    ingress_exist = True
    # Getting the ingress of the application if it exists
    try:
        hosts = _get_existing_hosts(
            app_cluster_context=app_cluster_context, app_name=app_name
        )
        hosts.append({"component_name": component_name, "port": port})
    except ApiException as e:
        if e.status == 404:
            ingress_exist = False
            hosts = [{"component_name": component_name, "port": port}]
        else:
            raise HTTPException(status_code=e.status)

    try:
        environment = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
        ingress_template = environment.get_template("ingress_template.yaml")
        rendered_ingress = ingress_template.render(
            app_name=app_name,
            component_name=component_name,
            hosts=hosts,
        )
        yaml_output = yaml.safe_load(rendered_ingress)
    except Exception as _:
        logging.error(
            "Error: <<app_controller.add_host_to_ingress>> when generating the yaml file"
        )
        raise HTTPException(status_code=500)

    try:
        api_instance = client.NetworkingV1Api()
        if ingress_exist == False:
            api_instance.create_namespaced_ingress(namespace=app_name, body=yaml_output)
            logging.info(f"ingress created successfully!")
        else:
            api_instance.replace_namespaced_ingress(
                name=f"{app_name}-ingress", namespace=app_name, body=yaml_output
            )
            logging.info("ingress updated successfully!")
    except ConfigException as _:
        logging.error("Error: load_kube_config [app_controller.add_host_to_ingress]")
        raise HTTPException(status_code=500)
    except ApiException as e:
        logging.error("Error: app_controller.add_host_to_ingress")
        raise HTTPException(status_code=e.status)


def remove_host_from_ingress(
    app_cluster_context: str, component_name: str, app_name: str
):
    try:
        hosts = _get_existing_hosts(
            app_cluster_context=app_cluster_context, app_name=app_name
        )
        hosts_list = [
            host for host in hosts if host["component_name"] != component_name
        ]

        # Updating or Deleting the ingress
        config.load_kube_config(context=app_cluster_context)
        api_instance = client.NetworkingV1Api()
        if len(hosts_list) == 0:
            # Remove the ingress
            api_instance.delete_namespaced_ingress(
                name=f"{app_name}-ingress", namespace=app_name
            )
            logging.info("ingress deleted successfully")
        else:
            environment = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
            ingress_template = environment.get_template("ingress_template.yaml")
            rendered_ingress = ingress_template.render(
                app_name=app_name,
                component_name=component_name,
                hosts=hosts_list,
            )
            yaml_output = yaml.safe_load(rendered_ingress)
            api_instance.replace_namespaced_ingress(
                name=f"{app_name}-ingress", namespace=app_name, body=yaml_output
            )
    except ConfigException as _:
        logging.error(
            "Error: load_kube_config [app_controller.remove_host_from_ingress]"
        )
        raise HTTPException(status_code=500)
    except ApiException as e:
        raise HTTPException(status_code=e.status)
    except Exception as _:
        raise HTTPException(status_code=500)


def update_host_in_ingress(
    app_cluster_context: str, component_name: str, app_name: str, new_port: int
):
    try:
        hosts = _get_existing_hosts(
            app_cluster_context=app_cluster_context, app_name=app_name
        )

        for host in hosts:
            if host["component_name"] == component_name:
                host["port"] = new_port
                break

        # Updating or Deleting the ingress
        environment = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
        ingress_template = environment.get_template("ingress_template.yaml")
        rendered_ingress = ingress_template.render(
            app_name=app_name,
            component_name=component_name,
            hosts=hosts,
        )
        yaml_output = yaml.safe_load(rendered_ingress)
        # Updating the ingress
        config.load_kube_config(context=app_cluster_context)
        api_instance = client.NetworkingV1Api()
        api_instance.replace_namespaced_ingress(
            name=f"{app_name}-ingress", namespace=app_name, body=yaml_output
        )
    except ConfigException as _:
        logging.error("Error: load_kube_config [app_controller.update_host_in_ingress]")
        raise HTTPException(status_code=500)
    except ApiException as e:
        raise HTTPException(status_code=e.status)
    except Exception as _:
        raise HTTPException(status_code=500)


def _get_existing_hosts(app_cluster_context: str, app_name: str):
    try:
        config.load_kube_config(context=app_cluster_context)
        api_instance = client.NetworkingV1Api()
        ingress = api_instance.read_namespaced_ingress(
            name=f"{app_name}-ingress", namespace=app_name
        )
        hosts = []
        for host in ingress.spec.rules:
            hosts.append(
                {
                    "component_name": host.http.paths[0].backend.service.name,
                    "port": host.http.paths[0].backend.service.port.number,
                }
            )
        return hosts
    except ConfigException as _:
        logging.error(
            "Error: load_kube_config [app_controller.add_host_to_ingress (_get_ingress)]"
        )
        raise HTTPException(status_code=500)
    except ApiException as e:
        raise e
