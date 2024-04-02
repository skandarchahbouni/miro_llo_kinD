# Readme

## Clone the repository

- `git clone ...`

## Creating the Clusters

### Create Clusters using the following commands:

- Run the following commands:
  - `kind create cluster --name="management-cluster"`
  - `kind create cluster --config="./config/kind-cluster-config.yaml" --name="workload-1"` <!-- Note: --config is necessary for nginx controller -->
  - `kind create cluster --config="./config/kind-cluster-config.yaml" --name="workload-2"`
  - .... (repeat for additional workload clusters if needed)

### Apply Custom Resource Definitions (CRDs) in the Management Cluster:

- Run the following commands:
  - `kubectl config use-context kind-management-cluster` <!-- switch the context to the management cluster, consider using kubectx for more flexibility -->
  - `kubectl apply -f crds` -`kubectl apply -f thanos`

## Setting Up NGINX Controller in the Workload Clusters

- Run the following commands for each workload cluster:
  - `kubectl config use-context kind-workload-1`
  - `kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml`
  - `kubectl wait --namespace ingress-nginx --for=condition=ready pod --selector=app.kubernetes.io/component=controller --timeout=90s`
- Repeat these commands for other workload clusters (kind-workload-2, ...)

## Installing Prometheus Operator in Each Workload Cluster

- Run the following commands for each workload cluster:
  - `cd config/monitoring-setup`
  - `kubectl config use-context kind-workload-1`
  - `kubectl create -f prometheus-operator-crds`
  - `kubectl create ns monitoring`
  - `kubectl apply -R -f prometheus-operator`
  - `kubectl get pods -n monitoring`
  - `kubectl apply -R -f prometheus`
  <!-- - `docker exec -it workload-2-control-plane bash`
  - `mkdir /mnt/data`
  - `exit` -->
- Confirm the installation by executing:
  - `kubectl port-forward svc/prometheus-operated 9090:9090 -n monitoring`
  - Visit http://localhost:9090/graph in your browser to verify.
- Repeat the process for all other workload clusters (kind-workload-2, ...)
- ...
- `cd ../..`

## Setting Up Ngrok Tunnel (for the Admission Webhook Controller)

- Install ngrok from https://dashboard.ngrok.com/get-started/setup/linux
- Run the following command: `ngrok config add-authtoken [YOUR_TOKEN]`

## Setting Up the Virtual Environment

- Create a virtual environment: `python -m venv venv`
- Activate the virtual environment: `source venv/bin/activate`
- Install the requirements: `pip install -r requirements.txt`

## Setting Persistent Environment Variables

- Add the following lines to `~/.bashrc` (or equivalent):

  - `export API_URL='http://127.0.0.1:8000/api/v1'`
  - `export TEMPLATE_DIR='YOUR_PATH_TO_TEMPLATES_HERE'` <!-- Example: `export TEMPLATE_DIR='/mnt/c/Users/skand/Downloads/PFE/miro_llo_kinD/miro_llo_kinD/templates'` -->
  - `export CRD_GROUP='miro.onesource.pt'`
  - `export CRD_VERSION='v1'`
  - `export MANAGEMENT_CLUSTER='YOUR_MANAGEMENT_CLUSTER_NAME'` <!-- Example: `export MANAGEMENT_CLUSTER='management-cluster'` -->
  - `export FORBIDDEN_NAMES='local-path-storage,kube-system,kube-public,kube-node-lease,ingress-nginx,monitoring,default'`

- Load the environment variables:

  - `source ~/.bashrc`

- Confirm that the environment variables exist:
  - `echo $API_URL`
  - `echo $TEMPLATE_DIR`
  - `echo $CRD_GROUP`
  - `echo $CRD_VERSION`
  - `echo $MANAGEMENT_CLUSTER`
  - `echo $FORBIDDEN_NAMES`

## Starting the REST API

- Execute the following commands:
  - `uvicorn be.main:app --reload`

## Starting the Operator

