import subprocess
import tempfile

def wait_for_ready_resources():
    cmd = "kubectl --all --all-namespaces wait --timeout 180s --for=condition=Ready cluster"
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")

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
    return output_file_path

def install_networking_addon(clusterName):
    kubeconfig = get_kubeconfig(clusterName)
    addon_artifact_path = "/home/mouad/pfe/miro_llo_kinD/be_infra/.config/addons/calico.yaml"
    cmd = f"kubectl apply -f {addon_artifact_path} --kubeconfig {kubeconfig}"
    try:
        subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")