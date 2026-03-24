# Модуль 5.5: Усунення мережевих несправностей

> **Складність**: `[COMPLEX]` — Кілька рівнів для налагодження
>
> **Час на виконання**: 50–60 хвилин
>
> **Передумови**: Модуль 5.1 (Методологія), Модуль 3.1–3.7 (Сервіси та мережа)

---

## Чому цей модуль важливий

Мережеві проблеми — одні з найскладніших для усунення, оскільки вони можуть виникнути на кількох рівнях — мережа Підів, мережа Сервісів, DNS, CNI або зовнішнє з'єднання. Систематичний підхід є критичним. На іспиті CKA питання з усунення мережевих несправностей поширені й часто приносять високі бали.

> **Аналогія з автомагістральною системою**
>
> Уявіть мережу кластера як систему автомагістралей. Під'и — це автомобілі з унікальними адресами (IP). Сервіси — це відомі з'їзди, що перенаправляють трафік до кількох пунктів призначення. DNS — це GPS, що переводить імена в адреси. NetworkPolicies — це пропускні пункти, що контролюють хто може в'їхати. Коли трафік не рухається — потрібно перевірити кожний контрольний пункт.

---

## Що ви дізнаєтесь

Після завершення цього модуля ви зможете:
- Діагностувати проблеми зв'язку Під-Під
- Усувати проблеми з DNS
- Виправляти проблеми зв'язку Сервісів
- Визначати блокування NetworkPolicy
- Налагоджувати проблеми CNI

---

## Чи знали ви?

- **Кожний Під отримує IP**: на відміну від Docker, Під'и Kubernetes мають власні IP-адреси — маппінг портів не потрібен
- **DNS-запити йдуть через CoreDNS**: весь DNS-резолвінг кластера проходить через Під'и CoreDNS у kube-system
- **NetworkPolicies адитивні**: якщо будь-яка політика дозволяє трафік — він дозволений. Але наявність БУДЬ-ЯКОЇ політики створює заборону за замовчуванням
- **Сервіси використовують kube-proxy**: IP-адреси Сервісів — віртуальні, kube-proxy програмує правила iptables/IPVS для маршрутизації трафіку

---

## Частина 1: Мережева модель Kubernetes

### 1.1 Мережеві рівні

```
┌──────────────────────────────────────────────────────────────┐
│                МЕРЕЖЕВІ РІВНІ KUBERNETES                      │
│                                                               │
│   Рівень 4: Зовнішній доступ                                 │
│   ┌─────────────────────────────────────────────────────┐    │
│   │ Ingress / LoadBalancer / NodePort                    │    │
│   └─────────────────────────────────────────────────────┘    │
│                            │                                  │
│   Рівень 3: Мережа Сервісів│                                 │
│   ┌─────────────────────────────────────────────────────┐    │
│   │ ClusterIP Сервіси (віртуальні IP через kube-proxy)  │    │
│   └─────────────────────────────────────────────────────┘    │
│                            │                                  │
│   Рівень 2: DNS            │                                  │
│   ┌─────────────────────────────────────────────────────┐    │
│   │ CoreDNS (service.namespace.svc.cluster.local)       │    │
│   └─────────────────────────────────────────────────────┘    │
│                            │                                  │
│   Рівень 1: Мережа Підів   │                                 │
│   ┌─────────────────────────────────────────────────────┐    │
│   │ CNI плагін (Під-Під, між вузлами)                   │    │
│   └─────────────────────────────────────────────────────┘    │
│                                                               │
│   Усувайте знизу вгору: Під → DNS → Сервіс → Зовнішній     │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 1.2 Швидкий тест з'єднання

```bash
# Створити debug-Під для тестування
k run netshoot --image=nicolaka/netshoot --rm -it --restart=Never -- bash

# Або простіше з busybox
k run debug --image=busybox:1.36 --rm -it --restart=Never -- sh
```

---

## Частина 2: Зв'язок Під-Під

### 2.1 Тестування зв'язку Підів

```bash
# Отримати IP Підів
k get pods -o wide

