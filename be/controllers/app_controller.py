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


# ------------------------------------------------------------ #
def create_app(spec: dict):
    # Retireving application cluster and application name from the body
    app_cluster = spec["cluster"]
    app_name = spec["name"]

    # Create namesapce in the app_cluster
    create_namespace(namespace_name=app_name, app_cluster=app_cluster)

    # Linking between the app_cluster and the components clusters
    components_list = spec["components"]

    # Unique list of components clusters
    components_clusters = list(set([comp["cluster"] for comp in components_list]))

    # Linking & ns offloading
    for cluster in components_clusters:
        if cluster != app_cluster:
            # TODO: Link the two clusters using by applying the link-crd
            # TODO: Offload the namespace
            pass


def delete_app(spec: dict):
    # Retireving application cluster and application name from the body
    app_name = spec["name"]
    app_cluster = spec["cluster"]
    components_list = spec["components"]

    print(components_list)
    # Removing all the components of the application
    for component in components_list:
        # Delete the component CRD from the management cluster
        delete_component(component_name=component["name"], app_name=app_name)

    # 2 - Unpeering and namespace un-offloading, if this will not break the current or another application
    # TODO: .......

    # 3 Deleting the namespace
    delete_namespace(namespace_name=app_name, app_cluster=app_cluster)


def update_app(spec: dict, old: list, new: list):
    added_components, removed_components, migrated_components = get_changes(old, new)

    # 1 - New components added to the application
    # We have to do the peering and the namespace offloading if this is not already done.
    if len(added_components):
        # The clusters already peered:
        peered_clusters = list(set([comp["cluster"] for comp in old]))
        for component in added_components:
            if component["cluster"] not in peered_clusters:
                # TODO: do the peering and the namespace offloading
                pass

    # 2 - Some components removed from the application
    # Here we have to delete the component, and un-offload the namespace and unpeer the clusters if this is not already done
    for component in removed_components:
        # Delete the component
        delete_component(component_name=component["name"], app_name=spec["name"])

    # TODO: unpeer and un-offload the namespace if it's not needed by the current or another application (removed component)

    # 3 - Migration
    for component in migrated_components:
        # TODO: launch the migration of the component from the old cluster to the new cluster
        pass


def create_comp(spec: dict):
    application = spec["application"]
    # install the deployment
    install_deployment(component=spec, app_name=application)

    # Installing service
    # First, we need to filter only the ports where "is-peered" is set to True (is-peered=True)
    peered_ports = [port for port in spec["expose"] if port["is-peered"] == True]
    if len(peered_ports):
        install_service(
            component_name=spec["name"],
            app_name=spec["application"],
            ports_list=peered_ports,
        )

    # Installing ServiceMonitor
    # First, we need to filter only the ports where "is-exposing-metrics" is set to True (is-exposing-metrics=True)
    exposing_metrics_ports = [
        item for item in spec["expose"] if item["is-exposing-metrics"] == True
    ]
    if len(exposing_metrics_ports):
        install_servicemonitor(
            app_name=spec["application"],
            component_name=spec["name"],
            ports_list=exposing_metrics_ports,
        )

    # Ingress
    for exp in spec["expose"]:
        if exp["is-public"] == True:
            add_host_to_ingress(
                app_name=spec["application"],
                component_name=spec["name"],
                port=exp["clusterPort"],
            )

            # Break because is-public could be true only once. [see validation admission webhook]
            break


def delete_comp(spec):
    application = spec["application"]
    # uninstall the deployment
    uninstall_deployment(
        component_name=spec["name"],
        app_name=application,
    )

    # uninstalling services, servicemonitors, ingresses ...
    if "expose" in spec and spec["expose"]:
        # Uninstall service
        for exp in spec["expose"]:
            if exp["is-peered"] == True:
                uninstall_service(
                    component_name=spec["name"],
                    app_name=spec["application"],
                )
                # Break since we have only one service for each component
                break

        # Uninstall ServiceMonitor
        for exp in spec["expose"]:
            if exp["is-exposing-metrics"] == True:
                uninstall_servicemonitor(
                    component_name=spec["name"],
                    app_name=spec["application"],
                )
                # Break since we have only one ServiceMonitor for each component
                break

        # Ingress
        for exp in spec["expose"]:
            if exp["is-public"] == True:
                remove_host_from_ingress(
                    app_name=spec["application"],
                    component_name=spec["name"],
                )
                break


