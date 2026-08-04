---
title: "First Hop Redundancy Protocols - HSRP, VRRP, and GLBP"
aliases:
  - First Hop Redundancy Protocols
  - FHRP
  - HSRP VRRP GLBP
tags:
  - ccna
  - fhrp
  - hsrp
  - vrrp
  - glbp
  - routing
  - redundancy
source: "CCNA 200-301 Day 29 - First Hop Redundancy Protocols"
date: 2026-07-31
---

# First Hop Redundancy Protocols - HSRP, VRRP, and GLBP

## Summary

A **First Hop Redundancy Protocol (FHRP)** prevents the default gateway from becoming a single point of failure. Multiple routers share a **virtual IP address** and **virtual MAC address**, while hosts use the virtual IP as their one default gateway.

One router normally forwards traffic for the virtual gateway. If it fails, another router assumes the forwarding role. Hosts keep the same default-gateway IP and virtual MAC, so failover requires no manual host reconfiguration.

For the CCNA, know:

- Why a normal default gateway is a single point of failure
- How virtual IP and MAC addresses provide transparent failover
- The roles, multicast addresses, and virtual MAC formats of HSRP, VRRP, and GLBP
- How HSRP elects the active router
- Why FHRPs are non-preemptive by default
- How to configure and verify basic HSRP

> [!important] Core idea
> Hosts point to the **virtual IP**, not either router's physical interface IP. The active router answers ARP for the virtual IP using the **virtual MAC**.

---

## The default-gateway problem

A host sends off-subnet traffic to its configured default gateway. If that gateway router or its LAN-facing interface fails, the host cannot automatically switch to another router just because a second router exists.

Example without an FHRP:

- R1 address: `172.16.0.254`
- R2 address: `172.16.0.253`
- Host default gateway: `172.16.0.254`

If R1 fails, the host continues sending traffic to `.254`. R2 cannot help unless the host's default gateway is changed manually or another redundancy mechanism is used.

An FHRP solves this by introducing a shared virtual gateway:

- R1 address: `172.16.0.254`
- R2 address: `172.16.0.253`
- Virtual IP: `172.16.0.252`
- Host default gateway: `172.16.0.252`

The routers exchange multicast Hello messages and decide which router currently owns the virtual gateway role.

---

## How an FHRP works

### Normal operation

1. Two or more routers are configured with the same FHRP group and virtual IP.
2. The protocol generates a virtual MAC address for that virtual IP.
3. The routers elect an active forwarding router and at least one backup.
4. Hosts use the virtual IP as their default gateway.
5. A host ARPs for the virtual IP.
6. The active router replies with the virtual MAC.
7. Off-subnet frames are sent to the virtual MAC and forwarded by the active router.

Example host frame:

```text
Source IP:       172.16.0.1
Destination IP:  8.8.8.8
Source MAC:      PC1's MAC
Destination MAC: FHRP virtual MAC
```

The Layer 3 destination remains the remote host. Only the Layer 2 destination is the default gateway's virtual MAC.

### Failover

If the active router stops sending Hellos:

1. The backup determines that the active router has failed.
2. The backup assumes the active forwarding role.
3. The new active router begins using the same virtual IP and virtual MAC.
4. It sends a **gratuitous ARP**.
5. Switches relearn the virtual MAC on the new port.
6. Hosts continue using their existing default-gateway and ARP entries.

> [!note] Gratuitous ARP
> A gratuitous ARP is an unsolicited ARP reply sent without receiving an ARP request first. It is broadcast to `FFFF.FFFF.FFFF`, allowing switches and hosts to update their Layer 2 information quickly.

### Non-preemption and preemption

FHRPs are **non-preemptive by default**. If the original preferred router recovers, it does not automatically take the active role back from the current active router.

**Preemption** changes this behavior. A router with superior election values can reclaim the active role after it comes online.

> [!tip] Memory cue
> **Priority chooses the preferred router. Preempt allows it to reclaim the role.**

---

## Comparing HSRP, VRRP, and GLBP

