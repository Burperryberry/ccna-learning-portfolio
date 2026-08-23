---
title: "CDP & LLDP"
aliases:
  - Layer 2 Discovery Protocols
  - Cisco Discovery Protocol
  - Link Layer Discovery Protocol
tags:
  - ccna
  - layer2
  - cdp
  - lldp
  - network-discovery
source: "Day 36 Slides - CDP & LLDP"
date: 2026-08-18
---

# CDP & LLDP

## Overview

**Layer 2 discovery protocols** let directly connected devices advertise information about themselves and learn information about their neighbors. The two protocols covered for the CCNA are:

- **CDP (Cisco Discovery Protocol):** Cisco proprietary and enabled by default on Cisco devices.
- **LLDP (Link Layer Discovery Protocol):** IEEE 802.1AB industry standard and usually disabled by default on Cisco devices.

Both protocols operate at Layer 2. Their frames do not require IP, although the information advertised inside a frame can include Layer 3 details such as an IP address.

> [!abstract] CCNA core idea
> CDP and LLDP discover only **directly connected neighbors**. Know which protocol is proprietary or open standard, their default timers and multicast MAC addresses, how to enable or disable them, and how to interpret the local interface and neighbor port fields.

> [!warning] Security tradeoff
> Discovery information is convenient for mapping and troubleshooting a network, but it can expose hostnames, models, interfaces, addresses, software versions, capabilities, and other details. Enable these protocols only where their operational value justifies the information disclosure.

## Layer 2 discovery protocol fundamentals

A device periodically sends discovery frames out participating interfaces. A directly connected neighbor processes the frame, records the advertised information in a neighbor table, and discards the frame rather than forwarding it.

```text
R1 G0/1 ---------------- G0/0 SW1
   |                         |
   |-- discovery frame ----->|  "I am R1; you connect to G0/1..."
   |<----- discovery frame --|  "I am SW1; you connect to G0/0..."
```

Typical neighbor information includes:

- Device ID or hostname
- Local interface
- Neighbor's interface or port ID
- Device type and capabilities
- Platform or hardware model
- Management or interface IP address, when available
- Operating system and software version
- Remaining holdtime
- Protocol-specific details

> [!important] Layer 2 does not mean “no Layer 3 information”
> CDP and LLDP operate at Layer 2 and do not need IP to transport their advertisements. They can still carry an IP address as advertised data.

### Why discovery stops at one link

CDP and LLDP use link-local multicast destinations. A receiving device processes and discards the frame; it does not flood or route the advertisement onward. Therefore, only devices connected to the same physical or logical Layer 2 link can become neighbors.

## CDP vs. LLDP comparison

| Feature | CDP | LLDP |
|---|---|---|
| Full name | Cisco Discovery Protocol | Link Layer Discovery Protocol |
| Standard | Cisco proprietary | IEEE 802.1AB industry standard |
| Multi-vendor use | Primarily Cisco devices | Supported by many vendors |
| Cisco default state | Globally and per-interface enabled | Usually globally and per-interface disabled |
| Destination multicast MAC | `0100.0CCC.CCCC` | `0180.C200.000E` |
| Default advertisement timer | 60 seconds | 30 seconds |
| Default holdtime | 180 seconds | 120 seconds |
| Additional timer | None emphasized for CCNA | Reinitialization delay: 2 seconds |
| Interface behavior | One control enables both sending and receiving | Transmit and receive are controlled separately |
| Default version | CDPv2 | Not versioned the same way for CCNA |
| VTP information | Can advertise it | Does not advertise Cisco-proprietary VTP data |
| Can coexist | Yes, CDP and LLDP can run simultaneously | Yes, CDP and LLDP can run simultaneously |

> [!tip] Fast memory pattern
> **CDP = Cisco, 60/180, `0100.0CCC.CCCC`.**  
> **LLDP = IEEE, 30/120/2, `0180.C200.000E`.**

## Cisco Discovery Protocol (CDP)

CDP is Cisco's proprietary Layer 2 discovery protocol. Cisco routers, switches, firewalls, IP phones, and other Cisco devices generally have CDP enabled by default.

### CDP operation and defaults

