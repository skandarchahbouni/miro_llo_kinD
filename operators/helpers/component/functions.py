from jinja2 import Environment, FileSystemLoader
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import yaml

# TODO: check what you have removed from the intall_deployment function (svc_list) .....
# TODO: handle exceptions 
# TODO: change this to env variable
TEMPLATE_DIR = "C:/Users/skand/Downloads/PFE/kopf/application/templates"

def install_deployment(component: dict, app_cluster_context: str):    
    # Get the deployment template 
    environment = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    deployment_template = environment.get_template("deployment_template.yaml")
    try:
        # Configure fields
        rendered_deployment = deployment_template.render(   name=component["name"], 
                                                            image=component["image"],
                                                            expose=component.get("expose", ""),
                                                            env=component.get("env", ""),
                                                            namespace=component["application"],
                                                            # secretName=secretName,
                                                            clusterLabel=component.get("cluster-selector", ""),
                                                            # service_list=service_list
                                                            service_list=[]
                                                    )
        
        yaml_output = yaml.safe_load(rendered_deployment)
        
    except :
        # TODO: handle exceptions
        print("Exception: install_deployment function")
        return
        
    # Applying the output yaml file 
    try:
        config.load_kube_config(context=app_cluster_context)
        api_instance = client.AppsV1Api()
        api_instance.create_namespaced_deployment(
            body=yaml_output,namespace=component["application"], pretty="true"
        )
        print("Deployment created successfully!")
    except ApiException as _:
        print(f"Exception when creating/updating Deployment")





def install_service(component: dict, app_cluster_context: str):
    # Get template
    environment = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    service_template = environment.get_template("service_template.yaml")
    try:
        rendered_service = service_template.render(     name=component["name"], 
                                                        expose=component["expose"],
                                                        namespace=component["application"]
                                                )
    
        yaml_output = yaml.safe_load(rendered_service)
    except Exception as _:
        # TODO: handle exception
        print("Exception: install_service function")
        return
    
    # Applying the output yaml_output  
    try:
        config.load_kube_config(context=app_cluster_context)
        api_instance = client.CoreV1Api()
        api_instance.create_namespaced_service(
            body=yaml_output,namespace=component["application"], pretty="true"
        )
        print(f"Service created successfully!")
    except ApiException as _:
        print(f"Exception when creating service")



def uninstall_deployment(component: dict, app_cluster_context: str):
    try:
        config.load_kube_config(context=app_cluster_context)
        api_instance = client.AppsV1Api()
        api_instance.delete_namespaced_deployment(
            name=component["name"], namespace=component["application"]
        )
        print("Deployment uninstalled successfully")
    except ApiException as _:
        print(f"Exception when deleting deployment")



def uninstall_service(component: dict, app_cluster_context: str):
    try:
        config.load_kube_config(context=app_cluster_context)
        api_instance = client.CoreV1Api()
        api_instance.delete_namespaced_service(
            name=component["name"], namespace=component["application"]
        )
        print("Service uninstalled successfully!")
    except ApiException as _:
        print(f"Exception when deleting service")


def install_service_monitor(namespace: str, component_name: str, cluster_port: int, app_cluster_context: str):
      # Get the ServiceMonitor template 
    environment = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    service_monitor_template = environment.get_template("ServiceMonitor_template.yaml")
    try:
        rendered_service_monitor = service_monitor_template.render(     
                                                        namespace=namespace,
                                                        component_name=component_name, 
                                                        cluster_port=cluster_port
                                                )
    
        yaml_output = yaml.safe_load(rendered_service_monitor)

        # Apply the CRD using the Kubernetes Python client library
        config.load_kube_config(context=app_cluster_context)
        api_instance = client.CustomObjectsApi()

        # creating the ServiceMonitor 
        api_version = yaml_output['apiVersion']

        # Apply the CRD
        api_instance.create_namespaced_custom_object(
            group=api_version.split('/')[0],
            version=api_version.split('/')[1],
            namespace=namespace,
            plural="servicemonitors",  # Assuming plural form, adjust if needed
            body=yaml_output,
        )
        print("ServiceMonitor Object created successfully!")
    except Exception as _:
        print(f"Exception install_service_monitor function.")
