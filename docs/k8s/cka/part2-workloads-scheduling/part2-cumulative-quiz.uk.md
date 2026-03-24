# Частина 2 — Підсумковий тест: Робочі навантаження та планування

> **Мета**: Перевірити засвоєння матеріалу з усіх модулів Частини 2 перед переходом до Частини 3.
>
> **Цільовий бал**: 80% (22/28), щоб впевнено рухатися далі
>
> **Обмеження часу**: 20 хвилин

---

## Інструкції

Дайте відповідь на всі 28 запитань, не заглядаючи в модулі. Цей тест охоплює 15% змісту іспиту CKA.

---

## Запитання

### Поди — поглиблений розбір (Модуль 2.1)

1. **Який найшвидший спосіб створити YAML-шаблон Пода без його застосування?**
   <details>
   <summary>Відповідь</summary>
   `kubectl run <name> --image=<image> --dry-run=client -o yaml`
   </details>

2. **Який тип контейнера виконується до завершення перед запуском основних контейнерів?**
   <details>
   <summary>Відповідь</summary>
   Init-контейнери
   </details>

3. **Який тип проби визначає, чи повинен контейнер отримувати трафік?**
   <details>
   <summary>Відповідь</summary>
   Readiness probe (проба готовності)
   </details>

4. **Як контейнери в одному Поді спілкуються між собою?**
   <details>
   <summary>Відповідь</summary>
   Через localhost (вони поділяють один мережевий простір імен)
   </details>

### Деплойменти та ReplicaSets (Модуль 2.2)

5. **Яка команда створює Деплоймент із 3 репліками?**
   <details>
   <summary>Відповідь</summary>
   `kubectl create deployment <name> --image=<image> --replicas=3`
   </details>

6. **Яка команда оновлює образ Деплойменту?**
   <details>
   <summary>Відповідь</summary>
   `kubectl set image deployment/<name> <container>=<new-image>`
   </details>

7. **Яка команда показує історію розгортань для Деплойменту?**
   <details>
   <summary>Відповідь</summary>
   `kubectl rollout history deployment/<name>`
   </details>

8. **Яке значення за замовчуванням має параметр maxUnavailable у стратегії rolling update?**
   <details>
   <summary>Відповідь</summary>
   25%
   </details>

### DaemonSets та StatefulSets (Модуль 2.3)

9. **Який тип робочого навантаження забезпечує один Под на кожному вузлі?**
   <details>
   <summary>Відповідь</summary>
   DaemonSet
   </details>

10. **Який тип Service потрібен для StatefulSets?**
    <details>
    <summary>Відповідь</summary>
    Headless Service (clusterIP: None)
    </details>

11. **У StatefulSet з іменем "web" і 3 репліками — яке ім'я хоста першого Пода?**
    <details>
    <summary>Відповідь</summary>
    web-0
    </details>

12. **Яке поле StatefulSet створює окремі PVC для кожного Пода?**
    <details>
    <summary>Відповідь</summary>
    volumeClaimTemplates
    </details>

### Jobs та CronJobs (Модуль 2.4)

13. **Яке поле змушує Job виконувати 5 задач паралельно?**
    <details>
    <summary>Відповідь</summary>
    `parallelism: 5`
    </details>

14. **Який розклад CronJob означає "щодня опівночі"?**
    <details>
    <summary>Відповідь</summary>
    `0 0 * * *`
    </details>

15. **Яке поле Job контролює кількість повторних спроб для невдалого Пода?**
    <details>
    <summary>Відповідь</summary>
    `backoffLimit`
    </details>

16. **Яку restartPolicy потрібно використовувати для Подів у Job?**
    <details>
    <summary>Відповідь</summary>
    `Never` або `OnFailure` (не `Always`)
    </details>

### Керування ресурсами (Модуль 2.5)

17. **У чому різниця між requests та limits для ресурсів?**
    <details>
    <summary>Відповідь</summary>
    Requests — гарантований мінімум (використовується для планування). Limits — максимально дозволений обсяг (застосовується під час виконання).
    </details>

18. **Який клас QoS отримує Под, коли requests дорівнюють limits для всіх контейнерів?**
    <details>
    <summary>Відповідь</summary>
    Guaranteed
    </details>

19. **Який ресурс встановлює квоти на рівні простору імен для CPU/пам'яті?**
    <details>
    <summary>Відповідь</summary>
    ResourceQuota
    </details>

20. **Що відбувається, коли контейнер перевищує свій ліміт пам'яті?**
    <details>
    <summary>Відповідь</summary>
    Контейнер отримує OOMKill (примусове завершення)
    </details>

### Планування (Модуль 2.6)

21. **Яке поле Пода призначає його на вузол із певною міткою?**
    <details>
    <summary>Відповідь</summary>
    `nodeSelector`
    </details>

22. **Яка команда додає taint до вузла?**
    <details>
    <summary>Відповідь</summary>
    `kubectl taint nodes <node> key=value:effect` (наприклад, `kubectl taint nodes node1 dedicated=gpu:NoSchedule`)
    </details>

23. **Який ефект tolerations дозволяє планування, але віддає перевагу іншим вузлам?**
    <details>
    <summary>Відповідь</summary>
    `PreferNoSchedule`
    </details>

24. **У чому різниця між requiredDuringScheduling та preferredDuringScheduling?**
    <details>
    <summary>Відповідь</summary>
    Required — жорстка вимога (Под не буде заплановано, якщо умова не виконана). Preferred — м'яка вимога (планувальник намагається, але розмістить Под в іншому місці за потреби).
    </details>