- CDP is globally enabled by default.
- CDP is enabled on each interface by default.
- Advertisements are sent from up interfaces every **60 seconds**.
- Advertisements use destination MAC `0100.0CCC.CCCC`.
- The default holdtime is **180 seconds**.
- If no new message arrives before the holdtime reaches zero, the neighbor is removed.
- CDP version 2 advertisements are sent by default.
- A received CDP frame is processed and discarded, not forwarded.

```text
Advertisement interval: 60 seconds
Holdtime after receipt:  180 seconds

180 -> ... -> about 120 -> new CDP frame -> reset to 180
180 -> ... -> 0 with no refresh        -> remove neighbor
```

### CDPv1 and CDPv2

There are two versions of CDP. CDPv2 is the default and adds capabilities beyond the older CDPv1, including help identifying native VLAN mismatches. The detailed version differences are not a major CCNA focus.

> [!note]
> The multicast address `0100.0CCC.CCCC` is also associated with other Cisco protocols, so a Wireshark destination label may mention CDP, VTP, DTP, PAgP, and UDLD rather than CDP alone.

## CDP configuration

### Global control

```cisco
R1(config)# cdp run
R1(config)# no cdp run
```

- `cdp run` enables CDP globally.
- `no cdp run` disables CDP globally on the entire device.

### Interface control

```cisco
R1(config)# interface g0/0
R1(config-if)# cdp enable
R1(config-if)# no cdp enable
```

`cdp enable` controls CDP on one interface and enables both sending and receiving. Global CDP must also be running.

### Timers and version

```cisco
R1(config)# cdp timer 60
R1(config)# cdp holdtime 180
R1(config)# cdp advertise-v2
```

Use `no cdp advertise-v2` to stop advertising CDPv2 and use CDPv1.

> [!example] Disable CDP only on an untrusted edge port
> ```cisco
> SW1(config)# interface g0/10
> SW1(config-if)# no cdp enable
> ```
> CDP remains available on other interfaces while the edge port stops participating.

## CDP show and verification commands

```cisco
R1# show cdp
R1# show cdp traffic
R1# show cdp interface
R1# show cdp interface g0/0
R1# show cdp neighbors
R1# show cdp neighbors detail
R1# show cdp entry SW1
```

| Command | What it verifies |
|---|---|
| `show cdp` | Global CDP state, message timer, holdtime, and advertisement version |
| `show cdp traffic` | Sent and received CDP packet counters, including version counters and errors |
| `show cdp interface` | CDP-enabled interfaces, interface state, encapsulation, timer, and holdtime |
| `show cdp neighbors` | Concise neighbor table with IDs, interfaces, holdtime, capabilities, platforms, and port IDs |
| `show cdp neighbors detail` | Detailed information for every CDP neighbor |
| `show cdp entry <name>` | The detailed information for one named neighbor |

If CDP is globally disabled, `show cdp` reports that CDP is not enabled.

### Reading `show cdp neighbors`

```text
Device ID   Local Intrfce   Holdtme   Capability   Platform   Port ID
SW1         Gig 0/0         153       R S I                    Gig 0/0
R2          Gig 0/1         146       R B                      Gig 0/0
```

| Field | Meaning |
|---|---|
| Device ID | Neighbor's hostname |
| Local Intrfce | Interface on the device where the command was entered |
| Holdtme | Remaining time before the neighbor entry is removed |
| Capability | Functions advertised by the neighbor |
| Platform | Neighbor's hardware model or product family |
| Port ID | Interface on the neighboring device |

> [!danger] Local interface vs. Port ID
> **Local Intrfce** belongs to the device where you entered the command. **Port ID** belongs to the neighbor. Mixing these up is a common exam and troubleshooting mistake.

### Important CDP capability codes

| Code | Meaning | CCNA relevance |
|---|---|---|
| `R` | Router | Memorize |
| `S` | Switch | Memorize |
| `I` | IGMP | Recognize; multicast detail is beyond this lesson |
| `B` | Source Route Bridge | Not a major CCNA focus |

A multilayer switch can advertise both `R` and `S` because it has both routing and switching capabilities.

### Detailed CDP neighbor information

