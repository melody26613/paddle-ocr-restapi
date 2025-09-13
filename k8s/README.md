## Installation
* install k8s
```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"

sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

# check version
kubectl version --client
```

[Install and Set Up kubectl on Linux](https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/)


* install minikube for development
```bash
curl -LO https://github.com/kubernetes/minikube/releases/latest/download/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube && rm minikube-linux-amd64

# start minikube
minikube start --driver=docker --container-runtime=docker --gpus all --memory=8192mb --cpus=4
minikube addons enable nvidia-device-plugin

# make docker image in minikube
# (1) copy docker image from host to minikube
minikube image load paddle_ocr_restapi:latest

# or (2) build image for minikube
eval $(minikube docker-env)
docker build -t paddle_ocr_restapi:latest -f Dockerfile .

# get ip
minikube ip

# ssh into minikube
minikube ssh

# stop minikube if needed
minikube stop
minikube delete
```

[minikube start](https://minikube.sigs.k8s.io/docs/start/?arch=%2Flinux%2Fx86-64%2Fstable%2Fbinary+download)


* install k8s nvidia gpu plugin
```bash
kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/v0.14.4/nvidia-device-plugin.yml

# check result
kubectl get pods -n kube-system | grep nvidia
kubectl describe node minikube | grep nvidia
```

## Deployment
```bash
kubectl apply -f deployment.yaml

kubectl get pod
kubectl get services

kubectl describe pod <your-pod-name>

#kubectl port-forward service/paddleocr-service 8000:20000 --address 0.0.0.0 &>/dev/null &

#minikube tunnel --bind-address=0.0.0.0 &>/dev/null &

# stop deployment if needed
kubectl delete -f deployment.yaml
```

* request
```bash
curl -X POST "http://192.168.50.19:20000/ocr/dict" \
-H "accept: application/json" \
-H "Content-Type: multipart/form-data" \
-F "file=@test.png"
```