# Тест з одного Підів до іншого
k exec <source-pod> -- ping -c 3 <target-pod-ip>
k exec <source-pod> -- wget -qO- --timeout=2 http://<target-pod-ip>:<port>
k exec <source-pod> -- nc -zv <target-pod-ip> <port>
```

### 2.2 Симптоми збоїв зв'язку Під-Під

```
┌──────────────────────────────────────────────────────────────┐
│           УСУНЕННЯ НЕСПРАВНОСТЕЙ ЗВ'ЯЗКУ ПІД-ПІД            │
│                                                               │
│   Симптом                          Ймовірна причина          │
│   ─────────────────────────────────────────────────────────  │
│   ping не проходить до жодного     CNI не працює             │
│   Підів                                                      │
│   ping працює, TCP ні              NetworkPolicy або         │
│                                    проблема додатку          │
│   На тому ж вузлі працює,         Проблема CNI між вузлами  │
│   між вузлами ні                                             │
│   Деякі Під'и працюють,           Проблема конкретного      │
│   деякі ні                        Підів/вузла               │
│   Періодичні збої                  Неспівпадіння MTU,        │
│                                    перевантаження            │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 2.3 Діагностика проблем CNI

```bash
# Перевірити чи Під'и CNI працюють
k -n kube-system get pods | grep -E "calico|flannel|weave|cilium"

# Перевірити логи Підів CNI
k -n kube-system logs <cni-pod>

# Перевірити конфігурацію CNI на вузлі
ls -la /etc/cni/net.d/
cat /etc/cni/net.d/*.conf

# Перевірити наявність бінарних файлів CNI
ls -la /opt/cni/bin/
```

### 2.4 Типові проблеми CNI

| Проблема | Симптом | Виправлення |
|----------|---------|-------------|
| Під'и CNI не працюють | Усі Під'и застрягли ContainerCreating | Розгорнути/виправити CNI плагін |
| Конфіг CNI відсутній | Під'и не отримують IP | Перевірити /etc/cni/net.d/ |
| Бінарний файл CNI відсутній | Помилки runtime | Встановити бінарні файли CNI |
| Перетин CIDR | Конфлікти IP | Переналаштувати pod CIDR |
| Неспівпадіння MTU | Періодичні втрати | Вирівняти налаштування MTU |

---

## Частина 3: Усунення несправностей DNS

### 3.1 Огляд DNS Kubernetes

```
┌──────────────────────────────────────────────────────────────┐
│                   ПОТІК РЕЗОЛВІНГУ DNS                        │
│                                                               │
│   Під робить DNS-запит                                       │
│        │                                                      │
│        ▼                                                      │
│   /etc/resolv.conf (вказує на Сервіс kube-dns)              │
│        │                                                      │
│        ▼                                                      │
│   Сервіс kube-dns (зазвичай 10.96.0.10)                     │
│        │                                                      │
│        ▼                                                      │
│   Під'и CoreDNS (у kube-system)                              │
│        │                                                      │
│        ├── Домен кластера (*.svc.cluster.local) → резолвити  │
│        │                                                      │
│        └── Зовнішній домен → перенаправити на upstream DNS    │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 Тестування DNS

```bash
# Перевірити конфігурацію DNS Підів
k exec <pod> -- cat /etc/resolv.conf

# Тест DNS кластера
k exec <pod> -- nslookup kubernetes
k exec <pod> -- nslookup kubernetes.default
k exec <pod> -- nslookup kubernetes.default.svc.cluster.local

# Тест DNS Сервісу
k exec <pod> -- nslookup <service-name>
k exec <pod> -- nslookup <service-name>.<namespace>
k exec <pod> -- nslookup <service-name>.<namespace>.svc.cluster.local

# Тест зовнішнього DNS
k exec <pod> -- nslookup google.com
```

### 3.3 Діагностика проблем DNS

```bash
# Перевірити Під'и CoreDNS
k -n kube-system get pods -l k8s-app=kube-dns
k -n kube-system logs -l k8s-app=kube-dns

# Перевірити Сервіс kube-dns
k -n kube-system get svc kube-dns

# Перевірити ConfigMap CoreDNS
k -n kube-system get configmap coredns -o yaml

# Перевірити endpoints
k -n kube-system get endpoints kube-dns
```

### 3.4 Типові проблеми DNS

| Проблема | Симптом | Діагностика | Виправлення |
|----------|---------|-------------|-------------|
| CoreDNS не працює | Весь DNS збоїть | Перевірити Під'и CoreDNS | Виправити/перезапустити CoreDNS |
| Неправильний nameserver | Тайм-аут DNS | Перевірити /etc/resolv.conf | Виправити конфіг DNS kubelet |
| CoreDNS падає циклічно | Періодичний DNS | Перевірити логи CoreDNS | Виправити виявлення циклу |
| NetworkPolicy блокує | DNS заблоковано | Перевірити політики | Дозволити DNS (порт 53) |
| Проблема ndots | Повільний зовнішній DNS | Перевірити ndots у resolv.conf | Налаштувати dnsConfig |

### 3.5 Виправлення проблем DNS

**CoreDNS не працює**:
```bash
# Перевірити Деплоймент
k -n kube-system get deployment coredns

