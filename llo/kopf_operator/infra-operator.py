import kopf
import logging
from kubernetes import client
from kubernetes.client.rest import ApiException
from infra_module import infra_module
import re

#-----------------------CONSTS-----------------------

API_GROUP = "miro.onesource.pt"
SUPPORTED_PROVIDERS_CM_NAME = "supported-providers"

#-----------------------STARTUP CONFIG-----------------------

@kopf.on.startup()
async def configure(
    settings: kopf.OperatorSettings, logger: kopf.Logger, memo: kopf.Memo, **_
):
    settings.admission.server = kopf.WebhookAutoTunnel()
    settings.admission.managed = 'auto.kopf.dev'

#-----------------------WEBHOOKS-----------------------
    
@kopf.on.validate("customcluster",operation="CREATE")
def check_clustername_uniqueness(spec, **_):
    cluster_name = spec["name"]
    clusters = client.CustomObjectsApi().list_cluster_custom_object(
        group=API_GROUP, version="v1", plural="customclusters"
    )
    cluster = [
        item
        for item in clusters["items"]
        if item["spec"]["name"] == cluster_name
    ]
    if len(cluster) != 0:
        raise kopf.AdmissionError(
            f"{cluster_name} cluster already exists"
        )

@kopf.on.validate("customcluster")
def check_infra_provider_support_and_properties(spec, **_):
    # get supported-providers configMap
    infra_provider = spec["infra-provider"]
    try:
        supported_providers_cm = client.CoreV1Api().read_namespaced_config_map(
            name=SUPPORTED_PROVIDERS_CM_NAME, namespace="default"
        )
    except ApiException:
        raise kopf.AdmissionError(
            f"configmap/{SUPPORTED_PROVIDERS_CM_NAME} does not exist."
        )

    # check infra-provider support
    infra_providers = supported_providers_cm.data["infra-providers"].split(",")
    if infra_provider not in infra_providers:
        raise kopf.AdmissionError(
            f"{infra_provider} is not supported as an infrastructure provider."
        )

    # get infra-provider-properties configMap
    INFRA_PROVIDER_PROPERTIES_CM_NAME = f"{infra_provider}-properties"
    try:
        infra_provider_properties_cm = client.CoreV1Api().read_namespaced_config_map(
            name=INFRA_PROVIDER_PROPERTIES_CM_NAME, namespace="default"
        )
    except ApiException:
        raise kopf.AdmissionError(
            f"configmap/{INFRA_PROVIDER_PROPERTIES_CM_NAME} does not exist."
        )

    # check infra-provider properties
    infra_provider_properties = [
        "flavor",
        "control-plane-flavor",
        "worker-machine-flavor",
        "image",
    ]
    for property in infra_provider_properties:
        if property in spec:
            flavor = spec[property]
            if flavor not in infra_provider_properties_cm.data[property].split(","):
                raise kopf.AdmissionError(
                    f"{flavor} is not a valid {property} for {infra_provider}."
                )

@kopf.on.validate("customcluster")
def check_bootstrap_provider_support(spec, **_):
    bootstrap_provider = spec["bootstrap-provider"]
    try:
        supported_providers_cm = client.CoreV1Api().read_namespaced_config_map(
            name=SUPPORTED_PROVIDERS_CM_NAME, namespace="default"
        )
    except ApiException:
        raise kopf.AdmissionError(
            f"configmap/{SUPPORTED_PROVIDERS_CM_NAME} does not exist."
        )
    if bootstrap_provider not in supported_providers_cm.data[
        "bootstrap-providers"
    ].split(","):
        raise kopf.AdmissionError(
            f"{bootstrap_provider} is not supported as a bootstrap provider."
        )

@kopf.on.validate('customcluster')
def check_infra_provider_config(spec, **_):
    config_name = spec["configMapRef"]["name"]
    try:
        config_map = client.CoreV1Api().read_namespaced_config_map(name=config_name,namespace="default")
    except ApiException:
        raise kopf.AdmissionError(f"configmap/{config_name} does not exist.")

@kopf.on.validate('customcluster')
def check_kube_version(spec, **_):
    kube_version = spec["kubernetes-version"]
    kubernetes_version_pattern = re.compile(
        r'^v\d+\.\d+\.\d+([+-].*)?$'
    )
    if not bool(kubernetes_version_pattern.match(kube_version)):
        raise kopf.AdmissionError(f"{kube_version} is not a valid kubernetes version.")
 
@kopf.on.validate('link')
def check_clusters(spec, **_):
    local_cluster = spec['local-cluster']
    remote_cluster = spec['remote-cluster']
    clusters = client.CustomObjectsApi().list_cluster_custom_object(group=API_GROUP, version="v1", plural="customclusters")
    peered_clusters = [item for item in clusters["items"] if item['spec']['name'] == local_cluster or item['spec']['name'] == remote_cluster]
    if len(peered_clusters) == 0:
        raise kopf.AdmissionError(f"Both {local_cluster} and {remote_cluster} don't exist.")
    elif len(peered_clusters) == 1:
        if peered_clusters[0]['spec']['name'] == local_cluster:
            raise kopf.AdmissionError(f"{remote_cluster} does not exist.")
        else:
            raise kopf.AdmissionError(f"{local_cluster} does not exist.")

