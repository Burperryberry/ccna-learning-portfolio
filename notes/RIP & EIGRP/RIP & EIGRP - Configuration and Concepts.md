---
title: "RIP & EIGRP - Configuration and Concepts"
aliases:
  - RIP and EIGRP
  - Routing Information Protocol
  - Enhanced Interior Gateway Routing Protocol
tags:
  - ccna
  - routing
  - rip
  - ripv2
  - eigrp
  - distance-vector
  - wildcard-mask
  - passive-interface
source: "CCNA 200-301 Day 25 - RIP & EIGRP"
date: 2026-07-27
---

# RIP & EIGRP: Configuration and Concepts

## Summary

RIP and EIGRP are dynamic Interior Gateway Protocols that use distance-vector logic.

- **RIP** is an industry-standard protocol that uses hop count. It is simple but slow, has a 15-hop limit, and ignores bandwidth.
- **EIGRP** is an advanced distance-vector protocol that reacts faster, uses a composite metric, and supports unequal-cost load balancing.

Both protocols use `network` commands to select interfaces, form neighbor relationships, and advertise the real prefixes configured on those interfaces.

> [!important] Core exam distinction
> The `network` command identifies **interfaces on which the protocol will operate**. It does not directly dictate the prefix that is advertised. The router advertises the actual network prefix configured on each matching interface.

---

## RIP overview

**RIP** stands for **Routing Information Protocol**.

### Characteristics

- Industry-standard protocol
- Distance-vector IGP
- Uses routing-by-rumor logic
- Uses **hop count** as its metric
- One router crossed equals one hop
- Bandwidth is irrelevant to the metric
- Maximum usable metric is 15 hops
- A metric of 16 means unreachable
- Sends its routing table every 30 seconds by default
- Default administrative distance is 120
- Supports Equal-Cost Multi-Path (ECMP)
- Installs up to 4 equal-cost paths by default in the examples

Because RIP ignores bandwidth, a two-hop route over slow links is preferred over a three-hop route across much faster links.

### RIP message types

RIP uses two message types:

- **Request** - asks a RIP-enabled neighbor to send routing information
- **Response** - sends the local routing table to neighboring routers

---

## RIP versions

RIP has three versions:

- **RIPv1** - IPv4
- **RIPv2** - IPv4
- **RIPng** - IPv6

### RIPv1

RIPv1 is classful:

- Advertises only classful network information
- Does not include subnet masks in Response messages
- Does not support VLSM
- Does not support CIDR
- Broadcasts updates to `255.255.255.255`

Classful conversion examples:

| Actual prefix | RIPv1 treats it as |
|---|---|
| `10.1.1.0/24` | `10.0.0.0/8` |
| `172.16.192.0/18` | `172.16.0.0/16` |
| `192.168.1.4/30` | `192.168.1.0/24` |

### RIPv2

RIPv2 is classless:

- Includes subnet-mask information in advertisements
- Supports VLSM
- Supports CIDR
- Multicasts updates to `224.0.0.9`

### Broadcast versus multicast

- A **broadcast** is delivered to every device on the local network.
- A **multicast** is delivered only to devices participating in the specified multicast group.

For modern IPv4 RIP configurations, use RIPv2 and disable automatic classful summarization.

---

## Basic RIPv2 configuration

```cisco
router rip
 version 2
 no auto-summary
 network 10.0.0.0
 network 172.16.0.0
```

### What each command does

- `router rip` - starts the RIP routing process
- `version 2` - sends and receives RIPv2 updates
- `no auto-summary` - disables automatic classful summarization
- `network 10.0.0.0` - activates RIP on matching interfaces in the Class A `10.0.0.0/8` range
- `network 172.16.0.0` - activates RIP on matching interfaces in the Class B `172.16.0.0/16` range

The RIP `network` command is classful and does not use a subnet mask. If `network 10.0.12.0` is entered, IOS converts it to:

```cisco
network 10.0.0.0
```

---

## How the `network` command works

The RIP `network` command tells the router to:

1. Find interfaces whose IP addresses are within the specified classful range.
2. Activate RIP on those interfaces.
3. Form neighbor relationships with connected RIP routers.
4. Send and receive RIP messages on those interfaces.
5. Advertise the **actual network prefix** of each matching interface.

The network command does **not** replace the interface's real subnet with the classful network.

### Example

