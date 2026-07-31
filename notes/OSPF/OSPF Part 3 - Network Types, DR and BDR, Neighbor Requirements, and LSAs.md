---
title: OSPF Part 3 - Network Types, DR and BDR, Neighbor Requirements, and LSAs
aliases:
  - OSPF Part 3
  - OSPF Network Types and LSAs
tags:
  - ccna
  - ospf
  - routing
  - ipv4
source: Day 28 Slides - OSPF (Part 3)
date: 2026-07-29
---

# OSPF Part 3 - Network Types, DR and BDR, Neighbor Requirements, and LSAs

## Summary

OSPF behavior changes according to the network type on an interface. Broadcast networks elect a Designated Router (DR) and Backup Designated Router (BDR) to reduce unnecessary LSA exchange, while point-to-point networks do not need a DR or BDR. Reliable adjacency formation also depends on matching essential settings between neighbors.

For the CCNA, focus on broadcast and point-to-point behavior, the non-preemptive DR/BDR election, OSPF multicast addresses, the eight neighbor requirements, and LSA Types 1, 2, and 5.

> [!tip] Part 2 connection
> Review [OSPF Part 2 - Cost, Neighbors, and Adjacencies](<OSPF Part 2 - Cost, Neighbors, and Adjacencies.md>) for OSPF cost, packet types, the neighbor-state sequence, and the meaning of a Full adjacency.

## Loopback interfaces

A loopback is a virtual router interface that remains up/up unless it is manually shut down. It is not tied to the state of a physical link, so it provides a stable address for management, reachability, and router identification.

```cisco
R1(config)# interface loopback 0
R1(config-if)# ip address 1.1.1.1 255.255.255.255
```

Benefits include:

- A consistent IP address even when a physical interface fails
- A dependable management destination
- A stable candidate for the OSPF router ID
- A useful endpoint for routing and reachability tests

> [!important]
> Creating a loopback does not automatically advertise it. OSPF must be activated on the interface or its address must be matched by an OSPF `network` statement.

## OSPF network types

The OSPF network type describes how OSPF operates on a connection between routers.

| Network type | Default link types | Neighbor discovery | DR/BDR | Default Hello/Dead |
|---|---|---|---|---|
| **Broadcast** | Ethernet and FDDI | Dynamic, using multicast | Elected | 10 / 40 seconds |
| **Point-to-point** | PPP and HDLC serial links | Dynamic, using multicast | Not elected | 10 / 40 seconds |
| **Non-broadcast** | Frame Relay and X.25 | Depends on configuration | Elected | 30 / 120 seconds |

The slides emphasize broadcast and point-to-point networks. Non-broadcast networking is included mainly so you recognize its default timers and legacy link types.

## Broadcast network type

Broadcast is the default OSPF network type on Ethernet interfaces. Routers dynamically discover neighbors by sending Hello packets to:

```text
224.0.0.5 - AllSPFRouters
```

Because an Ethernet segment can contain many OSPF routers, the segment elects:

- **DR - Designated Router**
- **BDR - Backup Designated Router**
- **DROther - Any router that is neither the DR nor the BDR**

### Why the DR and BDR exist

If every router on a multiaccess network formed a Full adjacency and exchanged LSAs with every other router, the number of relationships and duplicated updates would grow quickly.

Instead:

- The DR and BDR form a Full adjacency with every OSPF router on the segment.
- DROthers form a Full adjacency only with the DR and BDR.
- Two DROthers normally remain in the **2-Way** state with each other.
- All routers still receive the information needed to build the same LSDB.

Messages sent specifically to the DR and BDR use:

```text
224.0.0.6 - AllDRouters
```

> [!note]
> A neighbor remaining in `2WAY/DROTHER` on a broadcast segment can be completely normal. It does not automatically indicate an adjacency problem.

### DR/BDR election order

The election uses:

1. Highest OSPF interface priority
2. Highest OSPF router ID as the tiebreaker

The winning router becomes the DR, and the second-place router becomes the BDR.

- Default interface priority: **1**
- Priority range: **0 through 255**
- Priority **0** makes a router ineligible to become the DR or BDR.

```cisco
R1(config)# interface g0/0
R1(config-if)# ip ospf priority 255
```

To prevent a router from participating in the election:

```cisco
R1(config-if)# ip ospf priority 0
```

### The election is non-preemptive

Changing an interface to a higher priority does not immediately replace the current DR or BDR. Once elected, they keep their roles until an event forces a new election, such as:

- OSPF being reset
- The interface failing or being shut down
- The current DR or BDR becoming unavailable

If the DR fails:

1. The existing BDR becomes the new DR.
2. An election chooses a new BDR.

