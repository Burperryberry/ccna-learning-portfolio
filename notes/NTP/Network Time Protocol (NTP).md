---
title: "Network Time Protocol (NTP)"
aliases:
  - NTP
  - Network Time Protocol
  - Time Synchronization
tags:
  - ccna
  - ntp
  - time
  - network-services
  - troubleshooting
source: "Day 37 Slides - NTP"
date: 2026-08-20
---

# Network Time Protocol (NTP)

## Overview

**Network Time Protocol (NTP)** automatically synchronizes clocks across a network. Accurate time is essential for correlating logs, reconstructing failures, validating events, and troubleshooting interactions between devices.

Manually setting every device is not scalable, and internal clocks drift. NTP solves this by allowing clients to request time from one or more NTP servers.

> [!abstract] CCNA core idea
> NTP uses **UDP port 123**. Lower stratum values are closer to the reference clock. Configure a client with `ntp server <ip-address>`, then verify the selected peer and synchronization state with `show ntp associations` and `show ntp status`.

> [!important] Why accurate time matters
> From a CCNA perspective, the most important reason is **accurate log timestamps for troubleshooting**. Logs from devices with mismatched clocks cannot be reliably placed in chronological order.

## Why network-device time matters

Routers, switches, computers, firewalls, and other devices maintain internal clocks. Cisco IOS displays the software clock with:

```cisco
R1# show clock
R1# show clock detail
```

Example:

```text
*00:19:49.411 UTC Sat Dec 26 2020
Time source is hardware calendar
```

Important details:

- The default timezone is **UTC (Coordinated Universal Time)**.
- The hardware calendar is the default time source before a better source is configured.
- A leading `*` means IOS does **not consider the time authoritative**.
- `show clock detail` displays the current time source.
- The internal clock drifts over time and is not an ideal long-term source.

### Log correlation example

If R2 records an OSPF adjacency failure on December 27, but R3 records the related link failure on May 23, their logs appear unrelated even when the events occurred together. Synchronized clocks let an administrator reconstruct the real event sequence.

```cisco
R2# show logging
R2# show clock
R3# show logging
R3# show clock
```

> [!warning]
> Accurate timestamps do not fix a fault by themselves. They make evidence from multiple devices comparable, which is often what makes the fault diagnosable.

## Software clock vs. hardware calendar

Cisco devices can maintain two separate time values:

| Timekeeper | Common IOS term | Characteristics |
|---|---|---|
| Software clock | Clock | Used by the running IOS system and displayed by `show clock` |
| Hardware clock | Calendar | Battery-backed on supported hardware; continues tracking time through restarts or power loss |

When a device starts, the hardware calendar can initialize the software clock. The two values are separate and can be configured or synchronized independently.

> [!tip] Direction memory aid
> The word after `clock` tells you what happens to the **software clock**:
> - `clock read-calendar`: clock **reads from** calendar
> - `clock update-calendar`: clock **updates** calendar

## Manual time configuration

Manual configuration is useful in labs and as a temporary measure, but the time will still drift.

### Display the software clock

```cisco
R1# show clock
R1# show clock detail
```

### Set the software clock

`clock set` is a privileged EXEC command:

```cisco
R1# clock set 14:30:00 27 Dec 2020
```

General syntax:

```cisco
clock set hh:mm:ss {day month | month day} year
```

After manual configuration, detailed output reports:

```text
Time source is user configuration
```

### Display and set the hardware calendar

```cisco
R1# show calendar
R1# calendar set 14:35:00 27 Dec 2020
```

General syntax:

```cisco
calendar set hh:mm:ss {day month | month day} year
```

### Synchronize clock and calendar

Copy the software clock into the hardware calendar:

```cisco
R1# clock update-calendar
```

Copy the hardware calendar into the software clock:

```cisco
R1# clock read-calendar
```

| Command | Source | Destination |
|---|---|---|
| `clock update-calendar` | Software clock | Hardware calendar |
| `clock read-calendar` | Hardware calendar | Software clock |

