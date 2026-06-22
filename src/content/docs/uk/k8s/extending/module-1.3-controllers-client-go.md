---
title: "Модуль 1.3: Створення контролерів за допомогою client-go"
slug: "uk/k8s/extending/module-1.3-controllers-client-go"
sidebar:
  order: 4
revision_pending: false
en_commit: "26342c0ca358c92129aa43ee22f0519a67887176"
en_file: "src/content/docs/k8s/extending/module-1.3-controllers-client-go.md"
calque_review:
  reviewed_at: "2026-06-22"
  detector_version: "v2"
  status: "reviewed"
  flags_resolved: 5
  content_sha: "8aa73082acb3b19592fb68638a874fe73eba2a1c218fcf8c4d3af3f19e2dbf0c"
---

> **Складність**: `[СКЛАДНИЙ]` — повна реалізація контролера з нуля.
>
> **Час на проходження**: 5 годин.
>
> **Передумови**: Модуль 1.1 (Поглиблене вивчення API), Модуль 1.2 (Розширені CRD), середній рівень програмування мовою Go.

---

## Результати навчання

Після завершення цього модуля ви зможете:

1. **Створити** повноцінний контролер Kubernetes з нуля, використовуючи Informer'и, Lister'и та Workqueue з client-go.
2. **Реалізувати** цикл узгодження, який створює, оновлює та видаляє дочірні ресурси на основі специфікації власного ресурсу.
3. **Застосувати** посилання на власника (owner references) та збирання сміття, щоб дочірні ресурси автоматично прибиралися після видалення батьківського.
4. **Діагностувати** проблеми контролера, використовуючи запис подій, структуроване логування та метрики повторних спроб черги.

---

## Чому цей модуль важливий

Гіпотетичний сценарій: ваша платформова команда запровадила власний ресурс `WebApp`, щоб прикладні команди могли запросити образ, кількість реплік та порт сервісу, не вивчаючи кожне окреме поле Deployment та Service. API-сервер може зберегти цей об'єкт у сховищі, тому що для нього існує відповідний CRD, але саме лише зберігання не створює Под'ів, не виправляє дрейф конфігурації, не звітує про статус і не прибирає за собою дочірні ресурси. Без контролера, який стояв би за цим API, власний ресурс залишається лише довговічним записом у etcd — нотаткою про намір, — а та операційна обіцянка, що стоїть за оголошеним API, так і не виконується.

Контролер Kubernetes — це той механізм, який перетворює **декларативний намір** на **робочу реальність**. Коли ви створюєте Deployment, саме контролер створює та поступово коригує ReplicaSet'и під ним; а коли за Service змінюються endpoint'и, саме логіка контролера оновлює об'єкти виявлення, якими потім користуються клієнти. API-сервер є джерелом істини для бажаного стану, але контролери — це робітники, які безперервно порівнюють цю істину зі спостережуваним станом кластера й виконують найменшу безпечну дію, потрібну для того, щоб привести два стани до збіжності.

У цьому модулі ви побудуєте повноцінний контролер з нуля, використовуючи лише client-go, без жодного каркасу фреймворку, який приховував би від вас рухомі частини. Власноруч і покроково ви зберете докупи Informer, який спостерігає за ресурсами, Lister, який читає зі спільного кешу, Workqueue, яка буферизує ключі для обробки, цикл узгодження, який створює дочірні ресурси, та поведінку повторних спроб, яка не дає тимчасовим помилкам перерости в повноцінний збій. Kubebuilder та controller-runtime — це продуктивні й корисні інструменти, але якщо спочатку опанувати базовий патерн client-go, ви отримаєте той діагностичний словник, який дозволяє діагностувати згенеровані контролери саме тоді, коли абстракція дає течу й починає протікати.

Аналогія з термостатом корисна саме тому, що вона передає водночас і простоту, і дисципліну узгодження. Ви задаєте бажану температуру, термостат раз за разом спостерігає за поточною температурою в кімнаті й вмикає нагрів або охолодження лише тоді, коли ці два значення між собою різняться. Контролер Kubernetes робить точно те саме зі `spec` та поточними об'єктами кластера; він не повинен покладатися на пам'ять про те, яка саме була остання подія, і його має бути цілком безпечно запускати з тим самим порівнянням багаторазово, скільки б разів це не сталося.

---

## Частина 1: Патерн контролера

### 1.1 Спостерігай-Аналізуй-Дій

Кожен контролер Kubernetes слідує одному й тому самому трикроковому циклу: спостерігати за тим, що зараз існує, аналізувати різницю між бажаним і фактичним станом та діяти лише там, де ця різниця справді потребує зміни. Цей цикл навмисно зроблено нудним і одноманітним, бо надійність походить саме від повторюваності, а не від винахідливості. Якщо контролер можна перезапустити, затримати на якийсь час чи попросити обробити той самий ключ багато разів поспіль, і він усе одно щоразу ухвалить те саме рішення, то він добре пасує до моделі площини управління Kubernetes.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Controller Loop                                   │
│                                                                     │
│   ┌──────────────────────────────────────────────────────────┐     │
│   │                     OBSERVE                               │     │
│   │                                                           │     │
│   │   Informer watches API Server for resource changes        │     │
│   │   Lister reads current state from local cache             │     │
│   │   Event handlers enqueue changed object keys              │     │
│   └────────────────────────┬─────────────────────────────────┘     │
│                            │                                        │
│                            ▼                                        │
│   ┌──────────────────────────────────────────────────────────┐     │
│   │                     ANALYZE                               │     │
│   │                                                           │     │
│   │   Dequeue object key from Workqueue                       │     │
│   │   Read desired state (spec) from cache                    │     │
│   │   Read actual state (owned resources) from cache          │     │
│   │   Compare desired vs actual — what needs to change?       │     │
│   └────────────────────────┬─────────────────────────────────┘     │
│                            │                                        │
│                            ▼                                        │
│   ┌──────────────────────────────────────────────────────────┐     │
│   │                       ACT                                 │     │
│   │                                                           │     │
│   │   Create / Update / Delete child resources                │     │
│   │   Update status subresource                               │     │
│   │   Emit Kubernetes Events                                  │     │
│   │   Re-enqueue on failure (with backoff)                    │     │
│   └──────────────────────────────────────────────────────────┘     │
│                                                                     │
│   Then back to OBSERVE — the loop never ends                       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Спрацьовування за рівнем проти спрацьовування за фронтом

Найважливіший вибір у проєктуванні полягає в тому, що контролери Kubernetes спрацьовують за рівнем (level-triggered), а не за фронтом (edge-triggered). Система зі спрацьовуванням за фронтом реагує на сам факт того, що сталася подія `ADDED`, `MODIFIED` чи `DELETED`, тож пропущена подія може назавжди залишити систему в неправильному стані. Контролер зі спрацьовуванням за рівнем реагує на поточний рівень світу: бажаний стан з батьківського ресурсу, фактичний стан з дочірніх та розрив між ними.

| Підхід | На що реагує | Проблема |
|----------|----------|---------|
| **За фронтом** | Окремі події (ADDED, MODIFIED, DELETED) | Якщо пропустити подію, стан розходиться назавжди |
| **За рівнем** | Поточна різниця станів (бажаний проти фактичного) | Самовідновлення: завжди збігається незалежно від пропущених подій |

Контролери Kubernetes спрацьовують **за рівнем**, тож ваша функція узгодження не повинна питати, яка саме подія сталася. Вона має питати, який зараз бажаний стан, які фактичні ресурси існують у цю мить та яка мінімальна операція API зробила б обидва стани однаковими. Саме ця звичка дозволяє контролерам переживати пропущені події watch, перезапуски процесів, усування дублікатів у черзі та ручну зміну дочірніх ресурсів людьми.

Зупиніться та спрогнозуйте: припустімо, що процес вашого контролера завершено одразу після того, як API-сервер видав подію `ADDED` для нового ресурсу `WebApp`, але до того, як контролер її обробив. Коли контролер перезапуститься за кілька хвилин, старої події watch вже немає. Перш ніж читати далі, поясніть, як свіжий LIST, кеш Informer'а та узгодження за рівнем усе одно призводять до створення пов'язаного Deployment.

### 1.3 Ідемпотентність

Кожне узгодження має бути **ідемпотентним**, тобто його виконання один чи багато разів має лишати кластер у тому самому правильному стані. Ідемпотентність — це не питання стилю; вона потрібна, бо той самий ключ можна поставити в чергу багаторазово, робітник може зазнати збою після створення одного дочірнього ресурсу, а інший робітник може пізніше повторити спробу для того самого батька. Тому цикл узгодження мусить спершу прочитати поточний стан, а потім створити, оновити чи пропустити дію залежно від того, що він фактично знаходить.

Це означає:
- Використовуйте `Create` з виявленням конфліктів, а не сліпе створення.
- Використовуйте `Update` з перевіркою версії ресурсу.
- Перевіряйте, чи ресурс уже існує, перш ніж створювати його.
- Ухвалюйте рішення на основі поточного стану, а не історії подій.

Зупиніться та подумайте: якщо ваша функція `syncHandler` сліпо викликає `Create` для Deployment, не перевіряючи, чи він уже існує, то другий цикл узгодження для того самого `WebApp` стає вадою, а не нешкідливим повторенням. Вирішіть, чи слід трактувати такий збій як очікуваний дрейф, конфлікт, який треба розв'язати, чи сигнал про те, що дизайн контролера недостатньо ідемпотентний.

### 1.4 Розбір реального трасування узгодження

Уявіть, що користувач створює `WebApp` з іменем `demo-app`, образом `nginx:1.27`, трьома репліками та портом `80`. API-сервер зберігає цей об'єкт у своєму сховищі, а динамічний Informer згодом спостерігає його появу через потік LIST/watch. Сам обробник події при цьому нічого не створює; усе, що він робить, — обчислює ключ `default/demo-app`, кладе цей ключ у workqueue й одразу повертається, щоб спостереження за іншими об'єктами могло безперебійно тривати далі.

Трохи пізніше один з робітників дістає ключ `default/demo-app` з черги й аж тоді починає справжнє узгодження. Він розщеплює цей ключ на простір імен та ім'я, читає поточний `WebApp` з кешу Informer'а, застосовує значення за замовчуванням для необов'язкових полів, а потім за допомогою типізованих Lister'ів перевіряє, чи вже існують відповідні Deployment і Service. У цей момент контролер усе ще лише спостерігає та аналізує; жодного запису до API не має статися доти, доки він не матиме достатньо інформації, щоб упевнено знати, яка саме дія є необхідною.

Оскільки це перше узгодження, Deployment і Service відсутні, тож контролер створює обидва дочірні ресурси з мітками, селекторами, портами та посиланнями на власника, похідними від батька. Ці створення — це фаза «Дій». Якщо створення Deployment вдалося, а створення Service зазнало невдачі, пізніша повторна спроба має помітити, що Deployment уже існує, пропустити його повторне створення й продовжити з відсутнім Service. Саме в цьому практична цінність ідемпотентності.

