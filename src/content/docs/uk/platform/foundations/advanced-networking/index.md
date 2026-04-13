---
title: "Просунуті мережі"
slug: "uk/platform/foundations/advanced-networking/index"
sidebar:
  order: 0
  label: "Просунуті мережі"
en_commit: "47bf257c3ec7632099185c630faf64d73e48caea"
en_file: "src/content/docs/platform/foundations/advanced-networking/index.md"
---
**Мережі поза межами Kubernetes — що відбувається, коли трафік потрапляє у реальний світ.**

Мережі Kubernetes забезпечують зв'язок між подами (pod-to-pod communication). Проте у продакшені трафік проходить крізь DNS-резолвери, вузли CDN, правила WAF, точки BGP-пірингу та балансувальники навантаження ще до того, як потрапить у ваш кластер. Ці модулі охоплюють інфраструктуру, яка з'єднує ваші кластери з інтернетом.

---

## Модулі

| # | Модуль | Час | Що ви вивчите |
|---|--------|------|-------------------|
| 1.1 | [Масштабований DNS та глобальне керування трафіком](module-1.1-dns-at-scale/) | 3 год | Anycast, GeoDNS, DNSSEC, маршрутизація за затримками |
| 1.2 | [CDN та межові обчислення (Edge Computing)](module-1.2-cdn-edge/) | 2.5 год | Архітектура PoP, інвалідація кешу, edge-функції |
| 1.3 | [WAF та протидія DDoS-атакам](module-1.3-waf-ddos/) | 2.5 год | Правила OWASP, rate limiting, керування ботами |
| 1.4 | [BGP та магістральна маршрутизація](module-1.4-bgp-routing/) | 3.5 год | AS-піринг, вибір шляху, Direct Connect |
| 1.5 | [Глибоке занурення у хмарне балансування](module-1.5-load-balancing/) | 3 год | L4/L7, Proxy Protocol, session affinity |
| 1.6 | [Мережі Zero Trust та альтернативи VPN](module-1.6-zero-trust/) | 2.5 год | BeyondCorp, IAP, Tailscale, mTLS |

**Загальний час**: ~17 годин

---

## Попередні вимоги

- Базові знання DNS та HTTP
- Kubernetes Ingress/Services (з курсу CKA або «Основи»)
- Основи мереж Linux (з курсу Linux Deep Dive)