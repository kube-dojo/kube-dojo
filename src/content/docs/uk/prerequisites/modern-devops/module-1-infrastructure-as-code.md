---
title: "\u041c\u043e\u0434\u0443\u043b\u044c 1: \u0406\u043d\u0444\u0440\u0430\u0441\u0442\u0440\u0443\u043a\u0442\u0443\u0440\u0430 \u044f\u043a \u043a\u043e\u0434"
sidebar:
  order: 2
---
> **Складність**: `[MEDIUM]` — Базова концепція
>
> **Час на виконання**: 30–35 хвилин
>
> **Передумови**: Базові навички роботи з командним рядком

---

## Чому цей модуль важливий

До появи інфраструктури як коду (IaC) налаштування серверів було ручним, схильним до помилок і неможливим для відтворення. «Воно працює на моїй машині» — була відмовка кожного. IaC змінила все — інфраструктура стала версіонованою, тестованою та повторюваною. Розуміння IaC є обовʼязковим, тому що Kubernetes сам по собі є системою інфраструктури як коду.

---

## Старий спосіб: ClickOps

Уявіть собі: 2005 рік. Вам потрібно налаштувати вебсервер.

```
Ручний процес:
1. Замовити фізичний сервер (2–4 тижні)
2. Чекати, поки дата-центр його встановить (1 тиждень)
3. Зайти по SSH та встановити пакети
4. Налаштувати, редагуючи файли
5. Сподіватися, що пам'ятаєте, що робили
6. Молитися, щоб нічого не зламалося

Документація: «Запитайте Дейва, він це налаштовував»
```

**Проблеми**:
- Немає записів про те, що було зроблено
- Неможливо відтворити налаштування
- Різні «ідентичні» сервери поводяться по-різному
- Дейв іде у відпустку — все ламається

---

## Інфраструктура як код

IaC означає **опис інфраструктури у файлах, які можна версіонувати, ділитися ними та виконувати**.

```
┌─────────────────────────────────────────────────────────────┐
│              ІНФРАСТРУКТУРА ЯК КОД                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Традиційний підхід:                                        │
│  ┌─────────┐      ┌─────────┐      ┌─────────┐            │
│  │ Людина  │ ───► │ Консоль │ ───► │ Сервер  │            │
│  │         │      │  (GUI)  │      │         │            │
│  └─────────┘      └─────────┘      └─────────┘            │
│                                                             │
│  З IaC:                                                     │
│  ┌─────────┐      ┌─────────┐      ┌─────────┐            │
│  │   Код   │ ───► │Інструмент│ ───► │ Сервер  │            │
│  │ (файли) │      │(Terraform)│    │         │            │
│  └─────────┘      └─────────┘      └─────────┘            │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────┐                                               │
│  │   Git   │  Версіонований, рецензований, повторюваний    │
│  └─────────┘                                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Ключові принципи

### 1. Декларативний vs Імперативний

```
Імперативний (Як):
"Встанови nginx, потім відредагуй /etc/nginx/nginx.conf,
потім перезапусти nginx"

Декларативний (Що):
"Я хочу, щоб nginx працював з цією конфігурацією"
```

Декларативний підхід є кращим — ви описуєте бажаний стан, а інструмент визначає, як його досягти.

### 2. Ідемпотентність

Запуск одного й того ж коду кілька разів дає однаковий результат:

```bash
# Running this 10 times creates 10 servers (BAD)
create_server web-1

# Running this 10 times ensures 1 server exists (GOOD)
ensure_server_exists web-1
```

### 3. Контроль версій

```bash
git log --oneline infrastructure/
abc123 Add production database replica
def456 Increase web server count to 5
ghi789 Initial infrastructure setup

# "Who changed production?" - Just check git blame
```

---

## Ландшафт інструментів IaC

```
┌─────────────────────────────────────────────────────────────┐
│              КАТЕГОРІЇ ІНСТРУМЕНТІВ IaC                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ПРОВІЗІОНУВАННЯ (Створення інфраструктури)                 │
│  ├── Terraform (хмаро-незалежний, найпопулярніший)          │
│  ├── Pulumi (справжні мови програмування)                   │
│  ├── CloudFormation (лише AWS)                              │
│  └── ARM Templates (лише Azure)                             │
│                                                             │
│  КОНФІГУРУВАННЯ (Налаштування наявних машин)                │
│  ├── Ansible (безагентний, на базі SSH)                     │
│  ├── Chef (Ruby DSL, з агентом)                             │
│  ├── Puppet (з агентом, корпоративний)                      │
│  └── Salt (на базі Python)                                  │
│                                                             │
│  KUBERNETES-НАТИВНІ (Провізіонування та конфігурація K8s)   │
│  ├── Helm (пакетний менеджер для K8s)                       │
│  ├── Kustomize (кастомізація на базі патчів)                │
│  └── kubectl apply (пряме застосування YAML)                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Terraform: Галузевий стандарт