This sequence matters. A newly configured high-priority router can become the new BDR after the old DR fails, while the previous BDR advances to DR.

```cisco
R1# clear ip ospf process
```

> [!warning]
> `clear ip ospf process` tears down OSPF adjacencies and forces recalculation. Use it carefully on a production network.

### Verify the election

```cisco
R1# show ip ospf neighbor
R1# show ip ospf interface brief
R1# show ip ospf interface g0/0
```

Look for:

- `DR`, `BDR`, or `DROTHER` interface state
- Neighbor states such as `FULL/DR`, `FULL/BDR`, or `2WAY/DROTHER`
- Interface priority
- DR and BDR router IDs and interface addresses
- Network type and timers

## Point-to-point network type

Point-to-point is the default OSPF network type on serial interfaces using PPP or HDLC.

- Neighbors are dynamically discovered with Hellos to `224.0.0.5`.
- No DR or BDR is elected.
- The two routers form a Full adjacency directly with each other.
- Default timers are Hello 10 seconds and Dead 40 seconds.

There is no reason to elect a DR or BDR when exactly two routers share the link.

### Serial interface fundamentals

On a serial connection:

- One side is **DCE - Data Communications Equipment**.
- The other side is **DTE - Data Terminal Equipment**.
- The DCE side supplies the clock rate.
- Cisco HDLC is the default encapsulation.
- If PPP is configured, the encapsulation must match on both ends.

```cisco
R1# show controllers s2/0
R1(config)# interface s2/0
R1(config-if)# encapsulation ppp
R1(config-if)# clock rate 128000
```

The `clock rate` command is configured only on the DCE side.

### Configure point-to-point on Ethernet

Two routers connected directly by Ethernet do not need a DR/BDR election. The interface can be changed from broadcast to point-to-point:

```cisco
R1(config)# interface g0/0
R1(config-if)# ip ospf network point-to-point
```

Useful network-type options shown in the slides include:

```cisco
R1(config-if)# ip ospf network broadcast
R1(config-if)# ip ospf network non-broadcast
R1(config-if)# ip ospf network point-to-multipoint
R1(config-if)# ip ospf network point-to-point
```

Not every network type is supported on every Layer 2 link type.

## OSPF neighbor requirements

The slides identify eight important requirements:

| Requirement | What must agree |
|---:|---|
| 1 | Area number must match. |
| 2 | Connected interfaces must be in the same IP subnet. |
| 3 | The OSPF process must not be shut down. |
| 4 | OSPF router IDs must be unique. |
| 5 | Hello and Dead timers must match. |
| 6 | Authentication settings and keys must match. |
| 7 | IP MTU settings must match for OSPF to operate correctly. |
| 8 | OSPF network types must match for correct routing behavior. |

OSPF process IDs do **not** have to match. They are locally significant.

### Process state

An OSPF process can be administratively disabled:

```cisco
R1(config)# router ospf 1
R1(config-router)# shutdown
R1(config-router)# no shutdown
```

### Hello and Dead timers

Timers are configured per interface:

```cisco
R1(config)# interface g0/0
R1(config-if)# ip ospf hello-interval 5
R1(config-if)# ip ospf dead-interval 20
```

Restore the defaults with:

```cisco
R1(config-if)# no ip ospf hello-interval
R1(config-if)# no ip ospf dead-interval
```

If the timers do not match, the adjacency goes down.

### Authentication

The slides demonstrate simple OSPF interface authentication:

```cisco
R1(config)# interface g0/0
R1(config-if)# ip ospf authentication-key <shared-key>
R1(config-if)# ip ospf authentication
```

Both neighbors must use compatible authentication settings and the same key.

### MTU mismatch

An MTU mismatch can allow routers to discover one another but prevent the database exchange from completing. A common symptom is a neighbor stuck in **ExStart** or repeatedly resetting.

```cisco
R1(config)# interface g0/0
R1(config-if)# ip mtu 1400
```

Restore the interface default with:

```cisco
R1(config-if)# no ip mtu
```

### Network-type mismatch

Routers with mismatched network types can sometimes reach Full, but OSPF may still fail to install the expected routes because the routers model the link differently. Match the network type on both ends.

## Neighbor troubleshooting workflow

When an expected adjacency is missing or unstable:

1. Confirm both interfaces are up/up.
2. Confirm the IP addresses are in the same subnet.
3. Verify OSPF is enabled on both interfaces.
4. Compare the area numbers.
5. Confirm both OSPF processes are running.
6. Check for duplicate router IDs.
7. Compare Hello and Dead timers.
8. Compare authentication.
9. Compare interface MTU.
10. Compare OSPF network type.
11. Inspect the neighbor state for a clue.

