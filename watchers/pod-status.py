from kubernetes import client, config

def get_pod_conditions(namespace, pod_name):
    config.load_kube_config()
    v1 = client.CoreV1Api()

    try:
        # Retrieve the pod information
        pod_info = v1.read_namespaced_pod(name=pod_name, namespace=namespace)

        # Extract and print the pod conditions
        pod_conditions = pod_info.status.conditions
        for condition in pod_conditions:
            print(f"Condition Type: {condition.type}, Status: {condition.status}, Reason: {condition.reason}")

    except Exception as e:
        print(f"Error getting pod conditions: {e}")

if __name__ == "__main__":
    target_namespace = "default"
    target_pod_name = "failed-pod"

    get_pod_conditions(target_namespace, target_pod_name)