> [!question] Which command adjusts the software clock to match the hardware clock?
> `clock read-calendar` - the software clock reads the calendar.

## Timezone configuration

NTP distributes UTC time. Each device must be configured with the correct local timezone for local display.

```cisco
R1(config)# clock timezone JST 9
```

General syntax:

```cisco
clock timezone <name> <hours-offset> [minutes-offset]
```

Examples:

```cisco
R1(config)# clock timezone EST -5
R2(config)# clock timezone JST 9
R3(config)# clock timezone NST -3 30
```

The timezone name is a display label; the numeric values define its UTC offset.

> [!important]
> Timezone configuration does not change the underlying NTP reference. It changes how the UTC-based time is displayed locally.

## Daylight Saving Time (summer time)

IOS can apply a recurring daylight-saving rule:

```cisco
R1(config)# clock summer-time EDT recurring 2 Sunday March 02:00 1 Sunday November 02:00
```

This example starts daylight saving time on the second Sunday in March at 02:00 and ends it on the first Sunday in November at 02:00.

General form:

```cisco
clock summer-time <name> recurring <start-rule> <end-rule> [offset-minutes]
```

IOS can also configure absolute start and end dates with the `date` option. Always use the rule that applies to the device's actual jurisdiction.

## Manual time command review

```cisco
R1# show clock
R1# show clock detail
R1# clock set 14:30:00 27 Dec 2020

R1# show calendar
R1# calendar set 14:35:00 27 Dec 2020
R1# clock update-calendar
R1# clock read-calendar

R1(config)# clock timezone JST 9
R1(config)# clock summer-time EDT recurring 2 Sunday March 02:00 1 Sunday November 02:00
```

## NTP fundamentals

NTP provides automatic network-based time synchronization.

- NTP clients request time from NTP servers.
- A device can be an NTP client and server simultaneously.
- A client can synchronize with multiple servers.
- NTP uses **UDP port 123**.
- The lesson cites approximately **1 millisecond** accuracy on the same LAN and approximately **50 milliseconds** across a WAN or the Internet.
- NTP organizes time sources by **stratum**.

Public names such as `time.google.com` or `time.windows.com` may resolve to multiple server addresses. Production designs should follow the provider's published service guidance rather than copying temporary example addresses from a lab.

> [!warning]
> A successful DNS lookup only finds an address. NTP also needs IP reachability, UDP/123 permitted through filters, a working server, and enough successful exchanges to synchronize.

## Reference clocks and stratum

A **reference clock** is a highly accurate source such as an atomic clock or GPS clock.

| Stratum | Role |
|---:|---|
| 0 | Reference clock; not an ordinary network NTP server |
| 1 | NTP server directly connected to a stratum 0 reference clock |
| 2 | Server/client synchronized to a stratum 1 server |
| 3 | Server/client synchronized to a stratum 2 server |
| ... | Each downstream layer is one stratum higher |
| 15 | Highest usable stratum in the lesson |
| 16 | Unsynchronized/unreliable |

```text
Atomic/GPS reference clock       Stratum 0
            |
            v
Primary NTP server               Stratum 1
            |
            v
Secondary NTP server/client      Stratum 2
            |
            v
Downstream server/client         Stratum 3
```

**Stratum describes distance from the reference clock, not delay, bandwidth, or physical hop count.** A lower number is closer in the NTP hierarchy.

> [!tip] Stratum inheritance
> If R1 synchronizes to a stratum 1 server, R1 becomes stratum 2. A router synchronizing to R1 becomes stratum 3.

### Primary and secondary servers

- **Primary server:** Gets time directly from a reference clock; normally stratum 1.
- **Secondary server:** Gets time from another NTP server and provides time downstream. It operates as a client and server at the same time.

### Multiple servers and peering

An NTP client can use multiple servers for redundancy and better selection. Servers at the same stratum can also peer with one another in **symmetric active mode**.

Cisco devices can operate in three NTP modes:

1. Client mode
2. Server mode
3. Symmetric active mode

## Configure NTP client mode