# Масштабувати за потреби
k -n kube-system scale deployment coredns --replicas=2

# Перевірити проблеми Підів
k -n kube-system describe pod -l k8s-app=kube-dns
```

**Падіння CoreDNS через виявлення циклу**:
```bash
# Перевірити логи на повідомлення «Loop»
k -n kube-system logs -l k8s-app=kube-dns | grep -i loop

# Виправлення: відредагувати ConfigMap CoreDNS
k -n kube-system edit configmap coredns
# Видалити або закоментувати плагін 'loop'
```

**Неправильний resolv.conf**:
```bash
# Перевірити конфіг kubelet для DNS кластера
cat /var/lib/kubelet/config.yaml | grep -A 5 "clusterDNS"

# Має вказувати на IP Сервісу kube-dns
# clusterDNS:
# - 10.96.0.10
```

---

## Частина 4: Усунення несправностей Сервісів

### 4.1 Шлях з'єднання Сервісу

```
┌──────────────────────────────────────────────────────────────┐
│                ШЛЯХ З'ЄДНАННЯ СЕРВІСУ                        │
│                                                               │
│   Клієнтський Під                                            │
│        │                                                      │
│        ▼                                                      │
│   Резолвінг DNS (service.namespace → ClusterIP)              │
│        │                                                      │
│        ▼                                                      │
│   Правила kube-proxy (iptables/IPVS)                         │
│        │                                                      │
│        ▼                                                      │
│   Вибір endpoint (один із бекенд-Підів)                     │
│        │                                                      │
│        ▼                                                      │
│   Цільовий Під                                               │
│                                                               │
│   Кожний крок може збоїти — перевіряйте систематично        │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 4.2 Тестування з'єднання Сервісу

```bash
# Тест за ClusterIP
k exec <pod> -- wget -qO- --timeout=2 http://<service-cluster-ip>:<port>

# Тест за DNS-ім'ям
k exec <pod> -- wget -qO- --timeout=2 http://<service-name>:<port>

# Тест через curl, якщо доступний
k exec <pod> -- curl -s --connect-timeout 2 http://<service-name>:<port>
```

### 4.3 Діагностика проблем Сервісу

```bash
# Перевірити що Сервіс існує і має правильний тип/порти
k get svc <service-name>
k describe svc <service-name>

# КРИТИЧНО: перевірити endpoints
k get endpoints <service-name>
# Порожні endpoints = Сервіс не може знайти Під'и!

# Перевірити що selector збігається з Під'ами
k get svc <service-name> -o jsonpath='{.spec.selector}'
k get pods -l <selector>

# Перевірити чи Під'и Ready
k get pods -l <selector> -o wide
```

### 4.4 Типові проблеми Сервісів

| Проблема | Симптом | Діагностика | Виправлення |
|----------|---------|-------------|-------------|
| Немає endpoints | Connection refused | `k get endpoints` порожній | Виправити selector або створити Під'и |
| Неправильний selector | Endpoints порожні | Порівняти мітки | Виправити selector у Сервісі |
| Неправильний порт | Connection refused | Перевірити port vs targetPort | Виправити маппінг портів |
| Під'и не Ready | Деякі endpoints | Перевірити readiness Підів | Виправити readiness пробу |
| kube-proxy не працює | Усі Сервіси збоять | Перевірити Під'и kube-proxy | Перезапустити kube-proxy |

### 4.5 Виправлення проблем Сервісів

**Немає endpoints — неспівпадіння selector**:
```bash
# Отримати selector Сервісу
k get svc my-service -o jsonpath='{.spec.selector}'
# Вивід: {"app":"myapp"}

# Отримати мітки Підів
k get pods --show-labels

# Якщо не збігаються, виправити:
k patch svc my-service -p '{"spec":{"selector":{"app":"correct-label"}}}'
# Або виправити мітки Підів
```

**Неправильна конфігурація портів**:
```bash
# Перевірити порти Сервісу
k get svc my-service -o yaml | grep -A 10 "ports:"

# Перевірити чи Під слухає на targetPort
k exec <pod> -- netstat -tlnp
# Або
k exec <pod> -- ss -tlnp

# Виправити Сервіс
k patch svc my-service -p '{"spec":{"ports":[{"port":80,"targetPort":8080}]}}'
```

