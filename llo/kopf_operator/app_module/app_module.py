import logging
import requests
# from kopf_operator.app_module.exceptions.not_found_exception import NotFoundException

# API_URL = "http://orch-backend.orchestration.charity-project.eu/v1"
API_URL = "http://127.0.0.1:8000/api/v1"

# ******************************************************************************* #
# Common Functions (Used by both 'application-crd' and 'component-crd' operators)
# ******************************************************************************* #
def get_context(cluster: str) -> requests.Response|None:
    """
        - This function should return the context of a k8s cluster based on the cluster name passed as an argument.
    """
    logging.info("get_context function is called.")
    url = API_URL + f"/clusters/{cluster}/context"
    try:
        response = requests.get(url=url)
        return response
        # if response.status_code == 404:
        #     logging.info(f"Endpoint returned a 404 status code.")
        #     return None
        # return response.json().get("context")
    except requests.exceptions.ConnectionError:
        logging.error("A connection error occurred. [get_context function]")
    except requests.exceptions.Timeout:
        logging.error("The request timed out. [get_context function]")
    except requests.exceptions.HTTPError as _:
        logging.error("HTTP Error. [get_context function]")
    except requests.exceptions.RequestException as _:
        logging.error("An error occurred. [get_context function]")

def get_app_instance(application_name: str) -> requests.Response | None:
    """
        - This function returns the application instance named "application_name".
        - Euivalent to run the command: <<kubectl get apps "application_name">> in the management cluster.
    """
    logging.info("get_app_instance function is called.")
    url = API_URL + f"/applications/{application_name}"
    try:
        response = requests.get(url=url)
        return response
    except requests.exceptions.ConnectionError:
        logging.error("A connection error occurred. [get_app_instance function]")
    except requests.exceptions.Timeout:
        logging.error("The request timed out. [get_app_instance function]")
    except requests.exceptions.HTTPError as _:
        logging.error("HTTP Error. [get_app_instance function]")
    except requests.exceptions.RequestException as _:
        logging.error("An error occurred. [get_app_instance function]")


# ******************************************************************************* #
# Functions Needed by the 'application-crd' Operator
# ******************************************************************************* #
def create_namespace(namespace_name: str, app_cluster_context: str):
    """
        - This function should create a namespace named 'namespace_name' in the 'app_cluster'.
        - Equivalent tot the commands:
            - kubectl config use-context 'app_cluster_context' # Switch the context to the app_cluster.
            - kubectl create ns "namespace_name"
    """
    logging.info("create_namespace function is called.")
    url = API_URL + "/namespaces"
    body = {"namespace_name": namespace_name, "app_cluster_context": app_cluster_context}
    try:
        requests.post(url=url, json=body)
    except requests.exceptions.ConnectionError:
        logging.error("A connection error occurred. [create_namespace function]")
    except requests.exceptions.Timeout:
        logging.error("The request timed out. [create_namespace function]")
    except requests.exceptions.HTTPError as _:
        logging.error("HTTP Error. [create_namespace function]")
    except requests.exceptions.RequestException as _:
        logging.error("An error occurred. [create_namespace function]")


def delete_namespace(namespace_name: str, app_cluster_context: str):
    """
        - This function should delete the namespace named 'namespace_name' in the 'app_cluster'.
        - Equivalent tot the commands:
            - kubectl config use-context 'app_cluster_context' # Switch the context to the app_cluster.
            - kubectl delete ns "namespace_name"
    """
    logging.info("delete_namespace function is called.")
    url = API_URL + f"/namespaces/{namespace_name}"
    body = {"app_cluster_context": app_cluster_context}
    try:
        requests.delete(url=url, json=body)
    except requests.exceptions.ConnectionError:
        logging.error("A connection error occurred. [delete_namespace function]")
    except requests.exceptions.Timeout:
        logging.error("The request timed out. [delete_namespace function]")
    except requests.exceptions.HTTPError as _:
        logging.error("HTTP Error. [delete_namespace function]")
    except requests.exceptions.RequestException as _:
        logging.error("An error occurred. [delete_namespace function]")


