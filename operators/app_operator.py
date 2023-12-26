import kopf
from helpers.common import switch_config
from helpers.application.functions import create_namespace, delete_namespace
import os


# Global variables 
group = "charity-project.eu"  
version = "v1"  
plural = "applications"  

@kopf.on.create('Application')
def create_fn(body, **_):
    app_cluster = body['spec']['cluster']
    app_name = body['spec']['name']
    # Access the app cluster 
    try:
        print(f"---> switching the context to the {app_cluster} cluster")
        switch_config(app_cluster)
        # Creating the namespace in this cluster 
        create_namespace(namespace_name=app_name)
        # linking between the app_cluster and the components clusters 
        components_list = body["spec"]["components"]
        # Unique list of components clusters 
        components_clusters = list(set([comp["cluster"] for comp in components_list]))
        for cluster in components_clusters:
            if cluster != app_cluster:
                # Link the two clusters using liqo, + namespace offloading if this isn't already done 
                # TODO: ......;
                pass  
    except Exception as e:
        # TODO: handle exceptions 
        pass
    finally:
        # always switch back to the management cluster 
        management_cluster = os.environ.get('MANAGEMENT_CLUSTER')
        print("---> switching the context to the management cluster")
        switch_config(management_cluster)
          



@kopf.on.delete('Application')
def delete_fn(body, **_):
    # TODO: unoffload namespace + unpeer if this will not break another application 
    #  Delete the namespace : this will remove all the components of the application TODO: confirm about that 
    app_name = body["spec"]["name"]
    app_cluster = body["spec"]["cluster"]
    try:
        print(f"---> switching the context to the {app_cluster} cluster")
        switch_config(app_cluster)
        delete_namespace(namespace_name=app_name)
    except Exception as e:
        # TODO: handle exceptions
        pass
    finally:
        # always switch back to the management cluster 
        management_cluster = os.environ.get('MANAGEMENT_CLUSTER')
        print("---> switching the context to the management cluster")
        switch_config(management_cluster)
    

# **** TO BE IMPLEMENTED ****#
@kopf.on.field('Application', field='spec.components')
def handle_update_components_field(old, new, diff, **_):

    print('************* OLD *************')
    print(old)
    print('************* New *************')
    print(new)
    print('************* Diff *************')
    print(diff)
    # TODO: check migration  





# test