---

## Частина 5: Усунення несправностей NetworkPolicy

### 5.1 Поведінка NetworkPolicy

```
┌──────────────────────────────────────────────────────────────┐
│                  ЛОГІКА NETWORKPOLICY                         │
│                                                               │
│   Немає NetworkPolicy для Підів → Весь трафік дозволений    │
│                                                               │
│   Є NetworkPolicy для Підів → Заборона за замовчуванням:    │
│   ┌─────────────────────────────────────────────────────┐    │
│   │ Правила Ingress: Що може підключатись ДО цього Підів│    │
│   │ Правила Egress:  До чого цей Під може підключатись  │    │
│   │                                                      │    │
│   │ Немає правил ingress → Весь ingress заборонений     │    │
│   │ Немає правил egress  → Весь egress заборонений      │    │
│   └─────────────────────────────────────────────────────┘    │
│                                                               │
│   Політики адитивні: якщо БУДЬ-ЯКА політика дозволяє —      │
│   дозволено                                                  │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### 5.2 Діагностика проблем NetworkPolicy

```bash
# Перелік усіх NetworkPolicies
k get networkpolicy -A

# Перевірити політики в конкретному namespace
k get networkpolicy -n <namespace>

# Дослідити деталі політики
k describe networkpolicy <name> -n <namespace>

# Перевірити які Під'и вибрані
k get networkpolicy <name> -o jsonpath='{.spec.podSelector}'
```

### 5.3 Типові проблеми NetworkPolicy

| Проблема | Симптом | Виправлення |
|----------|---------|-------------|
| Egress блокує DNS | DNS не працює | Дозволити egress до kube-dns (порт 53) |
| Ingress занадто обмежувальний | Connection refused | Перевірити правила ingress, додати джерело |
| Забули namespace | Міжнамеспейсовий блокований | Додати namespaceSelector |
| Неправильний pod selector | Політика не застосована | Виправити мітки podSelector |

### 5.4 Виправлення проблем NetworkPolicy

**Дозволити DNS egress**:
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
spec:
  podSelector: {}  # Усі Під'и
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: kube-system
    ports:
    - protocol: UDP
      port: 53
    - protocol: TCP
      port: 53
```

**Налагодження через тимчасове видалення політики**:
```bash
# Зберегти політику
k get networkpolicy <name> -o yaml > policy-backup.yaml

# Видалити для тесту
k delete networkpolicy <name>

# Тестувати зв'язок
k exec <pod> -- wget -qO- http://<service>

# Відновити
k apply -f policy-backup.yaml
```

---

## Частина 6: Зовнішнє з'єднання

### 6.1 Вихідне з'єднання (Під до інтернету)

```bash
# Тест вихідного з'єднання
k exec <pod> -- wget -qO- --timeout=5 http://example.com

# Якщо не працює, перевірте:
# 1. Резолвінг DNS
k exec <pod> -- nslookup example.com

# 2. Мережевий шлях
k exec <pod> -- ping -c 2 8.8.8.8

# 3. З'єднання на рівні вузла (з вузла)
curl -I http://example.com
```

### 6.2 Вхідне з'єднання (зовнішнє до кластера)

```bash
# Для NodePort Сервісу
curl http://<node-ip>:<node-port>

# Для LoadBalancer (якщо доступний)
k get svc <service> -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
curl http://<lb-ip>

# Для Ingress
curl -H "Host: <hostname>" http://<ingress-ip>
```

### 6.3 Проблеми зовнішнього з'єднання

| Проблема | Перевірте | Виправлення |
|----------|-----------|-------------|
| NAT не працює | iptables вузла | Перевірити CNI, kube-proxy |
| Firewall блокує | Правила хмарного firewall | Відкрити необхідні порти |
| Немає маршруту до інтернету | Маршрутизація вузла | Виправити конфіг мережі вузла |
| LoadBalancer в pending | Cloud controller | Перевірити інтеграцію з хмарою |

---

## Типові помилки

| Помилка | Проблема | Рішення |
|---------|----------|---------|
| Не перевіряти endpoints | Пропуск неспівпадіння selector | Завжди перевіряйте `k get endpoints` |
| Забути DNS у NetPol | DNS ламається з egress-політикою | Дозволити UDP/TCP 53 до kube-system |
| Тестування з неправильного Підів | Різні мережеві політики застосовуються | Тестуйте з реального Підів-джерела |
| Ігнорування readiness Підів | Endpoints відсутні | Перевірте чи Під Ready |
| Плутанина port vs targetPort | З'єднання не працює | Порт Сервісу != порт контейнера |
| Не тестувати покроково | Неможливо ізолювати проблему | Під → DNS → Сервіс → Зовнішній |