| Protocol | Router roles | IPv4 multicast | Virtual MAC format | Cisco proprietary? | Main behavior |
|---|---|---|---|---|---|
| **HSRP v1** | Active / Standby | `224.0.0.2` | `0000.0c07.acXX` | Yes | One active gateway per group |
| **HSRP v2** | Active / Standby | `224.0.0.102` | `0000.0c9f.fXXX` | Yes | More groups and IPv6 support |
| **VRRP** | Master / Backup | `224.0.0.18` | `0000.5e00.01XX` | No | Open-standard gateway redundancy |
| **GLBP** | AVG / AVF | `224.0.0.102` | `0007.b400.XXYY` | Yes | Gateway redundancy plus load balancing |

`XX` or `XXX` represents the group number in hexadecimal. In the GLBP format, `XX` identifies the GLBP group and `YY` identifies the Active Virtual Forwarder.

---

## HSRP - Hot Standby Router Protocol

HSRP is Cisco proprietary. It elects:

- **Active router** - forwards traffic sent to the virtual gateway
- **Standby router** - takes over if the active router fails

### HSRP versions

| Feature | HSRP version 1 | HSRP version 2 |
|---|---|---|
| IPv4 multicast | `224.0.0.2` | `224.0.0.102` |
| Virtual MAC | `0000.0c07.acXX` | `0000.0c9f.fXXX` |
| Group range | `0-255` | `0-4095` |
| IPv6 support | No | Yes |

HSRP version 1 and version 2 are not compatible. All routers in the same HSRP group must use the same version.

### HSRP active-router election

The active router is selected in this order:

1. Highest HSRP priority
2. Highest interface IP address as the tiebreaker

The default HSRP priority is **100**. The valid priority range shown in IOS is `0-255`.

> [!warning]
> Raising a router's priority does not make it immediately active when another router already owns the role. Configure `preempt` on the router that should reclaim the active role.

### Load sharing across VLANs

HSRP normally has one active router per group. In a network with multiple VLANs, the administrator can distribute traffic by making:

- R1 active for one VLAN
- R2 active for another VLAN

This is per-VLAN or per-group load sharing. It is different from GLBP, which can load balance hosts within one subnet.

---

## VRRP - Virtual Router Redundancy Protocol

VRRP is an open-standard FHRP. It elects:

- **Master router** - forwards traffic for the virtual gateway
- **Backup router** - assumes the role if the master fails

Important values:

- IPv4 multicast: `224.0.0.18`
- Virtual MAC: `0000.5e00.01XX`
- `XX` is the VRRP group number in hexadecimal

Like HSRP, different routers can be made master for different VLANs to distribute traffic across the network.

> [!tip] Terminology
> HSRP uses **Active/Standby**. VRRP uses **Master/Backup**.

---

## GLBP - Gateway Load Balancing Protocol

GLBP is Cisco proprietary and provides redundancy plus load balancing within a single subnet.

### GLBP roles

- **AVG - Active Virtual Gateway**
  - Manages the GLBP group
  - Answers ARP requests for the virtual IP
  - Assigns hosts to different virtual forwarders
- **AVF - Active Virtual Forwarder**
  - Forwards traffic for a portion of the hosts
  - Uses its own virtual MAC address

One AVG is elected, and the AVG can assign up to **four AVFs**. The AVG can also serve as an AVF.

Important values:

- IPv4 multicast: `224.0.0.102`
- Virtual MAC: `0007.b400.XXYY`
- `XX` = GLBP group number
- `YY` = AVF number

GLBP can return different virtual MAC addresses to different hosts, allowing multiple routers to forward traffic for the same virtual IP.

---

## Basic HSRP configuration

Example topology:

- LAN: `172.16.0.0/24`
- R1 LAN address: `172.16.0.253`
- R2 LAN address: `172.16.0.252`
- HSRP virtual IP: `172.16.0.254`
- HSRP group: `1`
- Preferred active router: R1

### R1 - preferred active router

```cisco
R1(config)# interface g0/0
R1(config-if)# standby version 2
R1(config-if)# standby 1 ip 172.16.0.254
R1(config-if)# standby 1 priority 200
R1(config-if)# standby 1 preempt
```

