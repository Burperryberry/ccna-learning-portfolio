---
title: Rapid Spanning Tree Protocol (RSTP)
aliases:
  - RSTP
  - Rapid STP
  - Rapid PVST+
tags:
  - ccna
  - switching
  - rstp
  - rapid-pvst
  - spanning-tree
  - layer-2
source: CCNA 200-301 Day 22 - Rapid Spanning Tree Protocol
date: 2026-07-22
---

# Rapid Spanning Tree Protocol (RSTP)

> [!summary]
> **Rapid Spanning Tree Protocol (RSTP, IEEE 802.1w)** prevents Layer 2 loops like classic STP but converges much faster. It uses rapid switch-to-switch negotiation, reduces the port states to **Discarding, Learning, and Forwarding**, and divides the old non-designated role into **Alternate** and **Backup**. Cisco **Rapid PVST+** runs a separate RSTP instance per VLAN, allowing different VLANs to use different forwarding trees.

## Spanning-tree versions

| Version | Standard/vendor | VLAN instances | Load balancing |
|---|---|---|---|
| **STP (802.1D)** | IEEE | One instance shared by all VLANs | No per-VLAN load balancing |
| **PVST+** | Cisco enhancement of 802.1D | One classic STP instance per VLAN | Yes |
| **RSTP (802.1w)** | IEEE | One instance shared by all VLANs | No per-VLAN load balancing |
| **Rapid PVST+** | Cisco enhancement of 802.1w | One RSTP instance per VLAN | Yes |
| **MSTP (802.1s)** | IEEE | Multiple VLANs can be mapped to selected instances | Yes, without one instance per VLAN |

MSTP uses modified RSTP mechanics. For example, VLANs 1-5 can share one MST instance while VLANs 6-10 use another.

## What remains the same

RSTP and classic STP have the same fundamental purpose and election logic:

- Both prevent Layer 2 loops by blocking redundant paths.
- The switch with the lowest Bridge ID becomes the root bridge.
- Every non-root switch selects one best root port.
- Each segment selects one designated port.
- Path cost, neighbor Bridge ID, and Port ID still determine the preferred path.

The major difference is **how quickly the topology can safely change**.

## Why RSTP converges faster

Classic 802.1D depends heavily on timers. A blocked port may wait through Max Age, Listening, and Learning before it forwards.

RSTP uses a bridge-to-bridge proposal/agreement handshake on point-to-point links. This allows eligible ports to move to forwarding rapidly without waiting through the complete classic timer sequence.

> [!important]
> RSTP is not simply classic STP with shorter timers. Its rapid convergence comes primarily from new negotiation and synchronization behavior.

## RSTP path costs

RSTP uses a larger, long-form path-cost scale than the classic values shown in the previous STP lesson.

| Link speed | Classic STP cost | RSTP cost |
|---:|---:|---:|
| 10 Mbps | 100 | 2,000,000 |
| 100 Mbps | 19 | 200,000 |
| 1 Gbps | 4 | 20,000 |
| 10 Gbps | 2 | 2,000 |
| 100 Gbps | Not represented in the deck's classic table | 200 |
| 1 Tbps | Not represented in the deck's classic table | 20 |

Lower total path cost remains preferred.

## RSTP port states

RSTP simplifies the five classic states into three:

| RSTP state | Sends BPDUs? | Receives BPDUs? | Forwards user frames? | Learns MAC addresses? |
|---|---:|---:|---:|---:|
| **Discarding** | No | Yes | No | No |
| **Learning** | Yes | Yes | No | Yes |
| **Forwarding** | Yes | Yes | Yes | Yes |

### State mapping

| Classic STP state | RSTP equivalent |
|---|---|
| Disabled | Discarding |
| Blocking | Discarding |
| Listening | Discarding |
| Learning | Learning |
| Forwarding | Forwarding |

An administratively disabled interface is considered discarding. An enabled port that STP blocks to prevent a loop is also discarding.

## RSTP port roles

RSTP uses four primary port roles:

