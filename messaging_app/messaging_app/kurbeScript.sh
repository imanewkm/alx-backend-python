#!/bin/bash

# kurbeScript - Starts a Kubernetes cluster and retrieves pod information

# Exit on error
set -e

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

echo "🔍 Checking for Minikube..."
if ! command_exists minikube; then
    echo "❌ Minikube is not installed."
    echo "➡️ Please install Minikube: https://minikube.sigs.k8s.io/docs/start/"
    exit 1
else
    echo "✅ Minikube is installed."
fi

echo "🚀 Starting Minikube..."
minikube start

echo "✅ Verifying Kubernetes cluster status..."
kubectl cluster-info

echo "📦 Retrieving pods in all namespaces..."
kubectl get pods --all-namespaces

echo "🎉 Script completed successfully."