Після створення дочірніх ресурсів контролер оновлює статус, спираючись на спостережувану готовність Deployment. Спершу статус може показувати значення `Pending`, бо Под'и ще не встигли стати готовими, і це все одно корисний зворотний зв'язок, адже він доводить, що контролер таки спостеріг батька та створив дитину. Згодом, коли вбудований контролер Deployment оновить готовність реплік, вторинний шлях watch для Deployment може знову поставити батька в чергу, і вже тоді статус `WebApp` може просунутися від `Pending` до `Running`.

Це трасування також є контрольним списком для діагностики. Якщо Deployment не з'являється, перевірте, чи потрапив батьківський ключ до черги і чи знайшов `syncHandler` `WebApp` у кеші. Якщо Deployment з'являється, але статус лишається порожнім, перевірте підресурс статусу та шлях патчу. Якщо ручні зміни Deployment не виправляються, перевірте посилання на власника та вторинний обробник Informer'а.

---

## Частина 2: Архітектура контролера

### 2.1 Огляд компонентів

Архітектура контролера client-go навмисно відокремлює спостереження від дії, щоб API-сервер не зазнавав навантаження геть від кожного окремого рішення. Informer'и підтримують спільний локальний кеш, Lister'и читають саме з цього кешу, обробники подій ставлять у чергу легкі за вагою ключі, а робітники виконують узгодження вже поза самим шляхом watch. Саме завдяки цьому чіткому поділу обов'язків контролер може спостерігати за тисячами об'єктів одночасно, водночас тримаючи записи в API навмисними, виваженими та обмеженими за обсягом.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Controller Components                             │
│                                                                     │
│   API Server                                                        │
│       │                                                             │
│       │ WATCH (primary resource: WebApp)                           │
│       ▼                                                             │
│   ┌───────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│   │  Informer     │───▶│  DeltaFIFO   │───▶│  Indexer/Cache   │   │
│   │  (WebApp)     │    │              │    │                  │   │
│   └───────┬───────┘    └──────────────┘    └────────┬─────────┘   │
│           │                                          │             │
│           │ Event Handlers                          │ Lister      │
│           ▼                                          ▼             │
│   ┌───────────────┐                        ┌──────────────────┐   │
│   │  Workqueue    │                        │  Read desired    │   │
│   │  (rate-       │                        │  state from      │   │
│   │   limited)    │                        │  cache           │   │
│   └───────┬───────┘                        └──────────────────┘   │
│           │                                                        │
│           │ Dequeue keys                                          │
│           ▼                                                        │
│   ┌───────────────────────────────────────────────────────────┐   │
│   │                   syncHandler                              │   │
│   │                                                            │   │
│   │   1. Get WebApp from Lister                                │   │
│   │   2. Get/Create owned Deployment                           │   │
│   │   3. Get/Create owned Service                              │   │
│   │   4. Update WebApp status                                  │   │
│   │   5. Emit Events                                           │   │
│   │                                                            │   │
│   │   On error → re-enqueue with backoff                      │   │
│   │   On success → forget (reset backoff)                     │   │
│   └───────────────────────────────────────────────────────────┘   │
│                                                                     │
│   API Server                                                        │
│       │                                                             │
│       │ WATCH (secondary resources: Deployment, Service)           │
│       ▼                                                             │
│   ┌───────────────┐                                                │
│   │  Informers    │── Event handlers look up ownerRef             │
│   │  (Deployment, │   and enqueue the parent WebApp key           │
│   │   Service)    │                                                │
│   └───────────────┘                                                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

Ця діаграма також наочно показує, чому обробники подій контролера мають бути якомога меншими. Обробник події — це геть не те місце, де варто створювати Deployment'и, патчити статус чи викликати зовнішні системи, бо він виконується безпосередньо на боці спостереження контролера й блокує цей шлях. Натомість обробник має лише витягти ключ виду простір-імен/ім'я, додати цей ключ до workqueue й якомога швидше повернутися, щоб Informer міг безперебійно продовжувати обробляти оновлення watch та зміни в кеші.

### 2.2 Спостереження за власними ресурсами

Коли ваш контролер створює Deployment, вам також потрібно знати, коли цей Deployment змінюється, бо дочірні ресурси є частиною фактичного стану, за узгодження якого ви відповідаєте. Deployment може стати готовим, зазнати невдачі під час викочування, бути масштабованим вручну чи видаленим кимось, хто діагностує інцидент. Спостереження лише за батьківським `WebApp` пропустило б ці зміни на боці дитини, тож повноцінний контролер спостерігає за власними Deployment'ами та Service'ами як за вторинними ресурсами.

Хитрість у тому, що подія Deployment не повинна ставити в чергу сам Deployment; вона має ставити в чергу батьківський ключ `WebApp`. Посилання на власника забезпечує цей місток. Коли вторинний ресурс змінюється, контролер читає його контролерне посилання на власника, перевіряє, що тип власника — `WebApp`, будує батьківський ключ з простору імен та імені й дає звичайному циклу узгодження знову порівняти бажаний і фактичний стан.

Зупиніться та спрогнозуйте: ви вручну видаляєте Deployment, що належить власному ресурсу `WebApp`. Пройдіться точним ланцюжком подій на діаграмі архітектури контролера, який веде від події watch для Deployment до потрапляння батьківського ключа в чергу, а потім поясніть, чому Deployment-заміну має створити узгодження батька, а не сам обробник видалення.

```go
// When a Deployment changes, enqueue the owning WebApp
deploymentInformer.AddEventHandler(cache.ResourceEventHandlerFuncs{
    AddFunc: func(obj interface{}) {
        controller.handleOwnedResource(obj)
    },
    UpdateFunc: func(old, new interface{}) {
        controller.handleOwnedResource(new)
    },
    DeleteFunc: func(obj interface{}) {
        controller.handleOwnedResource(obj)
    },
})

func (c *Controller) handleOwnedResource(obj interface{}) {
    object, ok := obj.(metav1.Object)
    if !ok {
        tombstone, ok := obj.(cache.DeletedFinalStateUnknown)
        if !ok {
            return
        }
        object, ok = tombstone.Obj.(metav1.Object)
        if !ok {
            return // production code logs decode failures via utilruntime.HandleError
        }
    }

    // Look for an owner reference pointing to our CRD
    ownerRef := metav1.GetControllerOf(object)
    if ownerRef == nil || ownerRef.Kind != "WebApp" {
        return
    }

    // Enqueue the parent WebApp
    webapp, err := c.webappLister.WebApps(object.GetNamespace()).Get(ownerRef.Name)
    if err != nil {
        return
    }
    c.enqueue(webapp)
}
```

Зверніть увагу, що `handleOwnedResource` також обробляє «надгробки» (tombstones). Подія видалення може надійти як `cache.DeletedFinalStateUnknown`, коли кеш більше не має фінального об'єкта в очікуваному типі, особливо при пропущених видаленнях чи повторних списках (relist). Виробничим контролерам потрібен цей захисний шлях, бо паніка в обробнику видалення — саме той тип збою, який перетворює звичайну подію дрейфу на збій контролера.

### 2.3 Межі кешу та тиск подій

Кеш Informer'а слугує межею між API-сервером та вашим власним кодом узгодження. Замість того щоб кожен окремий робітник виконував живий мережевий GET для кожного батька та кожної дитини, спільний кеш виконує watch'і один раз та зберігає всі об'єкти локально в пам'яті. Такий дизайн суттєво зменшує тиск на API-сервер, але водночас означає, що контролер мусить поважати синхронізацію кешу та узгодженість у часі (eventual consistency). Кешоване читання є швидким та добре масштабованим, але воно стає по-справжньому надійним лише після того, як Informer завершив свій початковий повний LIST.

Ключі черги — це друга важлива межа. Вони навмисно відкидають детальний вміст самої події, бо цей вміст цілком може застаріти на той момент, коли робітник нарешті його побачить. Якщо `WebApp` оновлюється багаторазово підряд, поки один його ключ уже чекає в черзі, черга може згорнути весь цей сплеск оновлень в одне-єдине майбутнє узгодження. Робітник тоді просто читає найновіший об'єкт з кешу й ухвалює рішення вже на основі того фінального стану, який справді має значення.

Цей дизайн принципово відрізняється від звичайної черги повідомлень, яка обіцяє гарантовано доставити кожну окрему подію для бізнес-обробки. Контролер зовсім не намагається тарифікувати кожну модифікацію чи зберегти повний журнал аудиту; для цього в Kubernetes уже є окремі механізми аудиту на боці API-сервера. Контролер натомість намагається лише привести керовані ресурси до збіжності, а сама збіжність зазвичай виходить надійнішою саме тоді, коли дублікати та проміжні події є нешкідливими, а не обов'язковими до обробки.

Межі кешу також змінюють спосіб діагностики. Якщо логи контролера кажуть, що дочірній ресурс відсутній, але `kubectl get` показує, що він існує, спитайте, чи синхронізувався відповідний Informer, чи спостерігає контролер за правильним простором імен і чи дозволяє RBAC цей watch. Якщо кеш правильний, а черга не рухається, перевірте кількість робітників, затримки повторних спроб та чи не споживає увагу «отруйний» ключ.

Нарешті, пам'ятайте, що кеш зберігає об'єкти Kubernetes, а не ваші наміри. Якщо ваш контролер підтримує задані користувачем значення за замовчуванням, згенеровані імена чи зовнішні дані, ваш цикл узгодження мусить уміти щоразу відтворювати бажану форму дитини з поточної специфікації батька та будь-якого авторитетного зовнішнього стану. Прихований стан у пам'яті робить перезапуски небезпечними й робить майже неможливим міркування про зміну лідера.

---

## Частина 3: Повний контролер

### 3.1 Структура проєкту

Проєкту контролера потрібно більше, ніж функція узгодження, бо він є водночас клієнтом Kubernetes та довготривалим процесом. Точка входу будує конфігурацію, запускає фабрики Informer'ів, налаштовує запис подій та обробляє сигнали завершення. Файл контролера володіє підключенням кешу, обробкою черги, узгодженням та конструюванням дочірніх ресурсів. Поділ цих обов'язків полегшує тестування поведінки узгодження, не змішуючи її з кодом життєвого циклу процесу.

```
webapp-controller/
├── go.mod
├── go.sum
├── main.go              # Entry point, signal handling, leader election
├── controller.go        # Controller struct and reconcile logic
├── crd/
│   └── webapp-crd.yaml  # CRD definition from Module 1.2
└── deploy/
    └── rbac.yaml        # RBAC for the controller ServiceAccount
```

Цей модуль навмисно тримає проєкт малим, щоб частини client-go лишалися видимими. У більшому контролері ви зазвичай розділили б типи API, згенеровані клієнти, пакети контролера, маніфести й тести в окремі каталоги, але той самий потік керування лишається. Важлива звичка — знати, який код читає з кешів, який код пише до API-сервера й який код існує лише для того, щоб чисто запустити чи зупинити процес.

