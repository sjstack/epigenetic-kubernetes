#!/bin/bash

# Configuration
CLUSTER_NAME="chaos-genome-cluster"
REGION="nyc1"
NODE_SIZE="s-2vcpu-4gb"
NODE_COUNT=3

echo "🚀 Starting Chaos Genome Experiment Setup..."

# 1. Create the DigitalOcean Kubernetes Cluster
echo "🌐 Creating DOKS cluster: $CLUSTER_NAME..."
doctl k8s cluster create $CLUSTER_NAME \
    --region $REGION \
    --node-pool "name=worker-pool;size=$NODE_SIZE;count=$NODE_COUNT"

# 2. Get credentials
echo "🔑 Integrating cluster credentials..."
doctl k8s cluster kubeconfig save $CLUSTER_NAME

# 3. Create the Namespace
echo "🏗️  Creating the Ecological Niche..."
kubectl apply -f manifests/namespace.yaml

# 4. Install Chaos Mesh (The Environmental Stressor)
echo "🌪️  Installing Chaos Mesh..."
curl -sSL https://mirrors.chaos-mesh.org/v2.6.1/install.sh | bash

# 5. Wait for Chaos Mesh to be ready
echo "⏳ Waiting for Chaos Mesh components to initialize..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=chaos-mesh -n chaos-mesh --timeout=300s

echo "✅ Setup Complete. Your environment is ready for the organism."
