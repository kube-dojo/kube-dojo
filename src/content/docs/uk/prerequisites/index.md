---
title: "Передумови"
sidebar:
  order: 1
  label: "Основи"
---
**Почніть тут, якщо ви новачок у Kubernetes.**

Ці напрямки формують базові знання перед тим, як переходити до сертифікацій або складніших тем.

---

## Напрямки

### [Від нуля до термінала](zero-to-terminal/) — 10 модулів
*Ніколи не користувалися терміналом? Почніть тут. Від "що таке комп'ютер" до "я розгорнув вебсайт".*

| Модуль | Тема |
|--------|------|
| 0.1 | [Що таке комп'ютер?](zero-to-terminal/module-0.1-what-is-a-computer/) |
| 0.2 | [Що таке термінал?](zero-to-terminal/module-0.2-what-is-a-terminal/) |
| 0.3 | [Перші команди термінала](zero-to-terminal/module-0.3-first-commands/) |
| 0.4 | [Файли та директорії](zero-to-terminal/module-0.4-files-and-directories/) |
| 0.5 | [Редагування файлів](zero-to-terminal/module-0.5-editing-files/) |
| 0.6 | [Що таке мережа?](zero-to-terminal/module-0.6-what-is-networking/) |
| 0.7 | [Сервери та SSH](zero-to-terminal/module-0.7-servers-and-ssh/) |
| 0.8 | [Програмне забезпечення та пакети](zero-to-terminal/module-0.8-software-and-packages/) |
| 0.9 | [Що таке хмара?](zero-to-terminal/module-0.9-what-is-the-cloud/) |
| 0.10 | [Ваш перший сервер](zero-to-terminal/module-0.10-your-first-server/) |

### [Філософія та Дизайн](philosophy-design/) — 4 модулі
*Чому Kubernetes існує і як про нього думати.*

| Модуль | Тема |
|--------|------|
| 1.1 | [Чому Kubernetes переміг](philosophy-design/module-1.1-why-kubernetes-won/) |
| 1.2 | [Декларативний проти Імперативного](philosophy-design/module-1.2-declarative-vs-imperative/) |
| 1.3 | [Що ми не розглядаємо](philosophy-design/module-1.3-what-we-dont-cover/) |
| 1.4 | [Глухі кути — технології, яких слід уникати](philosophy-design/module-1.4-dead-ends/) |

### [Cloud Native 101](cloud-native-101/) — 5 модулів
*Контейнери, Docker та екосистема.*

| Модуль | Тема |
|--------|------|
| 1.1 | [Що таке контейнери?](cloud-native-101/module-1.1-what-are-containers/) |
| 1.2 | [Основи Docker](cloud-native-101/module-1.2-docker-fundamentals/) |
| 1.3 | [Що таке Kubernetes?](cloud-native-101/module-1.3-what-is-kubernetes/) |
| 1.4 | [Екосистема Cloud Native](cloud-native-101/module-1.4-cloud-native-ecosystem/) |
| 1.5 | [Від моноліту до мікросервісів](cloud-native-101/module-1.5-monolith-to-microservices/) |

### [Основи Kubernetes](kubernetes-basics/) — 8 модулів
*Практичні основи роботи з kubectl.*

| Модуль | Тема |
|--------|------|
| 1.1 | [Ваш перший кластер](kubernetes-basics/module-1.1-first-cluster/) |
| 1.2 | [Основи kubectl](kubernetes-basics/module-1.2-kubectl-basics/) |
| 1.3 | [Поди — атомарна одиниця](kubernetes-basics/module-1.3-pods/) |
| 1.4 | [Деплойменти — керування застосунками](kubernetes-basics/module-1.4-deployments/) |
| 1.5 | [Сервіси — стабільна мережа](kubernetes-basics/module-1.5-services/) |
| 1.6 | [ConfigMaps та Secrets](kubernetes-basics/module-1.6-configmaps-secrets/) |
| 1.7 | [Простори імен та Мітки](kubernetes-basics/module-1.7-namespaces-labels/) |
| 1.8 | [YAML для Kubernetes](kubernetes-basics/module-1.8-yaml-kubernetes/) |

### [Сучасні практики DevOps](modern-devops/) — 6 модулів
*Infrastructure as Code, GitOps та спостережуваність.*

| Модуль | Тема |
|--------|------|
| 1.1 | [Інфраструктура як код (IaC)](modern-devops/module-1.1-infrastructure-as-code/) |
| 1.2 | [GitOps](modern-devops/module-1.2-gitops/) |
| 1.3 | [CI/CD пайплайни](modern-devops/module-1.3-cicd-pipelines/) |
| 1.4 | [Основи спостережуваності](modern-devops/module-1.4-observability/) |
| 1.5 | [Платформна інженерія](modern-devops/module-1.5-platform-engineering/) |
| 1.6 | [Практики безпеки (DevSecOps)](modern-devops/module-1.6-devsecops/) |

---

## Рекомендований порядок

```
Від нуля до термінала → Філософія та Дизайн → Cloud Native 101 → Основи Kubernetes → Сучасні практики DevOps
```

Або переходьте одразу до **Основ Kubernetes**, якщо ви вже розумієте контейнери та термінал.

Бажаєте зануритися глибше в Linux? Перейдіть до напрямку [Linux](/linux/) (37 модулів, що охоплюють внутрішню будову ядра, примітиви контейнерів, мережу, безпеку та операції — а також шлях до сертифікації LFCS).

---

## Після передумов

Готові продовжувати? Оберіть свій шлях:

| Мета | Наступний крок |
|------|----------------|
| Опанувати Linux | [Linux](../linux/) (включає сертифікацію LFCS) |
| Отримати сертифікат | [Сертифікації Kubernetes](../k8s/) |
| Вивчити хмарних провайдерів | [Хмарні технології](../cloud/) |
| Запускати на власному обладнанні | [Локальний Kubernetes (On-Premises)](../on-premises/) |
| Поглибити знання | [Платформна інженерія](../platform/) |
| Дослідити cloud native інструменти | [Cloud Native інструменти](../platform/toolkits/) |