### ConfigMaps та Secrets (Модуль 2.7)

25. **Яка команда створює ConfigMap із літеральних значень?**
    <details>
    <summary>Відповідь</summary>
    `kubectl create configmap <name> --from-literal=key=value`
    </details>

26. **Що відбувається зі змінними середовища, коли ви оновлюєте ConfigMap?**
    <details>
    <summary>Відповідь</summary>
    Вони не оновлюються — Под потрібно перезапустити
    </details>

27. **Як декодувати значення Secret у форматі base64?**
    <details>
    <summary>Відповідь</summary>
    `kubectl get secret <name> -o jsonpath='{.data.<key>}' | base64 -d`
    </details>

28. **Що не так із `echo 'password' | base64` для створення Secrets?**
    <details>
    <summary>Відповідь</summary>
    Команда додає символ нового рядка. Використовуйте натомість `echo -n 'password' | base64`.
    </details>

---

## Оцінювання

Підрахуйте правильні відповіді:

| Бал | Оцінка | Дія |
|-----|--------|-----|
| 25–28 | Відмінно | Готові до Частини 3 |
| 20–24 | Добре | Перегляньте пропущені теми, потім рухайтеся далі |
| 15–19 | Задовільно | Перечитайте відповідні модулі, повторіть тест |
| <15 | Потрібно допрацювати | Виконайте всі вправи модулів ще раз |

---

## Огляд слабких місць

Якщо ви пропустили запитання, перегляньте відповідні розділи:

- Q1–4: Модуль 2.1 — Поди — поглиблений розбір
- Q5–8: Модуль 2.2 — Деплойменти та ReplicaSets
- Q9–12: Модуль 2.3 — DaemonSets та StatefulSets
- Q13–16: Модуль 2.4 — Jobs та CronJobs
- Q17–20: Модуль 2.5 — Керування ресурсами
- Q21–24: Модуль 2.6 — Планування
- Q25–28: Модуль 2.7 — ConfigMaps та Secrets

---

## Практична оцінка

Перед тим як рухатися далі, переконайтеся, що ви можете зробити це без допомоги:

- [ ] Створити багатоконтейнерний Под зі спільним томом менш ніж за 3 хвилини
- [ ] Розгорнути та масштабувати Деплоймент, а потім відкотити до попередньої ревізії
- [ ] Створити Job, що виконує 5 паралельних задач із 10 загальними завершеннями
- [ ] Налаштувати Под із requests, limits для ресурсів та readiness probe
- [ ] Запланувати Под на конкретний вузол за допомогою nodeSelector
- [ ] Додати taint до вузла та створити Под із відповідним toleration
- [ ] Створити ConfigMaps та Secrets, підключити їх як змінні середовища та volume mounts
- [ ] Декодувати значення Secret із командного рядка

---

## Швидкісні вправи

Засікайте час на цих типових завданнях іспиту:

| Завдання | Цільовий час |
|----------|-------------|
| Створити Под із певним образом | 15 секунд |
| Створити Деплоймент із 3 репліками | 20 секунд |
| Оновити образ Деплойменту | 15 секунд |
| Створити ConfigMap із літеральних значень | 20 секунд |
| Створити Secret та змонтувати в Под | 90 секунд |
| Додати ліміти ресурсів до наявного Пода | 60 секунд |
| Створити CronJob, що запускається щогодини | 45 секунд |

Якщо ви не вкладаєтеся в ці часові рамки, потренуйтеся у відповідних розділах кожного модуля.

---

## Наступні кроки

Коли ви набрали 20/28 або більше та виконали практичну оцінку:

> Переходьте до [Частина 3: Сервіси та мережа](../part3-services-networking/README.md)

Ця частина охоплює 20% іспиту та навчає, як Поди взаємодіють усередині та за межами кластера.

---

## Частина 2 — Короткий довідник

### Основні команди

```bash
# Поди
k run <name> --image=<img> $do           # Згенерувати YAML Пода
k run <name> --image=<img> --restart=Never # Створити Pod типу Job

# Деплойменти
k create deploy <name> --image=<img> --replicas=N
k set image deploy/<name> <container>=<new-image>
k rollout status/history/undo deploy/<name>
k scale deploy/<name> --replicas=N

# Jobs
k create job <name> --image=<img> -- <command>
k create cronjob <name> --image=<img> --schedule="*/5 * * * *" -- <cmd>

# Конфігурація
k create configmap <name> --from-literal=k=v --from-file=path
k create secret generic <name> --from-literal=k=v
k get secret <name> -o jsonpath='{.data.<key>}' | base64 -d

# Планування
k taint nodes <node> key=value:NoSchedule
k taint nodes <node> key=value:NoSchedule-  # Видалити taint
k label nodes <node> key=value
```

### Ключові YAML-шаблони

```yaml
# Керування ресурсами
resources:
  requests:
    memory: "128Mi"
    cpu: "250m"
  limits:
    memory: "256Mi"
    cpu: "500m"

# Проби
readinessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 10

# Вибір вузла
nodeSelector:
  disk: ssd

# Tolerations
tolerations:
- key: "dedicated"
  operator: "Equal"
  value: "gpu"
  effect: "NoSchedule"

# ConfigMap як змінні середовища
envFrom:
- configMapRef:
    name: app-config

# Secret як том
volumes:
- name: secret-vol
  secret:
    secretName: app-secret
```
