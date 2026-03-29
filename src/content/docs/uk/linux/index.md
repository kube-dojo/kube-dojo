---
title: "Поглиблене вивчення Linux"
sidebar:
  order: 1
  label: "Поглиблене вивчення Linux"
---

**Необхідні знання Linux для практиків Kubernetes та DevOps.**

Кожна проблема з контейнером — це зрештою проблема Linux. Цей трек дає вам глибокі системні знання, які відрізняють операторів від тих, хто вміє лише дебажити.

**37 модулів** у 6 розділах · ~50 годин загалом

---

## Розділи

### [Щоденне використання](/linux/foundations/everyday-use/) — 5 модулів
*Необхідні навички Linux для щоденної роботи.*

| # | Модуль | Час |
|---|--------|-----|
| 0.1 | [Досвідчений користувач CLI](/linux/foundations/everyday-use/module-0.1-cli-power-user/) | 30 хв |
| 0.2 | [Оточення та дозволи](/linux/foundations/everyday-use/module-0.2-environment-permissions/) | 30 хв |
| 0.3 | [Путівник по процесах і ресурсах](/linux/foundations/everyday-use/module-0.3-processes-resources/) | 30 хв |
| 0.4 | [Сервіси та логи без таємниць](/linux/foundations/everyday-use/module-0.4-services-logs/) | 30 хв |
| 0.5 | [Щоденні мережеві інструменти](/linux/foundations/everyday-use/module-0.5-networking-tools/) | 30 хв |

### [Основи системи](/linux/foundations/system-essentials/) — 4 модулі
*Ядро, процеси, файлова система, дозволи — фундамент усього.*

| # | Модуль | Час |
|---|--------|-----|
| 1.1 | [Архітектура ядра](/linux/foundations/system-essentials/module-1.1-kernel-architecture/) | 25-30 хв |
| 1.2 | [Процеси та systemd](/linux/foundations/system-essentials/module-1.2-processes-systemd/) | 30-35 хв |
| 1.3 | [Ієрархія файлової системи](/linux/foundations/system-essentials/module-1.3-filesystem-hierarchy/) | 25-30 хв |
| 1.4 | [Користувачі та дозволи](/linux/foundations/system-essentials/module-1.4-users-permissions/) | 25-30 хв |

### [Примітиви контейнерів](/linux/foundations/container-primitives/) — 4 модулі
*Функції Linux, що забезпечують роботу контейнерів — namespaces, cgroups, capabilities, оверлейні файлові системи.*

