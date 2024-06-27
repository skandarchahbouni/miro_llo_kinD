import docker
import pprint
import re
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from kubernetes.config.config_exception import ConfigException

def subscribe_cluster(cluster_name):
    config.load_kube_config()
    container_name=cluster_name+'-control-plane'
    ip=get_container_ip(container_name)
    api_instance = client.CoreV1Api()
    api_response = api_instance.read_namespaced_config_map('thanos-cm','monitoring')
    print("ConfigMap data:")
    api_response.data['sdfile.yaml']=api_response.data['sdfile.yaml']+ '  - ' + ip + ':10901\n'
    print(api_response.data['sdfile.yaml'])
    api_response = api_instance.patch_namespaced_config_map(
        name='thanos-cm',
        namespace='monitoring',
        body=api_response
    )
    
def unsubscribe_cluster(cluster_name):
    config.load_kube_config()
    container_name = cluster_name + '-control-plane'
    ip = get_container_ip(container_name)
    api_instance = client.CoreV1Api()
    api_response = api_instance.read_namespaced_config_map('thanos-cm', 'monitoring')
    
    print("ConfigMap data before unsubscribing:")
    print(api_response.data['sdfile.yaml'])
    
    # Construct the entry to remove
    entry_to_remove = '  - ' + ip + ':10901\n'
    
    # Remove the entry using regex
    api_response.data['sdfile.yaml'] = re.sub(re.escape(entry_to_remove), '', api_response.data['sdfile.yaml'])
    
    print("ConfigMap data after unsubscribing:")
    print(api_response.data['sdfile.yaml'])
    
    api_instance.patch_namespaced_config_map(
        name='thanos-cm',
        namespace='monitoring',
        body=api_response
    )


def get_container_ip(container_name):
    client = docker.from_env()
    
    try:
        container = client.containers.get(container_name)
        container_info = container.attrs
        
        # The IP address is usually found under the 'Networks' section
        ip_address = container_info['NetworkSettings']['Networks']['kind']['IPAddress']
        # print(container_info['NetworkSettings']['Networks']['kind']['IPAddress'])
        # print(ip_address)
        return ip_address
    except docker.errors.NotFound:
        return f"Container '{container_name}' not found."
    except Exception as e:
        return f"An error occurred: {e}"