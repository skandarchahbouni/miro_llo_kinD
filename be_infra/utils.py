import subprocess
import tempfile
import os
from kubernetes import client,config
from kubernetes.client.rest import ApiException
import time

def wait_for_ready_kubeconfig(clusterName):
    # cmd = "kubectl --all --all-namespaces wait --timeout 180s --for=condition=Ready cluster"
    cmd = f"kubectl wait cluster/{clusterName} --timeout 180s --for=condition=Ready"
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")

def are_nodes_ready(k8s_api):
    response = k8s_api.list_node()
    for node in response.items:
        is_node_ready = False
        for condition in node.status.conditions:
            if condition.type == "Ready" and condition.status == "True":
                is_node_ready = True
        if not is_node_ready:
            return False
    return True

def wait_for_ready_nodes(clusterName):
    # cmd = f"kubectl --all --all-namespaces wait --timeout 180s --for=condition=Ready node --kubeconfig {kubeconfig}"
    timeout_seconds= 180
    kubeconfig = get_kubeconfig(clusterName)
    config.load_kube_config(kubeconfig)
    api = client.CoreV1Api()
    start_time = time.time()
    while True:
        if are_nodes_ready(api):
            print("All nodes are ready!")
            break
        elif time.time() - start_time > timeout_seconds:
            print("Timeout reached, not all nodes are ready.")
            break
        time.sleep(5)

def are_deployments_and_daemonsets_ready(v1_apps_api, namespace):
    # Check deployments
    deployments = v1_apps_api.list_namespaced_deployment(namespace=namespace)
    for deployment in deployments.items:
        if deployment.status.replicas != deployment.status.available_replicas:
            return False
    # Check daemonsets
    daemonsets = v1_apps_api.list_namespaced_daemon_set(namespace=namespace)
    for daemonset in daemonsets.items:
        if daemonset.status.current_number_scheduled != daemonset.status.desired_number_scheduled:
            return False
    return True

def wait_for_ready_liqo(clusterName):
    timeout_seconds= 180
    kubeconfig = get_kubeconfig(clusterName)
    config.load_kube_config(kubeconfig)
    api = client.AppsV1Api()
    start_time = time.time()
    while True:
        if are_deployments_and_daemonsets_ready(api,"liqo"):
            print("All liqo resources are ready!")
            break
        elif time.time() - start_time > timeout_seconds:
            print("Timeout reached, not all liqo resources.")
            break
        time.sleep(5)

def get_kubeconfig(clusterName):
    kubeconfig_cmd = f"clusterctl get kubeconfig {clusterName}"
    output_file_path = None
    try:
        result = subprocess.run(kubeconfig_cmd, shell=True, check=True, stdout=subprocess.PIPE, text=True)
        output = result.stdout
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as output_file:
            output_file.write(output)
            output_file_path = output_file.name
    except (subprocess.CalledProcessError, IOError) as e:
        print(f"Error: {e}")
    print(f"{clusterName} : {output_file_path}")
    return output_file_path

def install_networking_addon(clusterName):
    kubeconfig = get_kubeconfig(clusterName)
    addon_artifact_path = os.environ.get("PACKAGES_PATH") + "/networking"
    cmd = f"kubectl apply -f {addon_artifact_path} --kubeconfig {kubeconfig}"
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")

def install_liqo(clusterName):
    # get cluster info
    config.load_kube_config()
    api = client.CustomObjectsApi()
    cluster = api.get_namespaced_custom_object(
        group="cluster.x-k8s.io",version="v1beta1",namespace="default",plural="clusters",name=clusterName
    )
    api_server_ip = cluster["spec"]["controlPlaneEndpoint"]["host"]
    api_server_port = cluster["spec"]["controlPlaneEndpoint"]["port"]
    api_server_url = f"https://{api_server_ip}:{api_server_port}"
    pods_cidr_block = cluster["spec"]["clusterNetwork"]["pods"]["cidrBlocks"][0]
    services_cidr_block = cluster["spec"]["clusterNetwork"]["services"]["cidrBlocks"][0]
    # get kubeconfig 
    kubeconfig = get_kubeconfig(clusterName)
    # get helm chart values.yaml
    values_file_path = None
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as values_file:
        values_file_path = values_file.name
        cmd1 = f"""
        liqoctl install --api-server-url={api_server_url} \
        --pod-cidr={pods_cidr_block} --service-cidr={services_cidr_block} --cluster-name {clusterName} \
        --service-type NodePort --only-output-values --dump-values-path {values_file_path} \
        --kubeconfig {kubeconfig}
        """
        subprocess.run(cmd1, shell=True, check=True)
    # create liqo namespace
    config.load_kube_config(config_file=kubeconfig)
    v1 = client.CoreV1Api()
    namespace = client.V1Namespace(
        metadata=client.V1ObjectMeta(
            name="liqo",
            labels={
                "kubernetes.io/metadata.name":"liqo",
                "name": "liqo",
                "pod-security.kubernetes.io/enforce":"privileged",
                "pod-security.kubernetes.io/enforce-version": "v1.28"
            }
        )
    )
    v1.create_namespace(namespace)
    # install liqo using helm chart
    cmd2 = f"""
    helm install liqo liqo/liqo --namespace liqo \
    --values {values_file_path} --kubeconfig {kubeconfig}
    """
    subprocess.run(cmd2, shell=True, check=True)