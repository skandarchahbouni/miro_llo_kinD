import kopf
from helpers.component.functions import install_deployment, install_service, uninstall_deployment, uninstall_service, install_service_monitor
from kubernetes import client, config
from kubernetes.client.rest import ApiException


# Global variables
# TODO: make this as envirement variables
group = "charity-project.eu"  
version = "v1"  
plural = "applications"  

@kopf.on.create('Component')
def create_fn(body, **_):
    # Get the application instance 
    config.load_kube_config()
    custom_objects_api = client.CustomObjectsApi()
    application = body["spec"]["application"]

    try:
    # Get the Custom Resource
        app_instance = custom_objects_api.get_namespaced_custom_object(
            group=group,
            version=version,
            namespace="default",
            plural=plural,
            name=application,
        )

    except ApiException as e:
        if (e.status == 404):
            print("The application doesn't exist. Please make sure to create the application before starting creating its components.")
        else:
            print('Something went wrong!')
        return  
    
    # THIS FIELD IS REQUIRED, the if below doesn't make sense (validation)
    # check whether the component is registered in the application, if not return an error 
    if 'components' not in app_instance['spec']:
        print("Error! Application doesn't contain the current component, please make sure to add the component to the application first.")
        return 
    
    components = app_instance['spec']['components']


    if len(components) == 0:
        print("Error! Application doesn't contain the current component, please make sure to add the component to the application first.")
        return 
    components_names = [comp["name"] for comp in components]
    component_name = body["metadata"]["name"]
    if (component_name not in components_names):
        print("Error! Application doesn't contain the current component, please make sure to add the component to the application first.")
        return 
    
    try:
        app_cluster = app_instance['spec']['cluster']
        # Creating the application
        component = body["spec"]
        component["name"] = component_name
        # install the deployment 
        install_deployment(component=component, app_cluster_context="kind-"+app_cluster)

        # Installing services
        if "expose" in component:
            # TODO: review this !!!!!!!! if len(exp)==2, install service should not be inside the for loop !!! 
            # logique 3yana bzaf hnaaa 
            for exp in component["expose"]: 
                if "is-peered" in exp and exp["is-peered"] == True:
                    install_service(component=component, app_cluster_context="kind-"+app_cluster)
                if "is-exposing-metrics" in exp and exp["is-exposing-metrics"] == True:
                    install_service_monitor(namespace=component['application'] ,component_name=component["name"], cluster_port=exp["clusterPort"], app_cluster_context="kind-"+app_cluster)
    except Exception as _:
        # TODO: handle exeptions 
        pass


                

@kopf.on.delete('Component')
def delete_fn(body, **_):
    # Get the application instance 
    config.load_kube_config()
    custom_objects_api = client.CustomObjectsApi()
    application = body["spec"]["application"]
    try:
        # Get the Custom Resource
        app_instance = custom_objects_api.get_namespaced_custom_object(
            group=group,
            version=version,
            namespace="default",
            plural=plural,
            name=application,
        )
    except ApiException as e:
        print('Something went wrong!')
        return
    
    app_cluster = app_instance["spec"]["cluster"]

    # No need to check that the component does exist in the application cluster or not.
    # if it exists : the app status becomes pending 
    # if it doesn't exist, it's impossible (this component shouldn't exist)
    # can update the app status from here ?

    try:
        # Deleting
        component = body["spec"]
        component["name"] = body["metadata"]["name"]
        # uninstall deployment 
        uninstall_deployment(component=component, app_cluster_context="kind-"+app_cluster)
        # uninstall services 
        if "expose" in component:
            for exp in component["expose"]:
                if "is-peered" in exp and exp["is-peered"] == True:
                    uninstall_service(component=component, app_cluster_context="kind-"+app_cluster)
    except:
        # TODO: handle exceptions 
        pass