- Execute the following commands:
  - `cd llo/kopf_operator`
  - `kopf run k8s-operator.py`

## Running Tests

- Navigate to the examples folder: `cd example`
- Ensure you are in the management cluster
- Run tests:
  - `kubectl apply -f app.yaml`
  - `kubectl apply -f comp-1.yaml`
  - `kubectl delete -f comp-1.yaml`
  - Make changes in the YAML file and apply again as needed
- To test ServiceMonitor functionality:
  - Port-forward the Prometheus operator in the workload cluster:
    - `kubectl port-forward svc/prometheus-operated 9090:9090 -n monitoring`
    - Visit http://localhost:9090/graph in your browser to confirm.
- To test hosts within the Ingress:
  - Add hosts to the "hosts" file in either "C:\Windows\System32\drivers\etc\hosts" or "/etc/hosts" for Linux.
  - Port forward the NodePort service within the workload cluster:
    - `kubectl port-forward svc/ingress-nginx-controller 80:80 -n ingress-nginx`
  - Access the specified URL in the Ingress in your browser.

## Remarks:

- Each time you open a new terminal session, ensure to run `source ~/.bashrc` to reload the environment variables.
- To run this repository, you will need at least three terminal sessions:
  - One to execute the REST API (the backend).
  - One to run the operator.
  - One to execute commands (`kubectl apply -f ...`).
- You will frequently need to switch the context between clusters and namespaces, making it more convenient to install the `kubectx` and `kubens` commands.

## Quick demo:

- You can view a quick demo via this [link](https://drive.google.com/file/d/1SmXic5TtOZNIYLTRFvr6lSF9BXHx6ptJ/view?usp=sharing).

## Running infra-be and infra-operator

in order to run this you need these packages to be installed on your machine:

- kubectl
- clusterctl
- liqoctl
- helm

after installing helm you need to install the liqo helm repo by running these commands:

- helm repo add liqo https://helm.liqo.io/
- helm repo update

### Create and set up management cluster

- run the script in config called create-management-cluster.sh
- apply some config maps and crds:
  - kubectl apply -f config/supported-providers-cm.yaml
  - kubectl apply -f config/providers/docker
  - kubectl apply -f crds

### Run Operator

- activate the virtual environment in a seperate terminal window ( source venv/bin/activate)
- set up ngrok as mentioned above in **Setting Up Ngrok Tunnel (for the Admission Webhook Controller)** section
- run : kopf run llo/kopf_operator/infra-operator.py

### Run be_infra

- activate the virtual environment in a seperate terminal window ( source venv/bin/activate)
- set env variables:
  - export CLUSTER_TEMPLATES_PATH="the absolute path to be_infra/config/cluster-templates"
  - export PACKAGES_PATH="the absolute path to be_infra/config/packages"
- run the following command: uvicorn be_infra.main:app --port 3000
  - port 3000 is important because it is hardcoded in the infra-operator

### create two clusters and peer between them

- kubectl apply -f example/custom-cluster-1.yaml
- wait for cluster-1 to finish creation (it will take about 4 min)
- kubectl apply -f example/custom-cluster-2.yaml
- wait for cluster-2 to finish creation (it will take about 4 min)
- k apply -f example/link.yaml

## Monitoring Setup

### 1. install thanos :

`kubectl apply -f ./config/monitoring-setup/thanos`

make sure that thanos querier is running

### 2. change and run installation script :

- `cd config`
- in the script :
  - change **CLUSTERNAME** variable to the desired name
  - change the **MANAGEMENT_CLUSTER** variable to your management cluster name
- run `sudo chmod +x ./install_new_cluster.sh`
- run `./install_new_cluster.sh`
- inside the new cluster run `kubectl apply -f metallb/`

you can check if the cluster is added by checking logs of thanos querier in the management cluster or running :

- `kubectl port-forward svc/querier -n monitoring 9090:9090`

**PS** : thanos might take some time to discover the new cluster
