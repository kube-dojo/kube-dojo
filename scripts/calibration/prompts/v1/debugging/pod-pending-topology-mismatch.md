A Pod stays `Pending` indefinitely on a 3-node EKS cluster that uses the AWS
EBS CSI driver with a `WaitForFirstConsumer` StorageClass. The PVC was created
yesterday; the PV bound this morning when the pod was first scheduled. After a
node-drain triggered by a kops upgrade, the pod was rescheduled — and it has
been Pending for 45 minutes.

Diagnose the root cause and produce a minimal patch. The fix must NOT involve
deleting the PVC or its data.

### Observed state

```text
$ kubectl get pod inference-0 -n llm
NAME           READY   STATUS    RESTARTS   AGE
inference-0    0/1     Pending   0          45m

$ kubectl describe pod inference-0 -n llm | tail -20
Events:
  Type     Reason            Age    From               Message
  ----     ------            ----   ----               -------
  Warning  FailedScheduling  44m    default-scheduler  0/3 nodes are available:
                                                       3 node(s) had volume node
                                                       affinity conflict.
  Warning  FailedScheduling  4m24s  default-scheduler  0/3 nodes are available:
                                                       3 node(s) had volume node
                                                       affinity conflict.

$ kubectl get pv $(kubectl get pvc inference-data -n llm -o jsonpath='{.spec.volumeName}') -o yaml | grep -A 6 nodeAffinity
  nodeAffinity:
    required:
      nodeSelectorTerms:
      - matchExpressions:
        - key: topology.ebs.csi.aws.com/zone
          operator: In
          values:
          - us-east-1a

$ kubectl get nodes -L topology.kubernetes.io/zone
NAME                        STATUS   ROLES    AGE    ZONE
ip-10-0-12-1.ec2.internal   Ready    worker   2d     us-east-1b
ip-10-0-13-1.ec2.internal   Ready    worker   2d     us-east-1b
ip-10-0-14-1.ec2.internal   Ready    worker   2d     us-east-1b
```

### Relevant manifests

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: gp3-wffc
provisioner: ebs.csi.aws.com
volumeBindingMode: WaitForFirstConsumer
allowedTopologies:
- matchLabelExpressions:
  - key: topology.ebs.csi.aws.com/zone
    values:
    - us-east-1a
    - us-east-1b
parameters:
  type: gp3
  fsType: ext4
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: inference-data
  namespace: llm
spec:
  storageClassName: gp3-wffc
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 200Gi
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: inference
  namespace: llm
spec:
  serviceName: inference
  replicas: 1
  selector: { matchLabels: { app: inference } }
  template:
    metadata: { labels: { app: inference } }
    spec:
      containers:
      - name: vllm
        image: ghcr.io/example/vllm:0.7.3
        volumeMounts:
        - { name: data, mountPath: /data }
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: inference-data
```

### Return

- **root cause**: one sentence naming the specific topology mismatch and which
  pair of objects disagree.
- **patch**: a unified diff showing the minimal change(s) you would make. Do
  NOT propose deleting the PVC. The PV must remain bound and its data preserved.
- **why minimal**: one sentence on why your patch does not require any
  broader rewrite.
