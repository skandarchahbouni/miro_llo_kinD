import requests
import os
import logging

# API_URL = "http://orch-backend.orchestration.miro.onesource.pt/v1"
API_URL = os.environ.get("API_URL")


# ---------------------------------- Functions Needed by the 'application-crd' Operator ---------------------------------- #
def create_app(spec: dict) -> requests.Response | None:
    logging.info("create_app function is called.")
    url = API_URL + "/apps"
    try:
        response = requests.post(url=url, json=spec)
        return response
    except requests.exceptions.ConnectionError:
        logging.error("A connection error occurred. [create_app function]")
    except requests.exceptions.Timeout:
        logging.error("The request timed out. [create_app function]")
    except requests.exceptions.HTTPError as _:
        logging.error("HTTP Error. [create_app function]")
    except requests.exceptions.RequestException as _:
        logging.error("An error occurred. [create_app function]")
    return None


def delete_app(spec: dict) -> requests.Response | None:
    logging.info("delete_app function is called.")
    url = API_URL + f"/apps/{spec['name']}"
    try:
        response = requests.delete(url=url, json=spec)
        return response
    except requests.exceptions.ConnectionError:
        logging.error("A connection error occurred. [delete_app function]")
    except requests.exceptions.Timeout:
        logging.error("The request timed out. [delete_app function]")
    except requests.exceptions.HTTPError as _:
        logging.error("HTTP Error. [delete_app function]")
    except requests.exceptions.RequestException as _:
        logging.error("An error occurred. [delete_app function]")
    return None


def update_app(spec: dict, old: list, new: list) -> requests.Response | None:
    logging.info("update_app function is called.")
    url = API_URL + f"/apps/{spec['name']}"
    try:
        response = requests.put(url=url, json={"spec": spec, "old": old, "new": new})
        return response
    except requests.exceptions.ConnectionError:
        logging.error("A connection error occurred. [update_app function]")
    except requests.exceptions.Timeout:
        logging.error("The request timed out. [update_app function]")
    except requests.exceptions.HTTPError as _:
        logging.error("HTTP Error. [update_app function]")
    except requests.exceptions.RequestException as _:
        logging.error("An error occurred. [update_app function]")
    return None


def create_comp(spec: dict) -> requests.Response | None:
    logging.info("create_comp function is called.")
    url = API_URL + "/comps"
    try:
        response = requests.post(url=url, json=spec)
        return response
    except requests.exceptions.ConnectionError:
        logging.error("A connection error occurred. [create_comp function]")
    except requests.exceptions.Timeout:
        logging.error("The request timed out. [create_comp function]")
    except requests.exceptions.HTTPError as _:
        logging.error("HTTP Error. [create_comp function]")
    except requests.exceptions.RequestException as _:
        logging.error("An error occurred. [create_comp function]")
    return None


def delete_comp(spec: dict) -> requests.Response | None:
    logging.info("delete_comp function is called.")
    url = API_URL + f"/comps/{spec['name']}"
    try:
        response = requests.delete(url=url, json=spec)
        return response
    except requests.exceptions.ConnectionError:
        logging.error("A connection error occurred. [delete_comp function]")
    except requests.exceptions.Timeout:
        logging.error("The request timed out. [delete_comp function]")
    except requests.exceptions.HTTPError as _:
        logging.error("HTTP Error. [delete_comp function]")
    except requests.exceptions.RequestException as _:
        logging.error("An error occurred. [delete_comp function]")
    return None


# ---------------------------------- Functions Needed by the 'application-crd' Operator ---------------------------------- #
def create_namespace(namespace_name: str, app_cluster: str) -> requests.Response | None:
    """
    - This function should create a namespace named 'namespace_name' in the 'app_cluster'.
    - Equivalent tot the commands:
        - kubectl config use-context 'app_cluster_context' # Switch the context to the app_cluster.
        - kubectl create ns "namespace_name"
    """
    logging.info("create_namespace function is called.")
    url = API_URL + "/namespaces"
    body = {
        "namespace_name": namespace_name,
        "app_cluster": app_cluster,
    }
    try:
        response = requests.post(url=url, json=body)
        return response
    except requests.exceptions.ConnectionError:
        logging.error("A connection error occurred. [create_namespace function]")
    except requests.exceptions.Timeout:
        logging.error("The request timed out. [create_namespace function]")
    except requests.exceptions.HTTPError as _:
        logging.error("HTTP Error. [create_namespace function]")
    except requests.exceptions.RequestException as _:
        logging.error("An error occurred. [create_namespace function]")
    return None


