import kopf
import kubernetes
from fastapi import status
import config
import os
import re
import logging


# ---------------------------------- ADMISSION WEBHOOKS ---------------------------------- #
@kopf.on.startup()
def setup(settings: kopf.OperatorSettings, **_):
    settings.admission.managed = "auto.kopf.dev"
    settings.admission.server = kopf.WebhookAutoTunnel()


# ---------------------------------- Application-validation ---------------------------------- #
@kopf.on.validate("Application")
def validate_app(body, spec, warnings: list[str], **_):
    # application name will be used as a DNS label
    regex = re.compile("^(?![0-9]+$)(?!-)[a-zA-Z0-9-]{,63}(?<!-)$")
    is_match = regex.match(spec.get("name")) is not None
    if not is_match:
        raise kopf.AdmissionError("application name must be a valid DNS label name.")

    # Similarly componnet name must also be valid DNS label.
    for component in spec.get("components"):
        is_match = regex.match(component.get("name")) is not None
        if not is_match:
            raise kopf.AdmissionError("component name must be a valid DNS label name.")

    # Forbidden names : There are some pre-created namespaces when creating a new k8s cluster, for example "default" and "kube-system"..
    # So the application name must not be one of those names.

    forbidden_names = os.environ.get("FORBIDDEN_NAMES").split(",")

    if spec.get("name") in forbidden_names:
        raise kopf.AdmissionError(
            "application name forbidden, please choose another name for your application."
        )

    # Cluster must not be the management cluster
    management_cluster = os.environ.get("MANAGEMENT_CLUSTER")
    if spec.get("cluster") == management_cluster:
        raise kopf.AdmissionError(f"cluster must not be the {management_cluster}")

    for component in spec.get("components"):
        if component.get("cluster") == management_cluster:
            raise kopf.AdmissionError(f"cluster must not be the {management_cluster}")

    contexts, _ = kubernetes.config.list_kube_config_contexts()
    clusters = [context.get("context").get("cluster") for context in contexts]
    if spec.get("cluster") not in clusters:
        raise kopf.AdmissionError("Application cluster doesn't exist")

    for component in spec.get("components"):
        if component.get("cluster") not in clusters:
            raise kopf.AdmissionError(
                f"Cluster of component {component.get('name')} doesn't exist"
            )

    if (
        "namespace" in body.get("metadata")
        and body.get("metadata").get("namespace") != "default"
    ):
        raise kopf.AdmissionError("namespace must be set to default")

    if body.get("metadata").get("name", "") != spec.get("name"):
        raise kopf.AdmissionError("metatdata.name must be the same as spec.name")


# ---------------------------------- Component-validation ---------------------------------- #
@kopf.on.validate("Component")
def validate_comp(body, spec, warnings: list[str], **_):
    # application name and component name will be used as a DNS label, see ingress template to understand
    regex = re.compile("^(?![0-9]+$)(?!-)[a-zA-Z0-9-]{,63}(?<!-)$")
    is_match = regex.match(spec.get("name")) is not None
    if not is_match:
        raise kopf.AdmissionError("component name must be a valid DNS label name.")

    is_match = regex.match(spec.get("application")) is not None
    if not is_match:
        raise kopf.AdmissionError("application name must be a valid DNS label name.")

    # is-public must be true only in one port at most
    temp_list = [exp.get("is-public") for exp in spec.get("expose", [])]
    if sum(temp_list) > 1:
        raise kopf.AdmissionError("is-public set to true for two deffirent ports")

    # if is-public = true, is-peered must be true too
    for exp in spec.get("expose", []):
        if exp.get("is-public") == True and exp.get("is-peered") == False:
            raise kopf.AdmissionError(
                "is-public set to true but is-peered set to false"
            )

    # if is-exposing-metrics = true, is-peered muse be true too
    for exp in spec.get("expose", []):
        if exp.get("is-exposing-metrics") == True and exp.get("is-peered") == False:
            raise kopf.AdmissionError(
                "is-exposing-metrics set to true but is-peered set to false"
            )

    if "namespace" in body.get("metadata") and body.get("metadata").get(
        "namespace"
    ) != spec.get("application"):
        raise kopf.AdmissionError(f"namespace must be set to {spec.get('application')}")

    if body.get("metadata").get("name", "") != spec.get("name"):
        raise kopf.AdmissionError("metatdata.name must be the same as spec.name")


