# from kubernetes import client, config, watch

# def watch_namespace_events(namespace):
#     config.load_kube_config()
#     v1 = client.CoreV1Api()

#     w = watch.Watch()
#     for event in w.stream(v1.list_event_for_all_namespaces):
#         event_namespace = event['object'].metadata.namespace
#         event_name = event['object'].metadata.name
#         event_type = event['type']
#         event_reason = event['object'].reason
#         event_message = event['object'].message

#         if event_namespace == namespace:
#             print(f"Event Type: {event_type}, Reason: {event_reason}")

# if __name__ == "__main__":
#     # Specify the namespace you want to watch
#     target_namespace = "default"

#     watch_namespace_events(target_namespace)









from kubernetes import client, config, watch

def watch_pods_across_namespaces():
    config.load_kube_config()
    v1 = client.CoreV1Api()

    w = watch.Watch()
    for event in w.stream(v1.list_pod_for_all_namespaces):
        pod_name = event['object'].metadata.name
        namespace = event['object'].metadata.namespace
        print(f"Event Type: {event['type']}, Pod: {pod_name}, Namespace: {namespace}")

        # Extract and print the pod conditions
        pod_conditions = event['object'].status.conditions
        try:
            for condition in pod_conditions:
                print(f"Condition Type: {condition.type}, Status: {condition.status}")
        except Exception as _:
            pass

if __name__ == "__main__":
    watch_pods_across_namespaces()

