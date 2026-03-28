#!/bin/bash
cat <<EOF2 | kind create cluster --name rook-test --config=-
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
  - role: worker
    extraMounts:
      - hostPath: /tmp/rook-osd-0
        containerPath: /var/lib/rook-osd-0
EOF2

for i in 0 1 2; do mkdir -p /tmp/rook-osd-; done

helm repo add rook-release https://charts.rook.io/release
helm install rook-ceph rook-release/rook-ceph   --namespace rook-ceph --create-namespace

kubectl -n rook-ceph wait --for=condition=Ready pod -l app=rook-ceph-operator --timeout=300s
kubectl apply -f https://raw.githubusercontent.com/rook/rook/release-1.16/deploy/examples/cluster-test.yaml
sleep 10
kubectl -n rook-ceph get cephcluster
kubectl -n rook-ceph get pods