`show cdp neighbors detail` and `show cdp entry <name>` can reveal information not shown by the concise neighbor table, including:

- Neighbor IP or management address
- IOS or software version
- Platform and capabilities
- Local interface and neighbor port ID
- Native VLAN
- Duplex setting
- VTP information on a Cisco switch

CDPv2 can help identify native VLAN and duplex mismatches. If the neighbor has no Layer 3 address to advertise, no IP address will appear.

> [!question] Which CDP command shows an IP address or OS version?
> Use `show cdp neighbors detail` or `show cdp entry <name>`. The concise `show cdp neighbors` output does not normally show those details.

## Link Layer Discovery Protocol (LLDP)

LLDP is the vendor-neutral Layer 2 discovery protocol defined by **IEEE 802.1AB**. It is useful when a network contains equipment from multiple vendors.

### LLDP operation and defaults

- LLDP is usually globally disabled by default on Cisco devices.
- LLDP is also disabled on interfaces by default in the Day 36 course model.
- Advertisements use destination MAC `0180.C200.000E`.
- The default advertisement timer is **30 seconds**.
- The default holdtime is **120 seconds**.
- The default reinitialization delay is **2 seconds**.
- A received LLDP frame is processed and discarded, not forwarded.
- CDP and LLDP may run at the same time.

The reinitialization delay postpones LLDP startup after the protocol is re-enabled globally or on an interface. This helps avoid rapid restart behavior when the state is flapping. It is a lower-priority CCNA detail, but it appears in configuration and verification output.

## LLDP configuration

### Global control

```cisco
R1(config)# lldp run
R1(config)# no lldp run
```

### Interface transmit and receive control

```cisco
R1(config)# interface g0/0
R1(config-if)# lldp transmit
R1(config-if)# lldp receive
```

To disable either direction:

```cisco
R1(config-if)# no lldp transmit
R1(config-if)# no lldp receive
```

> [!important] CDP and LLDP differ at the interface
> `cdp enable` controls both CDP transmission and reception. LLDP uses separate `lldp transmit` and `lldp receive` commands, so one direction can be enabled without the other.

### LLDP transmit/receive behavior

| Interface configuration | Sends LLDP? | Learns LLDP neighbors? |
|---|---:|---:|
| `lldp transmit` + `lldp receive` | Yes | Yes |
| `lldp transmit` only | Yes | No; received advertisements are discarded |
| `lldp receive` only | No | Yes |
| Neither command | No | No |

Global `lldp run` is still required for LLDP operation.

### Timers

```cisco
R1(config)# lldp timer 30
R1(config)# lldp holdtime 120
R1(config)# lldp reinit 2
```

> [!example] Enable full LLDP operation on two links
> ```cisco
> R1(config)# lldp run
> R1(config)# interface range g0/0 - 1
> R1(config-if-range)# lldp transmit
> R1(config-if-range)# lldp receive
> ```

## LLDP show and verification commands

```cisco
R1# show lldp
R1# show lldp traffic
R1# show lldp interface
R1# show lldp interface g0/0
R1# show lldp neighbors
R1# show lldp neighbors detail
R1# show lldp entry SW1
```

| Command | What it verifies |
|---|---|
| `show lldp` | Global state and the 30-second, 120-second, and 2-second timers |
| `show lldp traffic` | LLDP frames sent, received, discarded, and errored; TLV statistics |
| `show lldp interface` | Per-interface transmit/receive settings and current Tx/Rx state |
| `show lldp neighbors` | Concise neighbor table |
| `show lldp neighbors detail` | Detailed information for all LLDP neighbors |
| `show lldp entry <name>` | Detailed information for one LLDP neighbor |

Typical `show lldp interface` states include:

- **Tx state: IDLE** - waiting to send the next LLDP frame.
- **Rx state: WAIT FOR FRAME** - waiting for the next received LLDP frame.
- **WAIT PORT OPER** - waiting for the interface to become operational.

### Reading `show lldp neighbors`

```text
Device ID   Local Intf   Hold-time   Capability   Port ID
SW1         Gi0/0        120                      Gi0/0
R2          Gi0/1        120         R            Gi0/0
```

The concise LLDP table resembles the CDP table, but the displayed hold-time is the configured value rather than a visible countdown. Use the detailed form to see **time remaining**.

