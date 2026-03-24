# Частина 5: Усунення несправностей — Кумулятивний тест

> **30% іспиту CKA** | 35 питань | Ціль: 85%+

Цей тест охоплює всі теми усунення несправностей з Частини 5. Перевірте себе перед переходом до пробних іспитів.

---

## Інструкції

1. Дайте відповідь на кожне питання перед розкриттям рішення
2. Відстежуйте свій результат: ___/35
3. Перегляньте теми, де ваш результат нижче 80%
4. Повторіть тест після перегляду слабких місць

---

## Секція 1: Методологія усунення несправностей (5 питань)

### Q1: Перші кроки
Користувач повідомляє «додаток не працює». Яка ваша перша дія з усунення несправностей?

<details>
<summary>Відповідь</summary>

**Визначити симптом конкретно.** Задайте уточнюючі питання:
- Чи працює Під? (`k get pods`)
- Чи доступний Сервіс? (`k get svc, endpoints`)
- Яку помилку вони бачать?

Потім дотримуйтесь фреймворку: Визначити → Ізолювати → Діагностувати → Виправити

</details>

### Q2: Describe vs Logs
Чому слід перевіряти `kubectl describe pod` перед `kubectl logs`?

<details>
<summary>Відповідь</summary>

**Секція Events** у describe часто одразу виявляє проблему без потреби в логах:
- Збої розподілу
- Помилки витягування образів
- Проблеми монтування томів
- Помилки конфігурації

Логи корисні для проблем на рівні додатку, але багато проблем ловляться на рівні Kubernetes першими.

</details>

### Q3: Зберігання подій
Ви досліджуєте проблему, що сталась 3 години тому. Події нічого не показують. Чому?

<details>
<summary>Відповідь</summary>

**Події зникають через 1 годину** за замовчуванням. Докази зникли. Тому важливо:
- Перевіряти події одразу після інцидентів
- Мати рішення для агрегації логів для історичних даних
- Фіксувати повідомлення подій, коли ви їх бачите

</details>

### Q4: Коди виходу
Код виходу контейнера — 137. Що це означає?

<details>
<summary>Відповідь</summary>

Код виходу 137 = 128 + 9 (SIGKILL). Зазвичай означає:
- **OOMKilled** — контейнер перевищив ліміт пам'яті
- Процес був вбитий системою

Перевірте: `k describe pod | grep -i oom` та перевірте ліміти пам'яті.

</details>

### Q5: Порядок усунення несправностей
Перелічіть правильний порядок усунення несправностей для Підів, що застряг у Pending:

<details>
<summary>Відповідь</summary>

1. `k describe pod <pod>` — перевірити секцію Events для повідомлень планувальника
2. Перевірити доступність вузлів: `k get nodes`
3. Перевірити ресурси вузлів: `k describe nodes | grep -A 5 "Allocated resources"`
4. Перевірити taints: `k get nodes -o custom-columns='NAME:.metadata.name,TAINTS:.spec.taints[*].key'`
5. Перевірити nodeSelector/affinity Підів: `k get pod <pod> -o yaml`

</details>

---

## Секція 2: Збої додатків (6 питань)

### Q6: CrashLoopBackOff
Під у CrashLoopBackOff. Який максимальний час затримки між перезапусками?

<details>
<summary>Відповідь</summary>

**5 хвилин (300 секунд)**

Затримка подвоюється: 10с → 20с → 40с → 80с → 160с → 300с (максимум)

Після 10 хвилин успішної роботи лічильник скидається.

</details>

### Q7: Збій витягування образу
Під показує ImagePullBackOff. Перелічіть 3 можливі причини.

<details>
<summary>Відповідь</summary>

1. **Образ не існує** — неправильне ім'я або тег
2. **Помилка автентифікації реєстру** — відсутні або неправильні imagePullSecrets
3. **Реєстр недоступний** — проблеми мережі або firewall
4. **Ліміт запитів** — перевищено ліміти Docker Hub
5. **Приватний реєстр не налаштований** — відсутні облікові дані реєстру

</details>

### Q8: Відсутній ConfigMap
Під застряг у ContainerCreating. Події показують «configmap 'app-config' not found». Виправте.

<details>
<summary>Відповідь</summary>

```bash
# Створити відсутній ConfigMap
k create configmap app-config --from-literal=key=value

# Або якщо маєте дані
k create configmap app-config --from-file=config.yaml

# Перевірити що Під запускається
k get pods -w
```

</details>

