from controllers.helpers import k8s_resource_manager
from controllers.helpers.utils import get_changes
import os

group = os.environ.get("CRD_GROUP")
version = os.environ.get("CRD_VERSION")
TEMPLATE_DIR = os.environ.get("TEMPLATE_DIR")


# ------------------------------------------------------------ #
def create_app(spec: dict):
    # Retireving application cluster and application name from the body
    app_cluster = spec["cluster"]
    app_name = spec["name"]

    # Get the context of the app_cluster
    app_cluster_context = k8s_resource_manager.get_context(cluster=app_cluster)
    # Create namesapce in the app_cluster
    k8s_resource_manager.create_namespace(
        namespace_name=app_name, app_cluster_context=app_cluster_context
    )
    # Create namesapce in the management cluster
    k8s_resource_manager.create_namespace(
        namespace_name=app_name, app_cluster_context=None
    )
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

    for component in spec["components"]:
        # Delete the component CRD from the management cluster
        k8s_resource_manager.delete_component(
            component_name=component["name"], app_name=app_name
        )
    # TODO: .......
    # Deleting the namespace

    # Get the context of the app_cluster
    app_cluster_context = k8s_resource_manager.get_context(cluster=app_cluster)
    # Delete the namespace from the management cluster
    k8s_resource_manager.delete_namespace(
        namespace_name=app_name, app_cluster_context=None
    )
    # Delete the namespace from the app_cluster
    k8s_resource_manager.delete_namespace(
        namespace_name=app_name, app_cluster_context=app_cluster_context
    )


def update_app(spec: dict, old: list, new: list):
    added_components, removed_components, migrated_components = get_changes(old, new)

    # New components added to the application
    # We have to do the peering and the namespace offloading if this is not already done.
    if len(added_components):
        # The clusters already peered:
        peered_clusters = list(set([comp["cluster"] for comp in old]))
        for component in added_components:
            if component["cluster"] not in peered_clusters:
                # TODO: do the peering and the namespace offloading
                pass

    # Some components removed from the application
    # Here we have to delete the component, and un-offload the namespace and unpeer the clusters if this is not already done
    for component in removed_components:
        # Delete the component
        k8s_resource_manager.delete_component(
            component_name=component["name"], app_name=spec["name"]
        )

    # TODO: unpeer and un-offload the namespace if it's not needed by the current or another application (removed component)

    # Migration
    for component in migrated_components:
        # TODO: launch the migration of the component from the old cluster to the new cluster
        pass


# ------------------------------------------------------------ #
def create_comp(spec: dict):
    # get context
    app_cluster, _ = k8s_resource_manager.get_app_and_comp_cluster(
        app_name=spec["application"], component_name=spec["name"]
    )
    app_cluster_context = k8s_resource_manager.get_context(cluster=app_cluster)
    application = spec["application"]
    # apply the deployment
    k8s_resource_manager.apply_deployment(
        component=spec, app_cluster_context=app_cluster_context
    )

    # Applying service
    # First, we need to filter only the ports where "is-peered" is set to True (is-peered=True)
    peered_ports = [port for port in spec["expose"] if port["is-peered"] == True]
    if len(peered_ports):
        k8s_resource_manager.apply_service(
            component_name=spec["name"],
            app_name=spec["application"],
            app_cluster_context=app_cluster_context,
            ports_list=peered_ports,
        )

    # Applying ServiceMonitor
    # First, we need to filter only the ports where "is-exposing-metrics" is set to True (is-exposing-metrics=True)
    exposing_metrics_ports = [
        item for item in spec["expose"] if item["is-exposing-metrics"] == True
    ]
    if len(exposing_metrics_ports):
        k8s_resource_manager.apply_servicemonitor(
            app_name=spec["application"],
            app_cluster_context=app_cluster_context,
            component_name=spec["name"],
            ports_list=exposing_metrics_ports,
        )

    # Ingress
    for exp in spec["expose"]:
        if exp["is-public"] == True:
            k8s_resource_manager.add_host_to_ingress(
                app_name=spec["application"],
                app_cluster_context=app_cluster_context,
                component_name=spec["name"],
                port=exp["clusterPort"],
            )

            # Break because is-public could be true only once. [see validation admission webhook]
            break


