# Підсумковий тест частини 1: Архітектура кластера

> **Мета**: Перевірте свої знання з усіх модулів частини 1 перед переходом до частини 2.
>
> **Цільовий результат**: 80% (20/25) для впевненого переходу
>
> **Обмеження часу**: 20 хвилин

---

## Інструкції

Дайте відповідь на всі 25 запитань без звертання до модулів. Цей тест охоплює 25% змісту іспиту CKA.

---

## Запитання

### Площина управління (Модуль 1.1)

1. **Який компонент зберігає весь стан кластера?**
   <details>
   <summary>Відповідь</summary>
   etcd — розподілене сховище ключ-значення
   </details>

2. **Який компонент вирішує, на якому вузлі запускатиметься Под?**
   <details>
   <summary>Відповідь</summary>
   kube-scheduler
   </details>

3. **Який компонент створює Поди, коли ви створюєте Deployment?**
   <details>
   <summary>Відповідь</summary>
   kube-controller-manager (зокрема контролер Deployment та контролер ReplicaSet)
   </details>

4. **Яка команда перевіряє стан API-сервера?**
   <details>
   <summary>Відповідь</summary>
   `kubectl get --raw='/readyz'` або `kubectl get --raw='/healthz'`
   </details>

### Інтерфейси розширення (Модуль 1.2)

5. **Який інтерфейс реалізує Calico?**
   <details>
   <summary>Відповідь</summary>
   CNI (Container Network Interface)
   </details>

6. **Який інтерфейс реалізує containerd?**
   <details>
   <summary>Відповідь</summary>
   CRI (Container Runtime Interface)
   </details>

7. **Яка команда виводить список контейнерів через CRI?**
   <details>
   <summary>Відповідь</summary>
   `crictl ps` (або `sudo crictl ps`)
   </details>

8. **Де зазвичай зберігаються конфігурації CNI?**
   <details>
   <summary>Відповідь</summary>
   `/etc/cni/net.d/`
   </details>

### Helm (Модуль 1.3)

9. **Яка команда встановлює чарт із користувацькими значеннями?**
   <details>
   <summary>Відповідь</summary>
   `helm install <release> <chart> -f values.yaml` або `--set key=value`
   </details>

10. **Як оновити реліз, зберігаючи наявні значення?**
    <details>
    <summary>Відповідь</summary>
    `helm upgrade <release> <chart> --reuse-values`
    </details>

11. **Яка команда відкочує до попередньої ревізії релізу?**
    <details>
    <summary>Відповідь</summary>
    `helm rollback <release> <revision>`
    </details>

12. **Як переглянути всі налаштовувані значення для чарту?**
    <details>
    <summary>Відповідь</summary>
    `helm show values <chart>`
    </details>

### Kustomize (Модуль 1.4)

13. **Яка команда попередньо переглядає вивід Kustomize без застосування?**
    <details>
    <summary>Відповідь</summary>
    `kubectl kustomize <directory>` або `kustomize build <directory>`
    </details>

14. **Який прапорець застосовує Kustomize безпосередньо через kubectl?**
    <details>
    <summary>Відповідь</summary>
    `-k` (наприклад, `kubectl apply -k ./overlay/`)
    </details>

15. **У Kustomize, яка різниця між base та overlay?**
    <details>
    <summary>Відповідь</summary>
    Base містить оригінальні ресурси; overlay містить модифікації для конкретного середовища, які посилаються на base
    </details>

### CRD та Оператори (Модуль 1.5)

16. **Яка команда виводить список усіх Custom Resource Definitions?**
    <details>
    <summary>Відповідь</summary>
    `kubectl get crd`
    </details>

17. **Що необхідно створити перш ніж можна створювати екземпляри користувацьких ресурсів?**
    <details>
    <summary>Відповідь</summary>
    Спершу має існувати CRD (CustomResourceDefinition)
    </details>

18. **Яка різниця між CRD та CR?**
    <details>
    <summary>Відповідь</summary>
    CRD визначає схему/структуру; CR (Custom Resource) — це екземпляр цього типу
    </details>

### RBAC (Модуль 1.6)

19. **Яка різниця між Role та ClusterRole?**
    <details>
    <summary>Відповідь</summary>
    Role обмежена простором імен; ClusterRole діє на рівні всього кластера
    </details>

20. **Яка команда перевіряє, чи може користувач виконати дію?**
    <details>
    <summary>Відповідь</summary>
    `kubectl auth can-i <verb> <resource> --as=<user>`
    </details>

21. **Як надати ServiceAccount дозволи у просторі імен?**
    <details>
    <summary>Відповідь</summary>
    Створити Role та RoleBinding, які посилаються на ServiceAccount
    </details>

22. **Які три типи суб'єктів існують у прив'язках RBAC?**
    <details>
    <summary>Відповідь</summary>
    User, Group, ServiceAccount
    </details>

### kubeadm (Модуль 1.7)

23. **Яка команда запобігає плануванню нових Подів на вузлі?**
    <details>
    <summary>Відповідь</summary>
    `kubectl cordon <node>`
    </details>

24. **Яка різниця між cordon та drain?**
    <details>
    <summary>Відповідь</summary>
    Cordon лише запобігає розміщенню нових Подів; drain також виселяє наявні Поди
    </details>

25. **Яка команда генерує новий токен приєднання для робочих вузлів?**
    <details>
    <summary>Відповідь</summary>
    `kubeadm token create --print-join-command`
    </details>

---

## Оцінювання

Підрахуйте правильні відповіді:

| Результат | Оцінка | Дія |
|-----------|--------|-----|
| 23-25 | Відмінно | Готові до частини 2 |
| 20-22 | Добре | Перегляньте пропущені теми, потім продовжуйте |
| 16-19 | Задовільно | Перечитайте відповідні модулі, повторіть тест |
| <16 | Потребує роботи | Виконайте всі вправи модулів знову |

---

## Огляд слабких місць

Якщо ви пропустили запитання, перегляньте ці конкретні розділи:

- Q1-4: Модуль 1.1 — Площина управління
- Q5-8: Модуль 1.2 — Інтерфейси розширення
- Q9-12: Модуль 1.3 — Helm
- Q13-15: Модуль 1.4 — Kustomize
- Q16-18: Модуль 1.5 — CRD та Оператори
- Q19-22: Модуль 1.6 — RBAC
- Q23-25: Модуль 1.7 — kubeadm

---

## Практична оцінка

Перед переходом переконайтеся, що ви можете виконати це без допомоги:

- [ ] Створити повне налаштування RBAC (SA, Role, RoleBinding) менш ніж за 3 хвилини
- [ ] Встановити, оновити та відкотити реліз Helm
- [ ] Створити overlay Kustomize з простором імен та патчами
- [ ] Створити простий CRD та користувацький ресурс
- [ ] Виконати cordon, drain та uncordon вузла
- [ ] Згенерувати YAML для будь-якого ресурсу за допомогою `kubectl ... $do`

---

## Наступні кроки

Коли ви набрали 20/25 або вище та завершили практичну оцінку:

→ Переходьте до [Частина 2: Робочі навантаження та планування](../part2-workloads-scheduling/)

Це охоплює 15% іспиту та безпосередньо базується на концепціях архітектури кластера.