Point a Cisco device at an NTP server:

```cisco
R1(config)# ntp server 216.239.35.0
```

General syntax:

```cisco
ntp server <ip-address> [prefer]
```

Configure multiple servers for redundancy:

```cisco
R1(config)# ntp server 216.239.35.0 prefer
R1(config)# ntp server 216.239.35.4
R1(config)# ntp server 216.239.35.8
R1(config)# ntp server 216.239.35.12
```

The `prefer` keyword marks a preferred association. NTP still evaluates whether a source is usable.

> [!important] Command-direction trap
> `ntp server <address>` configures the local router as a **client of the addressed server**. There is no basic `ntp client <address>` command in this workflow.

## Verify NTP associations

```cisco
R1# show ntp associations
```

Example:

```text
  address         ref clock       st   when   poll reach  delay  offset   disp
*~216.239.35.0    .GOOG.           1     43     64    17 62.007 1401.54  0.918
+~216.239.35.8    .GOOG.           1     43     64    17 64.220 1416.65  0.939
```

### Association status symbols

| Symbol | Meaning in the slide legend |
|---|---|
| `*` | System peer - the source currently used for synchronization |
| `#` | Selected |
| `+` | Candidate |
| `-` | Outlier |
| `x` | Falseticker |
| `~` | Configured association |

Symbols can appear together. For example, `*~` means the association is configured and is the current system peer.

### Association fields

| Field | Meaning |
|---|---|
| `address` | NTP peer or server address |
| `ref clock` | Upstream reference used by that peer |
| `st` | Peer's stratum |
| `when` | Seconds since the last received NTP message |
| `poll` | Polling interval in seconds |
| `reach` | Octal reachability register for the last eight polls |
| `delay` | Estimated round-trip delay, normally milliseconds |
| `offset` | Difference between local and peer time |
| `disp` | Dispersion, an estimate of clock error/uncertainty |

The `reach` value is displayed in octal:

- `0` means no recent successful replies.
- It grows as polls succeed.
- `377` means the last eight polls succeeded.

> [!note]
> NTP synchronization is not instantaneous. A newly configured association may initially show reach `0` or `1`, large dispersion, and no selected peer while samples accumulate.

## Verify NTP status

```cisco
R1# show ntp status
```

High-value output includes:

```text
Clock is synchronized, stratum 2, reference is 216.239.35.12
```

This confirms:

- Whether the local clock is synchronized
- The local device's stratum
- The selected reference server
- Reference time and last update
- Poll interval
- Clock offset, delay, dispersion, and drift information

> [!question] Associations vs. status
> `show ntp associations` compares the available peers and their measurements. `show ntp status` states whether the local clock is synchronized and identifies the active reference.

## NTP, UTC, timezone, and the hardware calendar

NTP uses UTC. Configure the local timezone separately:

```cisco
R1(config)# clock timezone JST 9
```

To periodically copy NTP-learned time into the hardware calendar:

```cisco
R1(config)# ntp update-calendar
```

The hardware calendar continues tracking the date and time across restart or power loss on supported hardware. At startup, it can initialize the software clock before NTP resynchronizes.

> [!warning] Similar command names
> - `clock update-calendar` is an immediate privileged EXEC copy from software clock to calendar.
> - `ntp update-calendar` is a global configuration that periodically updates the calendar from NTP-synchronized time.

## Use a stable NTP source interface

By default, packets may use the IP address of the outgoing physical interface. A loopback provides a stable source independent of any single link.

```cisco
R1(config)# interface loopback0
R1(config-if)# ip address 10.1.1.1 255.255.255.255
R1(config-if)# exit
R1(config)# ntp source loopback0
```

An internal client can then use the loopback address:

```cisco
R2(config)# ntp server 10.1.1.1
```

Requirements:

- The client must have a route to the loopback.
- Return routing must exist.
- UDP/123 must be permitted.
- Any authentication configuration must match.

If R1 is synchronized at stratum 2, R2 synchronizing to R1 becomes stratum 3.

