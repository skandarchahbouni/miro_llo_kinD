


export CLUSTER_NAME="workload-1"
export INGRESS_URL=$CLUSTER_NAME."monitoring.onesource.pt"
export THANOS_QUERY_CONF="monitoring-setup/thanos/querier.yaml"
export MANAGEMENT_CLUSTER="management"
export CONTAINER_NAME=$CLUSTER_NAME"-control-plane"
export IP='8.8.8.8'

kind create cluster --config="./kind-cluster-config.yaml" --name=$CLUSTER_NAME

echo "[1] creating monitoring namespace"

kind get kubeconfig --name $CLUSTER_NAME > new-cluster.kubeconfig

export KUBECONFIG="./new-cluster.kubeconfig"

kubectl --kubeconfig=$KUBECONFIG create namespace monitoring


echo "[2] Installing Prometheus Operator CRDs..."

kubectl --kubeconfig=$KUBECONFIG create -R -f monitoring-setup/prometheus-operator-crds
# kubectl wait --for=condition=Ready pods -l  app.kubernetes.io/name=prometheus-operator -n

echo "[3] Installing Prometheus Operator ..."

kubectl --kubeconfig=$KUBECONFIG apply -R -f monitoring-setup/prometheus-operator
# kubectl wait --for=condition=Ready pods -l  app.kubernetes.io/name=prometheus-operator -n

echo "[4] Installing Prometheus server ..."

#### modifying external labels prometheus #### 
yq eval ".spec.externalLabels.cluster = \"$CLUSTER_NAME\"" -i monitoring-setup/prometheus/prometheus.yaml

#### modifying external labels prometheus #### 
yq eval ".spec.rules[0].host = \"$INGRESS_URL\"" -i monitoring-setup/prometheus/sidecar-ingress.yaml

kubectl --kubeconfig=$KUBECONFIG apply -R -f monitoring-setup/prometheus/
# kubectl wait --for=condition=Ready pods -l  app.kubernetes.io/name=prometheus-operator -n
echo "[5] isntalling metallb ..."

kubectl apply --kubeconfig=$KUBECONFIG -f https://raw.githubusercontent.com/metallb/metallb/v0.14.4/config/manifests/metallb-native.yaml
kubectl wait --for=condition=Ready deployment controller -n metallb-system

echo "[6] retrieving cluster ip ..."

export IP=$(docker container inspect $CONTAINER_NAME \
    --format '{{ .NetworkSettings.Networks.kind.IPAddress }}')

echo "new cluster IP $IP"
export NEWEP=$IP":10901"
yq eval ".spec.addresses[0] = \"$IP-$IP\"" -i metallb/config.yaml

kubectl apply --kubeconfig=$KUBECONFIG -f metallb 


echo "[7] Adding endpoint to thanos ..."

#the line below adds the new endpoint to the args in thanos querier, check thanos-querier.yaml line 33 to understand better
yq eval ".spec.template.spec.containers[0].args += \"--endpoint=$NEWEP\"" -i $THANOS_QUERY_CONF 

sudo kind get kubeconfig --name $MANAGEMENT_CLUSTER > management.kubeconfig

export KUBECONFIG="./management.kubeconfig"

kubectl --kubeconfig=$KUBECONFIG -n monitoring apply -f $THANOS_QUERY_CONF

#kubectl --kubeconfig=$KUBECONFIG -n monitoring rollout status deployment prometheus-deployment

# echo "[6] Restarting MetalLB..."

# while ! check_services_ip; do

# kubectl --kubeconfig=$KUBECONFIG -n metallb-system rollout restart deployment controller
# kubectl --kubeconfig=$KUBECONFIG -n metallb-system rollout status deployment controller
# kubectl --kubeconfig=$KUBECONFIG -n metallb-system rollout restart daemonset speaker
# kubectl --kubeconfig=$KUBECONFIG -n metallb-system rollout status daemonset speaker

sleep 5
echo "LOOPING"


#kubectl --kubeconfig=$KUBECONFIG apply -f ./prometheus/kube-state-metrics-configs/