# ---------------------------------- #


def create_namespace(namespace_name: str, app_cluster: str):
    try:
        # Create namespace in the app cluster
        app_cluster_context = _get_context(cluster=app_cluster)
        config.load_kube_config(context=app_cluster_context)
        api_instance = client.CoreV1Api()
        new_namespace = client.V1Namespace(
            metadata=client.V1ObjectMeta(name=namespace_name)
        )
        api_instance.create_namespace(body=new_namespace)
        # Create namespace in the management cluster
        config.load_kube_config()
        api_instance = client.CoreV1Api()
        new_namespace = client.V1Namespace(
            metadata=client.V1ObjectMeta(name=namespace_name)
        )
        api_instance.create_namespace(body=new_namespace)
        logging.info(f"Namespace {namespace_name} created successfully!.")
    except ConfigException as _:
        logging.error("Error: load_kube_config [create_namespace]")
        raise HTTPException(status_code=500)
    except ApiException as e:
        logging.error("Error: [create_namespace function].")
        raise HTTPException(status_code=e.status)


def delete_namespace(namespace_name: str, app_cluster: str):
    try:
        # Delete namespace in the app_cluster
        app_cluster_context = _get_context(app_cluster)
        config.load_kube_config(context=app_cluster_context)
        api_instance = client.CoreV1Api()
        api_instance.delete_namespace(
            name=namespace_name, body=client.V1DeleteOptions()
        )
        # Delete namespace in the management-cluster
        config.load_kube_config()
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


def install_deployment(component: dict, app_name: str, update: bool = False):
    # Get the app instance of the component
    app_cluster, comp_cluster = _get_app_and_comp_cluster(
        app_name=app_name, component_name=component["name"]
    )
    if comp_cluster != app_cluster:
        component["cluster-selector"] = comp_cluster

    # get the app_cluster context
    app_cluster_context = _get_context(cluster=app_cluster)

    # Loading the template
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


def uninstall_deployment(component_name: str, app_name: str):
    # Get the app instance of the component
    app_cluster, _ = _get_app_and_comp_cluster(
        app_name=app_name, component_name=component_name
    )
    # get the app_cluster context
    app_cluster_context = _get_context(cluster=app_cluster)

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
    update: bool = False,
):
    # Get the app instance of the component
    app_cluster, _ = _get_app_and_comp_cluster(
        app_name=app_name, component_name=component_name
    )

    # get the app_cluster context
    app_cluster_context = _get_context(cluster=app_cluster)

    # Loading the template
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


def uninstall_service(component_name: str, app_name: str):
    # Get the app instance of the component
    app_cluster, _ = _get_app_and_comp_cluster(
        app_name=app_name, component_name=component_name
    )
    # get the app_cluster context
    app_cluster_context = _get_context(cluster=app_cluster)

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
    update: bool = False,
):
    # Get the app instance of the component
    app_cluster, _ = _get_app_and_comp_cluster(
        app_name=app_name, component_name=component_name
    )
    # get the app_cluster context
    app_cluster_context = _get_context(cluster=app_cluster)

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
            # First get the resourceVersion of the serviceMonitor
            existing_servicemonitor = api_instance.get_namespaced_custom_object(
                group=api_version.split("/")[0],
                version=api_version.split("/")[1],
                namespace=app_name,
                name=component_name,
                plural="servicemonitors",
            )
            resource_version = existing_servicemonitor["metadata"]["resourceVersion"]
            yaml_output["metadata"]["resourceVersion"] = resource_version
            # Update
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