| # | Модуль | Час |
|---|--------|-----|
| 2.1 | [Linux Namespaces](/linux/foundations/container-primitives/module-2.1-namespaces/) | 30-35 хв |
| 2.2 | [Control Groups (cgroups)](/linux/foundations/container-primitives/module-2.2-cgroups/) | 30-35 хв |
| 2.3 | [Capabilities та модулі безпеки Linux](/linux/foundations/container-primitives/module-2.3-capabilities-lsms/) | 25-30 хв |
| 2.4 | [Об'єднані файлові системи](/linux/foundations/container-primitives/module-2.4-union-filesystems/) | 25-30 хв |

### [Мережа](/linux/foundations/networking/) — 4 модулі
*TCP/IP, DNS, мережеві namespaces, iptables — мережевий стек, на якому побудований Kubernetes.*

| # | Модуль | Час |
|---|--------|-----|
| 3.1 | [Основи TCP/IP](/linux/foundations/networking/module-3.1-tcp-ip-essentials/) | 30-35 хв |
| 3.2 | [DNS у Linux](/linux/foundations/networking/module-3.2-dns-linux/) | 25-30 хв |
| 3.3 | [Мережеві Namespaces та veth](/linux/foundations/networking/module-3.3-network-namespaces/) | 30-35 хв |
| 3.4 | [iptables та netfilter](/linux/foundations/networking/module-3.4-iptables-netfilter/) | 35-40 хв |

### [Безпека](/linux/security/hardening/) — 4 модулі
*Зміцнення ядра, AppArmor, SELinux, seccomp — захист хоста, на якому працюють ваші контейнери.*

| # | Модуль | Час |
|---|--------|-----|
| 4.1 | [Зміцнення ядра](/linux/security/hardening/module-4.1-kernel-hardening/) | 25-30 хв |
| 4.2 | [Профілі AppArmor](/linux/security/hardening/module-4.2-apparmor/) | 30-35 хв |
| 4.3 | [Контексти SELinux](/linux/security/hardening/module-4.3-selinux/) | 35-40 хв |
| 4.4 | [Профілі seccomp](/linux/security/hardening/module-4.4-seccomp/) | 25-30 хв |

### Операції — 16 модулів
*Аналіз продуктивності, усунення несправностей, скрипти оболонки, системне адміністрування.*

#### [Системне адміністрування](/linux/operations/) — 4 модулі

| # | Модуль | Час |
|---|--------|-----|
| 8.1 | [Управління сховищами](/linux/operations/module-8.1-storage-management/) | 30-35 хв |
| 8.2 | [Мережеве адміністрування](/linux/operations/module-8.2-network-administration/) | 30-35 хв |
| 8.3 | [Управління пакетами та користувачами](/linux/operations/module-8.3-package-user-management/) | 25-30 хв |
| 8.4 | [Планування завдань та резервне копіювання](/linux/operations/module-8.4-scheduling-backups/) | 25-30 хв |

#### [Продуктивність](/linux/operations/performance/) — 4 модулі

| # | Модуль | Час |
|---|--------|-----|
| 5.1 | [Метод USE](/linux/operations/performance/module-5.1-use-method/) | 25-30 хв |
| 5.2 | [CPU та планування](/linux/operations/performance/module-5.2-cpu-scheduling/) | 30-35 хв |
| 5.3 | [Управління пам'яттю](/linux/operations/performance/module-5.3-memory-management/) | 30-35 хв |
| 5.4 | [Продуктивність вводу/виводу](/linux/operations/performance/module-5.4-io-performance/) | 25-30 хв |

#### [Усунення несправностей](/linux/operations/troubleshooting/) — 4 модулі

| # | Модуль | Час |
|---|--------|-----|
| 6.1 | [Систематичне усунення несправностей](/linux/operations/troubleshooting/module-6.1-systematic-troubleshooting/) | 25-30 хв |
| 6.2 | [Аналіз логів](/linux/operations/troubleshooting/module-6.2-log-analysis/) | 25-30 хв |
| 6.3 | [Дебагінг процесів](/linux/operations/troubleshooting/module-6.3-process-debugging/) | 30-35 хв |
| 6.4 | [Дебагінг мережі](/linux/operations/troubleshooting/module-6.4-network-debugging/) | 30-35 хв |

#### [Скрипти оболонки](/linux/operations/shell-scripting/) — 4 модулі

| # | Модуль | Час |
|---|--------|-----|
| 7.1 | [Основи Bash](/linux/operations/shell-scripting/module-7.1-bash-fundamentals/) | 30-35 хв |
| 7.2 | [Обробка тексту](/linux/operations/shell-scripting/module-7.2-text-processing/) | 30-35 хв |
| 7.3 | [Практичні скрипти](/linux/operations/shell-scripting/module-7.3-practical-scripts/) | 25-30 хв |
| 7.4 | [Автоматизація DevOps](/linux/operations/shell-scripting/module-7.4-devops-automation/) | 30-35 хв |

---

## Рекомендований порядок

```
Щоденне використання → Основи системи → Примітиви контейнерів → Мережа → Безпека → Операції
```

Почніть із **Щоденного використання**, якщо ви новачок у Linux. Переходьте до **Примітивів контейнерів**, якщо вже знаєте основи й хочете зрозуміти, як контейнери працюють зсередини.

---

## Чому цей трек важливий для Kubernetes

- **Namespaces та cgroups І Є контейнерами** — розуміння цього демістифікує контейнерну технологію
- **Мережеві політики використовують iptables/eBPF** — неможливо дебажити мережу без розуміння стеку
- **Security contexts використовують capabilities/AppArmor/seccomp** — безпека Pod вимагає знань безпеки Linux
- **Ліміти ресурсів — це конфігурації cgroup** — розуміння cgroups пояснює управління ресурсами K8s

---

## Сертифікація: LFCS

**Linux Foundation Certified System Administrator (LFCS)** — сертифікація, що входить до цього треку. Модулі Linux вище охоплюють усі домени іспиту LFCS — основи системи, мережу, сховище, безпеку та операції.

| Ресурс | Посилання |
|--------|-----------|
| Шлях навчання LFCS | [Сертифікація LFCS](/k8s/lfcs/) |
| Деталі іспиту | [Linux Foundation LFCS](https://training.linuxfoundation.org/certification/linux-foundation-certified-sysadmin-lfcs/) |

---

## Після цього треку

- [Сертифікації Kubernetes](/k8s/) — CKA, CKAD, CKS — знання Linux необхідні для цих іспитів
- [Cloud](/cloud/) — вивчіть гіперскейлери, на яких працюють ваші кластери
- [On-Premises Kubernetes](/on-premises/) — запускайте K8s на bare metal
- [Platform Engineering](/platform/) — будуйте на фундаменті
- [Cloud Native Tools](/platform/toolkits/) — досліджуйте екосистему CNCF
