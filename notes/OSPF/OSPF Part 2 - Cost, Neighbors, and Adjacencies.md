---
title: OSPF Part 2 - Cost, Neighbors, and Adjacencies
aliases:
  - OSPF Part 2
  - OSPF Cost and Neighbors
tags:
  - ccna
  - ospf
  - routing
  - ipv4
source: Day 27 Slides - OSPF (Part 2)
date: 2026-07-28
---

# OSPF Part 2 - Cost, Neighbors, and Adjacencies

## Summary

OSPF selects paths by **cost**, forms neighbor relationships with Hello packets, synchronizes Link State Databases (LSDBs), and then maintains the adjacency. For the CCNA, know the cost formula, the neighbor-state order, the five OSPF packet types, the default Ethernet Hello/Dead timers, and the commands used to tune cost and activate OSPF directly on an interface.

> [!tip] Part 1 connection
> Review [OSPF Part 1 - Fundamentals, Areas, and Basic Configuration](<OSPF Part 1 - Fundamentals, Areas, and Basic Configuration.md>) for OSPF areas, router ID selection, `network` statements, passive interfaces, default-route advertisement, and verification fundamentals.

## OSPF cost

OSPF's routing metric is called **cost**:

```text
OSPF cost = reference bandwidth / interface bandwidth
```

- The default reference bandwidth is **100 Mbps**.
- Any calculated result below 1 is converted to **1**.
- Route cost is the sum of the costs of the **outgoing interfaces** along the path.
- A loopback interface has a cost of **1** by default.
- OSPF chooses the path with the lowest total cost.

### Default-cost limitation

With the default 100-Mbps reference bandwidth:

| Interface speed | Calculation | OSPF cost |
|---|---:|---:|
| 10 Mbps Ethernet | 100 / 10 | 10 |
| 100 Mbps FastEthernet | 100 / 100 | 1 |
| 1 Gbps GigabitEthernet | 100 / 1,000 | 1 |
| 10 Gbps Ethernet | 100 / 10,000 | 1 |

Because values below 1 become 1, OSPF cannot distinguish FastEthernet, Gigabit Ethernet, and 10-Gigabit Ethernet links with its default reference bandwidth.

> [!important]
> Set the same reference bandwidth on every OSPF router. Use a value high enough to distinguish the fastest current link and allow for future upgrades.

### Path-cost example

If the outgoing interfaces along a path have costs of 100, 100, and 100:

```text
Total route cost = 100 + 100 + 100 = 300
```

To reach a neighbor's loopback through a link with cost 100:

```text
Total route cost = 100 (exit link) + 1 (loopback) = 101
```

## Modifying OSPF cost

### 1. Change the reference bandwidth

Configure this under the OSPF process. The value is entered in **megabits per second**:

```cisco
R1(config)# router ospf 1
R1(config-router)# auto-cost reference-bandwidth 100000
```

With a reference bandwidth of 100,000 Mbps:

- FastEthernet: `100000 / 100 = 1000`
- Gigabit Ethernet: `100000 / 1000 = 100`

### 2. Set an interface's cost manually

```cisco
R1(config)# interface g0/0
R1(config-if)# ip ospf cost 50
```

This is the preferred way to tune the cost of a specific interface.

### 3. Change the interface bandwidth value

```cisco
R1(config)# interface g0/0
R1(config-if)# bandwidth 100000
```

The `bandwidth` value is entered in **kilobits per second**. It is an informational value used by routing protocols and other calculations; it does **not** change the physical link speed.

> [!warning]
> Do not change `bandwidth` merely to tune OSPF. It can affect other protocol calculations and management tools. Prefer a consistent reference bandwidth and `ip ospf cost` for individual exceptions. The `speed` command, not `bandwidth`, changes an interface's operating speed.

## OSPF neighbor formation

When OSPF is enabled on an interface, the router sends Hello packets to discover and maintain neighbors.

- Default Ethernet Hello interval: **10 seconds**
- Default Ethernet Dead interval: **40 seconds**
- Hello destination: **224.0.0.5** (AllSPFRouters)
- IP protocol number: **89**
- Receiving a valid Hello resets the Dead timer.
- If the Dead timer reaches zero, the neighbor is removed.

The overall process is:

1. Become neighbors on the same segment.
2. Exchange LSAs and synchronize LSDBs.
3. Run SPF, select the best routes, and install them in the routing table.

## Neighbor-state sequence

> [!abstract] Memorize this order
> **Down -> Init -> 2-Way -> ExStart -> Exchange -> Loading -> Full**

| State | What happens |
|---|---|
| **Down** | No Hello has been received from the neighbor. |
| **Init** | A Hello was received, but it does not contain this router's own router ID. Communication is only known to be one-way. |
| **2-Way** | A Hello containing this router's router ID was received. Bidirectional communication is confirmed. DR/BDR election occurs here on applicable multiaccess network types. |
| **ExStart** | Routers negotiate master/slave roles and the initial DBD sequence number. The router with the higher router ID becomes the master. |
| **Exchange** | Routers exchange DBD packets that summarize the LSAs in their LSDBs. |
| **Loading** | Routers request missing or newer LSAs with LSRs, receive them in LSUs, and acknowledge them with LSAcks. |
| **Full** | LSDBs are synchronized and a full adjacency exists. Hellos maintain the relationship, and new LSAs are exchanged as the topology changes. |

> [!note]
> A router can remain in **2-Way** with some neighbors on a broadcast multiaccess network and still be operating normally. Full adjacency is formed with the DR and BDR; DR/BDR behavior is covered in the next OSPF lesson.

### State-by-state mental model