### 3.2 Типи CRD (спрощено)

Оскільки ми не використовуємо генерацію коду, Informer для `WebApp` доставлятиме неструктуровані об'єкти, а контролер перетворюватиме їх на невеликий локальний Go-тип перед узгодженням. Це не той спосіб, яким пишуть більшість виробничих операторів, бо згенеровані типізовані клієнти дають сильнішу безпеку часу компіляції та чистіші lister'и. Тут це корисно, бо розкриває, що саме робить динамічний клієнт, і робить явним місток між загальними об'єктами Kubernetes та доменно-специфічною логікою контролера.

```go
// types.go
package main

import metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"

// WebApp represents our custom resource.
type WebApp struct {
	metav1.TypeMeta   `json:",inline"`
	metav1.ObjectMeta `json:"metadata,omitempty"`
	Spec              WebAppSpec   `json:"spec"`
	Status            WebAppStatus `json:"status,omitempty"`
}

type WebAppSpec struct {
	Image    string `json:"image"`
	Replicas *int32 `json:"replicas,omitempty"`
	Port     int32  `json:"port,omitempty"`
}

type WebAppStatus struct {
	ReadyReplicas int32  `json:"readyReplicas,omitempty"`
	Phase         string `json:"phase,omitempty"`
}
```

### 3.3 Реалізація контролера

Наведена нижче реалізація — серце модуля, і вона зберігає повний потік client-go: типізовані клієнти для вбудованих ресурсів, динамічний клієнт для CRD, фабрики Informer'ів для спостереження, Lister'и для кешованих читань, типізовану чергу з обмеженням швидкості для роботи та реєстратор подій для зрозумілого користувачеві зворотного зв'язку. Читайте її пошарово, а не намагайтеся запам'ятати кожен import. Спершу простежте, як об'єкти потрапляють у чергу, потім простежте, як робітники спорожнюють чергу, і лише тоді вивчайте специфічні для ресурсів рішення всередині `syncHandler`.

Перш ніж це запускати, спрогнозуйте, які виклики API стаються, коли з'являється новий `WebApp` з образом, трьома репліками та портом сервісу. Ви маєте вміти назвати кешоване читання для батька, кешовані читання для власних Deployment і Service, виклики створення для відсутніх дітей та патч статусу, який звітує про спостережувану готовність. Якщо ви не можете простежити ці операції, зупиніться на коментарях у коді й зіставте їх із фазами «Спостерігай», «Аналізуй» та «Дій».

```go
// controller.go
package main

import (
	"context"
	"encoding/json"
	"fmt"

	appsv1 "k8s.io/api/apps/v1"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/api/errors"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/runtime/schema"
	utilruntime "k8s.io/apimachinery/pkg/util/runtime"
	"k8s.io/apimachinery/pkg/util/intstr"
	"k8s.io/client-go/dynamic"
	"k8s.io/client-go/dynamic/dynamicinformer"
	"k8s.io/client-go/informers"
	"k8s.io/client-go/kubernetes"
	appslisters "k8s.io/client-go/listers/apps/v1"
	corelisters "k8s.io/client-go/listers/core/v1"
	"k8s.io/client-go/tools/cache"
	"k8s.io/client-go/tools/record"
	"k8s.io/client-go/util/workqueue"
	"k8s.io/klog/v2"
)

var webappGVR = schema.GroupVersionResource{
	Group:    "apps.kubedojo.io",
	Version:  "v1beta1",
	Resource: "webapps",
}

const (
	controllerName = "webapp-controller"
	maxRetries     = 5
)

// Controller manages WebApp resources.
type Controller struct {
	kubeClient    kubernetes.Interface
	dynamicClient dynamic.Interface

	// Listers for reading from cache
	deploymentLister appslisters.DeploymentLister
	serviceLister    corelisters.ServiceLister

	// Informer synced functions
	deploymentSynced cache.InformerSynced
	serviceSynced    cache.InformerSynced
	webappSynced     cache.InformerSynced

	// Dynamic informer for our CRD
	webappInformer cache.SharedIndexInformer

	// Workqueue
	queue workqueue.TypedRateLimitingInterface[string]

	// Event recorder
	recorder record.EventRecorder
}

// NewController creates a new WebApp controller.
func NewController(
	kubeClient kubernetes.Interface,
	dynamicClient dynamic.Interface,
	kubeInformerFactory informers.SharedInformerFactory,
	dynamicInformerFactory dynamicinformer.DynamicSharedInformerFactory,
	recorder record.EventRecorder,
) *Controller {

	// Get informers for owned resources
	deploymentInformer := kubeInformerFactory.Apps().V1().Deployments()
	serviceInformer := kubeInformerFactory.Core().V1().Services()

	// Get dynamic informer for our CRD
	webappInformer := dynamicInformerFactory.ForResource(webappGVR).Informer()

	c := &Controller{
		kubeClient:       kubeClient,
		dynamicClient:    dynamicClient,
		deploymentLister: deploymentInformer.Lister(),
		serviceLister:    serviceInformer.Lister(),
		deploymentSynced: deploymentInformer.Informer().HasSynced,
		serviceSynced:    serviceInformer.Informer().HasSynced,
		webappSynced:     webappInformer.HasSynced,
		webappInformer:   webappInformer,
		queue: workqueue.NewTypedRateLimitingQueueWithConfig(
			workqueue.DefaultTypedControllerRateLimiter[string](),
			workqueue.TypedRateLimitingQueueConfig[string]{
				Name: controllerName,
			},
		),
		recorder: recorder,
	}

	// Set up event handlers for WebApp (primary resource)
	webappInformer.AddEventHandler(cache.ResourceEventHandlerFuncs{
		AddFunc: func(obj interface{}) {
			c.enqueueWebApp(obj)
		},
		UpdateFunc: func(old, new interface{}) {
			c.enqueueWebApp(new)
		},
		DeleteFunc: func(obj interface{}) {
			c.enqueueWebApp(obj)
		},
	})

	// Set up event handlers for owned Deployments
	deploymentInformer.Informer().AddEventHandler(cache.ResourceEventHandlerFuncs{
		AddFunc: func(obj interface{}) {
			c.handleOwnedObject(obj)
		},
		UpdateFunc: func(old, new interface{}) {
			c.handleOwnedObject(new)
		},
		DeleteFunc: func(obj interface{}) {
			c.handleOwnedObject(obj)
		},
	})

	// Set up event handlers for owned Services
	serviceInformer.Informer().AddEventHandler(cache.ResourceEventHandlerFuncs{
		AddFunc: func(obj interface{}) {
			c.handleOwnedObject(obj)
		},
		UpdateFunc: func(old, new interface{}) {
			c.handleOwnedObject(new)
		},
		DeleteFunc: func(obj interface{}) {
			c.handleOwnedObject(obj)
		},
	})

	return c
}

func (c *Controller) enqueueWebApp(obj interface{}) {
	key, err := cache.MetaNamespaceKeyFunc(obj)
	if err != nil {
		utilruntime.HandleError(fmt.Errorf("getting key for object: %v", err))
		return
	}
	c.queue.Add(key)
}

func (c *Controller) handleOwnedObject(obj interface{}) {
	var object metav1.Object
	var ok bool

	if object, ok = obj.(metav1.Object); !ok {
		tombstone, ok := obj.(cache.DeletedFinalStateUnknown)
		if !ok {
			utilruntime.HandleError(fmt.Errorf("error decoding object, invalid type"))
			return
		}
		object, ok = tombstone.Obj.(metav1.Object)
		if !ok {
			utilruntime.HandleError(fmt.Errorf("error decoding tombstone, invalid type"))
			return
		}
	}

	ownerRef := metav1.GetControllerOf(object)
	if ownerRef == nil {
		return
	}

	if ownerRef.Kind != "WebApp" {
		return
	}

	// Enqueue the parent WebApp
	key := object.GetNamespace() + "/" + ownerRef.Name
	c.queue.Add(key)
}

// Run starts the controller.
func (c *Controller) Run(ctx context.Context, workers int) error {
	defer utilruntime.HandleCrash()
	defer c.queue.ShutDown()

	klog.Infof("Starting %s", controllerName)

	// Wait for all caches to sync
	klog.Info("Waiting for informer caches to sync")
	if ok := cache.WaitForCacheSync(ctx.Done(),
		c.deploymentSynced,
		c.serviceSynced,
		c.webappSynced,
	); !ok {
		return fmt.Errorf("failed to wait for caches to sync")
	}

	klog.Infof("Starting %d workers", workers)
	for i := 0; i < workers; i++ {
		go c.runWorker(ctx)
	}

	klog.Info("Controller started")
	<-ctx.Done()
	klog.Info("Shutting down controller")
	return nil
}

func (c *Controller) runWorker(ctx context.Context) {
	for c.processNextWorkItem(ctx) {
	}
}

func (c *Controller) processNextWorkItem(ctx context.Context) bool {
	key, shutdown := c.queue.Get()
	if shutdown {
		return false
	}
	defer c.queue.Done(key)

	err := c.syncHandler(ctx, key)
	if err == nil {
		// Success — reset the rate limiter for this key
		c.queue.Forget(key)
		return true
	}

	// Failure — re-enqueue with rate limiting
	if c.queue.NumRequeues(key) < maxRetries {
		klog.Warningf("Error syncing %q (retry %d/%d): %v",
			key, c.queue.NumRequeues(key)+1, maxRetries, err)
		c.queue.AddRateLimited(key)
		return true
	}

	// Too many retries — give up on this key
	klog.Errorf("Dropping %q after %d retries: %v", key, maxRetries, err)
	c.queue.Forget(key)
	utilruntime.HandleError(err)
	return true
}

// syncHandler is the core reconciliation logic.
func (c *Controller) syncHandler(ctx context.Context, key string) error {
	namespace, name, err := cache.SplitMetaNamespaceKey(key)
	if err != nil {
		return fmt.Errorf("invalid resource key: %s", key)
	}

	// OBSERVE: Get the WebApp from the cache
	unstructuredObj, err := c.webappInformer.GetIndexer().ByIndex(
		cache.NamespaceIndex, namespace)
	if err != nil {
		return err
	}

	// Find the specific WebApp
	var webapp *WebApp
	for _, item := range unstructuredObj {
		u := item.(*unstructured.Unstructured)
		if u.GetName() == name && u.GetNamespace() == namespace {
			webapp, err = unstructuredToWebApp(u)
			if err != nil {
				return fmt.Errorf("converting unstructured to WebApp: %v", err)
			}
			break
		}
	}

	if webapp == nil {
		// WebApp was deleted — owned resources will be garbage collected
		// via OwnerReferences
		klog.Infof("WebApp %s deleted, owned resources will be GC'd", key)
		return nil
	}

	// Set defaults
	replicas := int32(2)
	if webapp.Spec.Replicas != nil {
		replicas = *webapp.Spec.Replicas
	}
	port := int32(8080)
	if webapp.Spec.Port > 0 {
		port = webapp.Spec.Port
	}

	// ANALYZE + ACT: Ensure Deployment exists and matches spec
	deploymentName := webapp.Name
	deployment, err := c.deploymentLister.Deployments(namespace).Get(deploymentName)
	if errors.IsNotFound(err) {
		// Create the Deployment
		deployment, err = c.kubeClient.AppsV1().Deployments(namespace).Create(
			ctx,
			c.newDeployment(webapp, deploymentName, replicas, port),
			metav1.CreateOptions{},
		)
		if err != nil {
			return fmt.Errorf("creating deployment: %v", err)
		}
		klog.Infof("Created Deployment %s/%s", namespace, deploymentName)
		c.recorder.Eventf(webapp, corev1.EventTypeNormal, "DeploymentCreated",
			"Created Deployment %s", deploymentName)
	} else if err != nil {
		return fmt.Errorf("getting deployment: %v", err)
	} else {
		// Deployment exists — check if it needs updating
		if *deployment.Spec.Replicas != replicas ||
			deployment.Spec.Template.Spec.Containers[0].Image != webapp.Spec.Image {
			deploymentCopy := deployment.DeepCopy()
			deploymentCopy.Spec.Replicas = &replicas
			deploymentCopy.Spec.Template.Spec.Containers[0].Image = webapp.Spec.Image
			_, err = c.kubeClient.AppsV1().Deployments(namespace).Update(
				ctx, deploymentCopy, metav1.UpdateOptions{})
			if err != nil {
				return fmt.Errorf("updating deployment: %v", err)
			}
			klog.Infof("Updated Deployment %s/%s", namespace, deploymentName)
			c.recorder.Eventf(webapp, corev1.EventTypeNormal, "DeploymentUpdated",
				"Updated Deployment %s (replicas=%d, image=%s)",
				deploymentName, replicas, webapp.Spec.Image)
		}
	}

	// Ensure Service exists
	serviceName := webapp.Name
	_, err = c.serviceLister.Services(namespace).Get(serviceName)
	if errors.IsNotFound(err) {
		_, err = c.kubeClient.CoreV1().Services(namespace).Create(
			ctx,
			c.newService(webapp, serviceName, port),
			metav1.CreateOptions{},
		)
		if err != nil {
			return fmt.Errorf("creating service: %v", err)
		}
		klog.Infof("Created Service %s/%s", namespace, serviceName)
		c.recorder.Eventf(webapp, corev1.EventTypeNormal, "ServiceCreated",
			"Created Service %s", serviceName)
	} else if err != nil {
		return fmt.Errorf("getting service: %v", err)
	}

	// Update status
	err = c.updateStatus(ctx, webapp, deployment)
	if err != nil {
		return fmt.Errorf("updating status: %v", err)
	}

	return nil
}

func (c *Controller) newDeployment(webapp *WebApp, name string, replicas int32, port int32) *appsv1.Deployment {
	labels := map[string]string{
		"app":                          name,
		"app.kubernetes.io/managed-by": controllerName,
	}

	return &appsv1.Deployment{
		ObjectMeta: metav1.ObjectMeta{
			Name:      name,
			Namespace: webapp.Namespace,
			OwnerReferences: []metav1.OwnerReference{
				*metav1.NewControllerRef(webapp, schema.GroupVersionKind{
					Group:   "apps.kubedojo.io",
					Version: "v1beta1",
					Kind:    "WebApp",
				}),
			},
			Labels: labels,
		},
		Spec: appsv1.DeploymentSpec{
			Replicas: &replicas,
			Selector: &metav1.LabelSelector{
				MatchLabels: labels,
			},
			Template: corev1.PodTemplateSpec{
				ObjectMeta: metav1.ObjectMeta{
					Labels: labels,
				},
				Spec: corev1.PodSpec{
					Containers: []corev1.Container{
						{
							Name:  "app",
							Image: webapp.Spec.Image,
							Ports: []corev1.ContainerPort{
								{
									ContainerPort: port,
									Protocol:      corev1.ProtocolTCP,
								},
							},
						},
					},
				},
			},
		},
	}
}

func (c *Controller) newService(webapp *WebApp, name string, port int32) *corev1.Service {
	return &corev1.Service{
		ObjectMeta: metav1.ObjectMeta{
			Name:      name,
			Namespace: webapp.Namespace,
			OwnerReferences: []metav1.OwnerReference{
				*metav1.NewControllerRef(webapp, schema.GroupVersionKind{
					Group:   "apps.kubedojo.io",
					Version: "v1beta1",
					Kind:    "WebApp",
				}),
			},
			Labels: map[string]string{
				"app":                          name,
				"app.kubernetes.io/managed-by": controllerName,
			},
		},
		Spec: corev1.ServiceSpec{
			Selector: map[string]string{
				"app": name,
			},
			Ports: []corev1.ServicePort{
				{
					Port:       port,
					TargetPort: intstr.FromInt32(port),
					Protocol:   corev1.ProtocolTCP,
				},
			},
			Type: corev1.ServiceTypeClusterIP,
		},
	}
}

func (c *Controller) updateStatus(ctx context.Context, webapp *WebApp, deployment *appsv1.Deployment) error {
	readyReplicas := int32(0)
	phase := "Pending"

	if deployment != nil {
		readyReplicas = deployment.Status.ReadyReplicas
		if deployment.Status.ReadyReplicas == *deployment.Spec.Replicas {
			phase = "Running"
		} else if deployment.Status.ReadyReplicas > 0 {
			phase = "Deploying"
		}
	}

	// Build the status patch
	patch := map[string]interface{}{
		"status": map[string]interface{}{
			"readyReplicas": readyReplicas,
			"phase":         phase,
		},
	}

	patchBytes, err := json.Marshal(patch)
	if err != nil {
		return err
	}

	_, err = c.dynamicClient.Resource(webappGVR).Namespace(webapp.Namespace).Patch(
		ctx,
		webapp.Name,
		"application/merge-patch+json",
		patchBytes,
		metav1.PatchOptions{},
		"status",
	)
	return err
}

// unstructuredToWebApp converts an unstructured object to a WebApp.
func unstructuredToWebApp(u *unstructured.Unstructured) (*WebApp, error) {
	data, err := json.Marshal(u.Object)
	if err != nil {
		return nil, err
	}
	var webapp WebApp
	if err := json.Unmarshal(data, &webapp); err != nil {
		return nil, err
	}
	// Copy ObjectMeta fields that are needed
	webapp.Name = u.GetName()
	webapp.Namespace = u.GetNamespace()
	webapp.UID = u.GetUID()
	return &webapp, nil
}
```

