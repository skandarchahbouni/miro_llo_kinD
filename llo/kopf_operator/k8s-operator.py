import kopf
import logging
import kubernetes
from fastapi import status
import config
import re


# ---------------------------------- ADMISSION WEBHOOKS ---------------------------------- #
@kopf.on.startup()
def setup(settings: kopf.OperatorSettings, **_):
    settings.admission.managed = "auto.kopf.dev"
    settings.admission.server = kopf.WebhookAutoTunnel()


# ---------------------------------- Application-validation ---------------------------------- #
# def _validate_app_fields(spec):
#     # Regex for the application name
#     # application name will be used as a DNS label, see ingress template to understand
#     # Regex source: https://stackoverflow.com/questions/2063213/regular-expression-for-validating-dns-label-host-name
#     regex = re.compile("^(?![0-9]+$)(?!-)[a-zA-Z0-9-]{,63}(?<!-)$")
#     is_match = regex.match(spec.get("name")) is not None
#     if not is_match:
#         raise kopf.AdmissionError("application name must be a valid DNS label name.")

#     # Similarly application name must also be valid DNS label.
#     for component in spec.get("components"):
#         is_match = regex.match(component.get("name")) is not None
#         if not is_match:
#             raise kopf.AdmissionError("component name must be a valid DNS label name.")

#     # TODO: check clusters regex, and check that cluster exist and are ready

#     # Forbidden names : There are some pre-created namespaces when creating a new cluster, for example "default" and "kube-system"..
#     # So the application name must not be one of those names.
#     # TODO: use an api call to get this list instead of hardcoding it.
#     forbidden_names = [
#         "local-path-storage",
#         "kube-system",
#         "kube-public",
#         "kube-node-lease",
#         "ingress-nginx",
#         "monitoring",
#         "default",
#     ]

#     if spec.get("name") in forbidden_names:
#         raise kopf.AdmissionError(
#             "application name forbidden, please choose another name for your application."
#         )

#     contexts, _ = kubernetes.config.list_kube_config_contexts()
#     clusters = [context.get("context").get("cluster") for context in contexts]
#     if "kind-" + spec.get("cluster") not in clusters:
#         raise kopf.AdmissionError("Application cluster doesn't exist")

#     for component in spec.get("components"):
#         if "kind-" + component.get("cluster") not in clusters:
#             raise kopf.AdmissionError(
#                 f"Cluster of component {component.get('name')} doesn't exist"
#             )


# def _get_application_names() -> list[str]:
#     try:
#         kubernetes.config.load_kube_config()
#         custom_api = kubernetes.client.CustomObjectsApi()
#         # Replace "group", "version", and "plural" with your CRD details
#         group = "charity-project.eu"
#         version = "v1"
#         plural = "applications"
#         namespace = "default"
#         # Get the list of all instances of the "application" CRD in the specified namespace
#         resource_list = custom_api.list_namespaced_custom_object(
#             group, version, namespace, plural
#         )
#         # Extract and return the application names
#         return [resource["metadata"]["name"] for resource in resource_list["items"]]
#     except Exception as _:
#         raise kopf.AdmissionError("Something went wrong")