# ---------------------------------- APPLICATION-CRD ---------------------------------- #
@kopf.on.create("Application")
def create_app_handler(spec, **_):
    """
    This handler:
        - Creates the namespace in the application cluster.
        - Peers between the app_cluster and the component clusters if not already done.
        - Performs namespace offloading between app clusters and components clusters.
    """
    app_module = config.APPS["apps"]
    response = app_module.create_app(spec=spec.__dict__["_src"]["spec"])
    if response.status_code != status.HTTP_201_CREATED:
        logging.error("Something went wrong. [create_app_handler]")


@kopf.on.delete("Application")
def delete_app_handler(spec, **_):
    """
    This handler:
        - Deletes all the components of an application
        - Unpeer between clusters, if this will not break another application.
        - Unoffload the namespace of the application.
        - Deletes the namespace of the application from the application cluster.
    """
    app_module = config.APPS["apps"]
    response = app_module.delete_app(spec=spec.__dict__["_src"]["spec"])
    if response.status_code != status.HTTP_204_NO_CONTENT:
        logging.error("Something went wrong. [delete_app_handler]")


# Application name is immutable, so the only update that can happen to the Application crd is in the components list.
# component name is immutable as well, so the update is caused by three possibilities:
# - 01: a new component was added to the application
# - 02: a component was removed from the application
# - 03: a component migrated (changed cluster)
@kopf.on.update("Application", field="spec.components")
def update_app_handler(spec, old, new, **_):
    """
    This function:
        - Does all the peering and namespace offloading needed for the new added components to the application.
        - Does all the necessary unpeering and namespace un-offloading if a component was removed from the application.
        - Trigger the migration of a component if a component changed the cluster.
    """
    app_module = config.APPS["apps"]
    response = app_module.update_app(
        spec=spec.__dict__["_src"]["spec"], old=old, new=new
    )
    if response.status_code != status.HTTP_200_OK:
        logging.error("Something went wrong. [update_app_handler]")


# ---------------------------------- COMPONENT-CRD ---------------------------------- #
@kopf.on.create("Component")
def create_comp_handler(spec, **_):
    """
    This handler:
        - Creates deployment, service, servicemonitor, ingress ... related to the component.
    """
    app_module = config.APPS["apps"]
    response = app_module.create_comp(spec=spec.__dict__["_src"]["spec"])
    if response.status_code != status.HTTP_201_CREATED:
        logging.error("Something went wrong. [create_comp_handler]")


@kopf.on.delete("Component")
def delete_comp_handler(spec, **_):
    """
    This handler:
        - Deletes deployment, service, servicemonitor, ingress ... related to the component.
    """
    app_module = config.APPS["apps"]
    response = app_module.delete_comp(spec=spec.__dict__["_src"]["spec"])
    if response.status_code != status.HTTP_204_NO_CONTENT:
        logging.error("Something went wrong. [delete_comp_handler]")


# Note that this handler doesn't handle the update of "expose", "tls" fields. They are handled seperately
@kopf.on.update("Component", field="spec")
def update_comp_handler_deployment(body, **_):
    """
    - This function:
        - update the deployment related to the component.
    """
    # It will return "unchanged" if the deployment didn't change.
    try:
        app_module = config.APPS["apps"]
        component = body["spec"]
        application = body["spec"]["application"]

        # Re-apply the deployment
        response = app_module.install_deployment(
            component=component, app_name=application, update=True
        )
        if (response is None) or (response.status_code != status.HTTP_200_OK):
            logging.error("Error: app_module.install_deployment")

    except Exception as _:
        logging.error(
            "Exception in [on.update('Component') handler: [update_comp_handler_deployment] function.]"
        )


