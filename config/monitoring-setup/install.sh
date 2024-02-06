
cd $APP_PACKAGES_PATH

export SERVICE_NAME=$CLUSTER_NAME
export INGRESS_URL=$CLUSTER_NAME.monitoring.onesource.pt
#thanos path contains the path to thanos configuration path: in this case $THANOS_PATH= /src/monitoring/thano
export THANOS_QUERY_CONF=../../thanos/thanos-querier.yaml #this becomes /src/management-cluster/monitoring/thano/thanos-querier.yaml


# function check_services_ip() {
#     ip1=$(kubectl --kubeconfig=$KUBECONFIG -n monitoring get svc $CLUSTER_NAME | awk {'print $4'} | grep -v EXTERNAL-IP)

#     if [[ "$ip1" == "<pending>" ]]; then
#         echo "A service did not obtain external IP."
#         return 1
#     else
#         echo "Both services have obtained external IP."
#         return 0
#     fi
# }

echo "[1] creating monitoring name space"

kubectl --kubeconfig=$KUBECONFIG create namespace monitoring


echo "[2] Installing Prometheus Operator CRDs..."

kubectl --kubeconfig=$KUBECONFIG create -R -f ./prometheus/prometheus-operator-crds
# kubectl wait --for=condition=Ready pods -l  app.kubernetes.io/name=prometheus-operator -n

echo "[3] Installing Prometheus Operator ..."

kubectl --kubeconfig=$KUBECONFIG apply -R -f ./prometheus/prometheus-operator
# kubectl wait --for=condition=Ready pods -l  app.kubernetes.io/name=prometheus-operator -n

echo "[4] Installing Prometheus server ..."

#### modifying external labels prometheus #### 
yq eval ".spec.externalLabels.cluster = \"$CLUSTER_NAME\"" -i ./prometheus/prometheus/prometheus.yaml

#### modifying external labels prometheus #### 
yq eval ".spec.rules[0].host = \"$INGRESS_URL\"" -i ./prometheus/prometheus/sidecar-ingress.yaml

kubectl --kubeconfig=$KUBECONFIG apply -R -f ./prometheus/prometheus
# kubectl wait --for=condition=Ready pods -l  app.kubernetes.io/name=prometheus-operator -n

echo "[5] Adding endpoint to thanos ..."

#### add thanos sidecar endpoint and update thanos configuration ####

# INGRESS_URL = contains the url to the thanos sidecar inside the new cluster

#the line below adds the new endpoint to the args in thanos querier, check thanos-querier.yaml line 33 to understand better
yq eval ".spec.template.spec.containers[0].args += \"--endpoint=$INGRESS_URL\"" -i $THANOS_QUERY_CONF 

kubectl -n monitoring apply -f $THANOS_QUERY_CONF

#kubectl --kubeconfig=$KUBECONFIG -n monitoring rollout status deployment prometheus-deployment

# echo "[6] Restarting MetalLB..."

# while ! check_services_ip; do

# kubectl --kubeconfig=$KUBECONFIG -n metallb-system rollout restart deployment controller
# kubectl --kubeconfig=$KUBECONFIG -n metallb-system rollout status deployment controller
# kubectl --kubeconfig=$KUBECONFIG -n metallb-system rollout restart daemonset speaker
# kubectl --kubeconfig=$KUBECONFIG -n metallb-system rollout status daemonset speaker

sleep 5
echo "LOOPING"

done

#kubectl --kubeconfig=$KUBECONFIG apply -f ./prometheus/kube-state-metrics-configs/
