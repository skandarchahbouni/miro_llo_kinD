from kubernetes import client, config

def get_deployment_replica_info(namespace, deployment_name):
    config.load_kube_config()
    apps_v1 = client.AppsV1Api()

    try:
        # Retrieve the deployment information
        deployment = apps_v1.read_namespaced_deployment(name=deployment_name, namespace=namespace)

        # Extract and print the replica information
        replicas_info = deployment.status
        # updated_replicas_info = deployment.status.updated_replicas
        # available_replicas_info = deployment.status.available_replicas

        print(f"Available replicas: {replicas_info.available_replicas}   |  Non available replicas: {replicas_info.unavailable_replicas}")


    except Exception as e:
        print(f"Error getting deployment replica info: {e}")

if __name__ == "__main__":
    target_namespace = "default"
    target_deployment_name = "nginx-deployment"

    get_deployment_replica_info(target_namespace, target_deployment_name)

