---
title: "Dynamic Routing - Fundamentals"
aliases:
  - Dynamic Routing
  - Introduction to Dynamic Routing
tags:
  - ccna
  - routing
  - dynamic-routing
  - administrative-distance
  - metrics
  - ecmp
  - floating-static-route
source: "CCNA 200-301 Day 24 - Introduction to Dynamic Routing"
date: 2026-07-27
---

# Dynamic Routing: Fundamentals

## Summary

Dynamic routing protocols allow routers to advertise reachable networks, form neighbor relationships, learn alternate paths, and react to network changes automatically.

When several routes exist for the **same destination network and mask**:

1. **Administrative distance (AD)** selects the preferred route source or routing protocol.
2. **Metric** selects the best route learned by that same protocol.
3. If multiple routes from the same protocol have the same metric, the router can install all of them and perform **Equal-Cost Multi-Path (ECMP)** load balancing.

> [!important] The key distinction
> **AD compares different route sources. Metric compares routes from the same routing protocol. Lower is preferred in both cases.**

---

## Network routes and host routes

- A **network route** points to a network or subnet. Its prefix length is shorter than `/32`.
- A **host route** points to one specific IPv4 address and uses a `/32` prefix.

Examples:

- `192.168.4.0/24` - network route
- `10.0.12.1/32` - host route

Directly connected interfaces commonly create both:

- `C` - connected network route
- `L` - local `/32` host route for the router's own interface address

---

## Static routing versus dynamic routing

### Static routing

A network administrator manually enters each route. Static routes are simple and predictable, but they do not automatically discover a new path when the topology changes.

If a link on a manually configured path fails, a replacement route must already exist or the administrator must change the configuration.

### Dynamic routing

Routers running a dynamic routing protocol:

- Advertise the routes they know
- Form **adjacencies**, **neighbor relationships**, or **neighborships**
- Exchange routing information with adjacent routers
- Select superior routes
- Update their routing tables as the topology changes
- Withdraw routes that are no longer reachable

For example, a router connected to `192.168.4.0/24` can advertise that network to its neighbor. That neighbor can advertise it farther through the network.

### Why dynamic routing is useful

Dynamic routing is especially valuable in larger or changing networks because it:

- Reduces the amount of manual route configuration
- Learns remote networks automatically
- Can discover redundant paths
- Can reconverge after a link or neighbor failure
- Scales better than configuring every route manually

**Convergence** is the process by which routers learn about a change and agree on the current best paths.

---

## Types of dynamic routing protocols

Dynamic routing protocols are first divided by where they are used.

### Interior Gateway Protocols (IGPs)

An **IGP** shares routes inside one **autonomous system (AS)**.

An autonomous system is a network or collection of networks controlled by one organization, such as a company or service provider.

IGPs in the slides:

- RIP
- EIGRP
- OSPF
- IS-IS

### Exterior Gateway Protocols (EGPs)

An **EGP** shares routes between autonomous systems.

- **BGP** is the path-vector EGP used to exchange routes between organizations and across the Internet.

### Classification by algorithm

| Scope | Algorithm | Protocols |
|---|---|---|
| IGP | Distance vector | RIP, EIGRP |
| IGP | Link state | OSPF, IS-IS |
| EGP | Path vector | BGP |

> [!note]
> EIGRP is often described as an advanced distance-vector protocol. For the classification used in this course, place it in the distance-vector family.

---

## Distance-vector routing protocols

Distance-vector protocols send the following information to directly connected neighbors:

- Known destination networks
- The metric required to reach each destination

They are often described as **routing by rumor** because a router does not build a complete map of the network. It trusts and processes information advertised by its neighbors.

The name describes what the router learns:

- **Distance** - the metric to the destination
- **Vector** - the direction or next-hop router

### Example

R4 may advertise `192.168.4.0/24` with a metric of 1. A neighboring router adds its own distance and advertises the network onward with a higher metric.

Older examples include RIPv1 and Cisco's IGRP. IGRP was later developed into EIGRP.

---

## Link-state routing protocols

With a link-state protocol, each router develops a **connectivity map** of the network.

The general process is:

1. A router advertises information about its interfaces and connected networks.
2. The information is passed through the routing domain.
3. Routers build matching topology information.
4. Each router independently calculates its best routes.

Compared with traditional distance-vector protocols, link-state protocols:

- Share more topology information
- Use more router CPU and memory
- Generally react to network changes faster
- Calculate routes independently from a common topology view

OSPF and IS-IS are link-state IGPs.

---

## Routing protocol metrics

A **metric** is a protocol-specific value used to rank routes learned by the **same routing protocol**. A lower metric is preferred.

Different protocols calculate metrics differently, so an OSPF metric cannot be directly compared with an EIGRP or RIP metric.

| Protocol | Metric | How it works |
|---|---|---|
| RIP | Hop count | Each router in the path is one hop. Link speed is not considered. |
| EIGRP | Composite metric | By default, uses the slowest bandwidth in the path and the total delay of the path. |
| OSPF | Cost | Each link has a bandwidth-based cost; the route metric is the sum of the link costs. |
| IS-IS | Cost | The route metric is the sum of link costs. By default, links use a cost of 10 rather than calculating it automatically from bandwidth. |

### RIP limitation

RIP treats links of all speeds equally. A slow link and a fast link both add one hop, so the lowest-hop route is not necessarily the highest-bandwidth route.

### Reading `[AD/metric]`

IOS displays a dynamically learned route with values in brackets:

```text
O 192.168.4.0/24 [110/3] via 10.0.13.2
```

- `O` - route learned through OSPF
- `110` - OSPF administrative distance
- `3` - OSPF metric
- `10.0.13.2` - next hop

For a static route:

```text
S 192.168.4.0/24 [1/0] via 10.0.12.2
```

- `1` is the default static-route AD.
- `0` is the static route's metric as displayed by IOS.

---

## Equal-Cost Multi-Path (ECMP)

If a router learns two or more routes that have all of the following in common:

- Same destination network
- Same subnet mask
- Same routing protocol
- Same metric

the router can install multiple next hops in the routing table. This is called **Equal-Cost Multi-Path (ECMP)**.

Traffic is load-balanced across the installed paths.

Example OSPF result:

```text
O 192.168.4.0/24 [110/3] via 10.0.13.2
                     [110/3] via 10.0.12.2
```

### ECMP with static routes

Two static routes to the same prefix also form equal-cost paths when their AD values are equal:

```cisco
ip route 192.168.4.0 255.255.255.0 10.0.12.2
ip route 192.168.4.0 255.255.255.0 10.0.13.2
```

The routing table can install both:

```text
S 192.168.4.0/24 [1/0] via 10.0.13.2
                     [1/0] via 10.0.12.2
```

> [!important]
> ECMP occurs because the routes have equal costs. It is not the same as a backup route with a higher AD.

---

## Administrative distance

**Administrative distance (AD)** ranks the trustworthiness of different route sources. A lower AD is preferred.

AD is needed because different protocols use incompatible metrics. For example:

- An OSPF route might have a metric of 30.
- An EIGRP route might have a metric of 33,280.

Those values cannot be compared. The router first compares the protocols' AD values.

### Default administrative distances

| Route source | Default AD |
|---|---:|
| Directly connected | 0 |
| Static route | 1 |
| External BGP (eBGP) | 20 |
| Internal EIGRP | 90 |
| IGRP | 100 |
| OSPF | 110 |
| IS-IS | 115 |
| RIP | 120 |
| External EIGRP | 170 |
| Internal BGP (iBGP) | 200 |
| Unusable route | 255 |

An AD of **255** means the router does not trust the route source and will not install the route.

### Important AD order for CCNA

```text
Connected 0
Static 1
eBGP 20
EIGRP 90
OSPF 110
IS-IS 115
RIP 120
EIGRP external 170
iBGP 200
Unusable 255
```

### Route-selection example

R1 learns these routes to `10.1.1.0/24`:

- RIP via `192.168.1.1`, metric 5
- RIP via `192.168.2.1`, metric 3
- OSPF via `192.168.3.1`, metric 10

The router installs the **OSPF route**.

Why:

1. OSPF AD 110 is lower than RIP AD 120.
2. Therefore OSPF wins before RIP metrics are considered.
3. The RIP route with metric 3 does not beat OSPF merely because `3` is lower than OSPF's `10`; those are metrics from different protocols.

---

## The decision process

For routes to the same destination and prefix length:

```text
Different route sources?
        |
        v
Choose the lowest administrative distance
        |
        v
Multiple routes from the winning protocol?
        |
        v
Choose the lowest metric
        |
        v
Multiple routes with the same metric?
        |
        v
Install equal-cost paths with ECMP
```

### Memory aid

- **AD chooses the protocol.**
- **Metric chooses the path.**
- **Equal metric can choose multiple paths.**

---

## Changing the AD of a static route

The optional value at the end of an IPv4 static-route command changes its administrative distance:

```cisco
ip route destination mask next-hop administrative-distance
```

Example:

```cisco
ip route 10.0.0.0 255.0.0.0 10.0.13.2 100
```

The route appears as:

```text
S 10.0.0.0/8 [100/0] via 10.0.13.2
```

The configured AD can be from 1 through 255, although 255 makes the route unusable.

---

## Floating static routes

A **floating static route** is a backup static route configured with an AD higher than the preferred dynamic route.

Example: EIGRP internal routes have an AD of 90. A static route configured with AD 100 is less preferred:

```cisco
ip route 10.0.0.0 255.0.0.0 10.0.13.2 100
```

While the EIGRP route exists:

- EIGRP wins because `90 < 100`.
- The floating static route is not installed as the active route.

If the dynamic route disappears:

- The static route becomes the best available route.
- It is installed and provides backup reachability.

Typical causes of the dynamic route disappearing include:

- The remote router stops advertising the prefix
- An interface fails
- A routing-protocol neighbor adjacency is lost

> [!warning]
> The floating static route's AD must be **higher** than the dynamic protocol it backs up. If it is lower, the static route becomes the primary route.

---

## Verification commands

```cisco
show ip route
show ip route 192.168.4.0
```

When reading the routing table, check:

- Route code: `C`, `L`, `S`, `R`, `D`, `O`, and so on
- Destination prefix
- `[AD/metric]`
- Next-hop address
- Exit interface
- Whether multiple equal-cost next hops are installed

Common route codes from the slides:

| Code | Meaning |
|---|---|
| `L` | Local |
| `C` | Connected |
| `S` | Static |
| `R` | RIP |
| `D` | EIGRP |
| `EX` | EIGRP external |
| `O` | OSPF |
| `B` | BGP |

---

## Quiz review

### Quiz 1

R1 learns routes to `192.168.1.0/24` through RIP, EIGRP, OSPF, and IS-IS. Which route is installed?

**Answer: EIGRP only.**

Internal EIGRP has AD 90, lower than OSPF 110, IS-IS 115, and RIP 120.

### Quiz 2

Which type of protocol is called routing by rumor?

**Answer: Distance vector.**

Distance-vector routers learn destination, distance, and direction from neighbors rather than building a complete link-state map.

### Quiz 3

R1 learns two RIP routes to `172.16.0.0/16`. Both have a metric of 5, one through `10.0.0.1` and one through `10.1.0.1`. Which routes are installed?

**Answer: Both routes.**

They have the same destination, prefix length, protocol, and metric, so the router can install them as ECMP routes.

---

## Exam takeaways

- Dynamic routing protocols advertise reachable networks and form neighbor relationships.
- IGPs operate inside an autonomous system; EGPs operate between autonomous systems.
- RIP and EIGRP are classified as distance vector.
- OSPF and IS-IS are link state.
- BGP is path vector.
- Distance vector is known as routing by rumor.
- A lower metric is better, but metrics only compare routes from the same protocol.
- A lower administrative distance is preferred between different route sources.
- Memorize the common AD values, especially connected 0, static 1, EIGRP 90, OSPF 110, IS-IS 115, and RIP 120.
- `[110/3]` means AD 110 and metric 3.
- Equal-cost routes can be installed together using ECMP.
- A floating static route has an AD higher than the dynamic route it backs up.

## Related notes

- [[Static Routing]]
- [[EtherChannel - Link Aggregation]]
- [[Rapid Spanning Tree Protocol (RSTP)]]