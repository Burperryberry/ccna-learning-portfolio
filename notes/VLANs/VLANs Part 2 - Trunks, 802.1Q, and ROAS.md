---
title: "VLANs Part 2 - Trunks, 802.1Q, and ROAS"
aliases:
  - VLANs Part 2
  - VLAN Trunking
tags:
  - ccna
  - vlan
  - switching
  - 802-1q
  - roas
source: "Day 17 Slides - VLANs (Part 2)"
---

# VLANs Part 2: Trunks, 802.1Q, and Router-on-a-Stick

## Big picture

A VLAN separates a switched network into logical broadcast domains. **Access ports** normally carry traffic for one VLAN and send ordinary, untagged Ethernet frames. **Trunk ports** carry traffic for multiple VLANs over one physical link. To preserve the VLAN identity across a trunk, switches use **IEEE 802.1Q tags**.

Trunks avoid dedicating a separate physical interface to every VLAN. They are commonly used between switches and between a switch and a router.

## Access ports vs. trunk ports

| Feature | Access port | Trunk port |
|---|---|---|
| VLANs carried | Usually one | Multiple |
| Frames on the link | Untagged | Tagged with 802.1Q, except the native VLAN |
| Typical connection | Switch to endpoint | Switch to switch or switch to router |

The receiving device reads the 802.1Q tag to determine which VLAN a frame belongs to.

## IEEE 802.1Q tagging

802.1Q, often called **dot1q**, is the industry-standard VLAN trunking protocol. Cisco's older proprietary ISL protocol is obsolete and is not supported on many modern switches.

An 802.1Q tag:

- Is inserted between the Ethernet **Source MAC** and **Type/Length** fields.
- Adds **4 bytes (32 bits)** to the Ethernet frame.
- Contains a 16-bit **Tag Protocol Identifier (TPID)** and 16 bits of **Tag Control Information (TCI)**.

### Tag fields

| Field | Size | Purpose |
|---|---:|---|
| TPID | 16 bits | Set to `0x8100`, identifying an 802.1Q-tagged frame |
| PCP | 3 bits | Priority Code Point; supports Class of Service prioritization |
| DEI | 1 bit | Drop Eligible Indicator; marks traffic that may be dropped during congestion |
| VID | 12 bits | VLAN ID carried by the frame |

The 12-bit VID provides 4,096 possible values (`0-4095`), but VLAN IDs `0` and `4095` are reserved. The usable range is therefore **1-4094**.

- Normal-range VLANs: `1-1005`
- Extended-range VLANs: `1006-4094`

## Native VLAN

The **native VLAN** is the one VLAN whose frames are normally sent **untagged** across an 802.1Q trunk.

- The default native VLAN is VLAN 1.
- An untagged frame received on a trunk is assigned to the receiving port's native VLAN.
- Both ends of a trunk must use the same native VLAN.
- A mismatch can place traffic into the wrong VLAN or cause frames to be discarded.
- A security best practice is to change the native VLAN to an unused VLAN and configure the same value on both ends.

Example:

```text
interface gigabitEthernet0/0
 switchport trunk native vlan 1001
```

## Configuring a trunk

Basic Cisco IOS configuration:

```text
interface gigabitEthernet0/0
 switchport trunk encapsulation dot1q
 switchport mode trunk
```

`switchport trunk encapsulation dot1q` is needed only on switches that support more than one trunk encapsulation and default to `auto`. Many modern switches support only 802.1Q, so that command is unavailable or unnecessary.

### Controlling the allowed VLAN list

```text
switchport trunk allowed vlan 10,30
switchport trunk allowed vlan add 20
switchport trunk allowed vlan remove 20
switchport trunk allowed vlan all
switchport trunk allowed vlan except 1-5,10
switchport trunk allowed vlan none
```

Important behavior:

- `switchport trunk allowed vlan 10,30` **replaces** the current allowed list.
- `add` adds VLANs without replacing the existing list.
- `remove` removes only the specified VLANs.
- `all` restores all VLANs (`1-4094`), which is the default allowed state.
- `except` permits every VLAN except those listed.
- `none` permits no VLANs.

### Verification

```text
show interfaces trunk
show vlan brief
```

Use `show interfaces trunk` to confirm:

- Which ports are trunking
- Encapsulation and native VLAN
- VLANs allowed on the trunk
- VLANs allowed and active locally
- VLANs in spanning-tree forwarding state and not pruned

`show vlan brief` lists access ports assigned to VLANs; it does **not** list trunk ports under every VLAN they carry.

A VLAN can be in the trunk's allowed list but absent from **Vlans allowed and active in management domain** if that VLAN has not been created on the switch.

## Router-on-a-Stick (ROAS)

Router-on-a-Stick provides inter-VLAN routing through one physical router interface and one switch trunk port.

- The switch port connected to the router is configured as a normal trunk.
- The router's physical interface is divided into logical **subinterfaces**.
- Each subinterface is associated with a VLAN using `encapsulation dot1q <vlan-id>`.
- Each subinterface receives an IP address that acts as the default gateway for that VLAN.
- The router treats a received VLAN tag as traffic for the matching subinterface and tags outbound traffic accordingly.
- A subinterface number does not technically have to match its VLAN ID, but matching them is strongly recommended.

Example from the slideshow:

```text
interface gigabitEthernet0/0
 no shutdown

interface gigabitEthernet0/0.10
 encapsulation dot1q 10
 ip address 192.168.1.62 255.255.255.192

interface gigabitEthernet0/0.20
 encapsulation dot1q 20
 ip address 192.168.1.126 255.255.255.192

interface gigabitEthernet0/0.30
 encapsulation dot1q 30
 ip address 192.168.1.190 255.255.255.192
```

Verify the router configuration with:

```text
show ip interface brief
show ip route
```

When working correctly, each subinterface is up/up, and the VLAN subnets appear as connected routes.

## Common mistakes

- Native VLANs do not match on both ends of a trunk.
- `switchport trunk allowed vlan ...` accidentally replaces the existing allowed VLAN list because `add` was omitted.
- A VLAN is allowed on the trunk but has not been created locally.
- `show vlan brief` is used to verify trunks instead of `show interfaces trunk`.
- A switch that supports ISL and 802.1Q is left with encapsulation set to `auto`, causing `switchport mode trunk` to be rejected.
- The switch-to-router port in a ROAS design is configured as an access port instead of a trunk.
- The router's parent physical interface remains administratively down.

## Exam memory anchors

- **Trunk = many VLANs over one link.**
- **802.1Q tag = 4 bytes.**
- **TPID = `0x8100`.**
- **PCP 3 bits + DEI 1 bit + VID 12 bits.**
- **Usable VLAN IDs = `1-4094`.**
- **Native VLAN traffic is untagged by default.**
- **Native VLANs must match.**
- **ROAS = trunk on the switch, subinterfaces on the router.**
- **Verify trunks with `show interfaces trunk`.**

## One-sentence recap

802.1Q trunks efficiently carry multiple VLANs over one link, the matching native VLAN carries untagged traffic, and Router-on-a-Stick uses tagged router subinterfaces to route between those VLANs.