@kopf.on.validate("Application")
def validate_app(body, spec, warnings: list[str], **_):
    # Regex for the application name
    # application name will be used as a DNS label, see ingress template to understand
    # Regex source: https://stackoverflow.com/questions/2063213/regular-expression-for-validating-dns-label-host-name
    regex = re.compile("^(?![0-9]+$)(?!-)[a-zA-Z0-9-]{,63}(?<!-)$")
    is_match = regex.match(spec.get("name")) is not None
    if not is_match:
        raise kopf.AdmissionError("application name must be a valid DNS label name.")

    # Similarly application name must also be valid DNS label.
    for component in spec.get("components"):
        is_match = regex.match(component.get("name")) is not None
        if not is_match:
            raise kopf.AdmissionError("component name must be a valid DNS label name.")

    # TODO: check clusters regex, and check that cluster exist and are ready

    # Forbidden names : There are some pre-created namespaces when creating a new cluster, for example "default" and "kube-system"..
    # So the application name must not be one of those names.
    # TODO: use an api call to get this list instead of hardcoding it.
    forbidden_names = [
        "local-path-storage",
        "kube-system",
        "kube-public",
        "kube-node-lease",
        "ingress-nginx",
        "monitoring",
        "default",
    ]

    if spec.get("name") in forbidden_names:
        raise kopf.AdmissionError(
            "application name forbidden, please choose another name for your application."
        )

    # Cluster must not be the management cluster
    # Change this to env variable later
    if spec.get("cluster") == "management-cluster":
        raise kopf.AdmissionError("cluster must not be the management-cluster")

    for component in spec.get("components"):
        if component.get("cluster") == "management-cluster":
            raise kopf.AdmissionError("cluster must not be the management-cluster")

    contexts, _ = kubernetes.config.list_kube_config_contexts()
    clusters = [context.get("context").get("cluster") for context in contexts]
    if "kind-" + spec.get("cluster") not in clusters:
        raise kopf.AdmissionError("Application cluster doesn't exist")

    for component in spec.get("components"):
        if "kind-" + component.get("cluster") not in clusters:
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
    # warnings.append("Verified with the operator's hook. [CREATE OPERATION]")
    # Regex for the application name
    # application name and component name will be used as a DNS label, see ingress template to understand
    # Regex source: https://stackoverflow.com/questions/2063213/regular-expression-for-validating-dns-label-host-name
    regex = re.compile("^(?![0-9]+$)(?!-)[a-zA-Z0-9-]{,63}(?<!-)$")
    is_match = regex.match(spec.get("name")) is not None
    if not is_match:
        raise kopf.AdmissionError("component name must be a valid DNS label name.")

    is_match = regex.match(spec.get("application")) is not None
    if not is_match:
        raise kopf.AdmissionError("application name must be a valid DNS label name.")

    # Check that the application exist
    # app_module = config.APPS["apps"]
    # response = app_module.get_app_instance(
    #     application_name=spec.get("application")
    # )  # TODO: implement this function
    # if response is None:
    #     raise kopf.AdmissionError("Something went wrong!")
    # elif response.status_code == status.HTTP_404_NOT_FOUND:
    #     raise kopf.AdmissionError(
    #         "App instance doesn't exist. you have always to create the application before creating it's components."
    #     )
    # elif response.status_code != status.HTTP_200_OK:
    #     raise kopf.AdmissionError("Something went wrong!")

    # app_instance = response.json()
    # # check that the component name is registred in the application
    # components_names = [comp["name"] for comp in app_instance["spec"]["components"]]
    # if spec.get("name") not in components_names:
    #     raise kopf.AdmissionError("Component not registred in the application.")

    # is-public must be true only in one port at most
    temp_list = [exp.get("is-public") for exp in spec.get("expose", [])]
    if sum(temp_list) > 1:
        raise kopf.AdmissionError("is-public set to true for two deffirent ports")

    # if is-public = true than, is-peered must be true as well
    for exp in spec.get("expose", []):
        if exp.get("is-public") == True and exp.get("is-peered") == False:
            raise kopf.AdmissionError(
                "is-public set to true but is-peered set to false"
            )

    if (
        "namespace" in body.get("metadata")
        and body.get("metadata").get("namespace") != "default"
    ):
        raise kopf.AdmissionError(f"namespace must be set to default")

    if body.get("metadata").get("name", "") != spec.get("name"):
        raise kopf.AdmissionError("metatdata.name must be the same as spec.name")


# ---------------------------------- APPLICATION-CRD ---------------------------------- #
@kopf.on.create("Application")
def create_app_handler(body, **_):
    """
    This handler:
        - Creates the namespace in the application cluster.
        - Peers between the app_cluster and the component clusters if not already done.
        - Performs namespace offloading between app clusters and components clusters.
    """

    app_module = config.APPS["apps"]

    # Retireving application cluster and application name from the body
    app_cluster = body["spec"]["cluster"]
    app_name = body["spec"]["name"]

    try:
        # 1- Creating the namespace in the application cluster
        #  Before creating the namespcae, we have to get the context of the application cluster
        response = app_module.get_context(
            cluster=app_cluster
        )  # TODO: check whether the get context function should be in the app_module or another location, and implement it
        if (response is None) or (response.status_code != status.HTTP_200_OK):
            logging.error(f"Error while retrieving context of {app_cluster} cluster")

        app_cluster_context = response.json().get("context")
        # Now, create the namespcae in the application cluster
        response = app_module.create_namespace(
            namespace_name=app_name, app_cluster_context=app_cluster_context
        )  # TODO: ADD THIS FUNCTION
        if (response is None) or (response.status_code != status.HTTP_201_CREATED):
            logging.error("Error: app_module.create_namespace")

        # 2- Linking between the app_cluster and the components clusters
        components_list = body["spec"]["components"]

        # Unique list of components clusters
        components_clusters = list(set([comp["cluster"] for comp in components_list]))

        # Linking & ns offloading
        for cluster in components_clusters:
            if cluster != app_cluster:
                # TODO: Link the two clusters using by applying the link-crd
                # TODO: Offload the namespace
                pass

    except Exception as _:
        # TODO: handle exceptions
        logging.error("Exception in [on.create('Application') handler]")


