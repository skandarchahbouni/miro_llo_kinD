from fastapi import APIRouter
from be_infra.schemas.link import Link
from be_infra.utils import get_kubeconfig
import subprocess
import tempfile

links_router = APIRouter()

@links_router.post('/links')
def create_link(link: Link):
    localKubeconfig = get_kubeconfig(link.localCluster)
    remoteKubeconfig = get_kubeconfig(link.remoteCluster)
    try:
        with tempfile.NamedTemporaryFile(mode='w') as local_kubeconfig_file, tempfile.NamedTemporaryFile(mode='w') as remote_kubeconfig_file:
            local_kubeconfig_file.write(localKubeconfig)
            local_kubeconfig_file.seek(0)
            remote_kubeconfig_file.write(remoteKubeconfig)
            remote_kubeconfig_file.seek(0)
            cmd= [
                "liqoctl", "peer", "in-band", "--kubeconfig", local_kubeconfig_file.name,
                "--remote-kubeconfig", remote_kubeconfig_file.name
            ]
            subprocess.run(cmd, check=True)
    except (subprocess.CalledProcessError, IOError) as e:
        print(f"Error: {e}")

@links_router.delete('/links')
def delete_link(link: Link):
    localKubeconfig = get_kubeconfig(link.localCluster)
    remoteKubeconfig = get_kubeconfig(link.remoteCluster)
    try:
        with tempfile.NamedTemporaryFile(mode='w') as local_kubeconfig_file, tempfile.NamedTemporaryFile(mode='w') as remote_kubeconfig_file:
            local_kubeconfig_file.write(localKubeconfig)
            local_kubeconfig_file.seek(0)
            remote_kubeconfig_file.write(remoteKubeconfig)
            remote_kubeconfig_file.seek(0)
            cmd= [
                "liqoctl", "unpeer", "in-band", "--skip-confirm", 
                "--kubeconfig", local_kubeconfig_file.name, "--remote-kubeconfig", remote_kubeconfig_file.name
            ]
            subprocess.run(cmd, check=True)
    except (subprocess.CalledProcessError, IOError) as e:
        print(f"Error: {e}")