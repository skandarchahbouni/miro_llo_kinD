from kubernetes import client, config
from kubernetes.client.rest import ApiException
from fastapi import HTTPException

# Global variables (TODO: env variables)
group = "charity-project.eu"  
version = "v1"  
plural = "applications"  

# FUNCTIONS 
def get_app_instance(application_name: str) -> dict|None:
    config.load_kube_config()
    custom_objects_api = client.CustomObjectsApi()
    try:
    # Get the Custom Resource
        app_instance = custom_objects_api.get_namespaced_custom_object(
            group=group,
            version=version,
            namespace="default",
            plural=plural,
            name=application_name,
        )
        return app_instance
    except ApiException as e:
        if e.status == 404:
            # Resource not found, raise a 404 HTTPException
            raise HTTPException(status_code=404, detail="Resource not found")