## Server selection

The slides demonstrate R3 configured with two possible servers:

```cisco
R3(config)# ntp server 10.1.1.1
R3(config)# ntp server 10.2.2.2
```

The lower-stratum usable server is generally preferred. However, a real NTP selection algorithm also evaluates reachability and timing quality; a low stratum does not make an unreachable or invalid source usable.

## Configure NTP master mode

When no external source is available, a Cisco device can act as an NTP master using its local clock:

```cisco
R1(config)# ntp master
```

Optional syntax:

```cisco
R1(config)# ntp master <1-15>
```

The default device stratum for `ntp master` is **8**.

Typical default output:

```text
R1# show ntp associations
  address         ref clock       st
*~127.127.1.1     .LOCL.           7

R1# show ntp status
Clock is synchronized, stratum 8, reference is 127.127.1.1
```

`127.127.1.1` and `.LOCL.` represent the router's local NTP reference.

> [!danger] Operational caution
> `ntp master` makes the router advertise its own clock even without an external authoritative source. Use it deliberately for isolated networks or labs, and choose a stratum that will not override a better real source.

### Interpret `ntp master` quiz output

If the local association `127.127.1.1` is shown at stratum 8, the router itself operates one level higher at stratum 9. That output indicates:

```cisco
R1(config)# ntp master 9
```

This is different from the default `ntp master`, which makes the router stratum 8 and shows the local reference at stratum 7.

## Configure downstream clients

With R1 acting as an NTP master or synchronized internal server:

```cisco
R2(config)# ntp server 10.0.12.1
R3(config)# ntp server 10.0.12.1
```

Once synchronized, these clients can themselves provide time to downstream devices at one higher stratum.

## Configure symmetric active mode

Use `ntp peer` for peer relationships, typically between devices at the same hierarchical level:

```cisco
R2(config)# ntp peer 10.0.23.2
R3(config)# ntp peer 10.0.23.1
```

Symmetric active peers exchange time information with each other. Configure the peer relationship on both devices when building the two-way relationship shown in the lesson.

> [!tip] Mode comparison
> - `ntp server <address>`: local device acts as a client of that address
> - `ntp peer <address>`: symmetric active peer relationship
> - `ntp master [stratum]`: local device provides time from its own clock

## NTP authentication

NTP authentication is optional. It lets a client verify that time updates come from an intended source with the configured key.

The Day 37 IOS workflow uses three elements:

1. Create a key.
2. Mark the key as trusted.
3. Bind that key to the server or peer association.

### Authentication commands

```cisco
ntp authentication-key <key-number> md5 <key>
ntp trusted-key <key-number>
ntp server <ip-address> key <key-number>
ntp peer <ip-address> key <key-number>
```

Example server configuration:

```cisco
R1(config)# ntp authentication-key 1 md5 NTP_SHARED_KEY
R1(config)# ntp trusted-key 1
```

Example client configuration:

```cisco
R2(config)# ntp authentication-key 1 md5 NTP_SHARED_KEY
R2(config)# ntp trusted-key 1
R2(config)# ntp server 10.0.12.1 key 1
```

Example authenticated peer:

```cisco
R2(config)# ntp peer 10.0.23.2 key 1
R3(config)# ntp peer 10.0.23.1 key 1
```

Key numbers and key strings must correspond between the participating devices.

> [!important] Jeremy's IT Lab command behavior
> In the IOS version demonstrated in the slides, a separate `ntp authenticate` command is **not required**. The tested client-side commands are `ntp authentication-key`, `ntp trusted-key`, and `ntp server ... key ...` (or `ntp peer ... key ...`).

> [!warning] Protect real keys
> Treat authentication strings as secrets. Use an approved key-management process and avoid placing production keys in notes, screenshots, or shared configurations.

## Complete configuration examples

### Example 1: Internet-synchronized internal NTP server

R1 uses multiple upstream sources, prefers one, sources packets from a loopback, updates its calendar, and serves internal clients:

```cisco
R1(config)# interface loopback0
R1(config-if)# ip address 10.1.1.1 255.255.255.255
R1(config-if)# exit

R1(config)# ntp server 216.239.35.0 prefer
R1(config)# ntp server 216.239.35.4
R1(config)# ntp server 216.239.35.8
R1(config)# ntp server 216.239.35.12
R1(config)# ntp source loopback0
R1(config)# ntp update-calendar
R1(config)# clock timezone UTC 0
```

Internal clients:

```cisco
R2(config)# ntp server 10.1.1.1
R3(config)# ntp server 10.1.1.1
```

### Example 2: Isolated lab with local master

```cisco
R1# clock set 14:30:00 27 Dec 2020
R1# configure terminal
R1(config)# ntp master 8

R2(config)# ntp server 10.0.12.1
R3(config)# ntp server 10.0.12.1
```

The explicit stratum reminds administrators that this is a locally sourced clock, not a stratum 1 reference-backed server.

### Example 3: Authenticated internal client

```cisco
! R1 - intended time server
R1(config)# ntp authentication-key 10 md5 NTP_SHARED_KEY
R1(config)# ntp trusted-key 10

! R2 - client
R2(config)# ntp authentication-key 10 md5 NTP_SHARED_KEY
R2(config)# ntp trusted-key 10
R2(config)# ntp server 10.0.12.1 key 10
```

## Verification commands

```cisco
R1# show clock
R1# show clock detail
R1# show calendar
R1# show ntp associations
R1# show ntp status
R1# show running-config | include ^ntp|^clock
```

| Command | Verify |
|---|---|
| `show clock` | Current software time, timezone, and authoritative marker |
| `show clock detail` | Current time plus time source |
| `show calendar` | Hardware-calendar time |
| `show ntp associations` | Configured sources, selection symbols, stratum, reach, delay, offset, and dispersion |
| `show ntp status` | Local synchronization state, stratum, and selected reference |
| `show running-config` filter | NTP servers, peers, source interface, master mode, calendar update, timezone, and authentication configuration |

## Troubleshooting workflow

1. Check `show clock detail` to identify the current source.
2. Check `show ntp status` for synchronized or unsynchronized state.
3. Check `show ntp associations` for a `*` system peer.
4. Inspect `reach`; repeated `0` indicates the server is not responding.
5. Verify routing to the configured server or loopback source.
6. Confirm return routing to the selected NTP source address.
7. Confirm UDP port 123 is permitted through ACLs and firewalls.
8. Verify the server is operational and using a valid stratum.
9. If authentication is used, compare key numbers, key strings, trusted-key statements, and association key binding.
10. Allow time for multiple NTP polls; initial lack of synchronization is normal.
11. Check the configured timezone if the clock is synchronized but displayed local time appears wrong.
12. Compare software clock and hardware calendar if time becomes wrong after a restart.

> [!tip] Fast diagnostic split
> - **Wrong UTC/reference time:** investigate NTP synchronization.
> - **Correct UTC but wrong local display:** investigate `clock timezone` and summer-time settings.
> - **Correct while running but wrong after reboot:** investigate the hardware calendar and `ntp update-calendar`.

## Common mistakes

- Treating the hardware calendar and software clock as the same value
- Reversing `clock read-calendar` and `clock update-calendar`
- Expecting manual time to remain accurate indefinitely
- Assuming a configured timezone changes the time distributed by NTP
- Forgetting that NTP uses UTC internally
- Forgetting UDP port 123
- Calling a stratum 0 reference clock an ordinary network NTP server
- Thinking higher stratum is better
- Assuming stratum measures physical distance or network hop count
- Forgetting that a downstream synchronized router becomes one stratum higher than its source
- Using `ntp client <address>` instead of `ntp server <address>`
- Expecting `ntp server <address>` to make the addressed router a client of the local router
- Declaring success because an association is configured even though no `*` system peer is selected
- Reading `reach` as decimal rather than octal
- Expecting immediate synchronization after the first poll
- Forgetting routing to a loopback used with `ntp source`
- Allowing the forward path but blocking UDP/123 on the return path
- Using `ntp master` without understanding that it advertises the local clock
- Confusing default `ntp master` stratum 8 with the `.LOCL.` association stratum 7
- Configuring an authentication key without marking it trusted
- Marking a key trusted but failing to bind it to the server or peer association
- Assuming the slide's IOS requires a separate `ntp authenticate` command
- Leaving example keys or temporary public-server IP addresses in production configurations

