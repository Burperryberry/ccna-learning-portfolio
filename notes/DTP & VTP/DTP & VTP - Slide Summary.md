---
tags:
  - ccna
  - switching
  - vlans
  - dtp
  - vtp
source: "CCNA 200-301 Day 19 - DTP & VTP"
date: 2026-07-16
---

# DTP & VTP - Slide Summary

> [!summary]
> **DTP** negotiates whether a Cisco switch link becomes an access link or a trunk. **VTP** distributes a VLAN database between Cisco switches in the same VTP domain. The slides recommend manually configuring switchports and generally avoiding both protocols when they are not required.

The source deck notes that DTP and VTP were removed from its CCNA 200-301 exam topics list, but they remain useful concepts for understanding Cisco switching behavior.

## DTP - Dynamic Trunking Protocol

### Purpose

- Cisco-proprietary protocol that dynamically determines whether a switchport operates as an **access port** or a **trunk port**.
- DTP is enabled by default on Cisco switch interfaces unless the selected configuration disables negotiation.
- Manual configuration is safer and more predictable:

```cisco
switchport mode access
```

or

```cisco
switchport mode trunk
switchport nonegotiate
```

### DTP modes

| Mode | Behavior |
|---|---|
| `switchport mode trunk` | Statically places the port in trunk mode. |
| `switchport mode dynamic desirable` | Actively tries to form a trunk. |
| `switchport mode dynamic auto` | Passively waits for the neighbor to initiate trunking. |
| `switchport mode access` | Statically places the port in access mode and disables DTP negotiation. |

Older Cisco switches commonly default to **dynamic desirable**, while newer switches commonly default to **dynamic auto**. This explains why replacing a newer switch with an older one can unexpectedly cause a trunk to form.

### DTP negotiation results

| Side A | Side B | Result |
|---|---|---|
| Trunk | Trunk | Trunk |
| Trunk | Dynamic desirable | Trunk |
| Trunk | Dynamic auto | Trunk |
| Dynamic desirable | Dynamic desirable | Trunk |
| Dynamic desirable | Dynamic auto | Trunk |
| Dynamic auto | Dynamic auto | Access |
| Access | Dynamic desirable / dynamic auto / access | Access |
| Trunk | Access | Configuration mismatch - one side trunks while the other remains access |

Key idea: **desirable initiates; auto only responds**. DTP does not form a trunk with a router, PC, or other device that does not participate in DTP; the dynamic switchport operates as an access port.

### Disabling DTP

```cisco
switchport nonegotiate
```

- Use this on a manually configured trunk to stop DTP frames.
- `switchport mode access` also disables DTP negotiation.
- Best practice from the slides: manually configure every port as access or trunk and disable unnecessary negotiation.

### Legacy encapsulation negotiation

On older switches that support both **ISL** and **802.1Q**, DTP can also negotiate the trunk encapsulation:

```cisco
switchport trunk encapsulation negotiate
```

- If both switches support ISL, ISL is preferred by this legacy negotiation behavior.
- DTP frames use VLAN 1 with ISL or the native VLAN with 802.1Q; the default native VLAN is VLAN 1.

## VTP - VLAN Trunking Protocol

### Purpose

- Centralizes VLAN configuration on a **VTP server**.
- Other switches in the same **VTP domain** can synchronize their VLAN databases.
- VTP advertisements travel over trunk links.
- Intended to reduce repetitive VLAN configuration in large switched networks.
- The slides state that VTP is rarely used and recommend not using it in most environments because mistakes can affect the entire domain.
- Versions: **VTPv1, VTPv2, and VTPv3**.
- Modes: **server, client, and transparent**.
- Default mode on Cisco switches: **server**.

### VTP mode comparison

| Feature | Server | Client | Transparent |
|---|---:|---:|---:|
| Add, modify, or delete VLANs locally | Yes | No | Yes, for its local database |
| Synchronize from VTP advertisements | Yes | Yes | No |
| Advertise/forward VTP information | Yes | Yes | Forwards advertisements in the same domain |
| Store VLAN database in NVRAM | Yes | No in v1/v2; yes in v3 | Yes |
| Revision number increases after VLAN changes | Yes | No local changes permitted | Not participating in synchronization |

Important: a VTP server also behaves like a client. It can synchronize to another server in the same domain if the other server advertises a higher revision number.

### Domain and revision-number behavior

- Switches synchronize only when the **VTP domain matches**.
- A switch whose VTP domain is `NULL` can automatically join a domain after receiving an advertisement containing a domain name.
- Within the same domain, an advertisement with a **higher configuration revision number** is treated as newer, so the receiving switch updates its VLAN database to match it.
- Adding, modifying, or deleting a VLAN on a VTP server increases the revision number.

> [!danger] The major VTP hazard
> An old switch can contain a high revision number and an obsolete VLAN database. If it is connected to a network with the same VTP domain, the existing servers and clients may synchronize to that old database, potentially deleting valid VLANs and adding incorrect ones.

Two methods shown for resetting the revision number to `0`:

1. Change the VTP domain to an unused domain name.
2. Change the switch to VTP transparent mode.

### VTP versions

- **VTPv1/v2** do not support the extended VLAN range **1006-4094**.
- **VTPv3** supports extended-range VLANs and allows clients to retain the VLAN database in NVRAM.
- The main distinction highlighted between v1 and v2 is v2 support for **Token Ring VLANs**. Without Token Ring VLANs, the slides give no reason to prefer v2 over v1.

### Useful commands

```cisco
show vtp status

vtp domain CISCO
vtp mode server
vtp mode client
vtp mode transparent
vtp version 2
```

Use `show vlan brief` to inspect the VLANs currently present on a switch.

## DTP vs. VTP

| Protocol | What it controls | Main risk | Recommended approach |
|---|---|---|---|
| DTP | Whether a switch link becomes an access link or trunk | Unauthorized or accidental trunk formation | Configure access/trunk mode manually and disable negotiation |
| VTP | Distribution of the VLAN database | A higher revision can overwrite the domain's VLAN database | Avoid unless specifically required; verify domain, mode, and revision before connecting switches |


## Quick review

- **Desirable + auto = trunk**; **auto + auto = access**.
- `switchport nonegotiate` disables DTP on a manually configured trunk.
- VTP clients cannot create, modify, or delete VLANs.
- VTP transparent switches maintain their own VLAN databases and do not synchronize.
- A matching VTP domain plus a higher revision number can overwrite VLAN information across the domain.
- Reset the VTP revision by changing to an unused domain or switching to transparent mode.