Suppose R1 has:

- G0/0: `10.0.12.1/30`
- G1/0: `10.0.13.1/30`

This command:

```cisco
network 10.0.0.0
```

matches both interfaces because their addresses are inside `10.0.0.0/8`.

RIP is activated on G0/0 and G1/0, but R1 advertises:

- `10.0.12.0/30`
- `10.0.13.0/30`

It does not advertise `10.0.0.0/8` merely because that value appears in the `network` command.

> [!note]
> OSPF and EIGRP use their `network` commands for the same general purpose: matching interfaces on which the routing protocol should operate.

---

## Passive interfaces

An interface connected only to end devices has no routing-protocol neighbor. Sending updates out that interface wastes resources and exposes unnecessary routing information.

Use:

```cisco
router rip
 passive-interface g2/0
```

The command:

- Stops RIP advertisements from being sent out G2/0
- Prevents a RIP neighbor relationship from forming on that interface
- Does **not** stop the connected prefix from being advertised to RIP neighbors through other interfaces

Example:

- G2/0 uses `172.16.1.14/28`
- G2/0 is passive
- R1 still advertises `172.16.1.0/28` to R2 and R3

Use `passive-interface` on any interface that does not connect to another router running the protocol.

EIGRP and OSPF support the same passive-interface concept and command.

---

## Advertising a default route into RIP

First, the edge router needs a default route toward the Internet or upstream network:

```cisco
ip route 0.0.0.0 0.0.0.0 203.0.113.2
```

Then advertise the default route to RIP neighbors:

```cisco
router rip
 default-information originate
```

Other RIP routers learn a candidate default route marked `R*`:

```text
R* 0.0.0.0/0 [120/2] via 10.0.34.1
```

- `R` - learned through RIP
- `*` - candidate default route
- `120` - RIP administrative distance
- `2` - hop-count metric

> [!important]
> Configure `default-information originate` on the router that owns the default route and must advertise it into RIP.

---

## Verifying RIP

### `show ip protocols`

```cisco
show ip protocols
```

Useful RIP information includes:

- Routing protocol is `rip`
- Update and invalid timers
- RIP version sent and received on each interface
- Whether automatic summarization is active
- Maximum number of equal-cost paths
- Networks matched by `network` commands
- Passive interfaces
- Routing information sources
- Default administrative distance

Timers shown in the slides:

| Timer | Default |
|---|---:|
| Update | 30 seconds |
| Invalid | 180 seconds |
| Hold-down | 180 seconds |
| Flush | 240 seconds |

The displayed maximum paths value is 4.

### Optional RIP tuning shown

```cisco
router rip
 maximum-paths 8
 distance 85
```

- `maximum-paths 8` allows up to eight equal-cost RIP routes.
- `distance 85` changes RIP's administrative distance from its default of 120.

Changing protocol defaults should be deliberate and consistent with the network design.

### `show ip route`

RIP routes are marked with `R`:

```text
R 192.168.4.0/24 [120/2] via 10.0.13.2
```

The brackets contain `[administrative distance/metric]`.

---

## EIGRP overview

**EIGRP** stands for **Enhanced Interior Gateway Routing Protocol**.

### Characteristics

- Advanced or hybrid distance-vector IGP
- Originally Cisco proprietary
- Cisco later published the protocol so other vendors could implement it
- Reacts to topology changes much faster than RIP
- Does not have RIP's 15-hop maximum
- Uses multicast address `224.0.0.10`
- Default internal administrative distance is 90
- Default external administrative distance is 170
- Performs ECMP over 4 paths by default in the examples
- The only IGP that can perform unequal-cost load balancing

EIGRP's unequal-cost load balancing is configured with the `variance` feature. Its default variance is 1, which means only equal-cost routes are used unless the value is changed.

### EIGRP metric

By default, EIGRP's composite metric uses:

- Minimum bandwidth along the route
- Total delay along the route

The default K-values shown by `show ip protocols` are:

```text
K1=1, K2=0, K3=1, K4=0, K5=0
```

This enables bandwidth and delay in the metric calculation by default.

---

## Basic EIGRP configuration

```cisco
router eigrp 1
 no auto-summary
 passive-interface g2/0
 network 10.0.0.0
 network 172.16.1.0 0.0.0.15
```

### Autonomous system number

The number in:

```cisco
router eigrp 1
```

