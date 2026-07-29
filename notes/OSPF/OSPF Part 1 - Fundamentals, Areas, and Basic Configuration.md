---
title: OSPF Part 1 - Fundamentals, Areas, and Basic Configuration
aliases:
  - OSPF Part 1
  - OSPF Fundamentals
tags:
  - ccna
  - ospf
  - routing
  - ipv4
source: Day 26 Slides - OSPF (Part 1)
date: 2026-07-28
---

# OSPF Part 1 - Fundamentals, Areas, and Basic Configuration

## Summary

Open Shortest Path First (OSPF) is a link-state interior gateway protocol. OSPF routers form neighbor relationships, exchange Link State Advertisements (LSAs), build matching Link State Databases (LSDBs), and independently run the Shortest Path First (SPF) algorithm to select routes.

For the CCNA, focus on single-area OSPFv2 in area 0, basic `network` statements, passive interfaces, router ID selection, default-route advertisement, and verification with `show ip protocols`.

## Where OSPF fits

| Category | Protocols |
|---|---|
| IGP, distance vector | RIP, EIGRP |
| IGP, link state | OSPF, IS-IS |
| EGP, path vector | BGP |

- **OSPF** stands for **Open Shortest Path First**.
- **OSPFv2** is normally used for IPv4.
- **OSPFv3** is normally used for IPv6, although it can also support IPv4.
- OSPF uses Dijkstra's SPF algorithm.
- The default administrative distance of OSPF is **110**.

## How link-state routing works

Each router advertises information about its links and connected networks. These advertisements are flooded through the OSPF area until the routers share the same network map.

The basic OSPF process is:

1. Become neighbors with other OSPF routers on the same segment.
2. Exchange and flood LSAs.
3. Build the LSDB.
4. Run the SPF algorithm independently.
5. Install the best routes in the routing table.

### LSA and LSDB

- **LSA - Link State Advertisement:** Information a router advertises about the network.
- **LSDB - Link State Database:** The collection of LSAs that represents the area's topology.
- Routers in the same area should have the same LSDB.
- LSAs have an aging timer. The slides use a 30-minute refresh interval.

Link-state protocols generally require more CPU and memory than distance-vector protocols because they maintain a detailed topology database and run SPF. Their advantage is faster reaction to network changes.

## OSPF areas

An **area** is a set of routers and links that share the same LSDB. Areas divide a large OSPF network into smaller failure and calculation domains.

Without areas, a large topology can cause:

- A larger LSDB and higher memory use
- Longer SPF calculations and higher CPU use
- More LSA flooding
- Every small topology change to affect every router

### Area design rules

- **Area 0** is the backbone area.
- Every non-backbone area must connect to area 0 through an ABR.
- OSPF areas should be contiguous.
- Interfaces on the same subnet must belong to the same OSPF area.
- Small networks can operate as a single area.
- For CCNA configuration exercises, use single-area OSPF in area 0 unless told otherwise.

> [!important]
> Single-area OSPF does not technically have to use area 0, but area 0 is the expected CCNA design and is required as the backbone when multiple areas are used.

## OSPF router roles

| Role | Meaning |
|---|---|
| Internal router | All OSPF interfaces are in the same area |
| Backbone router | Has at least one interface in area 0 |
| Area Border Router (ABR) | Has interfaces in more than one area |
| Autonomous System Boundary Router (ASBR) | Connects the OSPF domain to an external routing domain and injects external routes |

An ABR maintains a separate LSDB for each connected area. The slides recommend limiting an ABR to a maximum of two areas when possible to avoid overburdening it.

### Route location terms

- **Intra-area route:** The destination is inside the router's current OSPF area.
- **Interarea route:** The destination is in a different OSPF area.

## Basic single-area OSPF configuration

### 1. Start an OSPF process

```cisco
R1(config)# router ospf 1
```

The process ID range is 1 through 65535. The process ID is **locally significant**, so neighboring routers do not need matching process IDs.

> [!warning]
> The OSPF process ID is not the area number and does not have to match it.

### 2. Activate OSPF on interfaces

```cisco
R1(config-router)# network 10.0.12.0 0.0.0.3 area 0
R1(config-router)# network 10.0.13.0 0.0.0.3 area 0
R1(config-router)# network 172.16.1.0 0.0.0.15 area 0
```

The `network` command:

1. Searches for local interfaces whose IP addresses match the specified address and wildcard mask.
2. Activates OSPF on those interfaces.
3. Places those interfaces in the specified area.
4. Allows the router to send OSPF hellos and form neighbors on those interfaces.
5. Causes the connected networks to be advertised in OSPF.

The command does not directly advertise an arbitrary network. It selects local interfaces by their IP addresses.

### Wildcard-mask reminder

Wildcard bits of `0` must match; wildcard bits of `1` can vary.

