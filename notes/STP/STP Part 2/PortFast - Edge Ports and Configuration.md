---
title: "PortFast - Edge Ports and Configuration"
aliases:
  - PortFast
  - STP PortFast
tags:
  - ccna
  - switching
  - stp
  - portfast
  - layer-2
  - edge-port
source: "CCNA 200-301 Day 21.1 - PortFast"
date: 2026-07-21
---

# PortFast: Edge Ports and Configuration

> [!summary]
> **PortFast** allows a switch port connected to a single end host to enter the STP **Forwarding** state immediately. It bypasses the normal Listening and Learning delays, giving the host immediate network access. PortFast is safe on true edge ports, but using it toward another switch can create a temporary Layer 2 loop.

## The problem PortFast solves

When an end host connects to a normal switch access port, the physical and data-link status may already show `up/up`, but classic STP does not forward data immediately.

The designated port normally transitions through:

```text
Listening     15 seconds
Learning      15 seconds
-----------------------
Total delay   30 seconds
```

During this delay, the user may see an active link but still be unable to reach the network. The delay protects against loops, but a direct switch-to-host link does not create a redundant Layer 2 path.

## The PortFast solution

With PortFast enabled, the edge port skips Listening and Learning:

```mermaid
flowchart LR
    A["Link comes up"] --> B["Forwarding immediately"]
```

The port can send and receive data as soon as the link comes online.

> [!important]
> PortFast changes how quickly a port enters forwarding. It does not turn off STP, and the port can still send and receive BPDUs.

## Where PortFast belongs

Use PortFast on links to single end devices such as:

- PCs and workstations
- Printers
- Servers
- IP phones
- Router-on-a-stick connections, when deliberately configured as a PortFast trunk
- Virtualization hosts carrying multiple VLANs, when deliberately configured as a PortFast trunk

Do not use ordinary PortFast toward:

- Another switch
- A hub or bridge
- Any device that can create a redundant Layer 2 path

> [!warning] Loop risk
> A PortFast port begins forwarding immediately. If it connects to another switch, it may forward before STP can block the redundant path, causing a temporary bridging loop.

## Configure PortFast on one access port

```cisco
interface g0/1
 spanning-tree portfast
```

This enables PortFast only on that interface. The standard per-interface command becomes active only while the interface operates as a non-trunking port.

Modern Cisco IOS may write the equivalent configuration with the `edge` keyword:

```cisco
interface g0/1
 spanning-tree portfast edge
```

Both forms produce the same edge-port behavior.

## Enable PortFast by default

```cisco
spanning-tree portfast default
```

This enables PortFast by default on access ports, not trunk ports. Modern IOS may store the command as:

```cisco
spanning-tree portfast edge default
```

If one access port should not use the global default, disable PortFast on that interface:

```cisco
interface g0/1
 spanning-tree portfast disable
```

The `disable` command does not use the `edge` keyword.

## PortFast on a trunk port

The normal per-port and global-default commands apply to access ports. A trunk requires the trunk-specific command:

```cisco
interface g0/1
 spanning-tree portfast trunk
```

Modern IOS may store it as:

```cisco
interface g0/1
 spanning-tree portfast edge trunk
```

Legitimate examples include:

- A trunk to a virtualization server hosting VMs in multiple VLANs
- A trunk to a router using router-on-a-stick

PortFast trunk must be configured per interface. The global PortFast default does not enable it on trunks.

> [!warning]
> A PortFast trunk should terminate on a single host or router. Do not use it for an ordinary switch-to-switch trunk.

## Edge and network PortFast

The deck identifies two PortFast types:

| Type | Purpose |
|---|---|
| **Edge** | End-host-facing behavior covered by the CCNA lesson |
| **Network** | Used with Bridge Assurance; outside this lesson's CCNA scope |

On modern Cisco switches, IOS automatically adds `edge` to the running configuration when the commands from this lesson are used.

| Entered command | Running configuration may show |
|---|---|
| `spanning-tree portfast` | `spanning-tree portfast edge` |
| `spanning-tree portfast trunk` | `spanning-tree portfast edge trunk` |
| `spanning-tree portfast default` | `spanning-tree portfast edge default` |

## Verification

### Inspect STP details for one interface

```cisco
show spanning-tree interface g0/1 detail
```

Look for lines such as:

```text
The port is in the portfast edge mode
```

For a PortFast trunk, look for:

```text
The port is in the portfast edge trunk mode
```

The detailed output also shows:

- Port role and state
- Path cost and Port ID
- Designated root and bridge
- Forwarding-state transition count
- Link type
- BPDUs sent and received

### Inspect the interface configuration

```cisco
show running-config interface g0/1
```

This reveals whether IOS stored the `edge` keyword. The command shown in the deck is not supported in Packet Tracer, so Packet Tracer behavior may differ from physical or virtual IOS devices.

## Command reference

| Goal | Command |
|---|---|
| Enable on one access port | `spanning-tree portfast [edge]` |
| Enable by default on access ports | `spanning-tree portfast [edge] default` |
| Disable on one port | `spanning-tree portfast disable` |
| Enable on one trunk | `spanning-tree portfast [edge] trunk` |
| Verify detailed port state | `show spanning-tree interface interface-name detail` |
| View interface configuration | `show running-config interface interface-name` |

Square brackets indicate that the `edge` keyword is optional when entering the command on modern IOS; the resulting behavior is the same.

## STP toolkit context

PortFast is one part of the broader STP toolkit:

| Feature | Purpose |
|---|---|
| **PortFast** | Immediately forwards on a trusted edge port |
| **BPDU Guard** | Disables an edge port if it receives a BPDU |
| **BPDU Filter** | Stops BPDU transmission and processing; use with great caution |
| **Root Guard** | Prevents a neighbor from becoming the root through a protected port |
| **Loop Guard** | Keeps a port from forwarding when expected BPDUs disappear |

> [!best-practice]
> PortFast and BPDU Guard are commonly paired. PortFast provides immediate connectivity, while BPDU Guard protects the topology if someone connects a switch to the edge port.

## Quick review

- A normal classic STP edge port may wait `15 + 15 = 30` seconds before forwarding.
- PortFast skips Listening and Learning.
- Standard PortFast commands apply to access ports.
- The global default enables PortFast on all access ports.
- Use `spanning-tree portfast disable` for an exception to the global default.
- Use the trunk-specific command only for a trusted single endpoint such as a virtualization server or ROAS router.
- Never use PortFast on an ordinary switch-to-switch link.
- Modern IOS may automatically add the `edge` keyword.
- Verify with `show spanning-tree interface interface-name detail`.

## Related notes

- [STP Part 2 - Port States, Timers, Toolkit, and Configuration](<STP Part 2 - Port States, Timers, Toolkit, and Configuration.md>)
- [STP Part 2 - Quiz Review](<STP Part 2 - Quiz Review.md>)
- [STP Part 1 - Redundancy, Root Bridge, and Port Roles](<STP Part 1 - Redundancy, Root Bridge, and Port Roles.md>)
- [VLANs Part 2 - Trunks, 802.1Q, and ROAS](<VLANs Part 2 - Trunks, 802.1Q, and ROAS.md>)