Important LLDP capability codes include:

| Code | Meaning |
|---|---|
| `B` | Bridge, meaning switch |
| `R` | Router |
| `T` | Telephone |
| `W` | WLAN access point |
| `P` | Repeater |
| `S` | Station |

> [!warning] Capability-code trap
> In CDP, `S` means **switch**. In LLDP, a switch is represented by `B` for **bridge**; LLDP's `S` means **station**.

### Detailed LLDP neighbor information

`show lldp neighbors detail` and `show lldp entry <name>` can show:

- System name and system description
- Chassis ID and port ID
- Local interface
- Management or IP address
- Software/OS version
- Time remaining
- System capabilities
- Enabled capabilities

LLDP distinguishes between:

- **System capabilities:** Functions the neighbor is capable of performing.
- **Enabled capabilities:** Functions currently active and advertised.

A multilayer switch can report system capabilities `B,R`. If routing is active, `R` can appear under enabled capabilities.

LLDP does not provide Cisco-proprietary VTP information. CDP can because both CDP and VTP are Cisco proprietary.

## Neighbor table interpretation example

Suppose R2 displays this CDP entry:

```text
Device ID   Local Intrfce   Holdtme   Capability   Platform   Port ID
SW2         Gig 0/1         173       R S I                    Gig 0/0
```

Interpret it as follows:

1. The local device is R2 because the command was entered on R2.
2. R2 reaches SW2 through **R2 G0/1**.
3. The neighbor side of that link is **SW2 G0/0**.
4. SW2 advertises routing and switching capabilities.
5. The entry remains valid while advertisements refresh its holdtime.

```text
R2 G0/1 ---------------- G0/0 SW2
   ^ Local interface        ^ Neighbor Port ID
```

## Wireshark observations

### CDP frame

- Destination MAC: `0100.0CCC.CCCC`
- CDP version: version 2 by default
- TTL: the CDP holdtime, normally 180 seconds
- Advertised values can include device ID, software version, platform, addresses, port ID, duplex, and capabilities
- No IP packet is required inside the Ethernet frame

### LLDP frame

- Destination MAC: `0180.C200.000E`
- TTL: the LLDP holdtime, normally 120 seconds
- Information is carried in **TLVs (Type-Length-Value fields)**
- Typical TLVs include chassis ID, port ID, system name, system description, capabilities, management address, and end-of-LLDPDU
- No IP packet is required inside the Ethernet frame

> [!note]
> The IP address displayed by a packet analyzer is advertised content inside the discovery data; the protocol itself still operates at Layer 2.

## Security considerations

Discovery protocols can help administrators map cabling, identify connected ports, confirm device models, and troubleshoot mismatches. The same information can also help an unauthorized connected device learn the network's structure.

Potentially exposed information includes:

- Hostnames and device roles
- Interface names and connections
- Management or interface IP addresses
- Hardware models and software versions
- Native VLAN, duplex, and VTP information through CDP
- Device capabilities

Practical controls:

- Disable CDP or LLDP globally if the network does not need it.
- Disable discovery selectively on Internet-facing, guest, or other untrusted edge ports.
- Keep discovery on trusted infrastructure links when it materially improves operations.
- Verify both the global state and per-interface state.
- Document exceptions so later troubleshooting does not mistake an intentional disable for a fault.

> [!danger]
> CDP and LLDP are discovery aids, not authentication or authorization mechanisms. A neighbor entry proves that an advertisement was received on a link; it does not establish that the sender is trustworthy.

## Troubleshooting workflow

1. Confirm the devices are directly connected and the physical interfaces are up.
2. Check the global protocol state with `show cdp` or `show lldp`.
3. Check the interface state with `show cdp interface` or `show lldp interface`.
4. For LLDP, verify both transmit and receive directions.
5. Check sent and received counters with the traffic command.
6. Review the concise neighbor table.
7. Use the detail or entry command for addresses, software, capabilities, and time remaining.
8. Confirm that the expected discovery protocol is supported on both devices.
9. Remember that CDP and LLDP do not discover devices beyond the directly connected link.

