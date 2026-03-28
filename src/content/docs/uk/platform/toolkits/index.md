---
title: "Набори інструментів"
sidebar:
  order: 1
---
> **Поточні інструменти для platform engineering** — практичні посібники з найважливіших cloud-native інструментів

## Про набори інструментів

Набори інструментів — це практичні посібники з конкретних інструментів. На відміну від основ (вічна теорія) та дисциплін (практики), набори інструментів еволюціонують разом з екосистемою. Ми зосереджуємося на CNCF-graduated та широко прийнятих інструментах.

## Структура

| Набір інструментів | Фокус | Модулі |
|--------------------|-------|--------|
| [Спостережуваність](observability/) | Prometheus, OpenTelemetry, Grafana, Loki, Pixie, Hubble, Coroot | 8 |
| [GitOps та розгортання](gitops-deployments/) | ArgoCD, Argo Rollouts, Flux, Helm | 4 |
| [CI/CD конвеєри](ci-cd-pipelines/) | Dagger, Tekton, Argo Workflows | 3 |
| [Інструменти IaC](iac-tools/) | Terraform, OpenTofu, Pulumi, Ansible, Wing, SST, System Initiative, Nitric | 10 |
| [Інструменти безпеки](security-tools/) | Vault, OPA/Gatekeeper, Falco, Tetragon, KubeArmor | 6 |
| [Мережа](networking/) | Cilium, Service Mesh | 2 |
| [Масштабування та надійність](scaling-reliability/) | Karpenter, KEDA, Velero | 3 |
| [Платформи](platforms/) | Backstage, Crossplane, cert-manager | 3 |
| [Досвід розробника](developer-experience/) | K9s, Telepresence, Local K8s, DevPod, Gitpod/Codespaces | 5 |
| [ML-платформи](ml-platforms/) | Kubeflow, MLflow, Feature Stores, vLLM, Ray Serve, LangChain | 6 |
| [Інструменти AIOps](aiops-tools/) | Виявлення аномалій, кореляція подій | 4 |
| [Системи контролю версій](source-control/) | GitLab, Gitea/Forgejo, GitHub Advanced | 3 |
| [Якість коду](code-quality/) | SonarQube, Semgrep, CodeQL, Snyk, Trivy | 5 |
| [Реєстри контейнерів](container-registries/) | Harbor, Zot, Dragonfly | 3 |
| [Дистрибутиви K8s](k8s-distributions/) | k3s, k0s, MicroK8s, Talos, OpenShift, Managed K8s | 6 |
| [Cloud-Native бази даних](cloud-native-databases/) | CockroachDB, CloudNativePG, Neon/PlanetScale, Vitess | 4 |
| [Сховище](storage/) | Rook/Ceph, MinIO, Longhorn | 3 |
| **Загалом** | | **78** |

## Як використовувати набори інструментів

1. **Спочатку прочитайте основи** — зрозумійте теорію
2. **Прочитайте дисципліни** — зрозумійте практики
3. **Обирайте інструменти за потребою** — не все стосується вас
4. **Практикуйтеся** — набори інструментів включають вправи
5. **Тримайте руку на пульсі** — інструменти еволюціонують, перевіряйте примітки до релізів

## Філософія вибору інструментів

Ми включаємо інструменти, які:

- **CNCF Graduated/Incubating** — підтвердження спільнотою
- **Перевірені у production** — випробувані у масштабі
- **Активно підтримуються** — регулярні релізи, активна спільнота
- **Сумісні** — працюють з екосистемою

## Передумови

Перед тим, як зануритися в набори інструментів:

- Пройдіть відповідні модулі [Основ](../foundations/)
- Зрозумійте [Дисципліну](../disciplines/), яку інструмент підтримує
- Майте кластер Kubernetes (kind/minikube для навчання)

## Почніть навчання

Оберіть набір інструментів залежно від вашого поточного фокусу:

- **Починаєте зі спостережуваності?** Почніть з [Prometheus](observability/module-1.1-prometheus/)
- **Впроваджуєте GitOps?** Почніть з [ArgoCD](gitops-deployments/module-2.1-argocd/)
- **Керуєте інфраструктурою?** Ознайомтеся з [Terraform](iac-tools/module-7.1-terraform/)
- **Будуєте платформу?** Ознайомтеся з [Backstage](platforms/module-7.1-backstage/)