| Symptom | Likely cause |
|---|---|
| No neighbor appears | OSPF not enabled, wrong area/subnet, passive interface, process shutdown, or connectivity failure |
| Neighbor drops after the Dead timer | Missing Hellos or timer mismatch |
| Neighbor remains in ExStart/Exchange | MTU mismatch, duplicate router ID, or database-exchange failure |
| Neighbor reaches Full but expected routes are missing | Network-type mismatch or advertisement problem |
| DROthers remain in 2-Way | Normal on a broadcast segment when neither router is the DR or BDR |

## OSPF LSA types

The LSDB is composed of LSAs. OSPF defines 11 LSA types, but the slides identify three required for the CCNA:

| Type | Name | Generated by | Purpose |
|---:|---|---|---|
| **1** | Router LSA | Every OSPF router | Identifies the router by router ID and describes networks attached to its OSPF-enabled interfaces. |
| **2** | Network LSA | The DR on a multiaccess network | Lists the routers attached to the broadcast or other multiaccess segment. |
| **5** | AS-External LSA | An ASBR | Describes destinations outside the OSPF autonomous system, such as redistributed or originated external routes. |

### Type 1 - Router LSA

- Every OSPF router generates one for each area in which it participates.
- The advertising router is identified by its router ID.
- It describes the router's OSPF links and attached networks.

### Type 2 - Network LSA

- Generated only by the DR of a multiaccess network.
- Represents the shared segment and the routers connected to it.
- A point-to-point network does not need a Type 2 LSA because it has no DR.

### Type 5 - AS-External LSA

- Generated by an ASBR.
- Describes routes external to the OSPF domain.
- A router that injects a default route with `default-information originate` is an example of an ASBR.

Verify LSAs with:

```cisco
R1# show ip ospf database
```

The output separates Router Link States, Net Link States, and Type-5 AS External Link States.

## High-value verification commands

```cisco
R1# show ip ospf neighbor
R1# show ip ospf interface brief
R1# show ip ospf interface g0/0
R1# show ip ospf database
R1# show ip route ospf
R1# show ip protocols
R1# show controllers s2/0
```

## Common mistakes

- Expecting a high-priority router to immediately preempt the current DR
- Forgetting that priority 0 prevents DR/BDR election
- Treating `2WAY/DROTHER` as a failure on a broadcast segment
- Assuming every OSPF neighbor must form a Full adjacency with every other router
- Forgetting that the BDR becomes DR before a new BDR is elected
- Electing a DR/BDR on a true point-to-point link
- Configuring PPP on only one end of a serial link
- Forgetting to configure the clock rate on the DCE side
- Assuming OSPF process IDs must match
- Ignoring an MTU or network-type mismatch because the routers appear as neighbors
- Confusing a Type 2 Network LSA with a Type 1 Router LSA

## Quiz review

1. The point-to-point characteristic that differs from broadcast is: **DR/BDR elections are not held**.
2. A DR on a broadcast network with four other routers forms **4 Full adjacencies**.
3. Neighbor requirements include **matching Hello/Dead timers** and **interfaces in the same area**.
4. The DR of a multiaccess network generates the **Type 2 Network LSA**.
5. Raising R1's priority does not preempt the existing DR/BDR, so **the DR and BDR initially remain unchanged**. If the DR is reset, the existing BDR becomes DR and high-priority R1 becomes the new BDR. The slide's correct answers are **D and F**.

## Exam takeaways

- Broadcast networks elect a DR and BDR; point-to-point networks do not.
- DR/BDR election uses interface priority first and router ID second.
- Priority 0 makes a router ineligible for DR or BDR.
- The election is non-preemptive.
- DROthers form Full adjacencies with the DR and BDR, but remain 2-Way with one another.
- `224.0.0.5` reaches all OSPF routers; `224.0.0.6` reaches the DR and BDR.
- Broadcast and point-to-point defaults use Hello 10 / Dead 40.
- Matching area, subnet, process state, router-ID uniqueness, timers, authentication, MTU, and network type are central to adjacency health.
- Type 1 is a Router LSA, Type 2 is a DR-generated Network LSA, and Type 5 is an ASBR-generated External LSA.

## Related notes

- [OSPF Part 1 - Fundamentals, Areas, and Basic Configuration](<OSPF Part 1 - Fundamentals, Areas, and Basic Configuration.md>)
- [OSPF Part 2 - Cost, Neighbors, and Adjacencies](<OSPF Part 2 - Cost, Neighbors, and Adjacencies.md>)
- [Dynamic Routing - Fundamentals](<../Dynamic Routing/Dynamic Routing - Fundamentals.md>)
- [RIP & EIGRP - Configuration and Concepts](<../RIP & EIGRP/RIP & EIGRP - Configuration and Concepts.md>)
