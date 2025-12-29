#!/bin/bash

# Configuration
EPIK_ENV=${EPIK_ENV:~"dev"}
CLUSTER_NAME="chaos-genome-cluster"
REGION="nyc1"

SSH_KEY_IDENTIFIER=${DO_SSH_KEY}

if [ "$EPIK_ENV" == "prod" ]; then
    echo "🌐 Deploying to PRODUCTION (DOKS)..."
    NODE_SIZE="s-2vpcu-4gb"
    NODE_COUNT=3

    doctl k8s cluster create $CLUSTER_NAME \
	  --region $REGION \
	  --node-pool "name=worker-pool;size=$NODE_SIZE;count=$NODE_COUNT"

    doctl k8s cluster kubeconfig save $CLUSTER_NAME
else
    echo "🛠️  Deploying to DEVELOPMENT (k3s on Droplet)..."

    if [ -z "$SSH_KEY_IDENTIFIER" ]; then
	echo "❌ Error: DO_SSH_KEY environment variable is not set."
        echo "Please run: export DO_SSH_KEY='your_fingerprint_or_id'"
        echo "You can find your key ID with: doctl compute ssh-key list"
        exit 1
    fi
    
    DROPLET_NAME="chaos-genome-dev"
    DROPLET_SIZE="s-1vpcu-2gb" # I need to figure out if this size droplet is big enough

    echo "📦 Creating Droplet: $DROPLET_NAME with SSH Key: $SSH_KEY_IDENTIFIER..."
    doctl compute droplet create $DROPLET_NAME \
	  --region $REGION \
	  --size $DROPLET_SIZE \
	  --image ubuntu-22-04-x64 \
	  --ssh-keys "$SSH_KEY_IDENTIFIER" \
	  --wait

    DROPLET_IP=$(doctl compute droplet get $DROPLET_NAME --format "PublicIPv4" --no-header)

    if [ -z "$DROPLET_IP" ]; then
	echo "❌ Error: Could not retrieve Droplet IP address."
	exit 1
    fi

    echo "🚀 Installing k3s on $DROPLET_IP..."

    echo "⏳ Waiting for SSH service to initialize..."
    until nc -z -v -w5 $DROPLET_IP 22; do
	sleep 5
    done
    
    doctl compute ssh $DROPLET_NAME --ssh-command "curl -sfL https://get.k3s.io | sh -"

    echo "🔑 Fetching k3s kubeconfig..."
    doctl compute ssh $DROPLET_NAME --ssh-command "sudo cat /etc/rancher/k3s/k3s.yaml" > k3s_config.yaml
    sed -i "s/127.0.0.1/$DROPLET_IP/g" k3s_config.yaml
    export KUBECONFIG=$(pwd)/k3s_config.yaml
    echo "KUBECONFIG set to local k3s_config.yaml"
fi
    
echo "🏗️  Creating the Ecological Niche..."
kubectl apply -f manifests/namespace.yaml

echo "🌪️  Installing Chaos Mesh..."
curl -sSL https://mirrors.chaos-mesh.org/v2.6.1/install.sh | bash

echo "⏳ Waiting for Chaos Mesh components to initialize..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=chaos-mesh -n chaos-mesh --timeout=300s

echo "✅ Setup Complete. Your environment is ready for the organism."

#echo "🧬 Deploying the Clonal Organism..."
#kubectl apply -f manifests/organism.yaml