@kopf.on.delete("Application")
def delete_app_handler(body, **_):
    """
    This handler:
        - Deletes all the components of an application
        - Unpeer between clusters, if this will not break another application.
        - Unoffload the namespace of the application.
        - Deletes the namespace of the application from the application cluster.
    """
    app_module = config.APPS["apps"]

    # Retireving application cluster and application name from the body
    app_name = body["spec"]["name"]
    app_cluster = body["spec"]["cluster"]
    components_list = body["spec"]["components"]

    try:
        # 1 - Removing all the components of the application
        for component in components_list:
            # Delete the component CRD from the management cluster
            response = app_module.delete_component(
                component_name=component["name"], app_name=app_name
            )  # TODO: implement this function
            if (response is None) or (
                response.status_code != status.HTTP_204_NO_CONTENT
            ):
                logging.error("Error: app_module.delete_component")

        # 2 - Unpeering and namespace un-offloading, if this will not break the current or another application
        # TODO: .......

        # 3 Deleting the namespace
        # Before deleting the namespcae, we have to get the context of the application cluster
        response = app_module.get_context(
            cluster=app_cluster
        )  # TODO: check whether the get context function should be in the app_module or another location, and implement it
        if (response is None) or (response.status_code != status.HTTP_200_OK):
            logging.error(f"Error while retrieving context of {app_cluster} cluster")

        app_cluster_context = response.json().get("context")
        response = app_module.delete_namespace(
            namespace_name=app_name, app_cluster_context=app_cluster_context
        )  # TODO: add this function
        if (response is None) or (response.status_code != status.HTTP_204_NO_CONTENT):
            logging.error("Error: app_module.delete_namespace")

    except Exception as _:
        # TODO: handle exceptions
        logging.error("Exception in [on.delete('Application') handler]")


# Application name is immutable, so the only update that can happen to the Application crd is in the components list.
# component name is immutable as well, so the update is caused by three possibilities:
# - 01: a new component was added to the application
# - 02: a component was removed from the application
# - 03: a component migrated (changed cluster)


@kopf.on.update("Application", field="spec.components")
def update_app_handler(body, old, new, **_):
    """
    This function:
        - Does all the peering and namespace offloading needed for the new added components to the application.
        - Does all the necessary unpeering and namespace un-offloading if a component was removed from the application.
        - Trigger the migration of a component if a component changed the cluster.
    """
    app_module = config.APPS["apps"]

    added_components, removed_components, migrated_components = app_module.get_changes(
        old, new
    )  # TODO : Implement this function

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
        response = app_module.delete_component(
            component_name=component["name"], app_name=body["spec"]["name"]
        )  # TODO: implement this function
        if (response is None) or (response.status_code != status.HTTP_204_NO_CONTENT):
            logging.error("Error: app_module.delete_component")

    # TODO: unpeer and un-offload the namespace if it's not needed by the current or another application (removed component)

    # 3 - Migration
    for component in migrated_components:
        # TODO: launch the migration of the component from the old cluster to the new cluster
        pass