### 3.4 Головна точка входу

Головна точка входу навмисно менша за контролер, бо запуск процесу має підготувати залежності, а потім передати керування рушієві узгодження. Вона підтримує і конфігурацію всередині кластера, і локальний kubeconfig, що дозволяє запускати контролер проти кластера kind під час лабораторної, а пізніше розгорнути той самий бінарний файл у Kubernetes. Вона також запускає обидві фабрики Informer'ів перед викликом `Run`, даючи контролеру шанс дочекатися синхронізації кешу, перш ніж робітники почнуть діяти.

```go
// main.go
package main

import (
	"context"
	"os"
	"os/signal"
	"path/filepath"
	"syscall"
	"time"

	"k8s.io/client-go/dynamic"
	"k8s.io/client-go/dynamic/dynamicinformer"
	"k8s.io/client-go/informers"
	"k8s.io/client-go/kubernetes"
	"k8s.io/client-go/kubernetes/scheme"
	typedcorev1 "k8s.io/client-go/kubernetes/typed/core/v1"
	corev1 "k8s.io/api/core/v1"
	"k8s.io/client-go/rest"
	"k8s.io/client-go/tools/clientcmd"
	"k8s.io/client-go/tools/record"
	"k8s.io/klog/v2"
)

func main() {
	klog.InitFlags(nil)

	// Build config (supports both in-cluster and kubeconfig)
	config, err := buildConfig()
	if err != nil {
		klog.Fatalf("Error building config: %v", err)
	}

	// Create clients
	kubeClient, err := kubernetes.NewForConfig(config)
	if err != nil {
		klog.Fatalf("Error creating kubernetes client: %v", err)
	}

	dynamicClient, err := dynamic.NewForConfig(config)
	if err != nil {
		klog.Fatalf("Error creating dynamic client: %v", err)
	}

	// Create informer factories
	kubeInformerFactory := informers.NewSharedInformerFactory(kubeClient, 30*time.Second)
	dynamicInformerFactory := dynamicinformer.NewDynamicSharedInformerFactory(
		dynamicClient, 30*time.Second)

	// Create event recorder
	eventBroadcaster := record.NewBroadcaster()
	eventBroadcaster.StartStructuredLogging(0)
	eventBroadcaster.StartRecordingToSink(&typedcorev1.EventSinkImpl{
		Interface: kubeClient.CoreV1().Events(""),
	})
	recorder := eventBroadcaster.NewRecorder(scheme.Scheme, corev1.EventSource{
		Component: controllerName,
	})

	// Create controller
	controller := NewController(
		kubeClient,
		dynamicClient,
		kubeInformerFactory,
		dynamicInformerFactory,
		recorder,
	)

	// Set up shutdown context
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
	go func() {
		sig := <-sigCh
		klog.Infof("Received signal %v, initiating shutdown", sig)
		cancel()
	}()

	// Start informer factories
	kubeInformerFactory.Start(ctx.Done())
	dynamicInformerFactory.Start(ctx.Done())

	// Run controller with 2 workers
	if err := controller.Run(ctx, 2); err != nil {
		klog.Fatalf("Error running controller: %v", err)
	}
}

func buildConfig() (*rest.Config, error) {
	// Try in-cluster config first
	config, err := rest.InClusterConfig()
	if err == nil {
		return config, nil
	}

	// Fall back to kubeconfig
	home, err := os.UserHomeDir()
	if err != nil {
		klog.Warningf("Could not determine home directory, using empty path: %v", err)
	}
	kubeconfig := filepath.Join(home, ".kube", "config")
	return clientcmd.BuildConfigFromFlags("", kubeconfig)
}
```

Порядок запуску має значення. Якщо робітники стартують до синхронізації кешів, контролер може ухвалювати рішення з порожнього чи неповного бачення світу й створювати ресурси, які вже існують. Якщо процес ігнорує сигнали, Kubernetes може завершити його, поки робітник на середині спроби узгодження. Поєднання скасування контексту, синхронізації кешу, завершення черги та циклів робітників дає вам контролер, який поводиться передбачувано, коли Под'и викочуються заново, ноди спорожнюються чи змінюється лідерство.

### 3.5 Читання `syncHandler` як контракту

