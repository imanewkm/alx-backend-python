#!/bin/bash

# Step 1: Scale deployment to 3 replicas
echo "[+] Scaling deployment to 3 replicas..."
kubectl scale deployment django-messaging-app --replicas=3

# Wait for pods to be ready
echo "[+] Waiting for pods to be ready..."
kubectl wait --for=condition=available deployment/django-messaging-app --timeout=90s

# Step 2: Get pod status
echo "[+] Current pods:"
kubectl get pods -l app=django-messaging

# Step 3: Run a quick load test with wrk (make sure wrk is installed locally)
echo "[+] Running load test using wrk..."
APP_PORT=$(kubectl get svc django-messaging-service -o jsonpath='{.spec.ports[0].nodePort}')
minikube service django-messaging-service --url | while read url; do
    wrk -t4 -c100 -d10s "$url" || echo "wrk failed — make sure wrk is installed!"
done

# Step 4: Monitor resource usage
echo "[+] Resource usage:"
kubectl top pods || echo "You may need to enable metrics server with: minikube addons enable metrics-server"
