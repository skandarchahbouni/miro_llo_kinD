from fastapi import APIRouter, Body
from typing import Dict
from be_infra.schemas.cluster import Cluster
from be_infra.schemas.cluster_update import ClusterUpdate

clusters_router = APIRouter()

@clusters_router.post('/clusters')
def create_cluster(cluster_info: Cluster):
    print(cluster_info)
    return cluster_info

@clusters_router.delete('/clusters/{cluster_name}')
def delete_cluster(cluster_name: str):
    print(cluster_name)
    return(cluster_name)

@clusters_router.patch('/clusters/{cluster_name}')
def update_cluster(cluster_name: str, cluster_update: ClusterUpdate):
    print(f'updated cluster name:{cluster_name}')
    print(f'updated cluster data:{cluster_update}')
    return cluster_update