Функція `syncHandler` — це значно більше, ніж просто довге тіло функції; по суті, це контракт між API `WebApp` та тими ресурсами, якими володіє контролер. Перша частина цього контракту каже, що ключ черги обов'язково мусить ідентифікувати дійсну пару простір-імен/ім'я. Погані, некоректні ключі — це насправді програмні помилки в самому коді, тож повернути помилку й дати робітнику її належно зафіксувати завжди краще, ніж мовчки проігнорувати некоректний ввід і вдати, що нічого не сталося.

Наступна частина контракту каже, що видалення батьківського ресурсу не є помилкою. Коли контролер не може знайти `WebApp` у своєму кеші, він обґрунтовано припускає, що батька було видалено, й тому успішно повертається, адже посилання на власника дозволяють механізму збирання сміття самостійно подбати про дітей. Цей шлях повернення дуже легко проґавити під час написання коду, але саме він не дає видаленому батьку перетворитися на назавжди невдалий, постійно повторюваний елемент черги.

Застосування значень за замовчуванням — ще одна межа контракту. У цьому модулі контролер застосовує значення за замовчуванням для реплік і порту перед побудовою дочірніх об'єктів, тоді як схема CRD також визначає значення за замовчуванням для цих полів. У виробництві ви маєте чітко знати, де відбувається задання значень за замовчуванням і як воно тестується. Якщо значення за замовчуванням живуть у схемі CRD, клієнти й контролери бачать узгодженіший об'єкт. Якщо значення за замовчуванням живуть лише в коді контролера, інші читачі API можуть бачити відсутні поля, доки узгодження не інтерпретує їх.

Блок узгодження Deployment демонструє поведінку «створи-або-онови». На «не знайдено» контролер створює дитину з бажаної форми. На інші помилки читання він повертає помилку, бо контролер не знає достатньо, щоб продовжувати. На наявному Deployment він порівнює лише поля, якими володіє, як-от кількість реплік та образ, а потім робить глибоку копію об'єкта перед оновленням, щоб не змінювати стан кешу напряму. Об'єкти, повернуті з lister'а, живуть у спільному кеші Informer'а й доступні лише для читання; зміна їх на місці псує кеш для кожного іншого читача й може спричинити тонкі, важко відтворювані вади узгодження, тож ви спершу копіюєте, а пишете вже копію.

Блок Service простіший, бо збережений код створює Service, коли той відсутній, а інакше лишає його як є. Це проєктне рішення, яке варто помітити. Якщо порт `WebApp` змінюється, суворіший контролер міг би пропатчити Service, тоді як консервативний контролер міг би трактувати зміни порту Service як незмінні й звітувати станом. Правильна відповідь залежить від контракту API, який ви документуєте для `WebApp`.

Узгодження статусу замикає цикл для користувачів. Батьківський ресурс, який створює дітей, але ніколи не звітує про спостережуваний стан, змушує користувачів вручну перевіряти Deployment'и, що зводить нанівець частину цінності API вищого рівня. Патч статусу має повідомляти те, що контролер спостеріг, а не те, на що він сподівається. Саме тому готові репліки беруться зі статусу Deployment, а не безпосередньо зі `spec.replicas`.

Запис подій обслуговує іншу аудиторію, ніж статус. Статус — це довговічний стан на власному ресурсі, тоді як Події — це нещодавня історія помітних переходів, яка з'являється в `kubectl describe`. Хороший контролер використовує обидва: статус для машинозчитуваних умов та прогресу, Події для зрозумілих людині пояснень створень, оновлень і збоїв. Логи теж корисні, але вони не повинні бути єдиним способом, яким власник ресурсу дізнається, що сталося.

Коли ви згодом перейдете від client-go до controller-runtime, збережіть цю модель контракту. Фреймворк перейменує деякі поверхні, згенерує узгоджувачі (reconcilers) та надасть помічники, але він не може вирішити вашу семантику володіння, класифікацію повторних спроб, словник статусу чи правила ідемпотентності. Ці рішення є частиною дизайну вашого API, а не лише частиною вашої Go-реалізації.

---

## Частина 4: Стратегії обмеження швидкості та повторних спроб

### 4.1 Вбудовані обмежувачі швидкості

Помилки — це цілком нормальне явище в коді контролера, бо API-сервер може відхиляти окремі записи, webhook'и можуть перевищувати відведений час очікування, версії ресурсів можуть між собою конфліктувати, а користувачі цілком можуть подавати недійсний бажаний стан. Workqueue — це саме те місце, де контролер перетворює всі ці помилки на контрольовані повторні спроби замість тісних, виснажливих циклів збоїв. Бібліотека client-go надає одразу кілька різних обмежувачів швидкості, і типовий обмежувач швидкості контролера поєднує поелементне експоненційне відкочування із загальним кошиком токенів, щоб один-єдиний зламаний об'єкт у жодному разі не міг спожити всю наявну потужність робітників.

```go
// Default: combines exponential backoff with a bucket rate limiter
queue := workqueue.NewTypedRateLimitingQueue(
    workqueue.DefaultTypedControllerRateLimiter[string](),
)

// Custom: exponential backoff (5ms base, 1000s max)
queue := workqueue.NewTypedRateLimitingQueue(
    workqueue.NewTypedItemExponentialFailureRateLimiter[string]
    (
        5*time.Millisecond,    // base delay
        1000*time.Second,      // max delay
    ),
)

// Custom: fixed rate (10 items/sec, burst of 100)
queue := workqueue.NewTypedRateLimitingQueue(
    &workqueue.TypedBucketRateLimiter[string]{
        Limiter: rate.NewLimiter(rate.Limit(10), 100),
    },
)

// Combine multiple limiters (all must allow)
queue := workqueue.NewTypedRateLimitingQueue(
    workqueue.NewTypedMaxOfRateLimiter(
        workqueue.NewTypedItemExponentialFailureRateLimiter[string]
        (
            5*time.Millisecond, 60*time.Second),
        &workqueue.TypedBucketRateLimiter[string]{
            Limiter: rate.NewLimiter(rate.Limit(10), 100)},
    ),
)
```

Приклади показують кілька форм контролю повторних спроб, але проєктне питання завжди те саме: чи ймовірно, що ця помилка успішно завершиться пізніше без втручання користувача, і як швидко контролер має спробувати знову? Конфлікт часто можна повторити скоро, бо інший записувач змінив об'єкт першим. Помилку валідації, спричинену недійсною специфікацією, зазвичай слід винести через статус чи Подію, а потім забути, доки користувач не змінить ресурс.

### 4.2 Найкращі практики повторних спроб

| Практика | Чому |
|----------|-----|
| Обмежуйте максимум повторних спроб (напр., 5-15) | Запобігає нескінченним циклам повторів |
| Використовуйте експоненційне відкочування | Запобігає «штампу натовпу» при тимчасових збоях |
| Логуйте повтори з лічильником | Уможливлює моніторинг та оповіщення |
| Забувайте (Forget) при успіху | Скидає відкочування для наступного збою |
| Розрізняйте повторювані та фатальні помилки | Не повторюйте помилки валідації |

Зупиніться та подумайте: користувач створює `WebApp` зі специфікацією, що містить значення, яке ваш контролер відображає в недійсний Deployment, через що API-сервер відхиляє створення. Вирішіть, чи має ваш контролер повторювати спробу з експоненційним відкочуванням, оновити статус чіткою умовою, видати попереджувальну Подію або поєднати ці варіанти поведінки. Важлива відмінність полягає в тому, чи може час виправити проблему, чи користувач мусить змінити бажаний стан.

```go
func (c *Controller) processNextWorkItem(ctx context.Context) bool {
    key, shutdown := c.queue.Get()
    if shutdown {
        return false
    }
    defer c.queue.Done(key)

    err := c.syncHandler(ctx, key)

    switch {
    case err == nil:
        c.queue.Forget(key)
    case errors.IsConflict(err):
        // Resource version conflict — retry immediately
        klog.V(4).Infof("Conflict on %s, retrying", key)
        c.queue.AddRateLimited(key)
    case errors.IsNotFound(err):
        // Resource gone — no point retrying
        klog.V(4).Infof("Resource %s not found, skipping", key)
        c.queue.Forget(key)
    case c.queue.NumRequeues(key) < maxRetries:
        klog.Warningf("Error syncing %s (attempt %d): %v",
            key, c.queue.NumRequeues(key)+1, err)
        c.queue.AddRateLimited(key)
    default:
        klog.Errorf("Dropping %s after %d attempts: %v",
            key, maxRetries, err)
        c.queue.Forget(key)
    }

    return true
}
```

Обробка повторних спроб також впливає на спостережуваність. Контролер, який відкидає ключ після надто багатьох спроб без запису Події чи умови статусу, лишає користувачів у здогадках, тоді як контролер, який повторює спроби вічно, може ховати «отруйний» об'єкт за галасливими логами. Виробничий патерн — обмежувати швидкість тимчасових збоїв, забувати успішні ключі, класифікувати постійні збої там, де можливо, та надавати достатньо інформації, щоб власник ресурсу полагодив свою специфікацію.

### 4.3 Класифікація збоїв

Класифікація збоїв починається з питання, чи могло б повторення того самого бажаного стану успішно завершитися пізніше. Перевищення часу очікування API-сервера, тимчасові збої admission-webhook'ів, конфлікти версій ресурсів та короткі мережеві розриви зазвичай придатні для повтору. Недійсні значення полів, заборонені операції через RBAC та зміни незмінних полів зазвичай потребують зміни специфікації, зміни прав чи іншої дії контролера. Черга може затримати повтори, але вона не може зробити недійсний дочірній об'єкт дійсним.

Конфлікти заслуговують особливої уваги, бо вони поширені в Kubernetes. Якщо інший актор оновив дочірній ресурс між вашим читанням і оновленням, API-сервер може відхилити ваш запис, бо версія ресурсу застаріла. Найбезпечніша відповідь — поставити в чергу заново й дати наступному узгодженню прочитати найновішу версію з кешу чи API. Спроба сліпо патчити без розуміння володіння може випадково стерти чужі поля.

Помилки «не знайдено» потребують контексту. Відсутній батько часто означає, що видалення вже збіглося, тож успіх доречний. Відсутня дитина може означати, що контролер має її відтворити, але лише якщо ця дитина все ще є частиною бажаного стану, а батько все ще існує. Трактування кожного «не знайдено» як повторюваної помилки створює галасливі цикли після законних видалень.

Для API, орієнтованих на користувача, постійні збої мають стати частиною спостережуваного стану ресурсу. `WebApp` з недійсною політикою образів, забороненим портом чи неможливою специфікацією дитини має показувати чітку умову чи Подію, а не просто зникати в логах контролера. Саме цей цикл зворотного зв'язку перетворює контролер з невидимого фонового процесу на надійну реалізацію API.

---

## Частина 5: Граційне завершення

### 5.1 Послідовність завершення