def delete_namespace(namespace_name: str, app_cluster: str) -> requests.Response | None:
    """
    - This function should delete the namespace named 'namespace_name' in the 'app_cluster'.
    - Equivalent tot the commands:
        - kubectl config use-context 'app_cluster_context' # Switch the context to the app_cluster.
        - kubectl delete ns "namespace_name"
    """
    logging.info("delete_namespace function is called.")
    url = API_URL + f"/namespaces/{namespace_name}"
    body = {"app_cluster": app_cluster}
    try:
        response = requests.delete(url=url, json=body)
        return response
    except requests.exceptions.ConnectionError:
        logging.error("A connection error occurred. [delete_namespace function]")
    except requests.exceptions.Timeout:
        logging.error("The request timed out. [delete_namespace function]")
    except requests.exceptions.HTTPError as _:
        logging.error("HTTP Error. [delete_namespace function]")
    except requests.exceptions.RequestException as _:
        logging.error("An error occurred. [delete_namespace function]")
    return None


def delete_component(component_name: str, app_name: str) -> requests.Response | None:
    """
    - This function should delete the component named 'component_name' in the 'app_cluster'.
    - Equivalent to "kubectl delete component <component_name>" command.
    - This function doesn't need the "app_cluster_context" argument, since the "component-crd" exists in the management cluster.
    """
    logging.info("delete_component function is called.")
    url = API_URL + f"/applications/{app_name}/components/{component_name}"
    try:
        response = requests.delete(url=url)
        return response
    except requests.exceptions.ConnectionError:
        logging.error("A connection error occurred. [delete_component function]")
    except requests.exceptions.Timeout:
        logging.error("The request timed out. [delete_component function]")
    except requests.exceptions.HTTPError as _:
        logging.error("HTTP Error. [delete_component function]")
    except requests.exceptions.RequestException as _:
        logging.error("An error occurred. [delete_component function]")
    return None


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


# ---------------------------------- Functions Needed by the 'component-crd' Operator ---------------------------------- #
def install_deployment(
    component: dict, app_name: str, update: bool = False
) -> requests.Response | None:
    """
    - This function creates a deployment in the "app_cluster".
    - Equivalent tot the commands:
        - kubectl config use-context 'app_cluster_context' # Switch the context to the app_cluster.
        - kubectl apply -f deployment.yaml, where deployment.yaml wasn't applied before.
    """
    logging.info("install_deployment function is called.")
    url = API_URL + "/deployments"
    body = {
        "component": component,
        "app_name": app_name,
        "update": update,
    }
    try:
        response = requests.post(url=url, json=body)
        return response
    except requests.exceptions.ConnectionError:
        logging.error("A connection error occurred. [install_deployment function]")
    except requests.exceptions.Timeout:
        logging.error("The request timed out. [install_deployment function]")
    except requests.exceptions.HTTPError as _:
        logging.error("HTTP Error. [install_deployment function]")
    except requests.exceptions.RequestException as _:
        logging.error("An error occurred. [install_deployment function]")
    return None


def install_service(
    component_name: str,
    app_name: str,
    ports_list: list,
    update: bool = False,
) -> requests.Response | None:
    """
    - This function creates a service in the "app_cluster".
    - Equivalent tot the commands:
        - kubectl config use-context 'app_cluster_context' # Switch the context to the app_cluster.
        - kubectl apply -f service.yaml, where service.yaml wasn't applied before.
    """
    logging.info("install_service function is called.")
    url = API_URL + "/services"
    body = {
        "component_name": component_name,
        "app_name": app_name,
        "ports_list": ports_list,
        "update": update,
    }
    try:
        response = requests.post(url=url, json=body)
        return response
    except requests.exceptions.ConnectionError:
        logging.error("A connection error occurred. [install_service function]")
    except requests.exceptions.Timeout:
        logging.error("The request timed out. [install_service function]")
    except requests.exceptions.HTTPError as _:
        logging.error("HTTP Error. [install_service function]")
    except requests.exceptions.RequestException as _:
        logging.error("An error occurred. [install_service function]")
    return None