def delete_comp(spec):
    # get context
    app_cluster, _ = k8s_resource_manager.get_app_and_comp_cluster(
        app_name=spec["application"], component_name=spec["name"]
    )
    app_cluster_context = k8s_resource_manager.get_context(cluster=app_cluster)

    #
    application = spec["application"]
    # delete the deployment
    k8s_resource_manager.delete_deployment(
        component_name=spec["name"],
        app_name=application,
        app_cluster_context=app_cluster_context,
    )

    # Deleting services, servicemonitors, ingresses ...
    if "expose" in spec and spec["expose"]:
        # Delete service
        for exp in spec["expose"]:
            if exp["is-peered"] == True:
                k8s_resource_manager.delete_service(
                    component_name=spec["name"],
                    app_name=spec["application"],
                    app_cluster_context=app_cluster_context,
                )
                # Break since we have only one service for each component
                break

        # Delete ServiceMonitor
        for exp in spec["expose"]:
            if exp["is-exposing-metrics"] == True:
                k8s_resource_manager.delete_servicemonitor(
                    component_name=spec["name"],
                    app_name=spec["application"],
                    app_cluster_context=app_cluster_context,
                )
                # Break since we have only one ServiceMonitor for each component
                break

        # Ingress
        for exp in spec["expose"]:
            if exp["is-public"] == True:
                k8s_resource_manager.remove_host_from_ingress(
                    app_name=spec["application"],
                    component_name=spec["name"],
                    app_cluster_context=app_cluster_context,
                )
                break


def update_comp_deployment(spec: dict):
    # get context
    app_cluster, _ = k8s_resource_manager.get_app_and_comp_cluster(
        app_name=spec["application"], component_name=spec["name"]
    )
    app_cluster_context = k8s_resource_manager.get_context(cluster=app_cluster)
    # Re-apply the deployment
    k8s_resource_manager.apply_deployment(
        component=spec, app_cluster_context=app_cluster_context, update=True
    )


def update_comp_expose_field(spec: dict, old: list, new: list):
    # get context
    app_cluster, _ = k8s_resource_manager.get_app_and_comp_cluster(
        app_name=spec["application"], component_name=spec["name"]
    )
    app_cluster_context = k8s_resource_manager.get_context(cluster=app_cluster)
    # Update
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
        k8s_resource_manager.apply_service(
            component_name=component_name,
            app_name=application,
            app_cluster_context=app_cluster_context,
            ports_list=peered_ports,
            update=update,
        )

    else:
        # len(peered_ports) = 0 => no port is peered => DELETE the service if it was existing before.
        # Check whether the service was created before
        if len(old_peered_ports):
            # Delete the service
            k8s_resource_manager.delete_service(
                component_name=component_name,
                app_name=application,
                app_cluster_context=app_cluster_context,
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
        k8s_resource_manager.apply_servicemonitor(
            app_name=application,
            app_cluster_context=app_cluster_context,
            component_name=component_name,
            ports_list=exposing_metrics_ports,
            update=update,
        )

    else:
        if len(old_exposing_metrics_ports):
            # Delete the ServiceMonitor
            k8s_resource_manager.delete_servicemonitor(
                component_name=component_name,
                app_name=application,
                app_cluster_context=app_cluster_context,
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
        k8s_resource_manager.add_host_to_ingress(
            app_name=application,
            app_cluster_context=app_cluster_context,
            component_name=component_name,
            port=new_public_port["clusterPort"],
        )

    # The component was public, and updated to be not public
    if new_public_port is None and old_public_port is not None:
        k8s_resource_manager.remove_host_from_ingress(
            app_name=application,
            app_cluster_context=app_cluster_context,
            component_name=component_name,
        )

    # The port updated
    if (
        new_public_port is not None
        and old_public_port is not None
        and new_public_port["clusterPort"] != old_public_port["clusterPort"]
    ):
        k8s_resource_manager.update_host_in_ingress(
            app_name=application,
            app_cluster_context=app_cluster_context,
            component_name=component_name,
            new_port=new_public_port["clusterPort"],
        )