Контролер мусить завершуватися чисто, бо Kubernetes ставиться до Под'ів контролера як до будь-якого іншого робочого навантаження: вони переплановуються, викочуються заново, виселяються та завершуються під час обслуговування. Контролер не може припускати, що робітник завжди завершить роботу природним чином, тож йому потрібна передбачувана послідовність завершення, яка зупиняє нові спостереження, дає робітникам докінчити поточний елемент і вивільняє ресурси процесу. Мета не в тому, щоб вічно зберігати чергу в пам'яті; мета в тому, щоб зупинитися, не пошкодивши цикл керування, бо майбутня активність LIST та watch може заново виявити поточний стан.

```
Signal received (SIGTERM/SIGINT)
    │
    ├── 1. Cancel context → informers stop watching
    │
    ├── 2. queue.ShutDown() → workers drain remaining items
    │
    ├── 3. Workers finish current item → return false
    │
    ├── 4. Event broadcaster stops
    │
    └── 5. Process exits
```

### 5.2 Реалізація

Шлях граційного завершення вже вбудований у наш контролер через скасування контексту та `queue.ShutDown`. Коли процес отримує `SIGTERM` чи `SIGINT`, `main` скасовує контекст, фабрики Informer'ів припиняють спостереження, і `Run` зрештою повертається після зупинки робітників. Цей патерн працює локально під час лабораторної й також чисто відображається на поведінку завершення Kubernetes, коли контролер виконується в Под'і.

Ключові моменти:

1. `ctx.Done()` зупиняє Informer'и.
2. `defer c.queue.ShutDown()` у `Run()` спорожнює чергу.
3. Робітники перевіряють `shutdown` з `queue.Get()` і виходять.
4. `defer cancel()` у `main()` забезпечує очищення на будь-якому шляху виходу.

Тонкий момент у тому, що граційне завершення та ідемпотентність підтримують одне одного. Якщо робітника перервано після створення Deployment, але до оновлення статусу, наступне узгодження має помітити, що Deployment уже існує, й продовжити звідти. Контролер, який зберігає істотний прогрес лише в пам'яті, крихкий; контролер, який виводить прогрес зі стану кластера, може відновитися після звичайних подій життєвого циклу процесу.

### 5.3 Режими збою при завершенні

Найпоширеніша вада завершення — починати нову роботу після того, як почалося скасування. Якщо Informer'и зупиняються, а робітники продовжують надто довго ухвалювати рішення зі застарілих кешів, контролер може діяти на дедалі старіше бачення кластера. Передавання того самого контексту через виклики клієнта й цикли робітників допомагає процесу припинити записи, щойно Kubernetes попросив Под завершитися.

Інша тонка вада — припущення, що завершення черги означає, що кожен бажаний стан узгоджено. Черга в пам'яті не довговічна, і це прийнятно, бо API-сервер лишається довговічним джерелом бажаного стану. Після перезапуску LIST Informer'а може заново виявити батьків і дітей, а узгодження за рівнем може полагодити все незавершене. Саме тому коректність має походити зі стану кластера, а не з вичерпання кожного історичного елемента черги.

Реєстратори подій та скидання логів теж мають значення під час завершення. Контролер, який виходить одразу після збою, може втратити видиму людині підказку, яка пояснила б наступну повторну спробу. У виробничому розгортанні поєднуйте граційну обробку процесу з готовністю Kubernetes, розумними періодами пільгового завершення та зворотними викликами вибору лідера, щоб активний узгоджувач відступав чисто.

---

## Частина 6: Вибір лідера

### 6.1 Навіщо вибір лідера?

Коли ви запускаєте кілька реплік свого контролера для високої доступності, лише **одна** має активно узгоджувати в кожен момент, якщо контролер явно не спроєктований для багатолідерної роботи. Кілька активних узгоджувачів можуть змагатися за оновлення статусу, дублювати Події та боротися за дочірні ресурси. Вибір лідера використовує ресурс Lease у координаційному API Kubernetes, щоб одна репліка тримала лідерство, поки інші репліки лишаються теплими резервами.

```go
// main.go — add leader election
import (
    "k8s.io/client-go/tools/leaderelection"
    "k8s.io/client-go/tools/leaderelection/resourcelock"
)

func runWithLeaderElection(ctx context.Context, kubeClient kubernetes.Interface,
    startFunc func(ctx context.Context)) {

    id, err := os.Hostname()
    if err != nil {
        klog.Warningf("Could not determine hostname for leader identity, using empty string: %v", err)
    }

    lock := &resourcelock.LeaseLock{
        LeaseMeta: metav1.ObjectMeta{
            Name:      "webapp-controller-leader",
            Namespace: "webapp-system",
        },
        Client: kubeClient.CoordinationV1(),
        LockConfig: resourcelock.ResourceLockConfig{
            Identity: id,
        },
    }

    leaderelection.RunOrDie(ctx, leaderelection.LeaderElectionConfig{
        Lock:            lock,
        LeaseDuration:   15 * time.Second,
        RenewDeadline:   10 * time.Second,
        RetryPeriod:     2 * time.Second,
        Callbacks: leaderelection.LeaderCallbacks{
            OnStartedLeading: func(ctx context.Context) {
                klog.Info("Became leader, starting controller")
                startFunc(ctx)
            },
            OnStoppedLeading: func() {
                klog.Info("Lost leadership, shutting down")
                os.Exit(0)
            },
            OnNewLeader: func(identity string) {
                if identity == id {
                    return
                }
                klog.Infof("New leader elected: %s", identity)
            },
        },
        ReleaseOnCancel: true,
    })
}
```

Вибір лідера не є заміною ідемпотентності. Активний лідер усе одно може зазнати збою після часткової дії, і наступний лідер мусить уміти узгодити стан, який він успадковує. Ставтеся до Lease як до способу зменшити непотрібних паралельних записувачів, а не як до гарантії, що лише один процес коли-небудь торкався ресурсу протягом його життя.

### 6.2 Параметри вибору лідера

| Параметр | Типове значення | Опис |
|-----------|--------------|-------------|
| LeaseDuration | 15с | Скільки нелідер чекає, перш ніж спробувати захопити |
| RenewDeadline | 10с | Скільки лідер має на поновлення, перш ніж втратить lease |
| RetryPeriod | 2с | Як часто повторювати спробу захоплення lease |
| ReleaseOnCancel | true | Звільнити lease при граційному завершенні |

Зупиніться та спрогнозуйте: у вас працюють дві репліки контролера, і Репліка A є лідером. Репліка A зазнає мережевого розриву й не може дістатися API-сервера, але її процес усе ще працює. Використайте тривалість lease, термін поновлення та період повтору, щоб пояснити, коли Репліка B може стати лідером і чому Репліка A мусить припинити узгодження, щойно вона більше не може поновити свій lease.

### 6.3 Лідерство та безпека узгодження

Вибір лідера захищає кластер від зайвих паралельних записувачів, але він також вносить часові вікна, які ваш код узгодження мусить терпіти. Лідер може втратити доступ до API-сервера, не зуміти поновити свій Lease і ще короткий час продовжувати працювати, доки його зворотний виклик не зупинить процес. Інша репліка може пізніше захопити лідерство й побачити дітей, яких старий лідер частково змінив. Ідемпотентне узгодження — це те, що робить таку передачу безпечною.

Часові налаштування Lease — це операційні компроміси. Короткі тривалості швидко перемикають лідера, але підвищують чутливість до затримок API-сервера та мережевих збоїв. Довші тривалості зменшують випадкову зміну лідерства, але подовжують час до того, як резервна репліка перебере на себе після справжнього збою. Універсального налаштування немає; обирайте значення на основі того, наскільки руйнівним було б дублювання узгодження, як швидко контролер мусить виправляти дрейф і наскільки стабільна мережа площини управління.

Вам також слід вирішити, що роблять нелідери. У багатьох контролерах нелідери запускають клієнтів і чекають усередині циклу вибору лідера, не запускаючи робітників. Це тримає їх готовими швидко перебрати керування, уникаючи водночас записів. Їм усе одно потрібен коректний RBAC для ресурсу Lease, і їм усе одно потрібні логи, які роблять стан лідерства зрозумілим під час операцій, бо здоровий резерв інакше може виглядати бездіяльним чи зламаним.

---

## Патерни та антипатерни

Найкращі контролери client-go виглядають консервативно ззовні, бо вони трактують кожне узгодження як спробу полагодження, а не як реакцію на одну подію. Вони читають з кешів, пишуть лише тоді, коли фактичний стан відрізняється від бажаного, та виявляють прогрес через статус, Події й логи. Антипатерни зазвичай з'являються, коли код контролера запозичує звички сервісів типу «запит-відповідь», як-от виконання важкої роботи в обробниках чи припущення, що процес запам'ятає те, що щойно зробив.

| Патерн | Коли застосовувати | Чому це працює |
|---------|-------------|--------------|
| Ставте в чергу ключі, а не об'єкти | Застосовуйте це майже для кожного обробника подій Informer'а | Дублікати ключів природно усуваються, і це змушує робітників читати поточний стан кешу перед дією |
| Спостерігайте за власними ресурсами | Застосовуйте це, коли батько володіє Deployment'ами, Service'ами, Job'ами, ConfigMap'ами чи Secret'ами | Дрейф дитини стає ще одним тригером узгодження батька замість прихованого стану |
| Патчте статус окремо | Застосовуйте це, коли CRD має підресурс статусу | Записувачі специфікації та статусу уникають боротьби за той самий шлях оновлення об'єкта |
| Записуйте Події Kubernetes для переходів, дієвих для користувача | Застосовуйте це для створень, оновлень, постійних збоїв валідації та повторюваних тимчасових збоїв | Користувачі можуть діагностувати ресурс через `kubectl describe`, не читаючи спершу логи контролера |

| Антипатерн | Що йде не так | Краща альтернатива |
|--------------|-----------------|--------------------|
| Обробка подій прямо в обробниках | Шлях Informer'а блокується, оновлення кешу відстають, тиск watch росте | Додайте ключ простір-імен/ім'я до черги й дайте робітникам узгодити |
| Порівняння подій замість станів | Пропущені події під час перезапуску можуть назавжди лишити дітей застарілими | Щоразу порівнюйте бажаний стан батька з фактичними дочірніми ресурсами |
| Повторення всіх помилок вічно | Недійсні специфікації стають «отруйними» елементами черги, а логи ховають корисні збої | Класифікуйте помилки, обмежуйте швидкість тимчасових збоїв та виносьте постійні збої в статус |
| Прямі читання API в гарячих шляхах | Великі кластери створюють зайве навантаження на API-сервер та нерівну затримку | Надавайте перевагу Lister'ам на основі спільних кешів Informer'ів для спостережуваного стану |

Ці патерни також створюють межу масштабування. Informer'и та Lister'и роблять читання дешевими після синхронізації кешу, тоді як workqueue дає вам зворотний тиск та контроль повторних спроб для записів. Якщо вашому контролеру потрібно викликати зовнішню систему, ставтеся до цього виклику, як до будь-якої іншої ненадійної залежності: зробіть його ідемпотентним, обмежте повтори й уникайте його виконання всередині зворотного виклику Informer'а.