is the EIGRP autonomous system number.

Directly connected EIGRP routers must use the same AS number to:

- Form an adjacency
- Exchange routing information

If the AS numbers do not match, the routers will not become EIGRP neighbors.

### Automatic summarization

Whether automatic summarization is enabled by default depends on the router and IOS version. If it is enabled, disable it:

```cisco
no auto-summary
```

### EIGRP network statements

If an EIGRP `network` statement omits a wildcard mask, IOS treats the address as classful.

```cisco
network 10.0.0.0
```

To precisely select interfaces, add a wildcard mask:

```cisco
network 172.16.1.0 0.0.0.15
```

This matches interfaces in `172.16.1.0/28`.

---

## Wildcard masks

A wildcard mask is an inverted subnet mask.

- Subnet-mask `1` becomes wildcard `0`.
- Subnet-mask `0` becomes wildcard `1`.

### Shortcut

Subtract every subnet-mask octet from 255:

```text
Wildcard octet = 255 - subnet-mask octet
```

Example:

```text
Subnet mask:   255.255.248.0
Subtract from: 255.255.255.255
Wildcard:        0.  0.  7.255
```

### Common conversions

| Prefix | Subnet mask       | Wildcard mask   |
| -----: | ----------------- | --------------- |
|   `/8` | `255.0.0.0`       | `0.255.255.255` |
|  `/14` | `255.252.0.0`     | `0.3.255.255`   |
|  `/16` | `255.255.0.0`     | `0.0.255.255`   |
|  `/19` | `255.255.224.0`   | `0.0.31.255`    |
|  `/21` | `255.255.248.0`   | `0.0.7.255`     |
|  `/24` | `255.255.255.0`   | `0.0.0.255`     |
|  `/25` | `255.255.255.128` | `0.0.0.127`     |
|  `/28` | `255.255.255.240` | `0.0.0.15`      |
|  `/30` | `255.255.255.252` | `0.0.0.3`       |
|  `/32` | `255.255.255.255` | `0.0.0.0`       |

### Matching logic

For every wildcard bit:

- `0` = the corresponding address bit **must match**
- `1` = the corresponding address bit **does not have to match**

### Matching examples

Interface address:

```text
172.16.1.14
```

This command matches because `.14` belongs to `172.16.1.0/28`:

```cisco
network 172.16.1.0 0.0.0.15
```

This command does not match because `.14` is outside `172.16.1.0/29`, whose range ends at `.7`:

```cisco
network 172.16.1.0 0.0.0.7
```

This command matches because `.14` belongs to `172.16.1.8/29`:

```cisco
network 172.16.1.8 0.0.0.7
```

The slides also demonstrate that wildcard masks can match broad or unusual ranges:

```cisco
network 168.0.0.0 7.255.255.255
```

This matches `172.16.1.14` because the wildcard allows the differing low-order bits in the first octet.

> [!tip] Fast lab method
> Convert the desired prefix's subnet mask to a wildcard mask, then confirm that every wildcard `0` aligns with a bit that matches the interface address.

---

## EIGRP router ID

EIGRP selects its router ID using this priority:

1. Manually configured router ID
2. Highest IPv4 address on a loopback interface
3. Highest IPv4 address on a physical interface

Configure it manually under the EIGRP process:

```cisco
router eigrp 1
 eigrp router-id 1.1.1.1
```

A manually configured router ID is preferred and makes the identity predictable.

---

## Verifying EIGRP

### `show ip protocols`

```cisco
show ip protocols
```

Check:

- EIGRP AS number
- Metric K-values
- Router ID
- Automatic summarization status
- Maximum equal-cost paths
- Network statements
- Passive interfaces
- Routing information sources
- Internal and external administrative distances
- Maximum hop count
- Variance value

Values shown in the slides include:

| Item | Value |
|---|---|
| Internal AD | 90 |
| External AD | 170 |
| Maximum paths | 4 |
| Maximum hop count | 100 |
| Variance | 1 |
| Active timer | 3 minutes |

### `show ip route`

EIGRP routes use:

- `D` - internal EIGRP route
- `EX` - external EIGRP route

Example:

```text
D 192.168.2.0/24 [90/3072] via 10.0.12.2
```

- `90` is the internal EIGRP AD.
- `3072` is the EIGRP composite metric.

The metric can vary between paths because EIGRP considers bandwidth and delay.

---

