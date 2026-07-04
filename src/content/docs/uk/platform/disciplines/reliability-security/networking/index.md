---
title: "Дисципліна Kubernetes Networking"
sidebar:
  order: 1
  label: "Kubernetes Networking"
en_commit: 47bf257c3ec7632099185c630faf64d73e48caea
---
**Від пакетів до політик — як дані рухаються у кластері та за його межами.**

Мережа Kubernetes часто вважається "чорною скринькою". Ця дисципліна відкриває її, пояснюючи все: від роботи CNI плагінів та iptables до просунутого трафік-менеджменту за допомогою Service Mesh та Gateway API. Ви навчитеся проєктувати, захищати та усувати несправності в мережевій інфраструктурі будь-якої складності.

---

## Модулі

| # | Модуль | Час | Що ви вивчите |
|---|--------|------|-------------------|
| 1.1 | [Архітектура CNI та шлях пакетів](module-1.1-cni-architecture/) | 3.5 год | Pod-to-Pod, Pod-to-Service, IPAM, veth pairs, overlay vs L3 |
| 1.2 | [Мережеві політики та безпека](module-1.2-network-policies/) | 2.5 год | Ingress/Egress правила, селектори, Cilium Network Policies |
| 1.3 | [Просунутий Ingress та Gateway API](/uk/k8s/cka/part3-services-networking/module-3.5-gateway-api/) | 3 год | Контролери, HTTPRoute, Canary розгортання на рівні мережі |
| 1.4 | [Service Mesh (Istio / Linkerd)](module-1.4-service-mesh/) | 4.5 год | Sidecars, mTLS, автоматичні повтори (retries), observability |
| 1.5 | [Мультикластерні мережі](module-1.5-multi-cluster-networking/) | 3 год | Submariner, MCS API, транзитні мережі, єдиний DNS |
| 1.6 | [Усунення мережевих несправностей](module-1.6-troubleshooting/) | 2.5 год | tcpdump, wireshark, перевірка коннективності, налагодження DNS |

**Загальний час**: ~19 годин

---

## Передумови

- [Просунуті мережі](../../../foundations/advanced-networking/) — DNS, BGP, основи трафіку
- Адміністрування Kubernetes (рівень CKA)
- Основи мереж Linux (маршрутизація, порти, протоколи)