### Q9: Попередні логи
Як переглянути логи контейнера, що впав?

<details>
<summary>Відповідь</summary>

```bash
k logs <pod> --previous

# Для багатоконтейнерного Підів
k logs <pod> -c <container> --previous
```

Це показує логи попереднього екземпляра контейнера перед його загибеллю.

</details>

### Q10: Відкат Деплоймента
Розгортання Деплоймента застрягло з новими Під'ами, що збоять. Яке найшвидше виправлення?

<details>
<summary>Відповідь</summary>

```bash
k rollout undo deployment/<name>
```

Це одразу відкотить до попередньої робочої версії. Дослідіть проблему пізніше.

</details>

### Q11: OOMKilled
Під постійно отримує OOMKilled. Як перевірити та виправити?

<details>
<summary>Відповідь</summary>

```bash
# Перевірити
k describe pod <pod> | grep -i oom
k get pod <pod> -o jsonpath='{.status.containerStatuses[0].lastState.terminated.reason}'

# Перевірити поточний ліміт
k get pod <pod> -o jsonpath='{.spec.containers[0].resources.limits.memory}'

# Виправити збільшенням ліміту
k patch deployment <name> -p '{"spec":{"template":{"spec":{"containers":[{"name":"<container>","resources":{"limits":{"memory":"512Mi"}}}]}}}}'
```

</details>

---

## Секція 3: Збої площини управління (5 питань)

### Q12: Розташування статичних Підів
Де зберігаються маніфести статичних Підів площини управління в кластерах kubeadm?

<details>
<summary>Відповідь</summary>

```
/etc/kubernetes/manifests/
```

Містить:
- kube-apiserver.yaml
- kube-scheduler.yaml
- kube-controller-manager.yaml
- etcd.yaml

</details>

### Q13: API-сервер не працює
Команди kubectl не відповідають. Ви підключились через SSH до площини управління. Що перевіряєте першим?

<details>
<summary>Відповідь</summary>

```bash
# Перевірити чи контейнер API-сервера працює
crictl ps | grep kube-apiserver

# Якщо не працює
crictl ps -a | grep kube-apiserver  # Перевірити чи існує
journalctl -u kubelet | grep apiserver  # Перевірити логи kubelet

# Перевірити маніфест
cat /etc/kubernetes/manifests/kube-apiserver.yaml
```

</details>

### Q14: Планувальник vs Controller Manager
Нові Під'и залишаються в Pending, але Деплойменти показують правильну кількість реплік. Який компонент збоїть?

<details>
<summary>Відповідь</summary>

**Планувальник**

- Controller manager створює ReplicaSets (працює — правильна кількість реплік)
- Планувальник призначає Під'и на вузли (збоїть — Під'и застрягли в Pending)

</details>

### Q15: Здоров'я etcd
Напишіть команду для перевірки здоров'я кластера etcd.

<details>
<summary>Відповідь</summary>

```bash
ETCDCTL_API=3 etcdctl endpoint health \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key
```

</details>

### Q16: Прострочення сертифікатів
Як перевірити чи сертифікати Kubernetes прострочені?

<details>
<summary>Відповідь</summary>

```bash
kubeadm certs check-expiration
```

Для оновлення:
```bash
kubeadm certs renew all
```

</details>

---

## Секція 4: Збої робочих вузлів (5 питань)

### Q17: Вузол NotReady
Вузол показує статус NotReady. Яка ваша послідовність усунення несправностей через SSH?

<details>
<summary>Відповідь</summary>

```bash
ssh <node>

# 1. Перевірити kubelet
sudo systemctl status kubelet
sudo journalctl -u kubelet -n 50

# 2. Перевірити container runtime
sudo systemctl status containerd
sudo crictl ps

# 3. Перевірити мережу до API-сервера
curl -k https://<api-server>:6443/healthz

# 4. Перевірити місце на диску
df -h
```

</details>

### Q18: kubelet не працює
Як запустити kubelet та забезпечити його запуск при завантаженні?

<details>
<summary>Відповідь</summary>

```bash
sudo systemctl start kubelet
sudo systemctl enable kubelet
sudo systemctl status kubelet
```

</details>

### Q19: crictl vs kubectl
Коли використовувати crictl замість kubectl?

<details>
<summary>Відповідь</summary>

Використовуйте **crictl** коли:
- kubelet або API-сервер не працює
- kubectl не працюватиме
- Налагодження на рівні container runtime
- Вузол NotReady

