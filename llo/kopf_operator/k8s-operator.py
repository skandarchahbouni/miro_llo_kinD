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
def update_comp_handler_deployment(spec, **_):
    """
    - This function:
        - update the deployment related to the component.
    """
    # It will return "unchanged" if the deployment didn't change.
    app_module = config.APPS["apps"]
    response = app_module.update_comp_deployment(spec=spec.__dict__["_src"]["spec"])
    if response.status_code != status.HTTP_200_OK:
        logging.error("Something went wrong. [update_comp_handler_deployment]")


# Handler for the expose field
@kopf.on.update("Component", field="spec.expose")
def update_comp_handler_expose_field(spec, old, new, **_):
    """
    - This function:
        - update the service, ingress, ServiceMonitor, By regenerating the yaml files and applying them again.
        - Delete the service, ingress, srvicemonitor if there is no longer need for them.
    """
    app_module = config.APPS["apps"]
    response = app_module.update_comp_expose_field(
        spec=spec.__dict__["_src"]["spec"], old=old, new=new
    )
    if response.status_code != status.HTTP_200_OK:
        logging.error("Something went wrong. [update_comp_handler_expose_field]")
