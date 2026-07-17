---
title: "VLANs Part 1 - LANs, Broadcast Domains, and Access Ports"
aliases:
  - VLANs Part 1
  - VLAN Fundamentals
tags:
  - ccna
  - vlan
  - switching
  - broadcast-domain
  - access-port
source: "Day 16 Slides - VLANs (Part 1)"
---

# VLANs Part 1: LANs, Broadcast Domains, and Access Ports

## Big picture

A **LAN** can be defined as a single **broadcast domain**: the collection of devices that receive a Layer 2 broadcast sent by another member. A **VLAN** logically divides a switch into multiple broadcast domains, even when the devices use the same physical switch.

VLANs improve performance by limiting unnecessary broadcasts and improve security by forcing traffic between groups to pass through a Layer 3 device, where policies can be applied.

## LANs and broadcast domains

A broadcast Ethernet frame uses the destination MAC address:

```text
FFFF.FFFF.FFFF
```

Switches flood a broadcast through the same broadcast domain, except out the port on which it arrived. Routers do not forward Layer 2 broadcasts by default, so every router interface forms a broadcast-domain boundary.

### How to count broadcast domains

- A normal switched segment without VLAN separation is one broadcast domain.
- Each VLAN is a separate broadcast domain.
- Each independent network connected to a router interface is a separate broadcast domain.
- A point-to-point link between two routers is also its own network and broadcast domain when Ethernet is used.

## What is a VLAN?

A **Virtual Local Area Network (VLAN)** is a logical Layer 2 network configured on switch interfaces. It groups selected ports into the same broadcast domain regardless of their physical location on the switch.

VLANs:

- Are configured on switches on a per-interface basis.
- Logically separate end hosts at Layer 2.
- Keep broadcast and unknown-unicast traffic inside the originating VLAN.
- Prevent a Layer 2 switch from directly forwarding traffic between different VLANs.

### VLANs vs. IP subnets

Subnets provide Layer 3 separation; VLANs provide Layer 2 separation. Merely giving departments different IP subnets does **not** create separate broadcast domains if all ports remain in the same VLAN.

A clean design normally maps one IP subnet to one VLAN. The slideshow uses:

| Department | VLAN | Subnet |
|---|---:|---|
| Engineering | 10 | `192.168.1.0/26` |
| HR | 20 | `192.168.1.64/26` |
| Sales | 30 | `192.168.1.128/26` |

## Why VLANs are useful

### Performance

Without VLAN separation, every broadcast is flooded to every host in the LAN. VLANs reduce the number of devices that must process each broadcast, limiting unnecessary traffic.

### Security

Hosts in the same VLAN can communicate directly at Layer 2, bypassing a router or firewall. Hosts in different VLANs require **inter-VLAN routing**, which creates a point where access-control and firewall policies can be enforced.

VLANs provide useful segmentation, but they are not a complete security system by themselves.

### Organization and flexibility

Devices can be grouped by department or purpose without requiring a separate physical switch for every group.

## Communication within and between VLANs

### Same VLAN

Hosts in the same VLAN communicate through the switch. Broadcasts remain inside that VLAN.

### Different VLANs

A Layer 2 switch does not route between VLANs. When the destination is in another VLAN:

1. The source host sends the packet toward its default gateway.
2. The Ethernet frame's destination MAC is the router's MAC address.
3. The router routes the packet into the destination VLAN.
4. The router builds a new Layer 2 frame using the destination host's MAC address.

The source and destination IP addresses remain end-to-end, while the Layer 2 MAC addresses change at the router.

## Access ports

An **access port** belongs to one VLAN and usually connects to an endpoint such as a PC, printer, or server.

```text
interface gigabitEthernet1/0
 switchport mode access
 switchport access vlan 10
```

The port sends and receives ordinary untagged frames for its assigned VLAN. Ports that carry multiple VLANs are called trunk ports; those are covered in [VLANs Part 2 — Trunks, 802.1Q, and ROAS](<VLANs Part 2 - Trunks, 802.1Q, and ROAS.md>).

## Configuring VLANs on Cisco switches

### Create and name a VLAN

```text
vlan 10
 name ENGINEERING

vlan 20
 name HR

vlan 30
 name SALES
```

### Assign access ports with interface ranges

```text
interface range gigabitEthernet1/0 - 3
 switchport mode access
 switchport access vlan 10

interface range gigabitEthernet2/0 - 2
 switchport mode access
 switchport access vlan 20

interface range gigabitEthernet3/0 - 3
 switchport mode access
 switchport access vlan 30
```

In the Cisco IOS behavior shown in the slideshow, assigning a port to an access VLAN that does not yet exist automatically creates that VLAN. It initially receives a default name such as `VLAN0010`; it can then be renamed from VLAN configuration mode.

### Verify VLANs and port assignments

```text
show vlan brief
```

This displays each VLAN's ID, name, status, and assigned access ports.

## Default Cisco VLANs

These VLANs exist by default and cannot be deleted:

- VLAN 1: the default Ethernet VLAN
- VLANs 1002-1005: legacy FDDI and Token Ring defaults

Therefore, a switch with newly created VLANs 10, 20, and 30 shows **eight VLANs** in `show vlan brief`: the five defaults plus the three new VLANs.

## Common mistakes

- Assuming separate IP subnets automatically create separate Layer 2 broadcast domains.
- Forgetting that every VLAN needs Layer 3 routing to communicate with other VLANs.
- Leaving user ports in the default VLAN instead of explicitly configuring access mode and the intended VLAN.
- Expecting a switch to forward broadcasts or unknown unicasts between VLANs.
- Counting switches as broadcast-domain boundaries; without VLANs, routers are the devices that separate broadcast domains.
- Treating VLAN segmentation as a replacement for router, firewall, or access-control policies.

## Exam memory anchors

- **LAN = one broadcast domain.**
- **Broadcast destination MAC = `FFFF.FFFF.FFFF`.**
- **Routers separate broadcast domains.**
- **Each VLAN is a separate Layer 2 broadcast domain.**
- **A switch does not route between VLANs.**
- **Access port = one VLAN, usually connected to an endpoint.**
- **One subnet per VLAN is the normal design.**
- **Verify VLANs and access ports with `show vlan brief`.**
- **VLANs 1 and 1002-1005 exist by default.**


## One-sentence recap

VLANs split a physical switch into separate Layer 2 broadcast domains, reducing broadcast traffic and requiring a router or Layer 3 switch for controlled communication between groups.