def install_servicemonitor(
    component_name: str,
    ports_list: list,
    app_name: str,
    update: bool = False,
) -> requests.Response | None:
    """
    - This function creates a ServiceMonitor in the 'app_cluster'.
    - Equivalent to the commands:
        - kubectl config use-context 'app_cluster_context' # Switch the context to the app_cluster.
        - kubectl apply -f servicemonitor.yaml, where servicemonitor.yaml wasn't applied before.
    """
    logging.info("install_servicemonitor function is called.")
    url = API_URL + "/servicemonitors"
    body = {
        "app_name": app_name,
        "component_name": component_name,
        "ports_list": ports_list,
        "update": update,
    }
    try:
        response = requests.post(url=url, json=body)
        return response
    except requests.exceptions.ConnectionError:
        logging.error("A connection error occurred. [install_servicemonitor function]")
    except requests.exceptions.Timeout:
        logging.error("The request timed out. [install_servicemonitor function]")
    except requests.exceptions.HTTPError as _:
        logging.error("HTTP Error. [install_servicemonitor function]")
    except requests.exceptions.RequestException as _:
        logging.error("An error occurred. [install_servicemonitor function]")
    return None


def uninstall_deployment(
    component_name: str, app_name: str
) -> requests.Response | None:
    """
    This function deletes the deployment named 'component_name' in the 'app_name' namespace, in the 'app_cluster' cluster.
    Equivalent to the commands:
        - kubectl config use-context 'app_cluster_context' # Switch the context to the app_cluster.
        - kubectl delete deployment 'component_name' --namespace='app_name'.
    """
    logging.info("uninstall_deployment function is called.")
    url = API_URL + f"/deployments/{component_name}"
    body = {
        "app_name": app_name,
    }
    try:
        response = requests.delete(url=url, json=body)
        return response
    except requests.exceptions.ConnectionError:
        logging.error("A connection error occurred. [uninstall_deployment function]")
    except requests.exceptions.Timeout:
        logging.error("The request timed out. [uninstall_deployment function]")
    except requests.exceptions.HTTPError as _:
        logging.error("HTTP Error. [uninstall_deployment function]")
    except requests.exceptions.RequestException as _:
        logging.error("An error occurred. [uninstall_deployment function]")
    return None


def uninstall_service(component_name: str, app_name: str) -> requests.Response | None:
    """
    This function deletes the deployment named 'component_name' in the 'app_name' namespace, in the 'app_cluster' cluster.
    Equivalent to the commands:
        - kubectl config use-context 'app_cluster_context' # Switch the context to the app_cluster.
        - kubectl delete deployment 'component_name' --namespace='app_name'.
    """
    logging.info("uninstall_service function is called.")
    url = API_URL + f"/services/{component_name}"
    body = {"app_name": app_name}
    try:
        response = requests.delete(url=url, json=body)
        return response
    except requests.exceptions.ConnectionError:
        logging.error("A connection error occurred. [uninstall_service function]")
    except requests.exceptions.Timeout:
        logging.error("The request timed out. [uninstall_service function]")
    except requests.exceptions.HTTPError as _:
        logging.error("HTTP Error. [uninstall_service function]")
    except requests.exceptions.RequestException as _:
        logging.error("An error occurred. [uninstall_service function]")
    return None


