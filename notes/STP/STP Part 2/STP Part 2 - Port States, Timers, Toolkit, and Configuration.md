---
title: "STP Part 2 - Port States, Timers, Toolkit, and Configuration"
aliases:
  - STP Part 2
  - Spanning Tree Protocol Part 2
tags:
  - ccna
  - switching
  - stp
  - spanning-tree
  - layer-2
  - portfast
  - bpdu-guard
source: "CCNA 200-301 Day 21 - STP (Spanning Tree Protocol) Part 2"
date: 2026-07-21
---

# STP Part 2: Port States, Timers, Toolkit, and Configuration

> [!summary]
> Classic **802.1D STP** prevents Layer 2 loops by keeping root and designated ports in a forwarding state while redundant non-designated ports block. A port that must begin forwarding normally moves through **Listening** and **Learning** first. The default timers can make recovery take as long as **50 seconds**. **PortFast** removes the startup delay on end-host ports, while **BPDU Guard** protects those ports from an accidentally connected switch.

## Original slides

*Day 21 Slides - STP Part 2.pdf*

## How Part 2 fits with Part 1

[Part 1](<STP Part 1 - Redundancy, Root Bridge, and Port Roles.md>) explains how STP elects the root bridge and assigns root, designated, and non-designated port roles. Part 2 explains what those ports do after their roles are selected, how long convergence can take, and how to configure the behavior.

> [!important] Protocol scope
> The blocking, listening, learning, and forwarding sequence in this deck describes **classic STP/PVST (802.1D behavior)**. Rapid STP and Rapid PVST+ use different roles and faster transition mechanisms.

## Classic STP port states

| State | Stable or transitional? | Sends BPDUs? | Receives BPDUs? | Forwards user frames? | Learns source MACs? |
|---|---|---:|---:|---:|---:|
| **Blocking** | Stable | No | Yes | No | No |
| **Listening** | Transitional | Yes | Yes | No | No |
| **Learning** | Transitional | Yes | Yes | No | Yes |
| **Forwarding** | Stable | Yes | Yes | Yes | Yes |
| **Disabled** | Stable | No | No | No | No |

### Blocking

- Used by non-designated ports to prevent loops.
- Does not carry normal network traffic.
- Receives BPDUs but does not send or forward them.
- Does not learn MAC addresses.

### Listening

- Entered by a root or designated port after blocking.
- Lasts **15 seconds** by default.
- Processes STP BPDUs but neither forwards user traffic nor learns MAC addresses.
- Gives STP time to confirm that forwarding will not create a loop.

### Learning

- Follows listening and lasts another **15 seconds** by default.
- Still does not forward user traffic.
- Begins learning source MAC addresses, allowing the switch to build its MAC address table before forwarding.

### Forwarding

- Stable state for root and designated ports.
- Sends and receives BPDUs.
- Forwards normal traffic and learns MAC addresses.

```mermaid
flowchart LR
    B["Blocking"] -->|"15 s forward delay"| L["Listening"]
    L -->|"15 s forward delay"| A["Learning"]
    A --> F["Forwarding"]
    F -->|"May block immediately"| B
```

> [!warning] Direction matters
> A forwarding port may move directly to blocking because blocking cannot create a loop. A blocking port cannot move directly to forwarding; it must pass through listening and learning first.

## STP timers

| Timer | Default | Purpose |
|---|---:|---|
| **Hello** | 2 seconds | How often the root bridge originates configuration BPDUs |
| **Forward Delay** | 15 seconds | Time spent in listening and, separately, in learning |
| **Max Age** | 20 seconds | How long stored BPDU information remains valid without a fresh BPDU |

The root bridge's timer values govern the entire STP topology. Each fresh BPDU resets the Max Age countdown.

### Worst-case classic convergence

If a blocked backup port stops receiving valid BPDUs and must become forwarding, the transition can take:

```text
Max Age       20 seconds
Listening     15 seconds
Learning      15 seconds
-----------------------
Total         50 seconds
```

If another valid BPDU arrives before Max Age expires, the timer resets and STP does not change the topology. If the timer reaches zero, the switch reevaluates the root bridge and its local port roles.

> [!tip] Why a newly connected PC may wait about 30 seconds
> A normal access port can spend 15 seconds listening and 15 seconds learning before it forwards. PortFast is the intended solution for a port connected to a single end host.

## BPDU behavior and fields

Switches exchange **Bridge Protocol Data Units (BPDUs)** to advertise the root bridge and maintain the loop-free topology.

### Important BPDU fields shown in the deck

- Protocol identifier, version, and BPDU type
- Flags, including topology-change information
- Root Bridge ID
- Root path cost
- Sender Bridge ID
- Sender Port ID
- Message Age, Max Age, Hello Time, and Forward Delay

The deck contrasts these destination MAC addresses:

| STP variant | Destination MAC |
|---|---|
| Standard IEEE STP | `0180.c200.0000` |
| Cisco PVST+ | `0100.0ccc.cccd` |

- Original Cisco **PVST** operated with ISL trunk encapsulation.
- **PVST+** adds support for 802.1Q trunks.
- In classic STP, designated ports send the root's BPDU information downstream. Root and non-designated ports do not forward received BPDUs out those same ports.

## STP toolkit

### PortFast

PortFast moves an eligible port directly to forwarding, bypassing listening and learning.

Use it only on ports connected to end hosts such as PCs, phones, printers, or servers. Enabling it toward another switch can allow a Layer 2 loop to form immediately.

Per-interface configuration:

```cisco
interface g0/2
 spanning-tree portfast
```