| Subnet mask | Wildcard mask |
|---|---|
| 255.255.255.252 (/30) | 0.0.0.3 |
| 255.255.255.240 (/28) | 0.0.0.15 |
| 255.255.255.128 (/25) | 0.0.0.127 |
| 255.255.255.0 (/24) | 0.0.0.255 |

Example: one statement that matches both `10.0.12.1/28` and `10.0.13.1/26` is:

```cisco
R1(config-router)# network 10.0.12.0 0.0.1.255 area 0
```

## Passive interfaces

Use a passive interface where a network should be advertised but no OSPF neighbor should exist:

```cisco
R1(config-router)# passive-interface g2/0
```

This stops OSPF hello messages on the interface, preventing neighbor formation. The connected subnet is still advertised to existing OSPF neighbors through LSAs.

Use `passive-interface` on LAN interfaces facing end devices and on other links with no OSPF router.

## Advertising a default route

First, create a default route toward the external next hop:

```cisco
R1(config)# ip route 0.0.0.0 0.0.0.0 203.0.113.2
```

Then inject it into OSPF:

```cisco
R1(config)# router ospf 1
R1(config-router)# default-information originate
```

The originating router becomes an ASBR. Other routers learn the default route as an OSPF external route, displayed in the slides as:

```text
O*E2 0.0.0.0/0 [110/1] via 10.0.12.1
```

- `O` = OSPF
- `*` = candidate default route
- `E2` = OSPF external type 2
- `110` = administrative distance

## OSPF router ID

The router ID is a 32-bit value written like an IPv4 address. Selection priority is:

1. Manually configured router ID
2. Highest IP address on a loopback interface
3. Highest IP address on an active physical interface

Configure it manually under the OSPF process:

```cisco
R1(config-router)# router-id 1.1.1.1
```

If the OSPF process is already running, the new router ID does not take effect immediately. Reload the router or reset the OSPF process:

```cisco
R1# clear ip ospf process
```

Resetting the process temporarily tears down OSPF neighbor relationships, so use it carefully.

## Verification

### Show protocol settings

```cisco
R1# show ip protocols
```

Check:

- OSPF process ID
- Router ID
- Whether the router is an ASBR
- Number and type of connected areas
- Maximum equal-cost paths
- `network` statements and their areas
- Passive interfaces
- OSPF routing information sources
- Administrative distance

### Show learned routes

```cisco
R1# show ip route
```

Common route codes in this lesson:

- `O` - OSPF intra-area route
- `O IA` - OSPF interarea route
- `O E1` - OSPF external type 1
- `O E2` - OSPF external type 2

### Optional process settings

```cisco
R1(config-router)# maximum-paths 8
R1(config-router)# distance 85
```

- `maximum-paths` controls how many equal-cost OSPF routes can be installed. The slides show a range of 1 to 32.
- `distance` changes OSPF's administrative distance. The default is 110; normally leave it unchanged unless there is a specific design requirement.
 
## Common mistakes

- Assuming neighboring process IDs must match
- Omitting `area` from the `network` command
- Treating the process ID as the area number
- Placing interfaces on the same subnet in different areas
- Sending OSPF hellos toward end-user devices instead of making the interface passive
- Configuring `default-information originate` without first ensuring the router has a default route
- Changing the router ID but forgetting to restart the OSPF process

## Quiz review

1. The false statements are **"Single-area OSPF must use area 0"** and **"The process ID must match the area number."**
2. To match both `10.0.12.1/28` and `10.0.13.1/26`: `network 10.0.12.0 0.0.1.255 area 0`.
3. In the diagram: **4 backbone routers, 3 ABRs, and 1 ASBR**.
4. A router with a static default route becomes an ASBR after `default-information originate`.
5. The manual router-ID command is `router-id 1.1.1.1`.

## Exam takeaways

- OSPF is a link-state IGP that uses Dijkstra's SPF algorithm.
- OSPF routers form neighbors, flood LSAs, build an LSDB, and calculate routes.
- Area 0 is the backbone; non-backbone areas connect to it through ABRs.
- OSPF process IDs are locally significant.
- `network` statements select interfaces and must include an area.
- Passive interfaces advertise their subnet but do not send OSPF hellos.
- Router ID priority is manual, highest loopback IP, then highest physical-interface IP.
- `default-information originate` injects a default route and makes the router an ASBR.
- OSPF has an administrative distance of 110 by default.

## Related notes

- [Dynamic Routing](<../Dynamic Routing/Dynamic Routing - Fundamentals.md>)
- [RIP & EIGRP - Configuration and Concepts](<../RIP & EIGRP/RIP & EIGRP - Configuration and Concepts.md>)
- [EIGRP Terminology and Unequal-Cost Load Balancing](<../RIP & EIGRP/EIGRP Terminology and Unequal-Cost Load Balancing.md>)