## RIP versus EIGRP

| Feature | RIP | EIGRP |
|---|---|---|
| Type | Distance vector | Advanced/hybrid distance vector |
| Standardization | Industry standard | Originally Cisco proprietary, now openly published |
| Metric | Hop count | Bandwidth and delay by default |
| IPv4 multicast | `224.0.0.9` for RIPv2 | `224.0.0.10` |
| Maximum route size | 15 hops; 16 is unreachable | No RIP-style 15-hop limit |
| Convergence | Relatively slow | Much faster |
| Internal AD | 120 | 90 |
| Default ECMP paths shown | 4 | 4 |
| Unequal-cost load balancing | No | Yes, using variance |
| Neighbor requirement | RIP enabled on connected interfaces | Matching EIGRP AS and compatible parameters |
| Interface selection | Classful `network` command | `network` command with optional wildcard mask |

---

## Troubleshooting checklist

### RIP route is missing

Check:

1. `router rip` is configured.
2. `version 2` is configured.
3. `no auto-summary` is present when required.
4. The classful `network` command matches the correct interface.
5. The transit interface is not unintentionally passive.
6. The neighbor is running compatible RIP.
7. The route is within RIP's 15-hop limit.
8. `show ip protocols` lists the expected network and information source.

### EIGRP adjacency or route is missing

Check:

1. Both routers use the same EIGRP AS number.
2. The `network` statement and wildcard mask match the intended interface.
3. The transit interface is not passive.
4. Interface IP addressing and subnetting allow direct communication.
5. `show ip protocols` lists the correct networks and router ID.
6. `show ip route` is checked for `D` or `EX` routes.

---

## Quiz review

### Quiz 1

R1 has a default route to the Internet and must advertise it to R2 through RIP. Which command is used?

**Answer:**

```cisco
R1(config-router)# default-information originate
```

The command belongs on the RIP router that originates the default route.

### Quiz 2

R1 has:

- G1/0: `172.20.20.17`
- G2/0: `172.26.20.12`

Which statement activates EIGRP on both interfaces?

**Answer:**

```cisco
network 128.0.0.0 127.255.255.255
```

The first address bit must match `1`, while all remaining bits can vary. Both `172.x.x.x` addresses satisfy that pattern.

### Quiz 3

What is the EIGRP router-ID priority?

**Answer:**

1. Manual configuration
2. Highest loopback IPv4 address
3. Highest physical-interface IPv4 address

---

## Quick command reference

### RIPv2

```cisco
router rip
 version 2
 no auto-summary
 network 10.0.0.0
 network 172.16.0.0
 passive-interface g2/0
 default-information originate

show ip protocols
show ip route
```

### EIGRP

```cisco
router eigrp 1
 no auto-summary
 network 10.0.0.0
 network 172.16.1.0 0.0.0.15
 passive-interface g2/0
 eigrp router-id 1.1.1.1

show ip protocols
show ip route
```

---

## Exam takeaways

- RIP uses hop count; bandwidth does not affect its metric.
- RIP can reach a maximum of 15 hops; 16 means unreachable.
- RIPv1 is classful and broadcasts to `255.255.255.255`.
- RIPv2 supports VLSM and CIDR and multicasts to `224.0.0.9`.
- RIP updates are sent every 30 seconds by default.
- The RIP `network` command is classful and does not include a mask.
- A `network` command selects interfaces; the router advertises the interfaces' actual prefixes.
- `passive-interface` stops protocol messages but does not stop the connected network from being advertised through other interfaces.
- `default-information originate` advertises a default route into RIP.
- EIGRP uses multicast `224.0.0.10`.
- EIGRP neighbors must use the same AS number.
- EIGRP uses bandwidth and delay in its default metric.
- EIGRP internal routes have AD 90; external routes have AD 170.
- EIGRP is the only IGP that supports unequal-cost load balancing.
- Wildcard `0` means must match; wildcard `1` means may differ.
- Calculate a wildcard mask by subtracting each subnet-mask octet from 255.
- EIGRP router ID priority is manual, highest loopback address, then highest physical-interface address.

## Related notes

- [Dynamic Routing - Fundamentals](<../Dynamic Routing/Dynamic Routing - Fundamentals.md>)
- Static Routing
- [EtherChannel - Link Aggregation](<../EtherChannel/EtherChannel - Link Aggregation.md>)
