---
title: "Модуль 7.4: Автоматизація DevOps"
slug: uk/linux/operations/shell-scripting/module-7.4-devops-automation
sidebar:
  order: 5
lab:
  id: linux-7.4-devops-automation
  url: https://killercoda.com/kubedojo/scenario/linux-7.4-devops-automation
  duration: "35 min"
  difficulty: advanced
  environment: ubuntu
en_commit: bf9159a224c23a4dd04882b23d9e86af3e985c98
---
> **Shell Scripting** | Складність: `[MEDIUM]` | Час: 30–35 хв

## Передумови

Перед початком цього модуля:
- **Обов'язково**: [Модуль 7.3: Практичні скрипти](../module-7.3-practical-scripts/)
- **Обов'язково**: Базові знання `kubectl`.
- **Бажано**: Досвід роботи з CI/CD.

---

## Що ви зможете робити після цього модуля

Після завершення цього модуля ви зможете:
- **Побудувати** скрипти автоматизації для деплойменту, моніторингу та реагування на інциденти
- **Інтегрувати** скрипти з API (curl + jq), Kubernetes (kubectl) та CI/CD конвеєрами
- **Спроєктувати** бібліотеку скриптів, що дотримується принципу DRY та зручна для підтримки командою
- **Оцінити**, коли використовувати bash, а коли Python/Go для задач автоматизації

---

## Чому цей модуль важливий

Робота в DevOps сповнена повторюваних завдань. Деплойменти, перевірки здоров'я систем, аналіз логів, керування кластерами — усе це потребує автоматизації. Bash-скрипти часто є найкращим інструментом: вони портативні, не потребують встановлення і чудово поєднуються з існуючими CLI-утилітами.

Розуміння автоматизації DevOps допоможе вам:

- **Прискорити операції** — одна команда замість десяти.
- **Зменшити кількість помилок** — скрипти не роблять друкарських помилок.
- **Забезпечити самообслуговування** — ваші скрипти зможуть використовувати колеги.
- **Документувати процеси** — скрипт — це документація, яку можна запустити.

Найкраща автоматизація — та, про яку ви забуваєте, бо вона просто працює.

---

## Скрипти з kubectl

Команда `kubectl` спеціально розроблена для автоматизації.

### Корисні формати виводу

```bash
# JSON для повної обробки через jq
kubectl get pods -o json

# JSONPath для вибору конкретних полів
kubectl get pods -o jsonpath='{.items[*].metadata.name}'

# Спеціальні колонки (Custom columns)
kubectl get pods -o custom-columns='NAME:.metadata.name,STATUS:.status.phase'

# Тільки назви (name)
kubectl get pods -o name
# Вивід: pod/nginx-abc123
```

### Корисні патерни

```bash
# Отримати список усіх образів, що використовуються в кластері
kubectl get pods -A -o jsonpath='{.items[*].spec.containers[*].image}' | tr ' ' '\n' | sort -u

# Отримати поди, що НЕ в стані Running
kubectl get pods --field-selector='status.phase!=Running'

# Дочекатися готовності пода
kubectl wait --for=condition=Ready pod -l app=nginx --timeout=60s
```

---

## Скрипти перевірки здоров'я (Health Check)

Приклад скрипта для перевірки стану вузлів (nodes):

```bash
#!/bin/bash
set -euo pipefail

echo "=== Статус вузлів кластера ==="
kubectl get nodes

# Знайти вузли в стані NotReady
NOT_READY=$(kubectl get nodes --no-headers | awk '$2 != "Ready" {print $1}')

if [[ -n "$NOT_READY" ]]; then
    echo "УВАГА: Наступні вузли не готові: $NOT_READY"
    exit 1
fi

echo "Усі вузли здорові!"
```

---

## Скрипти деплойменту

Приклад безпечного оновлення образу з автоматичним відкатом:

```bash
#!/bin/bash
set -euo pipefail

IMAGE=$1
DEPLOYMENT="myapp"

echo "Оновлюємо $DEPLOYMENT на образ $IMAGE..."

# Запуск оновлення
kubectl set image deployment/$DEPLOYMENT app=$IMAGE

# Очікування результату
if ! kubectl rollout status deployment/$DEPLOYMENT --timeout=5m; then
    echo "ПОМИЛКА: Оновлення не вдалося. Робимо відкат..."
    kubectl rollout undo deployment/$DEPLOYMENT
    exit 1
fi

echo "Деплой завершено успішно!"
```

---

## Тест

1. **Як отримати тільки IP-адресу конкретного пода в змінну Bash?**
   <details>
   <summary>Відповідь</summary>
   `IP=$(kubectl get pod <назва> -o jsonpath='{.status.podIP}')`.
   </details>

2. **Навіщо використовувати `kubectl wait` у скриптах?**
   <details>
   <summary>Відповідь</summary>
   Щоб призупинити виконання скрипта, поки ресурс не досягне потрібного стану (наприклад, поки под не стане Ready). Це надійніше, ніж використовувати `sleep`.
   </details>

3. **Як передати список усіх подів, що мають мітку `app=nginx`, команді `kubectl delete` через канал (pipe)?**
   <details>
   <summary>Відповідь</summary>
   `kubectl get pods -l app=nginx -o name | xargs kubectl delete`.
   </details>

4. **Який прапор `kubectl` дозволяє побачити, що зробить команда, не виконуючи її насправді?**
   <details>
   <summary>Відповідь</summary>
   `--dry-run=client`. У поєднанні з `-o yaml` це дозволяє генерувати маніфести в скриптах.
   </details>

---

## Практична вправа

**Завдання**: Написати скрипт для збору логів усіх подів з помилками.

1. Створіть файл `error-logs.sh`:
```bash
#!/bin/bash
set -euo pipefail

# Знайти всі поди з помилками
ERR_PODS=$(kubectl get pods --no-headers | awk '$3 != "Running" && $3 != "Completed" {print $1}')

if [[ -z "$ERR_PODS" ]]; then
    echo "Помилок не знайдено."
    exit 0
fi

for POD in $ERR_PODS; do
    echo "=== Логи для $POD ==="
    kubectl logs "$POD" --tail=20 || echo "Не вдалося отримати логи"
    echo ""
done
```
2. Зробіть його виконуваним та протестуйте.

**Критерії успіху**: Скрипт автоматично знаходить проблемні поди та виводить останні рядки їхніх логів.

---

## Підсумок

- **kubectl** ідеально підходить для скриптів.
- Використовуйте **jsonpath** для витягування даних.
- Завжди ставте **timeouts** на операції очікування.
- Додавайте **dry-run** режим для безпечного тестування автоматизації.

---

**Вітаємо!** Ви завершили великий розділ **«Операції та Скрипти»**. Тепер ви не просто користувач Linux, а інженер, здатний автоматизувати складні хмарні системи.

**Далі**: [Розділ 8: Просунуте адміністрування](/uk/linux/) — або переходьте до вивчення **[Сертифікацій Kubernetes](../../../../k8s/)**.
