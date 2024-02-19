from fastapi import APIRouter
from be_infra.schemas.link import Link
from be_infra.utils import get_kubeconfig
import subprocess
import time

links_router = APIRouter()

@links_router.post('/links')
def create_link(link: Link):
    localKubeconfig = get_kubeconfig(link.localCluster)
    remoteKubeconfig = get_kubeconfig(link.remoteCluster)
    cmd = f"liqoctl peer in-band --kubeconfig={localKubeconfig} --remote-kubeconfig={remoteKubeconfig}"
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")

@links_router.delete('/links')
def delete_link(link: Link):
    localKubeconfig = get_kubeconfig(link.localCluster)
    remoteKubeconfig = get_kubeconfig(link.remoteCluster)
    cmd = f"liqoctl unpeer in-band --skip-confirm --kubeconfig={localKubeconfig} --remote-kubeconfig={remoteKubeconfig}"
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")