## Каркас прийняття рішень

Використовуйте цей каркас прийняття рішень, коли обираєте, як структурувати контролер client-go чи діагностуєте той, що вже відмовляє. Головне питання не в тому, чи можете ви змусити контролер реагувати швидше; головне питання в тому, чи базується кожна реакція на достатньо повному баченні поточного стану, щоб бути безпечною. Швидше зламане узгодження лише раніше пошкоджує кластер.

Почніть зі зміненого ключа об'єкта, потім вирішіть, чи це первинний `WebApp`, чи власна дитина, яку треба відобразити назад на батька. Після цього переконайтеся, що кеші синхронізовані, перш ніж читати бажаний і фактичний стан з Lister'ів. Якщо фактичний стан уже збігається, оновіть статус за потреби й забудьте ключ. Якщо потрібна дія, створіть, оновіть, видаліть чи пропатчте дочірній ресурс, потім класифікуйте будь-який збій як повторюваний чи постійний, перш ніж вирішувати, обмежити швидкість ключа чи винести зрозумілу користувачеві умову.

| Рішення | Надавайте перевагу цьому | Уникайте цього |
|----------|-------------|------------|
| Доступ до батьківського об'єкта | Читайте з кешу Informer'а під час узгодження | Витягуйте з API-сервера для кожного елемента черги |
| Володіння дочірнім ресурсом | Встановлюйте контролерні посилання на власника для створених дітей | Покладайтеся лише на угоди про іменування для прибирання |
| Виявлення дрейфу | Спостерігайте за вторинними ресурсами й ставте в чергу батька | Чекайте зміни специфікації батька, перш ніж лагодити дітей |
| Стратегія повторних спроб | Використовуйте типізовані черги з обмеженням швидкості та обмеженою обробкою «отруйних» елементів | Ставте в чергу заново негайно в тісному циклі |
| Висока доступність | Додайте вибір лідера на основі Lease й тримайте узгодження ідемпотентним | Припускайте, що одна репліка означає відсутність збоїв процесу чи ноди |

Який підхід ви обрали б тут і чому: якщо користувач вручну редагує згенерований Service, щоб змінити його порт, чи має контролер негайно пропатчити його назад, лишити як є, чи звітувати про конфлікт у статусі? Відповідь на це питання змушує вас визначити, чи є порт Service частиною керованого бажаного стану, чи дозволено користувачам кастомізувати дітей і як контролер повідомляє межі володіння.

Корисне правило — зробити володіння явним, перш ніж писати код узгодження. Якщо `WebApp` володіє образом Deployment, кількістю реплік, мітками, селектором і портом Service, то контролер має лагодити дрейф у цих полях, а користувачі мають редагувати батька замість дітей. Якщо деякі поля дитини навмисно керовані користувачем, контролер має уникати їх перезапису й має документувати цю межу в API. Неоднозначне володіння створює дивовижні контролери: одне поле мовчки лагодиться, інше ігнорується, а третє відмовляє лише під час оновлень.

Каркас також допомагає вам вирішити, коли client-go з нуля є правильним вибором для навчання чи виробництва. Використовуйте прямий client-go, коли вам потрібно зрозуміти механіку, побудувати дуже малий спеціалізований контролер чи діагностувати поведінку, приховану фреймворком вищого рівня. Надавайте перевагу controller-runtime чи Kubebuilder, коли вам потрібні згенеровані типізовані клієнти, admission-webhook'и, conversion-webhook'и, підтримка envtest, підключення менеджера та звичні угоди контролерів. Суть цього модуля не в тому, щоб відкинути фреймворки; вона в тому, щоб зробити згенерований код фреймворку зрозумілим.

Нарешті, спроєктуйте поверхні зворотного зв'язку вашого контролера до того, як інциденти змусять вас це вирішувати. Логи — для операторів контролера, Події — для людей, що оглядають ресурс, а статус — і для людей, і для автоматизації, яким потрібен довговічний спостережуваний стан. Здоровий API `WebApp` має дозволяти користувачеві відповісти на три питання, не читаючи сирцевий код: що я попросив, що спостеріг контролер і яку дію мені вжити, якщо збіжність заблоковано?

## Чи знали ви?

- **kube-controller-manager запускає багато контролерів в одному бінарному файлі**, і кожен слідує тому самому широкому патерну «спостерігай, став у чергу, узгоджуй, повторюй», який ви тут практикуєте. Точний набір змінюється між релізами Kubernetes, але архітектурна ідея стабільна: спеціалізовані цикли безперервно приводять до збіжності різні зв'язки ресурсів.

- **Протокол watch Kubernetes парується з LIST задля коректності**, тож контролерам не потрібна досконала пам'ять про кожну історичну подію. На старті чи повторному списку Informer встановлює поточний стан, а потім оновлення watch тримають локальний кеш свіжим, починаючи з тієї версії ресурсу.

- **API `Lease` з coordination.k8s.io став стандартним легким примітивом для вибору лідера**, замінивши старіші патерни, що використовували важчі ресурси для тієї самої роботи координації. Lease малий, швидкий до оновлення й легкий для контролерів у поновленні на короткому такті.

- **Підресурси статусу навмисно відокремлюють бажаний стан від спостережуваного**, ось чому контролер може патчити `.status.readyReplicas`, не перезаписуючи `.spec.replicas` користувача. Це відокремлення — одна з найчистіших ознак того, що власний ресурс дозрів зі збереженої схеми в справжній API Kubernetes.

---

## Типові помилки

| Помилка | Чому вона трапляється | Як її виправити |
|---------|----------------|---------------|
| Не встановлено OwnerReferences | Контролер успішно створює дітей, тож про прибирання легко забути аж до тестування видалення | Завжди встановлюйте контролерне посилання на власника для згенерованих Deployment'ів та Service'ів |
| Немає обмеження швидкості черги | Ранні демо часто ставлять у чергу заново негайно, бо це виглядає простіше за класифікацію помилок | Використовуйте типізовану чергу з обмеженням швидкості й викликайте `Forget` після успішного узгодження |
| Один потік робітника назавжди | Перша реалізація працює в крихітній лабораторній і ніколи не переглядається для виробничого навантаження | Почніть з малої кількості робітників, виміряйте глибину й затримку черги, а потім налаштовуйте навмисно |
| Не обробляються надгробки | Обробники видалення тестуються лише на звичайних об'єктах і пропускають випадки `DeletedFinalStateUnknown` | Перевіряйте тип подій видалення й розгортайте надгробки перед читанням посилань на власника |
| Жорстко закодований простір імен | Локальні приклади використовують один простір імен, потім контролер розгортають загальнокластерно | Парсіть простір імен з ключа черги й передавайте його через кожен виклик lister'а та клієнта |
| Немає граційного завершення | Процес трактують як скрипт замість робочого навантаження Kubernetes | Використовуйте обробку сигналів, скасування контексту, завершення черги та перевірки виходу робітників |
| Ігнорування помилок `IsNotFound` | Видалені ресурси виглядають як збої, коли логіка узгодження очікує, що кожен ключ розв'яжеться | Трактуйте «не знайдено» як успішну збіжність для видалених батьків чи дітей |

---

## Тест

<details>
<summary>Сценарій: ваш контролер не працював десять хвилин через збій ноди. За цей час користувачі створили багато ресурсів `WebApp` і видалили кілька. Коли ваш контролер перезапускається, він не отримує історичний потік подій `ADDED` та `DELETED`. Як йому все одно вдається привести кластер до правильного стану?</summary>

Контролери Kubernetes використовують узгодження за рівнем, а не логіку за фронтом, тобто вони реагують на поточну різницю станів, а не на окремі події зміни. Коли контролер перезапускається, його Informer'и виконують операцію LIST, щоб заповнити локальний кеш поточним станом усіх ресурсів `WebApp`. Потім контролер порівнює цей бажаний стан з фактичним станом наявних Deployment'ів та Service'ів. Оскільки він не покладається на повтори історичних подій, він самовідновлюється й обробляє чистий результат усіх змін, що сталися під час простою.
</details>

<details>
<summary>Сценарій: користувач запускає скрипт, який патчить той самий ресурс `WebApp` багато разів за кілька секунд, щоб оновити анотації. Informer вашого контролера отримує багато подій `MODIFIED`. Чому контролер має уникати узгодження кожної проміжної версії об'єкта?</summary>

Контролери ставлять у чергу рядкові ключі на кшталт `namespace/name`, а не передають у workqueue повні об'єкти ресурсів напряму. Workqueue усуває дублікати однакових ключів, доданих до того, як робітник їх обробить, що зменшує зайву роботу під час сплесків. На момент, коли робітник дістає ключ з черги й вибирає об'єкт з локального кешу Informer'а, він читає найновішу версію ресурсу. Це робить так, що узгодження фокусується на поточному стані, а не на галасливих проміжних переходах.
</details>

<details>
<summary>Сценарій: ви виводите з експлуатації `WebApp` з іменем `frontend-app` командою `kubectl delete webapp frontend-app`. `syncHandler` контролера помічає видалення, але код явно не видаляє пов'язані Deployment і Service. Як прибираються дочірні ресурси?</summary>

Дочірні ресурси прибираються збирачем сміття Kubernetes, а не власним кодом видалення в цьому контролері. Коли контролер спершу створив Deployment і Service, він приєднав `OwnerReference`, що вказує назад на батьківський ресурс `WebApp`. Коли API-сервер обробляє видалення `WebApp`, збирач сміття виявляє ці посилання й ініціює каскадне видалення залежних. Цей механізм дає надійне прибирання, не вимагаючи finalizer'ів для цього простого зв'язку «батько-дитина».
</details>

<details>
<summary>Сценарій: ви прибираєте `cache.WaitForCacheSync` з `Run`, щоб пришвидшити запуск. При перезапуску робітники одразу обробляють ключі `WebApp`, і контролер починає створювати Deployment'и, які вже існують. Чому це сталося?</summary>

Без очікування синхронізації кешу робітники починають фазу «Аналізуй», поки локальні кеші Informer'ів порожні чи частково заповнені. Коли `syncHandler` питає `deploymentLister`, чи існує Deployment, кеш може помилково повернути «не знайдено», бо він не завершив отримання стану з API-сервера. Контролер інтерпретує цей відсутній запис кешу як відсутній фактичний стан і видає виклик Create. `WaitForCacheSync` захищає контролер від дії на основі неповного бачення світу.
</details>

<details>
<summary>Сценарій: ваш контролер намагається створити Deployment для `WebApp`, але API-сервер відхиляє запит, бо admission-webhook перевищив час очікування. `syncHandler` повертає помилку. Як workqueue має повторити це, не перевантажуючи API-сервер?</summary>

