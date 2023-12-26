from kubernetes import client, config

def create_namespace(namespace_name: str):
    config.load_kube_config()
    api_instance = client.CoreV1Api()
    new_namespace = client.V1Namespace(metadata=client.V1ObjectMeta(name=namespace_name))
    try:
        api_response = api_instance.create_namespace(body=new_namespace)
        print(f"Namespace {api_response.metadata.name} created successfully!.")
    except Exception as e:
        print(f"Error creating namespace: {e}")

def delete_namespace(namespace_name: str):
    config.load_kube_config()
    api_instance = client.CoreV1Api()
    try:
        api_instance.delete_namespace(name=namespace_name, body=client.V1DeleteOptions())
        print(f"Namespace {namespace_name} deleted successfully!")
    except Exception as e:
        print(f"Error deleting namespace: {e}")