# ---------------------------------- COMPONENT-CRD ---------------------------------- #
@kopf.on.create("Component")
def create_comp_handler(body, **_):
    """
    This function:
        - Creates deployment, service, servicemonitor, ingress ... related to the component.
    """
    app_module = config.APPS["apps"]

    component = body["spec"]
    # component["name"] = body["metadata"]["name"]
    application = body["spec"]["application"]

    # 1 - Get the application cluster from the application instance
    try:
        response = app_module.get_app_instance(
            application_name=application
        )  # TODO: implement this function
        if response is None:
            logging.error("Something went wrong!")

        elif response.status_code == status.HTTP_404_NOT_FOUND:
            logging.error(
                "App instance doesn't exist. you have always to create the application before creating it's components."
            )

        elif response.status_code != status.HTTP_200_OK:
            logging.error("Something went wrong!")

        app_instance = response.json()
    except Exception as _:
        logging.error("Exception in [on.create('Component') handler]")

    app_cluster = app_instance["spec"]["cluster"]

    # Confirm that the component is registred in the application
    components_names = [comp["name"] for comp in app_instance["spec"]["components"]]
    if body["spec"]["name"] not in components_names:
        logging.error("Component not registred in the application.")

    # Retrieve the component cluster
    for comp in app_instance["spec"]["components"]:
        if (comp["name"] == body["spec"]["name"]) and (comp["cluster"] != app_cluster):
            component["cluster-selector"] = comp["cluster"]
            break

    # 2 - Create the needed resources (deployment, service, ingress, servicemonitor ...)
    try:
        # Getting the app_cluster context
        resp = app_module.get_context(
            cluster=app_cluster
        )  # TODO: check whether the get context function should be in the app_module or another location, and implement it
        if (resp is None) or (resp.status_code != status.HTTP_200_OK):
            logging.error(f"Error while retrieving context of {app_cluster} cluster")

        app_cluster_context = resp.json().get("context")
        # install the deployment
        response = app_module.install_deployment(
            component=component, app_cluster_context=app_cluster_context
        )  # TODO: Customize this function
        if (response is None) or (response.status_code != status.HTTP_201_CREATED):
            logging.error("Error: app_module.install_deployment")

        # Installing service
        # First, we need to filter only the ports where "is-peered" is set to True (is-peered=True)
        peered_ports = [
            port for port in component["expose"] if port["is-peered"] == True
        ]
        if len(peered_ports):
            response = app_module.install_service(
                component_name=component["name"],
                app_name=component["application"],
                ports_list=peered_ports,
                app_cluster_context=app_cluster_context,
            )  # TODO: Customize this function
            if (response is None) or (response.status_code != status.HTTP_201_CREATED):
                logging.error("Error: app_module.install_service")

        # Installing ServiceMonitor
        # First, we need to filter only the ports where "is-exposing-metrics" is set to True (is-exposing-metrics=True)
        exposing_metrics_ports = [
            item for item in component["expose"] if item["is-exposing-metrics"] == True
        ]
        if len(exposing_metrics_ports):
            response = app_module.install_servicemonitor(
                app_name=component["application"],
                component_name=component["name"],
                ports_list=exposing_metrics_ports,
                app_cluster_context=app_cluster_context,
            )  # TODO: add this function
            if (response is None) or (response.status_code != status.HTTP_201_CREATED):
                logging.error("Error: app_module.install_servicemonitor")

        # Ingress
        for exp in component["expose"]:
            if exp["is-public"] == True:
                response = app_module.add_host_to_ingress(
                    app_cluster_context=app_cluster_context,
                    app_name=component["application"],
                    component_name=component["name"],
                    port=exp["clusterPort"],
                )
                if (response is None) or (response.status_code != status.HTTP_200_OK):
                    logging.error("Error: app_module.add_host_to_ingress")

                # Break because is-public could be true only once. [see validation admission webhook]
                break

        # TODO : Check anything else to do .....
    except Exception as _:
        logging.error("Exception in [on.create('Component') handler]")


