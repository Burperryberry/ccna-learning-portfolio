---
title: "VLANs Part 3 - Native VLANs, Multilayer Switching, and SVIs"
aliases:
  - VLANs Part 3
  - Inter-VLAN Routing with SVIs
tags:
  - ccna
  - vlan
  - switching
  - multilayer-switching
  - svi
  - roas
source: "Day 18 Slides - VLANs (Part 3)"
---

# VLANs Part 3: Native VLANs, Multilayer Switching, and SVIs

## Big picture

This lesson extends [[VLANs Part 2 - Trunks, 802.1Q, and ROAS]] in two directions:

1. It explains how a router handles the untagged **native VLAN** in a Router-on-a-Stick design.
2. It replaces Router-on-a-Stick with a **multilayer switch**, which performs inter-VLAN routing through Switch Virtual Interfaces (SVIs).

Packet captures demonstrate that non-native VLAN traffic is tagged with 802.1Q, while native VLAN traffic crosses the trunk untagged.

## Native VLANs in Router-on-a-Stick

The switch and router must agree about which VLAN is native. On the switch trunk, configure the same native VLAN on every relevant link:

```text
interface gigabitEthernet0/0
 switchport trunk native vlan 10
```

There are two valid ways to configure the router side.

### Method 1: Native VLAN on a subinterface

Add the `native` keyword to the subinterface's 802.1Q configuration:

```text
interface gigabitEthernet0/0.10
 encapsulation dot1q 10 native
 ip address 192.168.1.62 255.255.255.192

interface gigabitEthernet0/0.20
 encapsulation dot1q 20
 ip address 192.168.1.126 255.255.255.192

interface gigabitEthernet0/0.30
 encapsulation dot1q 30
 ip address 192.168.1.190 255.255.255.192
```

The router associates untagged frames with subinterface `G0/0.10`. VLANs 20 and 30 remain tagged.

### Method 2: Native VLAN on the physical interface

Assign the native VLAN's gateway address directly to the physical interface. No `encapsulation dot1q` command is required for the native VLAN:

```text
interface gigabitEthernet0/0
 ip address 192.168.1.62 255.255.255.192

interface gigabitEthernet0/0.20
 encapsulation dot1q 20
 ip address 192.168.1.126 255.255.255.192

interface gigabitEthernet0/0.30
 encapsulation dot1q 30
 ip address 192.168.1.190 255.255.255.192
```

The physical interface processes untagged native-VLAN traffic, while the subinterfaces process tagged traffic for the other VLANs.

## Wireshark evidence

The packet captures illustrate the difference between native and non-native VLAN traffic.

### Non-native VLAN traffic

A frame from VLAN 20 traveling from SW2 toward R1 contains:

- EtherType/TPID `0x8100`, indicating an 802.1Q tag
- VLAN ID `20`
- The original IPv4 packet inside the tagged Ethernet frame

### Native VLAN traffic

A frame sent into native VLAN 10 does not contain an 802.1Q header. The Ethernet header points directly to IPv4 with EtherType `0x0800`.

Memory rule:

> On an 802.1Q trunk, non-native VLAN traffic is tagged; native VLAN traffic is untagged by default.

## Layer 3 or multilayer switches

A **multilayer switch** can perform both Layer 2 switching and Layer 3 routing.

It can:

- Switch Ethernet frames within a VLAN.
- Route packets between VLANs and IP subnets.
- Assign IP addresses to physical interfaces.
- Create virtual Layer 3 interfaces for VLANs.
- Maintain a routing table and use static or dynamic routes.
- Replace an external router for local inter-VLAN routing.

## Switch Virtual Interfaces (SVIs)

An **SVI** is a virtual Layer 3 interface associated with a VLAN. Its interface name is `interface vlan <vlan-id>`.

Each host uses the IP address of its VLAN's SVI as its default gateway. Traffic destined for another subnet is sent to the multilayer switch, which routes it to the destination VLAN.

Example gateway plan:

| VLAN | Subnet | SVI/default gateway |
|---:|---|---|
| 10 | `192.168.1.0/26` | `192.168.1.62` |
| 20 | `192.168.1.64/26` | `192.168.1.126` |
| 30 | `192.168.1.128/26` | `192.168.1.190` |

### Configure the SVIs