| Role | Normal state | Purpose |
|---|---|---|
| **Root (R)** | Forwarding | Best path from a non-root switch to the root bridge |
| **Designated (D)** | Forwarding | Port that advertises the best BPDU on a segment |
| **Alternate (A)** | Discarding | Backup path toward the root through another switch |
| **Backup (B)** | Discarding | Backup for a designated port on the same shared segment |

### Root port

- Closest port to the root bridge according to total RSTP cost.
- Every non-root switch has exactly one root port.
- The root bridge has no root port.

### Designated port

- Sends the best BPDU on its segment.
- Each segment has one designated port.
- All ports on the root bridge are designated.

### Alternate port

An alternate port is a discarding port that receives a superior BPDU from **another switch**.

- It provides an alternate path toward the root bridge.
- It is equivalent to the common non-designated blocking port in classic STP.
- If the active root port fails, the best alternate can rapidly become the new root port and forward.
- This rapid failover provides functionality similar to classic STP's optional **UplinkFast** feature.

### Backup port

A backup port is a discarding port that receives a superior BPDU from **another interface on the same switch**.

- It backs up a designated port, not the root port.
- It occurs when two local interfaces connect to the same shared collision domain, typically through a hub.
- The local interface with the lower Port ID becomes designated; the other becomes backup.
- Backup ports are rare because hubs are uncommon in modern networks.

> [!tip] Alternate versus backup
> **Alternate = another switch offers the superior BPDU. Backup = another port on this same switch offers the superior BPDU.**

## Classic optional features built into RSTP

RSTP incorporates the behavior of several classic STP enhancements:

| Classic feature | Purpose in classic STP | RSTP behavior |
|---|---|---|
| **UplinkFast** | Rapidly activates a backup path when the root port fails | Alternate-port failover is built in |
| **BackboneFast** | Reacts more quickly to indirect topology failures | Rapid handling of inferior/superior BPDU changes is built in |
| **PortFast** | Allows a host-facing port to forward immediately | RSTP edge-port behavior; still configured with PortFast on Cisco IOS |

UplinkFast and BackboneFast do not need to be configured when running RSTP or Rapid PVST+.

## Compatibility with classic STP

RSTP is backward-compatible with classic 802.1D STP.

When an RSTP switch connects to a classic STP neighbor, the boundary interface operates using classic STP behavior, including the slower timer-driven state transitions.

> [!warning]
> A single legacy STP neighbor can remove rapid convergence from that link, even when the rest of the switch runs Rapid PVST+.

## RSTP BPDUs

Classic and rapid spanning tree differ in how BPDUs are generated:

| Classic STP | RSTP |
|---|---|
| The root originates configuration BPDUs; downstream switches relay the information | Every RSTP switch originates its own BPDUs on designated ports |
| BPDU information normally remains valid for 20 seconds | A neighbor is considered lost after three missed Hellos |

All RSTP switches send BPDUs every Hello interval, which is **2 seconds** by default.

```text
3 missed BPDUs x 2-second Hello interval = 6 seconds
```

After three missed BPDUs, the switch treats the neighbor as lost and flushes MAC addresses learned through the failed interface.

This faster neighbor-loss detection is one reason RSTP reacts more quickly than classic STP.

## RSTP link types

RSTP distinguishes three link types because each supports different convergence behavior.

| Link type | Connection | Duplex | Rapid behavior |
|---|---|---|---|
| **Edge** | Switch to an end host | Usually full | Moves directly to forwarding |
| **Point-to-point** | Direct switch-to-switch link | Full | Supports rapid proposal/agreement |
| **Shared** | Switches connected through a hub | Half | Cannot use the same rapid point-to-point negotiation |

### Edge

An edge port connects to an end host and can enter forwarding immediately because it should not create a Layer 2 loop.

On Cisco IOS, configure it with PortFast:

```cisco
interface g0/1
 spanning-tree portfast
```

An edge port still participates in spanning tree and sends BPDUs. It should normally be paired with BPDU Guard.

### Point-to-point

A point-to-point link directly connects two switches and operates in full-duplex mode. IOS normally detects it automatically.

Manual override:

```cisco
interface g0/1
 spanning-tree link-type point-to-point
```

### Shared

A shared link connects switches through a hub and operates in half-duplex mode. IOS normally detects it automatically.

Manual override:

```cisco
interface g0/1
 spanning-tree link-type shared
```

## Configure Rapid PVST+

```cisco
spanning-tree mode rapid-pvst
```

Verify the mode and per-VLAN topology:

```cisco
show spanning-tree
```

The output should identify the protocol as RSTP and show roles such as:

```text
Root
Desg
Altn
Back
```

Typical states include:

```text
FWD
LRN
BLK
```

## RSTP decision procedure

Use the same root and path-selection logic learned for classic STP:

1. Elect the switch with the lowest Bridge ID as root.
2. Mark all root-bridge ports as designated.
3. Select one root port on every non-root switch using lowest total cost.
4. Use neighbor Bridge ID and neighbor Port ID to break root-port ties.
5. Select one designated port on every remaining segment.
6. Classify a discarding port as alternate if the superior BPDU came from another switch.
7. Classify it as backup if the superior BPDU came from another local interface on the same shared segment.
8. Identify each link as edge, point-to-point, or shared.

## Quiz review

### Quiz 1 - Port roles

All switches use the same priority, so SW1's lowest MAC address makes it the root bridge.

- SW1's ports are designated.
- SW2's port toward SW1 is root; its downstream port is designated.
- SW3's port toward SW1 is root.
- On the hub segment, SW3's lower Port ID is designated and its other interface is backup.
- SW4's best path toward the root is its root port; its inferior redundant path is alternate.

### Quiz 2 - Features built into 802.1w

**Correct answers: B, D, and E**

- PortFast edge-port behavior
- UplinkFast functionality
- BackboneFast functionality

### Quiz 3 - Configure an edge port

**Correct answer: D**

```cisco
spanning-tree portfast
```

### Quiz 4 - Root, roles, and link types

SW1 is the root because its priority `4097` is the lowest.

- Ports connected to PCs are **edge** links.
- Direct full-duplex switch links are **point-to-point**.
- Links through the hub are **shared**.
- SW1's switch-facing ports are designated because SW1 is root.
- Each non-root switch chooses its lowest-cost path to SW1 as its root port.
- The redundant parallel SW1-SW3 path produces an alternate port on SW3.
- The hub topology produces designated, alternate, and backup roles depending on which switch and local interface advertises the best BPDU.

## Exam traps and practical takeaways

- RSTP is IEEE `802.1w`; classic STP is `802.1D`.
- Rapid PVST+ runs one RSTP instance per VLAN.
- Root-bridge, root-port, and designated-port elections use the same rules as classic STP.
- RSTP has three states: discarding, learning, and forwarding.
- Discarding combines classic disabled, blocking, and listening behavior.
- Alternate ports back up the root port.
- Backup ports back up a designated port on the same shared segment.
- UplinkFast and BackboneFast functionality is built into RSTP.
- Every RSTP switch originates BPDUs every 2 seconds.
- Three missed BPDUs normally indicate neighbor loss after 6 seconds.
- RSTP flushes MAC entries learned through a failed interface.
- Edge ports use `spanning-tree portfast`.
- Point-to-point means full-duplex switch-to-switch.
- Shared means half-duplex, typically through a hub.
- A link to a classic STP switch operates using classic STP behavior.

## Quick review

- Purpose: loop prevention with much faster convergence.
- Standard: `802.1w`.
- Cisco per-VLAN implementation: Rapid PVST+.
- States: discarding, learning, forwarding.
- Roles: root, designated, alternate, backup.
- Alternate BPDU source: another switch.
- Backup BPDU source: another interface on the same switch.
- Link types: edge, point-to-point, shared.
- Default Hello: 2 seconds.
- Neighbor loss: 3 missed BPDUs, normally 6 seconds.
- Configuration: `spanning-tree mode rapid-pvst`.

## Related notes

- [[STP Part 1 - Redundancy, Root Bridge, and Port Roles]]
- [[STP Part 2 - Port States, Timers, Toolkit, and Configuration]]
- [[PortFast - Edge Ports and Configuration]]
- [[BPDU Guard, BPDU Filter, and ErrDisable]]
- [[Root Guard - Root Bridge Protection]]
- [[Loop Guard - Unidirectional Link Protection]]