```cisco
R1# show cdp
R1# show cdp interface g0/0
R1# show cdp traffic
R1# show cdp neighbors detail

R1# show lldp
R1# show lldp interface g0/0
R1# show lldp traffic
R1# show lldp neighbors detail
```

> [!tip] Missing LLDP neighbor
> A working link is not enough. Confirm `lldp run`, then confirm `lldp transmit` on the neighbor and `lldp receive` on the local interface. Repeat in the opposite direction if both devices must learn each other.

## Common mistakes

- Treating CDP as an open standard instead of Cisco proprietary
- Treating LLDP as Cisco-only instead of IEEE 802.1AB
- Expecting either protocol to discover devices more than one link away
- Assuming Layer 2 discovery cannot advertise an IP address
- Forgetting that CDP is normally enabled by default on Cisco devices
- Expecting LLDP to work before enabling it globally
- Enabling only `lldp transmit` and expecting to learn neighbors
- Enabling only `lldp receive` and expecting the neighbor to learn this device
- Confusing the local interface with the neighbor's Port ID
- Confusing CDP `S` for switch with LLDP `S` for station
- Looking for a switch code `S` in LLDP instead of `B` for bridge
- Expecting `show cdp neighbors` to display the neighbor's IP address or OS version
- Expecting `show lldp neighbors` to show a visible per-neighbor countdown
- Assuming LLDP advertises Cisco-proprietary VTP information
- Changing timers without remembering the configured holdtime determines stale-entry removal
- Leaving discovery active on untrusted interfaces without considering information exposure

## CCNA exam tips

> [!example] High-value facts
> - **CDP:** Cisco proprietary; enabled by default
> - **LLDP:** IEEE 802.1AB; usually disabled by default on Cisco devices
> - **CDP MAC:** `0100.0CCC.CCCC`
> - **LLDP MAC:** `0180.C200.000E`
> - **CDP timers:** 60-second advertisements, 180-second holdtime
> - **LLDP timers:** 30-second advertisements, 120-second holdtime, 2-second reinit
> - **CDP interface command:** `[no] cdp enable`
> - **LLDP interface commands:** `[no] lldp transmit` and `[no] lldp receive`
> - **Scope:** directly connected neighbors only
> - **CDP switch code:** `S`
> - **LLDP switch/bridge code:** `B`
> - **Detailed neighbor information:** use `neighbors detail` or `entry <name>`

### Slide quiz review

1. **Which commands show the configured CDP timers?**  
   `show cdp` and `show cdp interface`. `show cdp neighbors` shows a remaining neighbor holdtime, not the complete configured timer information.

2. **Which commands represent the default CDP state?**  
   `cdp enable` under an interface and `cdp timer 60` globally. CDP is enabled by default, and its default holdtime is 180 seconds rather than 120.

3. **What system capabilities should LLDP show for a multilayer switch?**  
   `B,R`: `B` for bridge and `R` for router.

4. **Which LLDP statements are true?**  
   Interface transmit and receive operations are enabled separately, and LLDP can advertise a neighbor's OS version. LLDP is an industry standard, uses a 30-second default timer, and does not reveal OSPF or VTP settings.

5. **How do you identify which R2 interface connects to SW2?**  
   Read SW2's **Local Intrfce** field in R2's neighbor table. In the slide output, it is `G0/1`. The Port ID field belongs to SW2.

> [!question] Exam trap: timer output
> `show cdp neighbors` displays a neighbor entry's remaining holdtime. `show cdp` and `show cdp interface` display the configured CDP timer and holdtime.

> [!question] Exam trap: capability letters
> For a multilayer switch, CDP can show `R S`; LLDP can show `B,R`. Do not transfer one protocol's legend to the other.

## Flashcards

> [!question]- 1. What is the purpose of a Layer 2 discovery protocol?
> To exchange information with and learn information about directly connected devices.

> [!question]- 2. Do CDP and LLDP require IP to carry their advertisements?
> No. They operate at Layer 2, although their advertisements can include IP addresses as data.

> [!question]- 3. Why can only directly connected devices become CDP or LLDP neighbors?
> Received advertisements are processed and discarded rather than forwarded.

> [!question]- 4. Is CDP proprietary or standards-based?
> CDP is Cisco proprietary.

