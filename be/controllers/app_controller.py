from controllers.helpers.functions import (
    _get_app_and_comp_cluster,
    add_host_to_ingress,
    create_namespace,
    delete_component,
    delete_namespace,
    get_changes,
    install_deployment,
    install_service,
    install_servicemonitor,
    remove_host_from_ingress,
    remove_host_from_ingress_2,
    uninstall_deployment,
    uninstall_deployment_2,
    uninstall_service,
    uninstall_service_2,
    uninstall_servicemonitor,
    uninstall_servicemonitor_2,
    update_host_in_ingress,
)
import os
import time


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
    # 1 - Retireving application cluster and application name from the body
    app_name = spec["name"]
    app_cluster = spec["cluster"]
    for component in spec["components"]:
        # Delete the component CRD from the management cluster
        delete_component(component_name=component["name"], app_name=app_name)
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


# ------------------------------------------------------------ #
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
    _get_app_and_comp_cluster(app_name=spec["application"], component_name=spec["name"])
    application = spec["application"]
    # uninstall the deployment
    uninstall_deployment_2(
        component_name=spec["name"],
        app_name=application,
    )

    # uninstalling services, servicemonitors, ingresses ...
    if "expose" in spec and spec["expose"]:
        # Uninstall service
        for exp in spec["expose"]:
            if exp["is-peered"] == True:
                uninstall_service_2(
                    component_name=spec["name"],
                    app_name=spec["application"],
                )
                # Break since we have only one service for each component
                break

        # Uninstall ServiceMonitor
        for exp in spec["expose"]:
            if exp["is-exposing-metrics"] == True:
                uninstall_servicemonitor_2(
                    component_name=spec["name"],
                    app_name=spec["application"],
                )
                # Break since we have only one ServiceMonitor for each component
                break

        # Ingress
        for exp in spec["expose"]:
            if exp["is-public"] == True:
                remove_host_from_ingress_2(
                    app_name=spec["application"],
                    component_name=spec["name"],
                )
                break


def update_comp_deployment(spec: dict):
    application = spec["application"]
    # Re-apply the deployment
    install_deployment(component=spec, app_name=application, update=True)


def update_comp_expose_field(spec: dict, old: list, new: list):
    component_name = spec["name"]
    application = spec["application"]
    # ------------- UPDATE SERVICE -------------#
    # filter only the ports where "is-peered" is set to True (is-peered=True)
    peered_ports = [port for port in new if port["is-peered"] == True]
    old_peered_ports = [port for port in old if port["is-peered"] == True]
    if len(peered_ports):
        if len(old_peered_ports):
            update = True
        else:
            update = False
        install_service(
            component_name=component_name,
            app_name=application,
            ports_list=peered_ports,
            update=update,
        )

    else:
        # len(peered_ports) = 0 => no port is peered => DELETE the service if it was existing before.
        # Check whether the service was created before
        if len(old_peered_ports):
            # Delete the service
            uninstall_service(
                component_name=component_name,
                app_name=application,
            )

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
        install_servicemonitor(
            app_name=application,
            component_name=component_name,
            ports_list=exposing_metrics_ports,
            update=update,
        )

    else:
        if len(old_exposing_metrics_ports):
            # Delete the ServiceMonitor
            uninstall_servicemonitor(
                component_name=component_name,
                app_name=application,
            )

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
        add_host_to_ingress(
            app_name=application,
            component_name=component_name,
            port=new_public_port["clusterPort"],
        )

    # The component was public, and updated to be not public
    if new_public_port is None and old_public_port is not None:
        remove_host_from_ingress(
            app_name=application,
            component_name=component_name,
        )

    # The port updated
    if (
        new_public_port is not None
        and old_public_port is not None
        and new_public_port["clusterPort"] != old_public_port["clusterPort"]
    ):
        update_host_in_ingress(
            app_name=application,
            component_name=component_name,
            new_port=new_public_port["clusterPort"],
        )