### R2 - standby router

```cisco
R2(config)# interface g0/0
R2(config-if)# standby version 2
R2(config-if)# standby 1 ip 172.16.0.254
R2(config-if)# standby 1 priority 50
```

The essential commands are:

```cisco
standby version 2
standby group-number ip virtual-ip
standby group-number priority priority
standby group-number preempt
```

> [!important]
> The HSRP version, group number, and virtual IP must agree between the routers. The priorities may differ because they determine which router is preferred.

### What each command does

| Command | Purpose |
|---|---|
| `standby version 2` | Enables HSRP version 2 on the interface. |
| `standby 1 ip 172.16.0.254` | Creates group 1 and assigns its virtual IPv4 address. |
| `standby 1 priority 200` | Changes the router's election priority from the default of 100. |
| `standby 1 preempt` | Allows a superior router to take the active role from the current active router. |

---

## Verification

Use:

```cisco
R1# show standby
```

Important fields include:

- Interface and HSRP group
- HSRP version
- Local state: `Active` or `Standby`
- Virtual IP address
- Active virtual MAC address
- Hello and hold timers
- Whether preemption is enabled
- Active and standby router addresses
- Configured priority

Example interpretation:

```text
GigabitEthernet0/0 - Group 1 (version 2)
State is Active
Virtual IP address is 172.16.0.254
Active virtual MAC address is 0000.0c9f.f001
Preemption enabled
Priority 200
```

For HSRP version 2, group `1` becomes hexadecimal `001` at the end of the virtual MAC: `0000.0c9f.f001`.

---

## Troubleshooting checklist

If HSRP is not operating as expected, verify:

1. Both interfaces are up/up and in the same subnet.
2. Both routers use the same HSRP version.
3. Both routers use the same group number.
4. Both routers use the same virtual IP.
5. The hosts use the virtual IP as their default gateway.
6. The intended active router has the higher priority.
7. `preempt` is enabled if the preferred router should reclaim the role.
8. `show standby` displays one active router and one standby router.
9. Switches relearn the virtual MAC after failover.

### Common misunderstandings

- **The backup router's physical IP is not the host's alternate gateway.** Hosts use only the virtual IP.
- **Priority alone does not cause immediate takeover.** Preemption is required to reclaim the active role.
- **HSRP v1 and v2 cannot form one group together.**
- **HSRP and VRRP do not normally load balance hosts inside one group.** Use multiple groups/VLANs or GLBP, depending on the design.
- **A gratuitous ARP helps update Layer 2 forwarding information.** It does not change the host's configured default gateway.

---

## Exam-focused facts

- FHRPs protect the **first hop**, normally the host's default gateway.
- Hosts use a shared virtual IP and virtual MAC.
- The active router answers ARP for the virtual IP.
- A replacement router sends gratuitous ARP after failover.
- FHRPs are non-preemptive by default; preemption can be configured.
- HSRP: Active/Standby, Cisco proprietary.
- VRRP: Master/Backup, open standard.
- GLBP: AVG/AVF, Cisco proprietary, up to four AVFs.
- HSRP default priority: `100`.
- HSRP election: highest priority, then highest interface IP.
- HSRP v1 multicast: `224.0.0.2`.
- HSRP v2 and GLBP multicast: `224.0.0.102`.
- VRRP multicast: `224.0.0.18`.

---

## Knowledge check

1. **Which is a valid HSRP v1 virtual MAC?**  
   `0000.0c07.acab` - it matches `0000.0c07.acXX`.

2. **Which is a valid VRRP virtual MAC?**  
   `0000.5e00.010a` - it matches `0000.5e00.01XX`.

3. **What are the VRRP router roles?**  
   Master and Backup.

4. **What does the new active HSRP router send after failover?**  
   A gratuitous ARP.

5. **What is HSRP's purpose?**  
   It provides a redundant default-gateway address for hosts in a subnet.

---

## One-sentence takeaway

An FHRP lets multiple routers present one virtual default gateway, so a router failure can be hidden from hosts while HSRP, VRRP, or GLBP transfers or distributes the forwarding role.
