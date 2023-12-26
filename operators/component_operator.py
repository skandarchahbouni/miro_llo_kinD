import kopf
from helpers.component.functions import install_deployment, install_service, uninstall_deployment, uninstall_service
from helpers.common import switch_config
from kubernetes import client, config
import os
from kubernetes.client.rest import ApiException


# Global variables
# TODO: make this as envirement variables
group = "charity-project.eu"  
version = "v1"  
plural = "applications"  

@kopf.on.create('Component')
def create_fn(body, **kwargs):
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
        # switch from the management cluster to the app cluster (PRODUCTION NO!!)
        app_cluster = app_instance['spec']['cluster']
        print(f"---> switching the context to '{app_cluster}' cluster")
        switch_config(app_cluster)

        # Creating the application
        component = body["spec"]
        component["name"] = component_name
        # install the deployment 
        install_deployment(component)

        # Installing services
        if "expose" in component:
            for exp in component["expose"]:
                if "is-peered" in exp and exp["is-peered"] == True:
                    install_service(component)
    except Exception as e:
        # TODO: handle exeptions 
        pass
    finally:
        # always switch back to the management cluster 
        management_cluster = os.environ.get('MANAGEMENT_CLUSTER')
        print("---> switching the context to the management cluster")
        switch_config(management_cluster)


                



@kopf.on.delete('Component')
def delete_fn(body, **kwargs):
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

    # Switch from the management cluster to the app cluster 
    print(f"---> switching the context to the '{app_cluster}' cluster")
    switch_config(app_cluster)

    try:
        # Deleting
        component = body["spec"]
        component["name"] = body["metadata"]["name"]
        # uninstall deployment 
        uninstall_deployment(component)
        # uninstall services 
        if "expose" in component:
            for exp in component["expose"]:
                if "is-peered" in exp and exp["is-peered"] == True:
                    uninstall_service(component)
    except:
        # TODO: handle exceptions 
        pass
    finally:
        # always switch back to the management cluster 
        management_cluster = os.environ.get('MANAGEMENT_CLUSTER')
        print("---> switching the context to the management cluster")
        switch_config(management_cluster)





