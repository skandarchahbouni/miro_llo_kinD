#!/bin/bash

# Function to echo messages in green
echo_green() {
    echo -e "\e[32m$1\e[0m"
}

# Export the CLUSTER_TOPOLOGY variable
export CLUSTER_TOPOLOGY=true

cat > management-kind-cluster.yaml <<EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
networking:
  ipFamily: dual
nodes:
- role: control-plane
  extraMounts:
    - hostPath: /var/run/docker.sock
      containerPath: /var/run/docker.sock
EOF

echo_green "management-kind-cluster.yaml created successfully."

# Create a Kind cluster using the generated configuration
kind create cluster --name management --config management-kind-cluster.yaml

echo_green "Management kind cluster created successfully."

# Initialize clusterctl with the specified infrastructure provider (docker)
clusterctl init --infrastructure docker

kubectl --all --all-namespaces wait --timeout 180s --for=condition=Ready pod

echo_green "clusterctl initialized successfully."
