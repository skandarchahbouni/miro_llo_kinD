from fastapi import APIRouter, Body
from typing import Dict
from be_infra.schemas.cluster import Cluster
from be_infra.schemas.cluster_update import ClusterUpdate
from be_infra.schemas.cluster_template import DockerClusterTemplate
from be_infra.utils import install_networking_addon, wait_for_ready_resources
from kubernetes import client,config
from kubernetes.client.rest import ApiException

clusters_router = APIRouter()

@clusters_router.post('/clusters')
def create_cluster(cluster_info: Cluster):
    cluster_template = None
    if cluster_info.infraProvider == "docker":
        cluster_template = DockerClusterTemplate(cluster_info)
    cluster_template.set_env_vars()
    cluster_template.generate_cluster_artifact_from_template()
    if cluster_template.cluster_artifact_path:
        cluster_template.apply_cluster_artifact()
    # wait for ready resources
    wait_for_ready_resources()
    # install networking add-on
    install_networking_addon(cluster_info.clusterName)


@clusters_router.delete('/clusters/{cluster_name}')
def delete_cluster(cluster_name: str):
    config.load_kube_config()
    api = client.CustomObjectsApi()
    api_response = api.delete_namespaced_custom_object(
        group="cluster.x-k8s.io",version="v1beta1",namespace="default",plural="clusters",name=cluster_name
    )
    return api_response

@clusters_router.patch('/clusters/{cluster_name}')
def update_cluster(cluster_name: str, cluster_update: ClusterUpdate):
    print(f'updated cluster name:{cluster_name}')
    print(f'updated cluster data:{cluster_update}')
    return cluster_update