---

## Тест

### Q1: Порожні endpoints
Сервіс існує, але `k get endpoints <svc>` показує порожні endpoints. Яка найімовірніша причина?

<details>
<summary>Відповідь</summary>

**Selector Сервісу не збігається з жодними мітками Підів**, або відповідні Під'и не в стані **Ready**.

Кроки налагодження:
```bash
# Отримати selector Сервісу
k get svc <svc> -o jsonpath='{.spec.selector}'
# Знайти Під'и з відповідними мітками
k get pods -l <selector>
# Перевірити чи Під'и Ready
k get pods -l <selector> -o wide
```

</details>

### Q2: Збій DNS
Усі DNS-запити не проходять у Під'ах. Зовнішній DNS (8.8.8.8) доступний. Що ви перевіряєте?

<details>
<summary>Відповідь</summary>

Перевірте **Під'и CoreDNS** у kube-system:
```bash
k -n kube-system get pods -l k8s-app=kube-dns
k -n kube-system logs -l k8s-app=kube-dns
k -n kube-system get endpoints kube-dns
```

Також перевірте що Сервіс kube-dns існує і /etc/resolv.conf Підів вказує на нього.

</details>

### Q3: Поведінка NetworkPolicy за замовчуванням
Ви створюєте NetworkPolicy з `podSelector: {}` і лише правилами ingress. Що станеться з egress-трафіком?

<details>
<summary>Відповідь</summary>

**Egress залишається необмеженим.** NetworkPolicy впливає лише на типи трафіку, вказані в `policyTypes`. Якщо ви вказуєте лише правила ingress і маєте `policyTypes: [Ingress]`, egress не зачіпається.

Однак, якщо `policyTypes: [Ingress, Egress]` але без правил egress — весь egress **заборонений**.

</details>

### Q4: Зв'язок Підів між вузлами
Під'и на тому ж вузлі можуть спілкуватись, але Під'и на різних вузлах — ні. Що, ймовірно, зламано?

<details>
<summary>Відповідь</summary>

**Мережа CNI плагіна між вузлами** не працює. Це може бути:
- Під'и CNI не працюють на всіх вузлах
- Мережеве з'єднання між вузлами заблоковане
- Overlay-мережа (VXLAN/IPinIP) не налаштована
- Неспівпадіння MTU спричиняє втрату пакетів

Перевірте:
```bash
k -n kube-system get pods -o wide | grep <cni-name>
# Перевірте Під'и CNI на кожному вузлі
```

</details>

### Q5: Маппінг портів Сервісу
Сервіс має `port: 80, targetPort: 8080`. Контейнер слухає на 80. Чи працюватиме це?

<details>
<summary>Відповідь</summary>

**Ні.** Сервіс буде маршрутизувати трафік на порт 8080 Підів, але контейнер слухає на 80.

- `port`: порт, через який клієнти звертаються до Сервісу
- `targetPort`: порт на Підові/контейнері

Виправлення: або змініть `targetPort: 80`, або змусьте додаток слухати на 8080.

</details>

### Q6: Цикл CoreDNS
CoreDNS постійно падає з «Loop detected» у логах. Яке виправлення?

<details>
<summary>Відповідь</summary>

Це трапляється коли CoreDNS виявляє, що перенаправляє на себе (часто в середовищах, де /etc/resolv.conf вузла вказує на localhost).

Виправте, відредагувавши ConfigMap CoreDNS:
```bash
k -n kube-system edit configmap coredns
```

Один з варіантів:
1. Видалити рядок з плагіном `loop`
2. Налаштувати явні upstream DNS-сервери замість використання /etc/resolv.conf

</details>

---

## Практична вправа: Усунення мережевих несправностей

### Сценарій

Практика діагностики різних мережевих проблем.

### Підготовка

```bash
# Створити тестовий namespace
k create ns network-lab

# Створити тестовий Деплоймент
k -n network-lab create deployment web --image=nginx:1.25 --replicas=2

# Відкрити як Сервіс
k -n network-lab expose deployment web --port=80

# Створити клієнтський Під
k -n network-lab run client --image=busybox:1.36 --command -- sleep 3600
```