- **Down:** "I have not heard you."
- **Init:** "I heard you, but you have not confirmed hearing me."
- **2-Way:** "We can hear each other."
- **ExStart:** "Who controls the database exchange?"
- **Exchange:** "Here is a summary of my database."
- **Loading:** "Send me the specific information I am missing."
- **Full:** "Our databases are synchronized."

## OSPF packet types

| Type | Packet | Abbreviation | Purpose |
|---:|---|---|---|
| 1 | Hello | - | Discovers neighbors and maintains relationships. |
| 2 | Database Description | DBD | Summarizes the sender's LSDB so neighbors can compare database contents. |
| 3 | Link-State Request | LSR | Requests specific LSAs that are missing or outdated. |
| 4 | Link-State Update | LSU | Carries one or more LSAs to a neighbor. |
| 5 | Link-State Acknowledgment | LSAck | Confirms receipt of LSAs. |

> [!tip] Packet flow by state
> **Hello:** Down through 2-Way  
> **DBD:** ExStart and Exchange  
> **LSR, LSU, LSAck:** Loading  
> **Synchronized LSDB:** Full

Do not confuse an **LSU** with an **LSA**: an LSU is an OSPF packet that can carry one or more LSAs.

## Neighbor requirements and troubleshooting

If routers do not become neighbors, compare the two connected interfaces. Common requirements include:

- Interfaces are up/up and can communicate at Layer 3. 
- Interface IP addresses belong to the same subnet.
- OSPF is enabled on both interfaces.
- Interfaces are assigned to the same OSPF area.
- Hello and Dead timers match.
- Authentication settings match, if authentication is configured.
- OSPF network types are compatible.
- Router IDs are unique.
- Neither neighbor-facing interface is passive.

Useful symptom clues:

| Symptom | Likely focus |
|---|---|
| Neighbor remains **Down** | OSPF not enabled, interface/passive issue, addressing/connectivity problem, or Hellos not arriving |
| Neighbor remains **Init** | One-way communication or Hellos blocked in one direction |
| Neighbor remains **ExStart/Exchange** | MTU mismatch, duplicate router ID, or database-exchange problem |
| Neighbor repeatedly drops after the Dead interval | Hello loss, timer mismatch, or unstable link |

> [!warning]
> An OSPF process ID is locally significant and does not need to match between neighbors. The **area**, essential interface parameters, and adjacency settings do need to be compatible.

## Additional configuration

### Enable OSPF directly on an interface

Instead of using a router-process `network` statement, OSPF can be activated directly on the interface:

```cisco
R1(config)# interface g0/0
R1(config-if)# ip ospf 1 area 0
```

- `1` is the locally significant OSPF process ID.
- `0` is the OSPF area ID.
- This method avoids wildcard-mask matching.

### Passive-interface best practice

Make all interfaces passive by default, then enable Hellos only on links where a neighbor should form:

```cisco
R1(config)# router ospf 1
R1(config-router)# passive-interface default
R1(config-router)# no passive-interface g0/0
R1(config-router)# no passive-interface g1/0
```

Passive interfaces do not send OSPF Hellos or form neighbors, but their connected networks can still be advertised.

> [!success] Operational best practice
> `passive-interface default` is safer than individually making user-facing interfaces passive. New interfaces remain passive until deliberately enabled for neighbor formation.

## Verification commands

```cisco
R1# show ip ospf neighbor
R1# show ip ospf interface brief
R1# show ip ospf interface g0/0
R1# show ip ospf
R1# show ip protocols
R1# show ip route ospf
```

Check for:

- Expected neighbor router IDs
- Neighbor state (`FULL` where a full adjacency is expected)
- Correct interface and area
- Hello and Dead timers
- Interface cost and network type
- Correct OSPF-learned routes and total metrics

## Common mistakes

- Leaving the reference bandwidth at 100 Mbps in a modern network
- Configuring different reference bandwidths on different routers
- Adding inbound and outbound interface costs instead of only outgoing costs
- Assuming `bandwidth` changes the physical link speed
- Confusing `bandwidth` units (Kbps) with reference-bandwidth units (Mbps)
- Forgetting the neighbor-state order
- Confusing DBD summaries with full LSAs
- Assuming every healthy neighbor must reach Full on every network type
- Leaving end-user-facing interfaces non-passive
- Treating the process ID as if it must match between neighbors

## Exam tips

> [!example] High-value CCNA facts
> - Cost formula: **reference bandwidth / interface bandwidth**
> - Default reference bandwidth: **100 Mbps**
> - Values below 1 become **1**
> - Route metric: sum of **outgoing-interface** costs
> - Ethernet timers: **Hello 10 seconds, Dead 40 seconds**
> - Hello multicast: **224.0.0.5**
> - OSPF IP protocol: **89**
> - Master/slave roles are selected in **ExStart**
> - Highest router ID becomes the database-exchange master
> - Full adjacency means the neighbors' LSDBs are synchronized

### Quiz review

1. Neighbor states: **Down, Init, 2-Way, ExStart, Exchange, Loading, Full**.
2. By default, FastEthernet, Gigabit Ethernet, and 10-Gigabit Ethernet all have cost **1**.
3. Master/slave roles are decided in **ExStart**.
4. To give a 100-Mbps FastEthernet interface cost 100, use a 10,000-Mbps reference bandwidth: `10000 / 100 = 100`.
5. Default Ethernet timers are **Hello 10 seconds / Dead 40 seconds**.

## Related notes

- [OSPF Part 1 - Fundamentals, Areas, and Basic Configuration](<OSPF Part 1 - Fundamentals, Areas, and Basic Configuration.md>)
- [Dynamic Routing - Fundamentals](<../Dynamic Routing/Dynamic Routing - Fundamentals.md>)
- [EIGRP Terminology and Unequal-Cost Load Balancing](<../RIP & EIGRP/EIGRP Terminology and Unequal-Cost Load Balancing.md>)