Global default for access ports:

```cisco
spanning-tree portfast default
```

> [!warning]
> PortFast does not disable STP. A PortFast port still participates in spanning tree; it simply skips the normal startup delay.

### BPDU Guard

BPDU Guard protects an edge port. If the port receives a BPDU, the switch places it into an error-disabled state to prevent the newly detected switch from creating a loop.

Per-interface configuration:

```cisco
interface g0/2
 spanning-tree bpduguard enable
```

Global default on PortFast-enabled ports:

```cisco
spanning-tree portfast bpduguard default
```

> [!best-practice]
> On user-facing access ports, PortFast and BPDU Guard are complementary: PortFast gives fast connectivity, and BPDU Guard shuts the port if it unexpectedly hears a switch.

### Root Guard

Root Guard prevents a superior BPDU received on a protected interface from changing the intended root bridge. The port is placed into a root-inconsistent, non-forwarding condition while the superior BPDU is present.

### Loop Guard

Loop Guard prevents a non-designated port from incorrectly moving to forwarding when expected BPDUs stop arriving, such as during a unidirectional-link failure. The port is kept in a loop-inconsistent, non-forwarding condition.

For this deck's CCNA focus, know **PortFast** and **BPDU Guard** most thoroughly.

## STP configuration

### Select the spanning-tree mode

```cisco
spanning-tree mode ?
 mst
 pvst
 rapid-pvst

spanning-tree mode pvst
```

| Mode | Meaning |
|---|---|
| `mst` | Multiple Spanning Tree |
| `pvst` | Per-VLAN Spanning Tree using classic STP behavior |
| `rapid-pvst` | Per-VLAN Rapid Spanning Tree |

### Configure primary and secondary roots

```cisco
spanning-tree vlan 10 root primary
spanning-tree vlan 10 root secondary
```

- `root primary` normally sets the configurable bridge priority to `24576`.
- If another switch already has a lower priority, IOS attempts to set this switch to one `4096` step below that value.
- `root secondary` sets the configurable bridge priority to `28672`.
- The VLAN ID is added as the Extended System ID. For example, priority `24576` appears as `24577` in VLAN 1.

You can also set the priority directly:

```cisco
spanning-tree vlan 10 priority 24576
```

Valid bridge priorities range from `0` through `61440` in increments of `4096`.

### Per-VLAN STP load balancing

PVST allows a different root bridge in each VLAN. This does not balance individual frames; it makes different VLANs prefer different Layer 2 trees.

Example design:

```cisco
! SW1
spanning-tree vlan 10 root primary
spanning-tree vlan 20 root secondary

! SW2
spanning-tree vlan 20 root primary
spanning-tree vlan 10 root secondary
```

VLAN 10 then prefers SW1 as root, while VLAN 20 prefers SW2. Each switch backs up the other VLAN.

### Change interface cost or port priority

```cisco
interface g0/1
 spanning-tree vlan 1 cost 200
 spanning-tree vlan 1 port-priority 32
```

| Setting | Valid values shown in the deck | Effect |
|---|---|---|
| Path cost | `1`-`200000000` | Lower cost makes the path more preferred |
| Port priority | `0`-`224`, increments of `32` | Lower priority wins a Port ID tie-breaker |

Default port priority is `128`. In a Port ID such as `0x8002`, `0x80` represents decimal priority `128` and `0x002` represents port number 2.

## Verification

```cisco
show spanning-tree
```

Check:

- Spanning-tree mode and VLAN instance
- Root ID and local Bridge ID
- Root path cost and root port
- Interface roles and states
- Hello, Max Age, and Forward Delay values
- Port cost and Port ID
- Whether the switch considers itself the root

## Exam traps and practical takeaways

- **Blocking receives BPDUs** but does not forward frames or learn MAC addresses.
- **Learning learns MAC addresses** but still does not forward user traffic.
- The Forward Delay applies once to listening and again to learning: `15 + 15 = 30` seconds.
- A failed path can require `20 + 15 + 15 = 50` seconds in classic STP.
- PortFast belongs on **end-host ports**, not switch-to-switch links.
- BPDU Guard reacts to an unexpected BPDU by protecting the topology, typically through error-disable.
- Root Guard protects root-bridge placement; Loop Guard protects against loss of BPDUs on a redundant path.
- `root primary` and `root secondary` are convenience macros that adjust priority; they do not create new port roles.
- Per-VLAN load balancing is achieved by choosing different root bridges for different VLANs.
- A lower path cost or port priority is preferred.

## Quick review

- Stable states: blocking and forwarding.
- Transitional states: listening and learning.
- Defaults: Hello `2`, Forward Delay `15`, Max Age `20` seconds.
- PortFast skips listening and learning on an edge port.
- BPDU Guard protects an edge port from an attached switch.
- The root bridge supplies timer values for the STP domain.
- PVST+ supports 802.1Q and runs a separate spanning-tree instance per VLAN.
- Use different per-VLAN roots to distribute traffic across redundant links.
- Use `show spanning-tree` to verify the result.

## Related notes

- [STP Part 1 - Redundancy, Root Bridge, and Port Roles](<STP Part 1 - Redundancy, Root Bridge, and Port Roles.md>)
- [STP Part 2 - Quiz Review](<STP Part 2 - Quiz Review.md>)
- [VLANs Part 2 - Trunks, 802.1Q, and ROAS](<VLANs Part 2 - Trunks, 802.1Q, and ROAS.md>)
- [DTP & VTP - Slide Summary](<DTP & VTP - Slide Summary.md>)