def uninstall_servicemonitor(
    component_name: str, app_name: str
) -> requests.Response | None:
    """
    This function deletes the ServiceMonitor named 'component_name' in the 'app_name' namespace, in the 'app_cluster' cluster.
    Equivalent to the commands:
        - kubectl config use-context 'app_cluster_context' # Switch the context to the app_cluster.
        - kubectl delete servicemonitor 'component_name' --namespace='app_name'.
    """
    logging.info("uninstall_servicemonitor function is called.")
    url = API_URL + f"/servicemonitors/{component_name}"
    body = {"app_name": app_name}
    try:
        response = requests.delete(url=url, json=body)
        return response
    except requests.exceptions.ConnectionError:
        logging.error(
            "A connection error occurred. [uninstall_servicemonitor function]"
        )
    except requests.exceptions.Timeout:
        logging.error("The request timed out. [uninstall_servicemonitor function]")
    except requests.exceptions.HTTPError as _:
        logging.error("HTTP Error. [uninstall_servicemonitor function]")
    except requests.exceptions.RequestException as _:
        logging.error("An error occurred. [uninstall_servicemonitor function]")
    return None


def add_host_to_ingress(
    app_name: str, component_name: str, port: int
) -> requests.Response | None:
    """
    This function adds a host in the ingress of the application, or create an ingress if it doesn't already exist.
    Equivalent to the commands:
        - kubectl config use-context 'app_cluster_context' # Switch the context to the app_cluster.
        - get the app ingress, add this component as a host.
        - kubectl apply -f ingress.yaml --namespace='app_name'.
    """
    logging.info("add_host_to_ingress function is called.")
    url = API_URL + f"/ingress/{app_name}/hosts/{component_name}"
    body = {
        "port": port,
    }
    try:
        response = requests.post(url=url, json=body)
        return response
    except requests.exceptions.ConnectionError:
        logging.error("A connection error occurred. [add_host_to_ingress function]")
    except requests.exceptions.Timeout:
        logging.error("The request timed out. [add_host_to_ingress function]")
    except requests.exceptions.HTTPError as _:
        logging.error("HTTP Error. [add_host_to_ingress function]")
    except requests.exceptions.RequestException as _:
        logging.error("An error occurred. [add_host_to_ingress function]")
    return None


def remove_host_from_ingress(
    app_name: str, component_name: str
) -> requests.Response | None:
    """
    This function removes a host in the ingress of the application, or delete it if it doesn't already exist.
    Equivalent to the commands:
        - kubectl config use-context 'app_cluster_context' # Switch the context to the app_cluster.
        - get the app ingress, remove this component from the hosts list.
        - if app has otehr hosts:
            - kubectl apply -f ingress.yaml --namespace='app_name'.
        - else:
            - kubectl apply -f ingress.yaml --namespace='app_name'.
    """
    logging.info("remove_host_from_ingress function is called.")
    url = API_URL + f"/ingress/{app_name}/hosts/{component_name}"
    try:
        response = requests.delete(url=url)
        return response
    except requests.exceptions.ConnectionError:
        logging.error(
            "A connection error occurred. [remove_host_from_ingress function]"
        )
    except requests.exceptions.Timeout:
        logging.error("The request timed out. [remove_host_from_ingress function]")
    except requests.exceptions.HTTPError as _:
        logging.error("HTTP Error. [remove_host_from_ingress function]")
    except requests.exceptions.RequestException as _:
        logging.error("An error occurred. [remove_host_from_ingress function]")
    return None


def update_host_in_ingress(
    app_name: str, component_name: str, new_port: int
) -> requests.Response | None:
    """
    This function update the component host port in the ingress.
    Equivalent to the commands:
        - kubectl config use-context 'app_cluster_context' # Switch the context to the app_cluster.
        - get the app ingress, update the component port number.
        - kubectl apply -f ingress.yaml --namespace='app_name'.
    """
    logging.info("update_host_in_ingress function is called.")
    url = API_URL + f"/ingress/{app_name}/hosts/{component_name}"
    body = {"new_port": new_port}
    try:
        response = requests.put(url=url, json=body)
        return response
    except requests.exceptions.ConnectionError:
        logging.error("A connection error occurred. [update_host_in_ingress function]")
    except requests.exceptions.Timeout:
        logging.error("The request timed out. [update_host_in_ingress function]")
    except requests.exceptions.HTTPError as _:
        logging.error("HTTP Error. [update_host_in_ingress function]")
    except requests.exceptions.RequestException as _:
        logging.error("An error occurred. [update_host_in_ingress function]")
    return None
