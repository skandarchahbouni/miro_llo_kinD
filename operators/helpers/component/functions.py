from jinja2 import Environment, FileSystemLoader
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import yaml

# TODO: check what you have removed from the intall_deployment function (svc_list) .....
# TODO: handle exceptions 
# TODO: change this to env variable
TEMPLATE_DIR = "C:/Users/skand/Downloads/PFE/kopf/application/templates"

def install_deployment(component):    
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
    config.load_kube_config()
    api_instance = client.AppsV1Api()
    try:
        api_instance.create_namespaced_deployment(
            body=yaml_output,namespace=component["application"], pretty="true"
        )
        print("Deployment created successfully!")
    except ApiException as e:
        print(f"Exception when creating/updating Deployment: {e}")





def install_service(component):
    # Get template
    environment = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    service_template = environment.get_template("service_template.yaml")
    try:
        rendered_service = service_template.render(     name=component["name"], 
                                                        expose=component["expose"],
                                                        namespace=component["application"]
                                                )
    
        yaml_output = yaml.safe_load(rendered_service)
    except:
        # TODO: handle exception
        print("Exception: install_service function")
        return
    
    # Applying the output yaml_output  
    config.load_kube_config()
    api_instance = client.CoreV1Api()
    try:
        api_instance.create_namespaced_service(
            body=yaml_output,namespace=component["application"], pretty="true"
        )
        print(f"Service created successfully!")
    except ApiException as e:
        print(f"Exception when creating service: {e}")



def uninstall_deployment(component):
    config.load_kube_config()
    api_instance = client.AppsV1Api()
    try:
        api_instance.delete_namespaced_deployment(
            name=component["name"], namespace=component["application"]
        )
        print("Deployment uninstalled successfully")
    except ApiException as e:
        print(f"Exception when deleting deployment: {e}")



def uninstall_service(component):
    config.load_kube_config()
    api_instance = client.CoreV1Api()
    try:
        api_instance.delete_namespaced_service(
            name=component["name"], namespace=component["application"]
        )
        print("Service uninstalled successfully!")
    except ApiException as e:
        print(f"Exception when deleting service: {e}")
    



    