def delete_component(component_name: str, app_name: str):
    """
        - This function should delete the component named 'component_name' in the 'app_cluster'.
        - Equivalent to "kubectl delete component <component_name>" command.
        - This function doesn't need the "app_cluster_context" argument, since the "component-crd" exists in the management cluster.
    """
    logging.info("delete_component function is called.")
    url = API_URL + f"/applications/{app_name}/components/{component_name}"
    try:
        requests.delete(url=url)
    except requests.exceptions.ConnectionError:
        logging.error("A connection error occurred. [delete_component function]")
    except requests.exceptions.Timeout:
        logging.error("The request timed out. [delete_component function]")
    except requests.exceptions.HTTPError as _:
        logging.error("HTTP Error. [delete_component function]")
    except requests.exceptions.RequestException as _:
        logging.error("An error occurred. [delete_component function]")


def get_changes(old: dict | None, new: dict | None) -> tuple[list, list, list]:
    """
        This function compares between the old and new dict and returns the changes detected, which could be:
            - New components added to the application.
            - Some components Deleted from the application.
            - Some components changed the cluster (migration).  
    """
    logging.info("get_changes function is called.")
     # All the components were added
    if (old is None):
        return new, [], []
  
    # All the components were removed   
    if (new is None):
        return [], old, []

    added_components = [obj for obj in new if obj not in old]
    removed_components = [obj for obj in old if obj not in new]
    
    old_dict = {obj['name']: obj['cluster'] for obj in old}
    new_dict = {obj['name']: obj['cluster'] for obj in new}
    
    migrated_components = [
        {'name': name, 'old_cluster': old_dict[name], 'new_cluster': new_dict[name]}
        for name in set(old_dict) & set(new_dict)
        if old_dict[name] != new_dict[name]
    ]

    return added_components, removed_components, migrated_components

# ******************************************************************************* #
# Functions Needed by the 'component-crd' Operator
# ******************************************************************************* #
def install_deployment(component: dict, app_cluster_context: str):
    """
        - This function creates a deployment in the "app_cluster". 
        - Equivalent tot the commands:
            - kubectl config use-context 'app_cluster_context' # Switch the context to the app_cluster.
            - kubectl apply -f deployment.yaml, where deployment.yaml wasn't applied before.
    """
    logging.info("install_deployment function is called.")
    url = API_URL + "/deployments"
    body = {"component" : component, "app_cluster_context": app_cluster_context}
    try:
        requests.post(url=url, json=body)
    except requests.exceptions.ConnectionError:
        logging.error("A connection error occurred. [install_deployment function]")
    except requests.exceptions.Timeout:
        logging.error("The request timed out. [install_deployment function]")
    except requests.exceptions.HTTPError as _:
        logging.error("HTTP Error. [install_deployment function]")
    except requests.exceptions.RequestException as _:
        logging.error("An error occurred. [install_deployment function]")

def install_service(component_name: str, ports_list: list, app_cluster_context: str):
    """
        - This function creates a service in the "app_cluster". 
        - Equivalent tot the commands:
            - kubectl config use-context 'app_cluster_context' # Switch the context to the app_cluster.
            - kubectl apply -f service.yaml, where service.yaml wasn't applied before.
    """
    logging.info("install_service function is called.")
    url = API_URL + "/services"
    body = {"component_name" : component_name, "ports_list": ports_list, "app_cluster_context": app_cluster_context}
    try:
        requests.post(url=url, json=body)
    except requests.exceptions.ConnectionError:
        logging.error("A connection error occurred. [install_service function]")
    except requests.exceptions.Timeout:
        logging.error("The request timed out. [install_service function]")
    except requests.exceptions.HTTPError as _:
        logging.error("HTTP Error. [install_service function]")
    except requests.exceptions.RequestException as _:
        logging.error("An error occurred. [install_service function]")