crictl спілкується безпосередньо з containerd, обминаючи Kubernetes API.

</details>

### Q20: Дренування вузла
Яка команда для безпечного дренування вузла для обслуговування?

<details>
<summary>Відповідь</summary>

```bash
k drain <node> --ignore-daemonsets --delete-emptydir-data
```

Після обслуговування:
```bash
k uncordon <node>
```

</details>

### Q21: MemoryPressure
Вузол показує MemoryPressure=True. Які наслідки?

<details>
<summary>Відповідь</summary>

1. **Нові Під'и не розподіляються** на цей вузол
2. **Існуючі Під'и можуть бути евіктовані** (починаючи з BestEffort, потім Burstable)
3. Вузол позначений як такий, що має тиск, в умовах

Виправлення: звільніть пам'ять евікцією Підів, вбиванням процесів або додаванням потужностей.

</details>

---

## Секція 5: Усунення мережевих несправностей (6 питань)

### Q22: Тест DNS-резолвінгу
Як перевірити DNS-резолвінг зсередини Підів?

<details>
<summary>Відповідь</summary>

```bash
# Тест DNS кластера
k exec <pod> -- nslookup kubernetes

# Тест DNS Сервісу
k exec <pod> -- nslookup <service-name>

# Тест зовнішнього DNS
k exec <pod> -- nslookup google.com

# Перевірити конфіг DNS
k exec <pod> -- cat /etc/resolv.conf
```

</details>

### Q23: Усунення несправностей CoreDNS
Усі DNS-запити не проходять. Що ви перевіряєте?

<details>
<summary>Відповідь</summary>

```bash
# Перевірити Під'и CoreDNS
k -n kube-system get pods -l k8s-app=kube-dns

# Перевірити логи CoreDNS
k -n kube-system logs -l k8s-app=kube-dns

# Перевірити Сервіс kube-dns
k -n kube-system get svc kube-dns
k -n kube-system get endpoints kube-dns
```

</details>

### Q24: Порожні endpoints
Сервіс існує, але `k get endpoints <svc>` показує `<none>`. Причина?

<details>
<summary>Відповідь</summary>

**Неспівпадіння selector** — selector Сервісу не збігається з жодними мітками Підів, або відповідні Під'и не Ready.

```bash
# Перевірити selector
k get svc <svc> -o jsonpath='{.spec.selector}'

# Знайти відповідні Під'и
k get pods -l <selector>

# Перевірити чи Під'и Ready
k get pods -l <selector> -o wide
```

</details>

### Q25: Зв'язок між вузлами
Під'и на тому ж вузлі спілкуються, але між вузлами ні. Що, ймовірно, зламано?

<details>
<summary>Відповідь</summary>

**Мережа CNI плагіна між вузлами** не працює:
- Під'и CNI не працюють на всіх вузлах
- Мережеве з'єднання між вузлами заблоковане
- Overlay-мережа (VXLAN/IPinIP) неправильно налаштована
- Неспівпадіння MTU

```bash
k -n kube-system get pods -o wide | grep <cni-name>
```

</details>

### Q26: Поведінка NetworkPolicy за замовчуванням
Ви створюєте NetworkPolicy, що вибирає Під'и, лише з правилами ingress. Що станеться з egress?

<details>
<summary>Відповідь</summary>

Залежить від `policyTypes`:
- Якщо `policyTypes: [Ingress]` тільки → Egress **необмежений**
- Якщо `policyTypes: [Ingress, Egress]` без правил egress → Весь egress **заборонений**

NetworkPolicies впливають лише на типи трафіку, вказані в policyTypes.

</details>

### Q27: Усунення несправностей CNI
Під'и застрягли в ContainerCreating з «network not ready». Що ви перевіряєте?

<details>
<summary>Відповідь</summary>

```bash
# Перевірити Під'и CNI
k -n kube-system get pods | grep -E "calico|flannel|weave|cilium"

# Перевірити конфігурацію CNI на вузлі
ls /etc/cni/net.d/

# Перевірити бінарні файли CNI
ls /opt/cni/bin/

# Перевірити логи Підів CNI
k -n kube-system logs <cni-pod>
```

</details>

---

## Секція 6: Усунення несправностей Сервісів (4 питання)

### Q28: Port vs TargetPort
Сервіс має `port: 80, targetPort: 8080`. Контейнер слухає на 80. Чи працюватиме це?

<details>
<summary>Відповідь</summary>

**Ні.** Трафік приходить на порт Сервісу 80, але перенаправляється на порт Підів 8080, де нічого не слухає.