# Handler for the expose field
@kopf.on.update("Component", field="spec.expose")
def update_comp_handler_expose_field(body, old, new, **_):
    """
    - This function:
        - update the service, ingress, ServiceMonitor, By regenerating the yaml files and applying them again.
        - Delete the service, ingress, srvicemonitor if there is no longer need for them.
    """

    try:
        app_module = config.APPS["apps"]
        component_name = body["spec"]["name"]
        application = body["spec"]["application"]
        # ------------- UPDATE SERVICE -------------#
        # filter only the ports where "is-peered" is set to True (is-peered=True)
        peered_ports = [port for port in new if port["is-peered"] == True]
        old_peered_ports = [port for port in old if port["is-peered"] == True]
        if len(peered_ports):
            if len(old_peered_ports):
                update = True
            else:
                update = False
            response = app_module.install_service(
                component_name=component_name,
                app_name=application,
                ports_list=peered_ports,
                update=update,
            )
            if (response is None) or (response.status_code != status.HTTP_200_OK):
                logging.error("Error: app_module.install_service")

        else:
            # len(peered_ports) = 0 => no port is peered => DELETE the service if it was existing before.
            # Check whether the service was created before
            if len(old_peered_ports):
                # Delete the service
                response = app_module.uninstall_service(
                    component_name=component_name,
                    app_name=application,
                )
                if (response is None) or (
                    response.status_code != status.HTTP_204_NO_CONTENT
                ):
                    logging.error("Error: app_module.uninstall_service")

        # ------------- UPDATE SERVICEMONITOR -------------#
        # Exactly the same logic as above with "Service"
        exposing_metrics_ports = [
            port for port in new if port["is-exposing-metrics"] == True
        ]
        old_exposing_metrics_ports = [
            port for port in old if port["is-exposing-metrics"] == True
        ]
        if len(exposing_metrics_ports):
            if len(old_exposing_metrics_ports):
                update = True
            else:
                update = False
            # Re-aplly the ServiceMonitor
            response = app_module.install_servicemonitor(
                app_name=application,
                component_name=component_name,
                ports_list=exposing_metrics_ports,
                update=update,
            )
            if (response is None) or (response.status_code != status.HTTP_200_OK):
                logging.error("Error: app_module.install_servicemonitor")

        else:
            if len(old_exposing_metrics_ports):
                # Delete the ServiceMonitor
                response = app_module.uninstall_servicemonitor(
                    component_name=component_name,
                    app_name=application,
                )
                if (response is None) or (
                    response.status_code != status.HTTP_204_NO_CONTENT
                ):
                    logging.error("Error: app_module.uninstall_servicemonitor")

        # ------------- UPDATE INGRESS -------------#

        # maximum length of this list is 1
        new_public_port = None
        for port in new:
            if port["is-public"] == True:
                new_public_port = port
                break

        old_public_port = None
        for port in old:
            if port["is-public"] == True:
                old_public_port = port
                break

        # The component was not public, and updated to be public
        if new_public_port is not None and old_public_port is None:
            response = app_module.add_host_to_ingress(
                app_name=application,
                component_name=component_name,
                port=new_public_port["clusterPort"],
            )
            if response is None or response.status_code != status.HTTP_200_OK:
                logging.error("ERROR: app_module.add_host_to_ingress")

        # The component was public, and updated to be not public
        if new_public_port is None and old_public_port is not None:
            response = app_module.remove_host_from_ingress(
                app_name=application,
                component_name=component_name,
            )
            if response is None or response.status_code != status.HTTP_200_OK:
                logging.error("ERROR: app_module.remove_host_from_ingress")

        # The port updated
        if (
            new_public_port is not None
            and old_public_port is not None
            and new_public_port["clusterPort"] != old_public_port["clusterPort"]
        ):
            response = app_module.update_host_in_ingress(
                app_name=application,
                component_name=component_name,
                new_port=new_public_port["clusterPort"],
            )
            if response is None or response.status_code != status.HTTP_200_OK:
                logging.error("ERROR: app_module.update_host_in_ingress")

    except Exception as _:
        logging.error(
            "Exception in [on.update('Component') handler: [update_comp_handler_expose_field] function.]"
        )