@kopf.on.delete("Component")
def delete_comp_handler(body, **_):
    """
    This function:
        - Deletes deployment, service, servicemonitor, ingress ... related to the component.
    """

    component = body["spec"]
    # component["name"] = body["metadata"]["name"]
    application = body["spec"]["application"]
    app_module = config.APPS["apps"]

    # 1 - Get the application cluster from the application instance, as well as the component cluster
    try:
        response = app_module.get_app_instance(
            application_name=application
        )  # TODO: implement this function
        if (response is None) or (response.status_code != status.HTTP_200_OK):
            logging.error("Something went wrong!")

        app_instance = response.json()
    except Exception as _:
        # TODO: handle exceptions
        logging.error("Exception in [on.delete('Component') handler]")

    app_cluster = app_instance["spec"]["cluster"]

    # TODO :
    # !!! IMPORTANT !!! #
    # Do we need to pass the component cluster in order to delete the deployment ????
    # The deployment delete should be applied in the app_cluster or in the component_cluster or both ...?
    # If we have to apply the delete command in the "component cluster", than we have to retrive and pass it's context....(code will change)
    # !!! IMPORTANT !!! #

    # 2 - Delete resources (deployment, service, ingress, servicemonitor ...) related to the component
    try:
        # Getting the app_cluster context
        resp = app_module.get_context(
            cluster=app_cluster
        )  # TODO: check whether the get context function should be in the app_module or another location, and implement it
        if (resp is None) or (resp.status_code != status.HTTP_200_OK):
            logging.error(f"Error while retrieving context of {app_cluster} cluster")

        app_cluster_context = resp.json().get("context")
        # uninstall the deployment
        response = app_module.uninstall_deployment(
            component_name=component["name"],
            app_name=component["application"],
            app_cluster_context=app_cluster_context,
        )  # TODO: Customize this function
        if (response is None) or (response.status_code != status.HTTP_204_NO_CONTENT):
            logging.error("Error: app_module.uninstall_deployment")

        # uninstalling services, servicemonitors, ingresses ...
        if "expose" in component and component["expose"]:
            # Uninstall service
            for exp in component["expose"]:
                if exp["is-peered"] == True:
                    response = app_module.uninstall_service(
                        component_name=component["name"],
                        app_name=component["application"],
                        app_cluster_context=app_cluster_context,
                    )  # TODO: Customize this function
                    if (response is None) or (
                        response.status_code != status.HTTP_204_NO_CONTENT
                    ):
                        logging.error("Error: app_module.uninstall_service")

                    # Break since we have only one service for each component
                    break

            # Uninstall ServiceMonitor
            for exp in component["expose"]:
                if exp["is-exposing-metrics"] == True:
                    response = app_module.uninstall_servicemonitor(
                        component_name=component["name"],
                        app_name=component["application"],
                        app_cluster_context=app_cluster_context,
                    )  # TODO: add this function
                    if (response is None) or (
                        response.status_code != status.HTTP_204_NO_CONTENT
                    ):
                        logging.error("Error: app_module.uninstall_servicemonitor")

                    # Break since we have only one ServiceMonitor for each component
                    break

            # Ingress
            for exp in component["expose"]:
                if exp["is-public"] == True:
                    response = app_module.remove_host_from_ingress(
                        app_cluster_context=app_cluster_context,
                        app_name=component["application"],
                        component_name=component["name"],
                    )
                    if (response is None) or (
                        response.status_code != status.HTTP_200_OK
                    ):
                        logging.error("Error: app_module.remove_host_from_ingress")
                    break

    except Exception as _:
        # TODO: handle exeptions
        logging.error("Exception in [on.delete('Component') handler]")