def uninstall_servicemonitor(component_name: str, app_name: str):
    # Get the app instance of the component
    app_cluster, _ = _get_app_and_comp_cluster(
        app_name=app_name, component_name=component_name
    )
    # get the app_cluster context
    app_cluster_context = _get_context(cluster=app_cluster)

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
            namespace=app_name,
            name=component_name,
            plural="components",
            body=client.V1DeleteOptions(),
        )
    except ConfigException as _:
        logging.error("Error: load_kube_config [app_controller.delete_component]")
        raise HTTPException(status_code=500)
    except ApiException as e:
        if e.status == 404:
            logging.info("Component doesn't exist.")
        else:
            logging.error("Exception: [delete_component function]")
            raise HTTPException(status_code=e.status)


def add_host_to_ingress(app_name: str, component_name: str, port: int):
    # Get the app instance of the component
    app_cluster, _ = _get_app_and_comp_cluster(
        app_name=app_name, component_name=component_name
    )
    # get the app_cluster context
    app_cluster_context = _get_context(cluster=app_cluster)

    # Getting the ingress of the application if it exists
    ingress_exist = True
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


def remove_host_from_ingress(component_name: str, app_name: str):
    # Get the app instance of the component
    app_cluster, _ = _get_app_and_comp_cluster(
        app_name=app_name, component_name=component_name
    )
    # get the app_cluster context
    app_cluster_context = _get_context(cluster=app_cluster)

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


def update_host_in_ingress(component_name: str, app_name: str, new_port: int):
    # Get the app instance of the component
    app_cluster, _ = _get_app_and_comp_cluster(
        app_name=app_name, component_name=component_name
    )
    # get the app_cluster context
    app_cluster_context = _get_context(cluster=app_cluster)

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


# ---------------------------------- Helper functions ---------------------------------- #
def _get_context(cluster: str) -> str:
    contexts, _ = config.list_kube_config_contexts()
    for context in contexts:
        cluster_name = context["context"]["cluster"]
        if cluster_name == cluster:
            return context["name"]
    # Raise exception if cluster not found
    logging.error("ERROR: cluster context not found! [_get_context]")
    raise HTTPException(status_code=500)


def _get_app_and_comp_cluster(
    app_name: str, component_name: str
) -> tuple[str | None, str | None]:
    try:
        config.load_kube_config()
        custom_objects_api = client.CustomObjectsApi()
        # Get the Custom Resource
        app_instance = custom_objects_api.get_namespaced_custom_object(
            group=group,
            version=version,
            namespace="default",
            plural="applications",
            name=app_name,
        )
        # Application cluster
        app_cluster = app_instance["spec"]["cluster"]
        # Component cluster
        comp_cluster = None
        for component in app_instance["spec"]["components"]:
            if component["name"] == component_name:
                comp_cluster = component["cluster"]
                break
        return app_cluster, comp_cluster
    except ConfigException as _:
        logging.error("Error: load_kube_config [app_controller.get_app_instance]")
        raise HTTPException(status_code=500)
    except ApiException as e:
        logging.error("Error: app_controller.get_app_instance")
        raise HTTPException(status_code=e.status)


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


def get_changes(old: dict | None, new: dict | None) -> tuple[list, list, list]:
    """
    This function compares between the old and new dict and returns the changes detected, which could be:
        - New components added to the application.
        - Some components Deleted from the application.
        - Some components changed the cluster (migration).
    """
    logging.info("get_changes function is called.")
    # All the components were added
    if old is None:
        return new, [], []

    # All the components were removed
    if new is None:
        return [], old, []

    added_components = [obj for obj in new if obj not in old]
    removed_components = [obj for obj in old if obj not in new]

    old_dict = {obj["name"]: obj["cluster"] for obj in old}
    new_dict = {obj["name"]: obj["cluster"] for obj in new}

    migrated_components = [
        {"name": name, "old_cluster": old_dict[name], "new_cluster": new_dict[name]}
        for name in set(old_dict) & set(new_dict)
        if old_dict[name] != new_dict[name]
    ]

    return added_components, removed_components, migrated_components