## CCNA exam tips

> [!example] High-value facts
> - **Protocol/port:** NTP uses UDP 123
> - **Main purpose:** automatic clock synchronization
> - **Operational value:** accurate log timestamps
> - **Default timezone:** UTC
> - **Hardware clock term:** calendar
> - **Calendar -> software clock:** `clock read-calendar`
> - **Software clock -> calendar:** `clock update-calendar`
> - **NTP time -> calendar periodically:** `ntp update-calendar`
> - **Client configuration:** `ntp server <ip-address> [prefer]`
> - **Peer configuration:** `ntp peer <ip-address>`
> - **Local server:** `ntp master [stratum]`
> - **Default `ntp master` device stratum:** 8
> - **Stable source:** `ntp source <interface>`
> - **Verify peers:** `show ntp associations`
> - **Verify synchronization:** `show ntp status`
> - **Best selected association:** marked with `*`
> - **Successful last eight polls:** reach `377`
> - **Maximum usable stratum:** 15; 16 means unsynchronized

### Slide quiz review

1. **Which command adjusts the software clock to match the hardware calendar?**  
   `clock read-calendar`.

2. **Which command configures the timezone?**  
   From global configuration mode: `clock timezone <name> <offset>`.

3. **`show ntp associations` displays `.LOCL.` at stratum 8. Which master command was configured?**  
   `ntp master 9`. The local reference appears one stratum lower than the router's advertised device stratum.

4. **Which command configures NTP client mode?**  
   `ntp server 216.239.35.0` or, generally, `ntp server <ip-address>`.

5. **Which client commands enable authenticated synchronization in the slide workflow?**  
   `ntp authentication-key <number> md5 <key>`, `ntp trusted-key <number>`, and `ntp server <ip-address> key <number>`.

> [!question] Exam trap: server keyword
> The word `server` identifies the remote time source. Entering `ntp server 10.0.0.1` makes the local device an NTP client of `10.0.0.1`.

> [!question] Exam trap: master stratum
> Default `ntp master` makes the router stratum 8 and displays its `.LOCL.` reference as stratum 7. A `.LOCL.` row at stratum 8 indicates `ntp master 9`.

## Flashcards

> [!question]- 1. What does NTP stand for?
> Network Time Protocol.

> [!question]- 2. Which transport protocol and port does NTP use?
> UDP port 123.

> [!question]- 3. Why is accurate time especially important for CCNA troubleshooting?
> It gives logs accurate, comparable timestamps across devices.

> [!question]- 4. Which command displays the Cisco IOS software clock?
> `show clock`.

> [!question]- 5. Which command displays the clock's time source?
> `show clock detail`.

> [!question]- 6. What does a leading `*` in `show clock` mean?
> The time is not considered authoritative.

> [!question]- 7. What is the default Cisco IOS timezone?
> UTC.

> [!question]- 8. What IOS term refers to the hardware clock?
> Calendar.

> [!question]- 9. Which command sets the software clock manually?
> `clock set hh:mm:ss day month year` from privileged EXEC mode.

> [!question]- 10. Which command sets the hardware calendar manually?
> `calendar set hh:mm:ss day month year`.

> [!question]- 11. Which command copies the calendar into the software clock?
> `clock read-calendar`.

> [!question]- 12. Which command copies the software clock into the calendar?
> `clock update-calendar`.

> [!question]- 13. Which command configures a timezone?
> `clock timezone <name> <hours-offset> [minutes-offset]`.

> [!question]- 14. Does NTP distribute local timezone time?
> No. NTP uses UTC; each device applies its configured timezone for display.