Terraform від HashiCorp — найпоширеніший інструмент IaC:

```hcl
# main.tf - Terraform configuration

# Define provider (where to create resources)
provider "aws" {
  region = "us-west-2"
}

# Define a resource
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"

  tags = {
    Name = "web-server"
    Environment = "production"
  }
}

# Define output
output "public_ip" {
  value = aws_instance.web.public_ip
}
```

```bash
# Terraform workflow
terraform init      # Download providers
terraform plan      # Preview changes
terraform apply     # Create infrastructure
terraform destroy   # Tear it all down
```

### Чому Terraform перемагає

| Функція | Terraform | CloudFormation |
|---------|-----------|----------------|
| Підтримка хмар | Будь-яка хмара | Лише AWS |
| Управління станом | Вбудоване | Керується AWS |
| Синтаксис | HCL (зрозумілий) | JSON/YAML (багатослівний) |
| Крива навчання | Помірна | Специфічна для AWS |
| Спільнота | Величезна | Обмежена AWS |

---

## Ansible: Конфігурування — просто

Ansible використовує YAML-«плейбуки» для конфігурування машин:

```yaml
# playbook.yml - Ansible playbook
---
- name: Configure web server
  hosts: webservers
  become: yes  # Run as root

  tasks:
    - name: Install nginx
      apt:
        name: nginx
        state: present
        update_cache: yes

    - name: Copy configuration
      template:
        src: nginx.conf.j2
        dest: /etc/nginx/nginx.conf
      notify: Restart nginx

    - name: Ensure nginx is running
      service:
        name: nginx
        state: started
        enabled: yes

  handlers:
    - name: Restart nginx
      service:
        name: nginx
        state: restarted
```

```bash
# Run the playbook
ansible-playbook -i inventory.ini playbook.yml
```

**Ключова перевага**: Безагентний. Потрібен лише SSH-доступ.

---

## IaC для Kubernetes

Kubernetes — ЦЕ інфраструктура як код:

```yaml
# deployment.yaml - Desired state
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: nginx
        image: nginx:1.25
```

```bash
# Apply desired state
kubectl apply -f deployment.yaml

# Kubernetes reconciles actual state to match desired state
# This is IaC in action!
```

Звʼязок: **Kubernetes використовує ті самі декларативні, ідемпотентні принципи, що й Terraform та Ansible.**

---

## Найкращі практики IaC

### 1. Все — у Git

```bash
infrastructure/
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── kubernetes/
│   ├── deployments/
│   └── services/
└── ansible/
    └── playbooks/
```

### 2. Використовуйте модулі та повторно використовувані компоненти

```hcl
# Don't repeat yourself
module "web_server" {
  source = "./modules/ec2-instance"

  name          = "web-1"
  instance_type = "t2.micro"
}

module "api_server" {
  source = "./modules/ec2-instance"

  name          = "api-1"
  instance_type = "t2.small"
}
```

### 3. Розділяйте середовища

```bash
environments/
├── dev/
│   └── main.tf      # Small instances, single replica
├── staging/
│   └── main.tf      # Medium instances, testing
└── prod/
    └── main.tf      # Large instances, high availability
```

### 4. Ніколи не редагуйте вручну

```
Золоте правило: Якщо цього немає в коді — цього не існує.

Ручні зміни = дрейф конфігурації = баги о 3-й ночі
```

---

## Робочий процес IaC