```text
interface vlan 10
 ip address 192.168.1.62 255.255.255.192
 no shutdown

interface vlan 20
 ip address 192.168.1.126 255.255.255.192
 no shutdown

interface vlan 30
 ip address 192.168.1.190 255.255.255.192
 no shutdown
```

### Enable Layer 3 routing

```text
ip routing
```

This global command is essential. Without it, the switch has Layer 3 interfaces but does not route traffic between them.

## Routed ports

A multilayer-switch interface can operate as a router-style Layer 3 port rather than a Layer 2 switchport.

```text
interface gigabitEthernet0/1
 no switchport
 ip address 192.168.1.193 255.255.255.252
```

- `no switchport` converts the interface into a **routed port**.
- A routed port receives an IP address directly.
- It does not belong to an access VLAN and does not operate as a trunk.
- `show interfaces status` displays `routed` in the VLAN column.

The slideshow connects the routed port to R1 using `192.168.1.192/30`:

| Device | Interface address |
|---|---|
| SW2 | `192.168.1.193/30` |
| R1 | `192.168.1.194/30` |

## Default route toward an upstream router

After enabling IP routing, configure a normal Layer 3 default route on the multilayer switch:

```text
ip route 0.0.0.0 0.0.0.0 192.168.1.194
```

The switch uses its connected SVI routes for the internal VLANs and sends unknown destinations toward R1. In a complete design, the upstream router must also have a return route to the VLAN subnets.

## When an SVI becomes up/up

An SVI will be operational only when all required conditions are met:

1. The VLAN exists on the switch.
2. The VLAN itself is not shut down.
3. The SVI has been enabled with `no shutdown`.
4. At least one Layer 2 port associated with that VLAN is operational:
   - An access port in the VLAN is up/up, and/or
   - An up/up trunk permits the VLAN.

An SVI can therefore remain **down/down** even after receiving an IP address and `no shutdown` if the VLAN does not exist or has no active Layer 2 path.

## Verification commands

```text
show ip interface brief
show ip route
show interfaces status
show vlan brief
show interfaces trunk
```

Look for:

- SVIs showing `up/up`
- The routed port showing `routed`
- Connected routes for every SVI subnet
- A default route pointing to the upstream router
- The required VLANs existing and active
- Access or trunk ports providing an active Layer 2 path for each SVI

## Router-on-a-Stick vs. multilayer switching

| Feature | Router-on-a-Stick | Multilayer switch with SVIs |
|---|---|---|
| Inter-VLAN gateway | Router subinterfaces | Switch SVIs |
| Switch-to-router link | 802.1Q trunk | Not required for local inter-VLAN routing |
| Physical Layer 3 uplink | Router interface | Routed switch port with `no switchport` |
| Routing command | Router routes by default | Enable `ip routing` on the switch |
| Typical advantage | Works with a Layer 2 switch | Faster and more scalable local routing |

## Common mistakes

- Native VLANs do not match between the switch and router.
- The `native` keyword is omitted from the native router subinterface.
- The native VLAN is configured both on a subinterface and on the physical router interface.
- Hosts still use the external router instead of their local SVI as the default gateway.
- `ip routing` is missing on the multilayer switch.
- `no switchport` is omitted from the routed uplink.
- An IP address is assigned to a physical switchport that is still operating at Layer 2.
- An SVI remains down because the VLAN is missing or has no active access/trunk port.
- Return routes to the internal VLAN subnets are missing on the upstream router.

## Exam memory anchors

- **ROAS native subinterface:** `encapsulation dot1q <vlan-id> native`.
- **Alternative native method:** place the IP address on the router's physical interface.
- **Native VLAN frames are untagged by default.**
- **SVI = virtual Layer 3 gateway for a VLAN.**
- **Enable multilayer routing with `ip routing`.**
- **Convert a switchport to Layer 3 with `no switchport`.**
- **SVI up/up requires the VLAN and an active Layer 2 path.**
- **Hosts use the SVI, not the external router, as their gateway.**

## Lesson boundary

The overview slides mention DTP (Dynamic Trunking Protocol) and VTP (VLAN Trunking Protocol), but explicitly mark both as material for the next video; this deck does not teach their operation or configuration.

## One-sentence recap

Native VLAN traffic is handled untagged by the router, while a multilayer switch uses SVIs, `ip routing`, and routed ports to provide scalable inter-VLAN routing and upstream connectivity.