Коли `syncHandler` повертає повторювану помилку, робітник має викликати `AddRateLimited`, щоб повернути ключ у workqueue під відкочуванням. Обмежувач швидкості затримує наступну спробу для цього ключа й не дає тісному циклу гамселити API-сервер під час тимчасового збою. Якщо збої тривають за межами налаштованого бюджету повторів, контролер має забути чи класифікувати ключ і виявити достатньо статусу чи Подій, щоб оператори побачили проблему. Важлива поведінка — обмежені повтори з корисним зворотним зв'язком, а не нескінченна негайна повторна обробка.
</details>

<details>
<summary>Сценарій: адміністратор запускає `kubectl scale deployment my-webapp --replicas=0`, перевизначаючи Deployment, що належить `WebApp`, чия специфікація просить три репліки. Deployment невдовзі масштабується назад угору. Як контролер виявив і виправив цей дрейф?</summary>

Контролер спостерігає за вторинними ресурсами, як-от Deployment'ами та Service'ами, на додачу до первинного ресурсу `WebApp`. Коли адміністратор масштабував Deployment, API-сервер видав подію modified для цього Deployment, і Informer Deployment доставив її контролеру. Обробник події дослідив посилання на власника Deployment, ідентифікував батьківський `WebApp` і поставив у чергу батьківський ключ. Наступне узгодження порівняло бажані репліки з фактичними й оновило Deployment назад до керованого стану.
</details>

<details>
<summary>Сценарій: робітник успішно узгоджує `WebApp` і викликає `queue.Done(key)`, але забуває `queue.Forget(key)`. Пізніше той самий ключ один раз відмовляє через конфлікт і отримує дивовижно довгу затримку повтору. Що спричинило затримку?</summary>

`queue.Done(key)` сигналізує, що робітник завершив обробку елемента, але він не очищає історію збоїв обмежувача швидкості для цього ключа. `queue.Forget(key)` відповідає за скидання стану відкочування після успіху. Якщо успішне узгодження пропускає `Forget`, обмежувач швидкості може пам'ятати попередні збої й застосувати більшу затримку до пізнішого непов'язаного збою. Контролери мають викликати `Forget` після успішного узгодження, щоб нові збої починалися з передбаченого початкового відкочування.
</details>

---

## Практична вправа

**Завдання**: побудувати, розгорнути й протестувати повний власний контролер, який спостерігає за WebApp CR'ами та створює Deployment'и й Service'и.

Сценарій вправи: ви готуєте невеликий платформовий API для прикладних команд, який має створювати Deployment і Service з єдиного ресурсу `WebApp`. Мета не в тому, щоб відправити саме цей контролер незмінним у виробництво; мета в тому, щоб довести, що ви можете підключити Informer'и, workqueue, узгодження, посилання на власника, оновлення статусу та виправлення дрейфу без опори на фреймворк. Тримайте відкритим термінал для логів контролера, поки ви виконуєте перевірки `kubectl`, бо найшвидший спосіб опанувати цикл — спостерігати, як ключ рухається від події до черги й до дії.

Використайте цей блок налаштування, щоб створити одноразовий кластер kind та встановити спрощений CRD `WebApp`, за яким спостерігає контролер. CRD містить підресурс статусу та стовпці друку, щоб ви могли бачити спостережуваний стан контролера прямо з `kubectl get`.
```bash
# Create a cluster
kind create cluster --name controller-lab

# Apply the WebApp CRD from Module 1.2
# (use the simplified version below)
cat << 'EOF' | kubectl apply -f -
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: webapps.apps.kubedojo.io
spec:
  group: apps.kubedojo.io
  names:
    kind: WebApp
    listKind: WebAppList
    plural: webapps
    singular: webapp
    shortNames: ["wa"]
  scope: Namespaced
  versions:
  - name: v1beta1
    served: true
    storage: true
    subresources:
      status: {}
    additionalPrinterColumns:
    - name: Image
      type: string
      jsonPath: .spec.image
    - name: Replicas
      type: integer
      jsonPath: .spec.replicas
    - name: Ready
      type: integer
      jsonPath: .status.readyReplicas
    - name: Phase
      type: string
      jsonPath: .status.phase
    - name: Age
      type: date
      jsonPath: .metadata.creationTimestamp
    schema:
      openAPIV3Schema:
        type: object
        properties:
          spec:
            type: object
            required: ["image"]
            properties:
              image:
                type: string
              replicas:
                type: integer
                minimum: 1
                maximum: 50
                default: 2
              port:
                type: integer
                minimum: 1
                maximum: 65535
                default: 8080
          status:
            type: object
            properties:
              readyReplicas:
                type: integer
              phase:
                type: string
EOF
```

Опрацюйте ці шість завдань по порядку, тримаючи процес контролера видимим, поки ви застосовуєте ресурси з другого термінала. Кожне завдання додає один шар доказів: компіляція, синхронізація кешу, спостереження батька, створення дитини, виправлення дрейфу та прибирання через збирач сміття.

1. **Створіть проєкт і залежності**. Це завдання дає вам чистий Go-модуль і завантажує бібліотеки Kubernetes, які використовує збережений код контролера. Тримайте проєкт поза репозиторієм KubeDojo, щоб згенеровані зміни `go.sum` та локальні бінарні файли ніколи не з'являлися в цьому документаційному worktree.
```bash
mkdir -p ~/extending-k8s/webapp-controller && cd ~/extending-k8s/webapp-controller
go mod init github.com/example/webapp-controller
go get k8s.io/client-go@latest k8s.io/apimachinery@latest k8s.io/api@latest k8s.io/klog/v2@latest
```

2. **Створіть файли сирцевого коду** з коду в Частинах 3.2, 3.3 та 3.4. Покладіть визначення типів, реалізацію контролера та головну точку входу в окремі файли, щоб помилки компілятора вказували на ті самі концептуальні межі, що використовуються в уроці.

3. **Зберіть і запустіть контролер локально**. Запустіть його з докладним логуванням і лишіть процес працювати, щоб він міг спостерігати за кластером kind через ваш kubeconfig. Перш ніж створювати `WebApp`, шукайте рядки логів про синхронізацію кешу; якщо кеші не синхронізуються, узгодження не повинно починатися.
```bash
go build -o webapp-controller .
./webapp-controller -v=2
```

4. **Створіть `WebApp` з іншого термінала**. Це перший повний прохід «Спостерігай-Аналізуй-Дій»: з'являється батьківський об'єкт, ключ ставиться в чергу, контролер створює дочірні ресурси, а статус починає відображати готовність Deployment.
```bash
cat << 'EOF' | kubectl apply -f -
apiVersion: apps.kubedojo.io/v1beta1
kind: WebApp
metadata:
  name: demo-app
spec:
  image: nginx:1.27
  replicas: 3
  port: 80
EOF
```

5. **Перевірте створення, володіння, Події та самовідновлення**. Виконайте перевірки до й після видалення згенерованого Deployment, щоб побачити і створення, спричинене батьком, і виправлення дрейфу, спричинене дитиною. Важливий доказ не лише в тому, що ресурси існують, а в тому, що Deployment контролюється `WebApp` і що Події контролера описують дії.
```bash
# Check WebApp status
kubectl get webapp demo-app

# Check created Deployment
kubectl get deployment demo-app
kubectl describe deployment demo-app | grep "Controlled By"

# Check created Service
kubectl get svc demo-app

# Check events
kubectl get events --sort-by=.lastTimestamp | grep webapp
```

```bash
# Delete the Deployment — controller should recreate it
kubectl delete deployment demo-app
sleep 5
kubectl get deployment demo-app

# Scale the WebApp
kubectl patch webapp demo-app --type=merge -p '{"spec":{"replicas":5}}'
sleep 5
kubectl get deployment demo-app
```

6. **Протестуйте каскад видалення та прибирання**. Видалення батька має прибрати дочірні Deployment і Service через збирач сміття Kubernetes, бо контролер встановив посилання на власника, коли їх створював. Після перевірки видаліть кластер kind, щоб лабораторна не лишила за собою локальних робочих навантажень.
```bash
kubectl delete webapp demo-app
sleep 5
kubectl get deployment demo-app     # Should be gone (GC'd via OwnerRef)
kubectl get svc demo-app             # Should be gone
```

7. **Прибирання**:
```bash
kind delete cluster --name controller-lab
```

Використовуйте цей контрольний список як контракт завершення лабораторної, а не як вільну пропозицію. Якщо один пункт відмовляє, зіставте його з архітектурою контролера: синхронізація кешу, обробка черги, посилання на власника, watch'і дітей, патчинг статусу чи поведінка завершення.
- [ ] Контролер компілюється й стартує без помилок
- [ ] Синхронізація кешу завершується (перевірте логи)
- [ ] Створення WebApp запускає створення Deployment + Service
- [ ] Deployment має правильний OwnerReference, що вказує на WebApp
- [ ] Видалення Deployment змушує контролер відтворити його
- [ ] Оновлення реплік WebApp оновлює Deployment
- [ ] Видалення WebApp каскадно видаляє Deployment + Service
- [ ] Записуються Події Kubernetes для дій створення/оновлення
- [ ] Ctrl+C запускає граційне завершення

<details>
<summary>Нотатки розв'язання для лабораторної</summary>

Якщо контролер стартує, але дочірні ресурси не з'являються, спершу перевірте синхронізацію кешу, потім підтвердьте, що група, версія та plural CRD збігаються з `webappGVR` у контролері. Якщо Deployment існує, але видалення `WebApp` лишає його, перевірте посилання на власника Deployment і переконайтеся, що UID вказує на батька, а не лише на збіжне ім'я. Якщо самовідновлення не відбувається після видалення чи масштабування Deployment, вторинний Informer Deployment, імовірно, не ставить у чергу батьківський ключ з посилання на власника.
</details>

---

## Джерела

- https://kubernetes.io/docs/concepts/architecture/controller/
- https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/
- https://kubernetes.io/docs/tasks/extend-kubernetes/custom-resources/custom-resource-definitions/
- https://kubernetes.io/docs/concepts/overview/working-with-objects/owners-dependents/
- https://kubernetes.io/docs/concepts/architecture/garbage-collection/
- https://kubernetes.io/docs/reference/using-api/api-concepts/
- https://kubernetes.io/docs/reference/using-api/server-side-apply/
- https://kubernetes.io/docs/reference/kubernetes-api/cluster-resources/lease-v1/
- https://pkg.go.dev/k8s.io/client-go/tools/cache
- https://pkg.go.dev/k8s.io/client-go/util/workqueue
- https://pkg.go.dev/k8s.io/client-go/tools/leaderelection
- https://pkg.go.dev/k8s.io/client-go/tools/record

---

## Наступний модуль

[Модуль 1.4: Патерн оператора та Kubebuilder](../module-1.4-kubebuilder/) — використовуйте фреймворк Kubebuilder, щоб будувати оператори з меншою кількістю шаблонного коду та більшою структурою.