```
┌─────────────────────────────────────────────────────────────┐
│              РОБОЧИЙ ПРОЦЕС IaC                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Написати ───►  2. Рецензія  ───►  3. Тестування        │
│     код            (PR/MR)            (Plan)                │
│       │                                 │                   │
│       │                                 ▼                   │
│  6. Моніторинг ◄── 5. Застосувати ◄── 4. Затвердити        │
│     стану          зміни              (Merge)               │
│                                                             │
│  Всі зміни проходять код-рецензію                          │
│  Всі зміни відстежуються                                   │
│  Всі зміни є зворотними                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Чи знали ви?

- **NASA використовує Terraform** для управління хмарною інфраструктурою. Якщо це достатньо добре для космосу, то й для вашого стартапу підійде.

- **Назва Ansible** походить із науково-фантастичних романів Урсули Ле Ґуїн, де «ансібль» — це пристрій для миттєвого зв'язку через космос.

- **«Худоба, а не домашні улюбленці»** — це принцип IaC. Ставтеся до серверів як до худоби (замінні, пронумеровані), а не як до домашніх улюбленців (з іменами, незамінні). Ви повинні мати змогу знищити та відтворити будь-який сервер без хвилювань.

---

## Типові помилки

| Помилка | Чому це болить | Рішення |
|---------|----------------|---------|
| Ручні зміни після IaC-деплою | Дрейф конфігурації | Передеплоїти з коду |
| Невикористання контролю версій | Немає аудиту, немає відкату | Все — у Git |
| Хардкод секретів | Витік безпеки | Використовуйте менеджери секретів |
| Монолітні конфігурації | Важко підтримувати | Використовуйте модулі |
| Відсутність бекапу стану | Втрата стану інфраструктури | Віддалене зберігання стану |

---

## Тест

1. **Що означає «ідемпотентний» у контексті IaC?**
   <details>
   <summary>Відповідь</summary>
   Запуск одного й того ж коду кілька разів дає однаковий результат. Незалежно від того, чи ви застосуєте Terraform-план один раз або десять разів, кінцевий стан буде ідентичним.
   </details>

2. **Яка різниця між Terraform та Ansible?**
   <details>
   <summary>Відповідь</summary>
   Terraform провізіонує інфраструктуру (створює ВМ, мережі, бази даних). Ansible конфігурує наявні машини (встановлює програми, керує конфігами). Їх часто використовують разом.
   </details>

3. **Чому декларативний підхід кращий за імперативний?**
   <details>
   <summary>Відповідь</summary>
   Декларативний описує «що» ви хочете, а не «як» цього досягти. Інструмент бере на себе деталі реалізації, що робить код простішим і більш стійким до початкових умов.
   </details>

4. **Як Kubernetes повʼязаний з IaC?**
   <details>
   <summary>Відповідь</summary>
   Kubernetes — ЦЕ IaC. Ви описуєте бажаний стан у YAML, а Kubernetes безперервно узгоджує фактичний стан із бажаним. Ті самі принципи (декларативний, ідемпотентний, з контролем версій) застосовуються.
   </details>

---

## Практична вправа

**Завдання**: Відчути принципи IaC на практиці з kubectl.

```bash
# This exercise uses Kubernetes to demonstrate IaC concepts

# 1. Create a deployment declaratively
cat << 'EOF' > deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: iac-demo
spec:
  replicas: 2
  selector:
    matchLabels:
      app: iac-demo
  template:
    metadata:
      labels:
        app: iac-demo
    spec:
      containers:
      - name: nginx
        image: nginx:1.25
EOF

# 2. Apply it (IaC in action)
kubectl apply -f deployment.yaml

# 3. Check state
kubectl get deployment iac-demo

# 4. Apply again (idempotency)
kubectl apply -f deployment.yaml
# "deployment.apps/iac-demo unchanged" - Same result!

# 5. Modify the code
sed -i '' 's/replicas: 2/replicas: 4/' deployment.yaml

# 6. Apply change
kubectl apply -f deployment.yaml

# 7. Verify change
kubectl get deployment iac-demo
# Now shows 4 replicas

# 8. Version control (simulate)
# In real world: git add deployment.yaml && git commit

# 9. Cleanup
kubectl delete -f deployment.yaml
rm deployment.yaml
```

**Критерії успіху**: Розуміння того, як декларативні файли + apply = інфраструктура як код.

---

## Підсумок

**Інфраструктура як код** трансформує управління інфраструктурою:

**Основні принципи**:
- Декларативний підхід замість імперативного
- Ідемпотентні операції
- Контроль версій
- Рецензовані зміни

**Ключові інструменти**:
- Terraform: Провізіонування хмарних ресурсів
- Ansible: Конфігурування машин
- Kubernetes: Оркестрація контейнерів (IaC вбудований)

**Чому це важливо**:
- Відтворювані середовища
- Аудит усіх змін
- Відновлення після катастроф (перебудова з коду)
- Співпраця через код-рецензію

**Звʼязок з Kubernetes**: Все, що ви робите в Kubernetes, слідує принципам IaC. YAML-файли — це ваш інфраструктурний код.

---

## Наступний модуль

[Модуль 2: GitOps](module-1.2-gitops/) — Використання Git як єдиного джерела правди для інфраструктури.