> [!question]- 5. Which standard defines LLDP?
> IEEE 802.1AB.

> [!question]- 6. What is CDP's default state on Cisco devices?
> Globally enabled and enabled on interfaces.

> [!question]- 7. What is LLDP's default state in the Day 36 Cisco course model?
> Usually globally disabled and disabled on interfaces.

> [!question]- 8. What destination MAC address does CDP use?
> `0100.0CCC.CCCC`.

> [!question]- 9. What destination MAC address does LLDP use?
> `0180.C200.000E`.

> [!question]- 10. What are the default CDP timer and holdtime?
> Advertisements every 60 seconds and a 180-second holdtime.

> [!question]- 11. What are the default LLDP timers?
> 30-second advertisements, a 120-second holdtime, and a 2-second reinitialization delay.

> [!question]- 12. What happens when a discovery neighbor's holdtime expires?
> The neighbor entry is removed from the table.

> [!question]- 13. Which command enables CDP globally?
> `cdp run`.

> [!question]- 14. Which command disables CDP globally?
> `no cdp run`.

> [!question]- 15. Which command disables CDP on one interface?
> `no cdp enable` under that interface.

> [!question]- 16. Which command enables LLDP globally?
> `lldp run`.

> [!question]- 17. Which LLDP commands enable both directions on an interface?
> `lldp transmit` and `lldp receive`.

> [!question]- 18. What does an LLDP transmit-only interface do?
> It sends LLDP advertisements but does not learn received LLDP neighbors.

> [!question]- 19. Which command lists concise CDP neighbors?
> `show cdp neighbors`.

> [!question]- 20. Which command shows detailed information for one CDP neighbor named SW1?
> `show cdp entry SW1`.

> [!question]- 21. Which command shows per-interface LLDP Tx/Rx status?
> `show lldp interface`.

> [!question]- 22. What is the difference between Local Intrfce and Port ID?
> Local Intrfce belongs to the device running the show command; Port ID belongs to the neighbor.

> [!question]- 23. What does `S` mean in CDP capability output?
> Switch.

> [!question]- 24. What does `B` mean in LLDP capability output?
> Bridge, meaning switch.

> [!question]- 25. What does `S` mean in LLDP capability output?
> Station, not switch.

> [!question]- 26. Which protocol can display Cisco VTP information?
> CDP. LLDP does not advertise Cisco-proprietary VTP information.

> [!question]- 27. Can CDP and LLDP run at the same time?
> Yes.

> [!question]- 28. Why might an administrator disable CDP or LLDP?
> They expose useful device and topology information to anything connected to the link.

## Quick reference

```cisco
! -------------------- CDP --------------------
! Global and interface state
cdp run
interface g0/0
 cdp enable

! Defaults
cdp timer 60
cdp holdtime 180
cdp advertise-v2

! Disable globally or per-interface
no cdp run
interface g0/10
 no cdp enable

! Verify
show cdp
show cdp traffic
show cdp interface
show cdp neighbors
show cdp neighbors detail
show cdp entry SW1

! -------------------- LLDP -------------------
! Global and interface state
lldp run
interface g0/0
 lldp transmit
 lldp receive

! Defaults
lldp timer 30
lldp holdtime 120
lldp reinit 2

! Disable one direction on one interface
interface g0/10
 no lldp transmit
 no lldp receive

! Verify
show lldp
show lldp traffic
show lldp interface
show lldp neighbors
show lldp neighbors detail
show lldp entry SW1
```

## Related notes

- [Day 05 - Ethernet LAN Switching (Part 1)](<../Ethernet LAN Switching/Day 05 - Ethernet LAN Switching (Part 1).md>)
- [DTP & VTP - Slide Summary](<../DTP & VTP/DTP & VTP - Slide Summary.md>)
- [VLANs Part 2 - Trunks, 802.1Q, and ROAS](<../VLANs/VLANs Part 2 - Trunks, 802.1Q, and ROAS.md>)
- [VLANs Part 3 - Native VLANs, Multilayer Switching, and SVIs](<../VLANs/VLANs Part 3 - Native VLANs, Multilayer Switching, and SVIs.md>)