### Завдання 1: Перевірка базового з'єднання

```bash
# Зачекати поки Під'и будуть готові
k -n network-lab get pods -w

# Отримати IP Сервісу та Підів
k -n network-lab get svc,pods -o wide

# Тест від клієнта до Сервісу
k -n network-lab exec client -- wget -qO- --timeout=2 http://web

# Тест DNS-резолвінгу
k -n network-lab exec client -- nslookup web
k -n network-lab exec client -- nslookup web.network-lab.svc.cluster.local
```

### Завдання 2: Перевірка endpoints

```bash
# Перевірити що endpoints існують
k -n network-lab get endpoints web

# Повинні показувати IP Підів web
# Якщо порожні, перевірте:
k -n network-lab get svc web -o jsonpath='{.spec.selector}'
k -n network-lab get pods --show-labels
```

### Завдання 3: Симуляція неспівпадіння selector

```bash
# Зламати Сервіс зміною selector
k -n network-lab patch svc web -p '{"spec":{"selector":{"app":"wrong"}}}'

# Спробувати підключитись (не вдасться)
k -n network-lab exec client -- wget -qO- --timeout=2 http://web

# Перевірити endpoints (повинні бути порожні)
k -n network-lab get endpoints web

# Виправити
k -n network-lab patch svc web -p '{"spec":{"selector":{"app":"web"}}}'

# Перевірити що виправлено
k -n network-lab get endpoints web
k -n network-lab exec client -- wget -qO- --timeout=2 http://web
```

### Завдання 4: Тест NetworkPolicy

```bash
# Застосувати обмежувальну політику
cat <<EOF | k apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
  namespace: network-lab
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
EOF

# Тестувати з'єднання (тепер повинно не працювати)
k -n network-lab exec client -- wget -qO- --timeout=2 http://web

# Перевірити які політики існують
k -n network-lab get networkpolicy

# Видалити політику для відновлення з'єднання
k -n network-lab delete networkpolicy deny-all

# Перевірити відновлення
k -n network-lab exec client -- wget -qO- --timeout=2 http://web
```

### Критерії успіху

- [ ] Перевірили зв'язок Під-Сервіс
- [ ] Підтвердили що DNS-резолвінг працює
- [ ] Зрозуміли зв'язок з endpoints
- [ ] Змоделювали та виправили неспівпадіння selector
- [ ] Спостерігали блокування трафіку NetworkPolicy

### Очищення

```bash
k delete ns network-lab
```

---

## Практичні вправи

### Вправа 1: Перевірка DNS-резолвінгу (30 с)
```bash
# Завдання: Тест DNS з Підів
k exec <pod> -- nslookup kubernetes
```

### Вправа 2: Перевірка endpoints (30 с)
```bash
# Завдання: Переглянути endpoints Сервісу
k get endpoints <service>
```

### Вправа 3: Тест з'єднання Сервісу (1 хв)
```bash
# Завдання: Тест HTTP до Сервісу з Підів
k exec <pod> -- wget -qO- --timeout=2 http://<service>
```

### Вправа 4: Перевірка CoreDNS (1 хв)
```bash
# Завдання: Перевірити що CoreDNS здоровий
k -n kube-system get pods -l k8s-app=kube-dns
k -n kube-system logs -l k8s-app=kube-dns --tail=20
```

### Вправа 5: Перевірка конфігурації DNS Підів (30 с)
```bash
# Завдання: Переглянути конфігурацію DNS Підів
k exec <pod> -- cat /etc/resolv.conf
```

### Вправа 6: Перелік NetworkPolicies (30 с)
```bash
# Завдання: Знайти всі NetworkPolicies у namespace
k get networkpolicy -n <namespace>
```

### Вправа 7: Перевірка Підів CNI (1 хв)
```bash
# Завдання: Перевірити що Під'и CNI працюють
k -n kube-system get pods | grep -E "calico|flannel|weave|cilium"
```

### Вправа 8: Налагодження мережевого з'єднання (2 хв)
```bash
# Завдання: Повне налагодження з'єднання
k exec <pod> -- nslookup <service>     # DNS
k exec <pod> -- nc -zv <service> 80    # TCP
k get endpoints <service>              # Endpoints
```

---

## Наступний модуль

Переходьте до [Модуль 5.6: Усунення несправностей Сервісів](module-5.6-services.uk.md) для глибшого занурення в усунення несправностей Сервісів, Ingress та LoadBalancer.