#-----------------------CUSTOM CLUSTER OPERATIONS-----------------------

def getClusterData(spec):
    # required fields
    clusterData = {
        "infraProvider": spec["infra-provider"],
        "infraProviderConfig": spec["configMapRef"]["name"],
        "clusterName": spec["name"],
        "kubernetesVersion": spec["kubernetes-version"],
        "workerMachineCount": spec["worker-machine-count"],
    }
    # optional fields
    if "bootstrap-provider" in spec:
        clusterData["bootstrapProvider"] = spec["bootstrap-provider"]
    if "flavor" in spec:
        clusterData["flavor"] = spec["flavor"]
    if "control-plane-count" in spec:
        clusterData["controlPlaneCount"] = spec["control-plane-count"]
    if "control-plane-flavor" in spec:
        clusterData["controlPlaneFlavor"] = spec["control-plane-flavor"]
    if "worker-machine-flavor" in spec:
        clusterData["workerMachineFlavor"] = spec["worker-machine-flavor"]
    if "image" in spec:
        clusterData["image"] = spec["image"]
    return clusterData

@kopf.on.create("customcluster")
def customcluster_create(body, **kwargs):
    clusterData = getClusterData(body["spec"])
    logging.info(f"Cluster spec: {clusterData}")
    infra_module.create_cluster(clusterData)
    logging.info(f"{clusterData['clusterName']} created!")

@kopf.on.update("customcluster") 
def customcluster_update(diff, body, **_kwargs):
    # diff structure:
    # (
    #     ('change', ('spec', 'worker-machine-count'), 1, 2),
    #     ('change', ('spec', 'control-plane-count'), 1, 2)
    # )
    cluster_name = body['spec']['name']
    cluster_update = {}
    for d in diff:
        if d[0] == 'change' and d[1] == ('spec', 'worker-machine-count'):
            cluster_update['workerMachineCount'] = d[3]
        if d[0] == 'change' and d[1] == ('spec', 'control-plane-count'):
            cluster_update['controlPlaneCount'] = d[3]
    if cluster_update:
        logging.info(f"{cluster_name} update: {cluster_update}")
        infra_module.update_cluster(cluster_name, cluster_update)
        logging.info(f"{cluster_name} updated!")

@kopf.on.delete("customcluster")
def customcluster_delete(body, **kwargs):
    cluster_name = body["spec"]["name"]
    infra_module.delete_cluster(cluster_name)
    logging.info(f"{cluster_name} deleted!")

#-----------------------LINK OPERATIONS-----------------------

@kopf.on.create("link")
def link_create(body, **kwargs):
    linkData = {
        "localCluster": body["spec"]["local-cluster"],
        "remoteCluster": body["spec"]["remote-cluster"] 
    }
    logging.info(f"Link spec: {linkData}")
    infra_module.link_clusters(linkData)
    logging.info(f"Link between {linkData['localCluster']} and {linkData['remoteCluster']} created!")

@kopf.on.delete("link")
def link_delete(body, **kwargs):
    linkData = {
        "localCluster": body["spec"]["local-cluster"],
        "remoteCluster": body["spec"]["remote-cluster"] 
    }
    logging.info(f"Link spec: {linkData}")
    infra_module.unlink_clusters(linkData)
    logging.info(f"Link between {linkData['localCluster']} and {linkData['remoteCluster']} deleted!")

#-----------------------STATUS PROPAGATION-----------------------
    
# watch event happening on cluster resource in order to propagate their status to customcluster
@kopf.on.event('cluster')
def get_customcluster_status_from_cluster(event, **kwargs):
    # get cluster name
    name = event["object"]["metadata"]["name"]
    # get phase, infrastructureReady and controlPlaneReady from cluster (ClusterAPI CR) status
    status = {}
    if "phase" in event["object"]["status"]:
        status["phase"] = event["object"]["status"]["phase"]
    if "infrastructureReady" in event["object"]["status"]:
        status["infrastructure-ready"] = event["object"]["status"]["infrastructureReady"]
    if "controlPlaneReady" in event["object"]["status"]:
        status["control-plane-ready"] = event["object"]["status"]["controlPlaneReady"]
    # add phase, infrastructureReady and controlPlaneReady status to customcluster
    try:
        client.CustomObjectsApi().patch_namespaced_custom_object_status(group=API_GROUP,version="v1",namespace="default",plural="customclusters",name=name,body={"status": status})
    except ApiException:
        logging.error(f"{name} customcluster does not exists or already deleted!")