# Please note that this function doesn't handle the update of "expose", "tls" fields.
# They are handled seperately
# This function is the same as the beginning create component handler... we can create a function for the common part.
# The function that handle the update of : 'application_name', '', '' fields. are listed below this handler.
@kopf.on.update("Component", field="spec")
def update_comp_handler_deployment(body, **_):
    """
    - This function:
        - update the deployment related to the component.
    """
    # It will return "unchanged" if the deployment didn't change.

    app_module = config.APPS["apps"]
    component = body["spec"]
    # component["name"] = body["metadata"]["name"]
    application = body["spec"]["application"]

    # 1 - Get the application cluster from the application instance
    try:
        response = app_module.get_app_instance(
            application_name=application
        )  # TODO: implement this function
        if (response is None) or (response.status_code != status.HTTP_200_OK):
            logging.error("Something went wrong!")

        app_instance = response.json()
    except Exception as _:
        # TODO: handle exceptions
        logging.error(
            "Exception in [on.update('Component') handler: [update_comp_handler_deployment] function.]"
        )

    app_cluster = app_instance["spec"]["cluster"]

    # Retrieve the component cluster
    for comp in app_instance["spec"]["components"]:
        if comp["name"] == body["spec"]["name"]:
            component["cluster-selector"] = comp["cluster"]
            break

    # 2 - Update the deployment
    try:
        # Getting the app_cluster context
        resp = app_module.get_context(
            cluster=app_cluster
        )  # TODO: check whether the get context function should be in the app_module or another location, and implement it
        if (resp is None) or (resp.status_code != status.HTTP_200_OK):
            logging.error(f"Error while retrieving context of {app_cluster} cluster")

        app_cluster_context = resp.json().get("context")
        # Re-apply the deployment (we can rename the "install_deployment" function to "apply_deployment")
        # ZZZZZZZZ
        response = app_module.install_deployment(
            component=component, app_cluster_context=app_cluster_context
        )
        if (response is None) or (response.status_code != status.HTTP_201_CREATED):
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
    app_module = config.APPS["apps"]

    # Get the application cluster from the application instance
    try:
        response = app_module.get_app_instance(
            application_name=body["spec"]["application"]
        )  # TODO: implement this function
        if (response is None) or (response.status_code != status.HTTP_200_OK):
            logging.error("Something went wrong!")

        app_instance = response.json()
    except Exception as _:
        # TODO: handle exceptions
        logging.error(
            "Exception in [on.update('Component') handler: [update_comp_handler_expose_field] function.]"
        )

    app_cluster = app_instance["spec"]["cluster"]

    # Retrieving the app_cluster context
    resp = app_module.get_context(
        cluster=app_cluster
    )  # TODO: check whether the get context function should be in the app_module or another location, and implement it
    if (resp is None) or (resp.status_code != status.HTTP_200_OK):
        logging.error(f"Error while retrieving context of {app_cluster} cluster")

    app_cluster_context = resp.json().get("context")

    try:
        # ------------- UPDATE SERVICE -------------#
        # filter only the ports where "is-peered" is set to True (is-peered=True)
        peered_ports = [port for port in new if port["is-peered"] == True]
        if len(peered_ports):
            # Re-aplly the service,
            response = app_module.install_service(
                component_name=body["spec"]["name"],
                app_name=body["spec"]["application"],
                ports_list=peered_ports,
                app_cluster_context=app_cluster_context,
            )  # TODO: Customize this function
            if (response is None) or (response.status_code != status.HTTP_201_CREATED):
                logging.error("Error: app_module.install_service")

        else:
            # len(peered_ports) = 0 => no port is peered => DELETE the service if it was existing before.
            # Check whether the service was created before
            old_peered_ports = [port for port in old if port["is-peered"] == True]
            if len(old_peered_ports):
                # Delete the service
                response = app_module.uninstall_service(
                    component_name=body["spec"]["name"],
                    app_name=body["spec"]["application"],
                    app_cluster_context=app_cluster_context,
                )  # TODO: Customize this function
                if (response is None) or (
                    response.status_code != status.HTTP_204_NO_CONTENT
                ):
                    logging.error("Error: app_module.uninstall_service")

        # ------------- UPDATE SERVICEMONITOR -------------#
        # Exactly the same logic as above with "Service"
        exposing_metrics_ports = [
            port for port in new if port["is-exposing-metrics"] == True
        ]
        if len(exposing_metrics_ports):
            # Re-aplly the service,
            response = app_module.install_servicemonitor(
                app_name=body["spec"]["application"],
                component_name=body["spec"]["name"],
                ports_list=exposing_metrics_ports,
                app_cluster_context=app_cluster_context,
            )  # TODO: Customize this function
            if (response is None) or (response.status_code != status.HTTP_201_CREATED):
                logging.error("Error: app_module.install_servicemonitor")

        else:
            old_exposing_metrics_ports = [
                port for port in old if port["is-exposing-metrics"] == True
            ]
            if len(old_exposing_metrics_ports):
                # Delete the service
                response = app_module.uninstall_servicemonitor(
                    component_name=body["spec"]["name"],
                    app_name=body["spec"]["application"],
                    app_cluster_context=app_cluster_context,
                )  # TODO: Customize this function
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
                app_cluster_context=app_cluster_context,
                app_name=body["spec"]["application"],
                component_name=body["spec"]["name"],
                port=new_public_port["clusterPort"],
            )
            if response is None or response.status_code != status.HTTP_200_OK:
                logging.error("ERROR: app_module.add_host_to_ingress")

        # The component was public, and updated to be not public
        if new_public_port is None and old_public_port is not None:
            response = app_module.remove_host_from_ingress(
                app_cluster_context=app_cluster_context,
                app_name=body["spec"]["application"],
                component_name=body["spec"]["name"],
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
                app_cluster_context=app_cluster_context,
                app_name=body["spec"]["application"],
                component_name=body["spec"]["name"],
                new_port=new_public_port["clusterPort"],
            )
            if response is None or response.status_code != status.HTTP_200_OK:
                logging.error("ERROR: app_module.update_host_in_ingress")

    except Exception as _:
        logging.error(
            "Exception in [on.update('Component') handler: [update_comp_handler_expose_field] function.]"
        )


# Handler for the tls field
@kopf.on.update("Component", field="spec.tls")
def update_comp_handler_tls_field(old, new, **_):
    """
    - This function:
        - ........
    """
    pass