> [!question]- 15. What is a stratum 0 device?
> A highly accurate reference clock such as an atomic or GPS clock.

> [!question]- 16. What is a stratum 1 NTP server?
> A server directly connected to a stratum 0 reference clock.

> [!question]- 17. If R1 uses a stratum 1 source, what stratum is R1?
> Stratum 2.

> [!question]- 18. What is the maximum usable NTP stratum?
> Stratum 15; stratum 16 is unsynchronized.

> [!question]- 19. What three NTP modes can Cisco devices use in this lesson?
> Client, server, and symmetric active modes.

> [!question]- 20. Which command configures an NTP client?
> `ntp server <ip-address> [prefer]`.

> [!question]- 21. Which command configures a symmetric active peer?
> `ntp peer <ip-address>`.

> [!question]- 22. Which command makes a router serve time from its local clock?
> `ntp master [stratum]`.

> [!question]- 23. What is the default device stratum of `ntp master`?
> Stratum 8.

> [!question]- 24. Which address represents the local NTP reference in show output?
> `127.127.1.1`, usually labeled `.LOCL.`.

> [!question]- 25. Which command chooses a stable source interface for NTP packets?
> `ntp source <interface>`.

> [!question]- 26. Which command periodically copies NTP time to the hardware calendar?
> `ntp update-calendar`.

> [!question]- 27. Which command lists NTP peers and association measurements?
> `show ntp associations`.

> [!question]- 28. Which command confirms whether the local clock is synchronized?
> `show ntp status`.

> [!question]- 29. What does `*` mean in `show ntp associations`?
> System peer - the source currently used for synchronization.

> [!question]- 30. What does `+` mean in `show ntp associations`?
> Candidate.

> [!question]- 31. What does `~` mean in `show ntp associations`?
> The association was configured.

> [!question]- 32. What does reach `377` mean?
> The last eight NTP polls succeeded; the value is octal.

> [!question]- 33. What three pieces are required for the authenticated client association shown in the slides?
> Create the authentication key, trust the key number, and bind that key to the `ntp server` association.

> [!question]- 34. Is `ntp authenticate` required in the IOS workflow demonstrated by Jeremy's slides?
> No.

> [!question]- 35. If `.LOCL.` appears at stratum 8, which master stratum is the router using?
> Stratum 9, configured with `ntp master 9`.

## Quick reference

```cisco
! ---------------- Manual time ----------------
show clock
show clock detail
clock set 14:30:00 27 Dec 2020

show calendar
calendar set 14:35:00 27 Dec 2020
clock read-calendar
clock update-calendar

clock timezone EST -5
clock summer-time EDT recurring 2 Sunday March 02:00 1 Sunday November 02:00

! ---------------- NTP client -----------------
ntp server 10.1.1.1 prefer
ntp server 10.2.2.2
ntp source loopback0
ntp update-calendar

! ---------------- NTP server -----------------
ntp master 8

! ---------------- NTP peer -------------------
ntp peer 10.0.23.2

! ---------------- Authentication ------------
ntp authentication-key 1 md5 NTP_SHARED_KEY
ntp trusted-key 1
ntp server 10.1.1.1 key 1
ntp peer 10.0.23.2 key 1

! ---------------- Verification --------------
show clock detail
show calendar
show ntp associations
show ntp status
```

```text
Stratum 0  = reference clock
Stratum 1  = directly connected primary NTP server
Stratum 2+ = downstream/secondary server or client
Stratum 15 = maximum usable
Stratum 16 = unsynchronized

UDP port   = 123
*          = current system peer
~          = configured association
+          = candidate
reach 377  = last eight polls succeeded
```

## Related notes

- [CDP & LLDP](<../CDP & LLDP/CDP & LLDP.md>)
- [OSPF Part 2 - Cost, Neighbors, and Adjacencies](<../OSPF/OSPF Part 2 - Cost, Neighbors, and Adjacencies.md>)
- IPv4 Addressing
- DNS
- Syslog