def install_servicemonitor(component_name: str, ports_list: list, app_cluster_context: str):
    """
        - This function creates a ServiceMonitor in the 'app_cluster'.
        - Equivalent to the commands:
            - kubectl config use-context 'app_cluster_context' # Switch the context to the app_cluster.
            - kubectl apply -f servicemonitor.yaml, where servicemonitor.yaml wasn't applied before.
    """
    logging.info("install_servicemonitor function is called.")
    url = API_URL + "/servicemonitors"
    body = {"component_name" : component_name, "ports_list": ports_list, "app_cluster_context": app_cluster_context}
    try:
        requests.post(url=url, json=body)
    except requests.exceptions.ConnectionError:
        logging.error("A connection error occurred. [install_servicemonitor function]")
    except requests.exceptions.Timeout:
        logging.error("The request timed out. [install_servicemonitor function]")
    except requests.exceptions.HTTPError as _:
        logging.error("HTTP Error. [install_servicemonitor function]")
    except requests.exceptions.RequestException as _:
        logging.error("An error occurred. [install_servicemonitor function]")


def uninstall_deployment(component_name: str, app_name: str, app_cluster_context: str):
    """
    This function deletes the deployment named 'component_name' in the 'app_name' namespace, in the 'app_cluster' cluster.
    Equivalent to the commands:
        - kubectl config use-context 'app_cluster_context' # Switch the context to the app_cluster.
        - kubectl delete deployment 'component_name' --namespace='app_name'.
    """
    logging.info("uninstall_deployment function is called.")
    url = API_URL + f"/deployments/{component_name}"
    body = {"namespace": app_name, "app_cluster_context": app_cluster_context}
    try:
        requests.delete(url=url, json=body)
    except requests.exceptions.ConnectionError:
        logging.error("A connection error occurred. [uninstall_deployment function]")
    except requests.exceptions.Timeout:
        logging.error("The request timed out. [uninstall_deployment function]")
    except requests.exceptions.HTTPError as _:
        logging.error("HTTP Error. [uninstall_deployment function]")
    except requests.exceptions.RequestException as _:
        logging.error("An error occurred. [uninstall_deployment function]")



def uninstall_service(component_name: str, app_name: str, app_cluster_context: str):
    """
    This function deletes the deployment named 'component_name' in the 'app_name' namespace, in the 'app_cluster' cluster.
    Equivalent to the commands:
        - kubectl config use-context 'app_cluster_context' # Switch the context to the app_cluster.
        - kubectl delete deployment 'component_name' --namespace='app_name'.
    """
    logging.info("uninstall_service function is called.")
    url = API_URL + f"/deployments/{component_name}"
    body = {"namespace": app_name, "app_cluster_context": app_cluster_context}
    try:
        requests.delete(url=url, json=body)
    except requests.exceptions.ConnectionError:
        logging.error("A connection error occurred. [uninstall_service function]")
    except requests.exceptions.Timeout:
        logging.error("The request timed out. [uninstall_service function]")
    except requests.exceptions.HTTPError as _:
        logging.error("HTTP Error. [uninstall_service function]")
    except requests.exceptions.RequestException as _:
        logging.error("An error occurred. [uninstall_service function]")


def uninstall_servicemonitor(component_name: str, app_name: str, app_cluster_context: str):
    """
    This function deletes the ServiceMonitor named 'component_name' in the 'app_name' namespace, in the 'app_cluster' cluster.
    Equivalent to the commands:
        - kubectl config use-context 'app_cluster_context' # Switch the context to the app_cluster.
        - kubectl delete servicemonitor 'component_name' --namespace='app_name'.
    """
    logging.info("uninstall_servicemonitor function is called.")
    url = API_URL + f"/servicemonitors/{component_name}"
    body = {"namespace": app_name, "app_cluster_context": app_cluster_context}
    try:
        requests.delete(url=url, json=body)
    except requests.exceptions.ConnectionError:
        logging.error("A connection error occurred. [uninstall_servicemonitor function]")
    except requests.exceptions.Timeout:
        logging.error("The request timed out. [uninstall_servicemonitor function]")
    except requests.exceptions.HTTPError as _:
        logging.error("HTTP Error. [uninstall_servicemonitor function]")
    except requests.exceptions.RequestException as _:
        logging.error("An error occurred. [uninstall_servicemonitor function]")