Виправлення: змініть `targetPort: 80` або змусьте контейнер слухати на 8080.

</details>

### Q29: NodePort не працює
NodePort працює зсередини кластера, але не ззовні. Що не так?

<details>
<summary>Відповідь</summary>

**Firewall або security group** блокує порт ззовні:
- iptables вузла
- Cloud security groups
- Network ACL

NodePort має бути відкритий на всіх вузлах з зовнішньої мережі.

</details>

### Q30: LoadBalancer у Pending
Сервіс LoadBalancer залишається `<pending>` для EXTERNAL-IP. Чому?

<details>
<summary>Відповідь</summary>

Немає cloud controller або MetalLB:
- Cloud controller manager не встановлений
- Неправильні хмарні облікові дані
- Немає підтримки LoadBalancer (bare metal без MetalLB)

```bash
k -n kube-system get pods | grep cloud-controller
k get events --field-selector involvedObject.name=<svc>
```

</details>

### Q31: kube-proxy
Усі Сервіси перестали працювати на вузлі. Яка ймовірна проблема?

<details>
<summary>Відповідь</summary>

**kube-proxy** не працює або неправильно налаштований на цьому вузлі:

```bash
k -n kube-system get pods -l k8s-app=kube-proxy -o wide
k -n kube-system logs -l k8s-app=kube-proxy

# Перевірити правила iptables
sudo iptables -t nat -L KUBE-SERVICES | head
```

</details>

---

## Секція 7: Логування та моніторинг (4 питання)

### Q32: Логи попереднього контейнера
Коли використовувати прапорець `--previous` з kubectl logs?

<details>
<summary>Відповідь</summary>

Коли контейнер **впав і перезапустився** (CrashLoopBackOff). Показує логи попереднього екземпляра перед його загибеллю.

```bash
k logs <pod> --previous
```

</details>

### Q33: Metrics Server
`kubectl top pods` повертає «metrics not available». Як виправити?

<details>
<summary>Відповідь</summary>

**Встановити Metrics Server**:

```bash
# Перевірити чи встановлений
k -n kube-system get pods | grep metrics-server

# Якщо ні, встановити
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

</details>

### Q34: Розташування логів
Де зберігаються логи контейнерів на вузлі?

<details>
<summary>Відповідь</summary>

```
/var/log/containers/<pod>_<namespace>_<container>-<id>.log
```

Це symlinks, якими керує container runtime. kubelet обробляє ротацію логів.

</details>

### Q35: Логи kubelet
Як переглянути логи kubelet на вузлі?

<details>
<summary>Відповідь</summary>

```bash
# SSH на вузол
ssh <node>

# Переглянути логи
journalctl -u kubelet

# Слідкувати за логами
journalctl -u kubelet -f

# Останні помилки
journalctl -u kubelet --since "10 minutes ago" | grep -i error
```

</details>

---

## Оцінювання

| Результат | Оцінка |
|-----------|--------|
| 32–35 (90%+) | Відмінно — Готові до питань з усунення несправностей |
| 28–31 (80–89%) | Добре — Перегляньте пропущені теми |
| 24–27 (70–79%) | Задовільно — Потрібно більше практики |
| <24 (<70%) | Ретельно перегляньте модулі Частини 5 |

**Ваш результат: ___/35 = ___%**

---

## Посібник з перегляду тем

Якщо ви отримали низький результат у конкретних секціях:

| Секція | Модуль для перегляду |
|--------|----------------------|
| Методологія | 5.1 |
| Збої додатків | 5.2 |
| Площина управління | 5.3 |
| Робочі вузли | 5.4 |
| Мережа | 5.5 |
| Сервіси | 5.6 |
| Логування | 5.7 |

---

## Наступні кроки

З завершенням Частини 5 ви охопили:
- Частина 0: Середовище (5 модулів)
- Частина 1: Архітектура кластера (7 модулів) — 25% іспиту
- Частина 2: Робочі навантаження та розподіл (7 модулів) — 15% іспиту
- Частина 3: Сервіси та мережа (7 модулів) — 20% іспиту
- Частина 4: Сховище (5 модулів) — 10% іспиту
- Частина 5: Усунення несправностей (7 модулів) — 30% іспиту

**Усього: 38 модулів, що охоплюють 100% доменів іспиту CKA**

Переходьте до [Частина 6: Пробні іспити](../part6-mock-exams/README.md) для тренування на час в умовах іспиту.
