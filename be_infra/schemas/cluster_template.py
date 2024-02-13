from be_infra.schemas.cluster import Cluster
from pathlib import Path
import os
import tempfile
import subprocess

class ClusterTemplate:
    templates_root_path = Path(os.environ.get("CLUSTER_TEMPLATES_PATH"))
    env_vars = {}

    def __init__(self, cluster_info: Cluster) -> None:
        template_file_name = "cluster-template.yaml"
        if cluster_info.flavor:
            template_file_name = f"cluster-template-{cluster_info.flavor}.yaml"
        self.template_file_path = self.templates_root_path / cluster_info.infraProvider / cluster_info.bootstrapProvider / template_file_name
        self.cluster_info = cluster_info
    
    def set_env_vars(self):
        for attr,var_name in self.env_vars.items():
            os.environ[var_name] = str(getattr(self.cluster_info, attr, None))

    def generate_cluster_artifact_from_template(self):
        cluster_artifact_path = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as cluster_artifact:
                cluster_artifact_path = cluster_artifact.name
                command = f"clusterctl generate cluster {self.cluster_info.clusterName} --from {self.template_file_path} > {cluster_artifact_path}"
                subprocess.run(command, shell=True, check=True)
        except (subprocess.CalledProcessError, IOError) as e:
            print(f"Error: {e}")
        self.cluster_artifact_path = cluster_artifact_path
    
    def apply_cluster_artifact(self):
        command = f"kubectl apply -f {self.cluster_artifact_path}"
        try:
            subprocess.run(command, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")


class DockerClusterTemplate(ClusterTemplate):
    env_vars = {
        "clusterName" : "CLUSTER_NAME",
        "controlPlaneCount" : "CONTROL_PLANE_MACHINE_COUNT",
        "kubernetesVersion" : "KUBERNETES_VERSION",
        "workerMachineCount" : "WORKER_MACHINE_COUNT"
    }
    def set_env_vars(self):
        super().set_env_vars()
        os.environ["NAMESPACE"] = "default"
    
    def apply_clusterclass_artifact(self):
        clusterclass_artifact_path = self.templates_root_path / self.cluster_info.infraProvider / self.cluster_info.bootstrapProvider / "clusterclass-quick-start.yaml"
        command = f"kubectl apply -f {str(clusterclass_artifact_path)}"
        try:
            subprocess.run(command, shell=True, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Error: {e}")

    def apply_cluster_artifact(self):
        self.apply_clusterclass_artifact()
        super().apply_cluster_artifact()
