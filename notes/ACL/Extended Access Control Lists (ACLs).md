---
title: Extended Access Control Lists (ACLs)
aliases:
  - Extended ACLs
  - Extended IPv4 ACLs
tags:
  - ccna
  - acl
  - security
  - ipv4
  - tcp
  - udp
source: Day 35 Slides - Extended ACLs
date: 2026-08-17
---

# Extended Access Control Lists (ACLs)

## Overview

An **extended IPv4 ACL** is an ordered packet-filtering policy that can match multiple fields at once. Unlike a standard ACL, an extended ACL can examine the packet's:

- IP protocol
- Source IPv4 address
- Destination IPv4 address
- TCP or UDP source port
- TCP or UDP destination port

This precision lets an administrator block a specific service between two networks while permitting other traffic between the same devices.

> [!abstract] CCNA core idea
> Extended ACLs are processed top to bottom, the first matching ACE wins, all specified fields must match, and unmatched traffic reaches an implicit deny. Place an extended ACL close to the source when practical.

> [!tip] Prerequisite
> Review [Standard Access Control Lists (ACLs)](<Standard Access Control Lists (ACLs).md>) for ACE ordering, wildcard masks, interface direction, implicit deny, and the one-ACL-per-protocol/interface/direction rule.

## Standard vs. extended ACLs

| Feature | Standard IPv4 ACL | Extended IPv4 ACL |
|---|---|---|
| Matches source address | Yes | Yes |
| Matches destination address | No | Yes |
| Matches IP protocol | No | Yes |
| Matches TCP/UDP ports | No | Yes |
| Original number range | `1-99` | `100-199` |
| Expanded number range | `1300-1999` | `2000-2699` |
| General placement | Close to the destination | Close to the source |
| Precision | Broad | High |

### Why extended ACLs go near the source

Because an extended ACE can identify the exact source, destination, protocol, and service, it can safely discard unwanted traffic near where that traffic originates. This prevents denied packets from consuming bandwidth across the rest of the network.

> [!note]
> “Close to the source” is a design guideline, not an unbreakable rule. The chosen location and direction must enforce the requirement without disrupting legitimate traffic or router control-plane traffic.

## Processing logic

Extended ACLs use the same core logic as standard ACLs:

1. ACEs are examined from the lowest sequence number to the highest.
2. A packet must match **every field specified in one ACE**.
3. When an ACE matches, its `permit` or `deny` action is taken immediately.
4. Entries below the first match are ignored.
5. If no configured ACE matches, the implicit deny drops the packet.

```text
protocol AND source address AND source port
         AND destination address AND destination port
                         |
                  all fields match?
                    /         \
                  yes          no
                   |            |
          take ACE action    check next ACE
```

> [!important] Logical AND
> If an ACE specifies TCP, source `192.168.1.0/24`, destination `10.0.1.100`, and destination port 443, a packet must match **all four** conditions. Matching three out of four is not enough.

> [!warning] First match, not best match
> ACL processing is not routing-table longest-prefix matching. A broad early ACE can shadow a more specific ACE below it.

## Implicit deny

Every extended IPv4 ACL ends with an invisible entry equivalent to:

```cisco
deny ip any any
```

Therefore, an ACL containing only one deny statement also denies every other IPv4 packet that reaches the end of the list.

To deny selected traffic and allow everything else:

```cisco
ip access-list extended BLOCK_HTTPS
 10 deny tcp 192.168.1.0 0.0.0.255 host 10.0.1.100 eq 443
 20 permit ip any any
```

> [!warning]
> `permit tcp any any` permits only TCP. Use `permit ip any any` when the policy intends to allow all remaining IPv4 protocols, including UDP, ICMP, OSPF, and EIGRP.

## Numbered and named extended ACLs

Extended ACLs may be identified by a number or a name.

### Number ranges

- Original extended range: `100-199`
- Expanded extended range: `2000-2699`

### Traditional numbered syntax

```cisco
Router(config)# access-list <100-199 | 2000-2699> {permit | deny} <protocol> <source> <destination>
```

Example:

```cisco
R1(config)# access-list 100 deny tcp 192.168.1.0 0.0.0.255 host 10.0.1.100 eq 443
R1(config)# access-list 100 permit ip any any
```

### Named ACL configuration mode

```cisco
Router(config)# ip access-list extended <acl-name>
Router(config-ext-nacl)# [sequence] {permit | deny} <protocol> <source> <destination>
```

Example:

```cisco
R1(config)# ip access-list extended BLOCK_HTTPS
R1(config-ext-nacl)# 10 deny tcp 192.168.1.0 0.0.0.255 host 10.0.1.100 eq 443
R1(config-ext-nacl)# 20 permit ip any any
```

### Configure a numbered ACL in ACL submode

Modern IOS can configure numbered ACLs with the same subcommand workflow as named ACLs:

```cisco
R1(config)# ip access-list extended 100
R1(config-ext-nacl)# 10 deny tcp 192.168.1.0 0.0.0.255 host 10.0.1.100 eq 443
R1(config-ext-nacl)# 20 permit ip any any
```

The running configuration may display the numbered ACL in traditional `access-list 100 ...` form even when it was entered in ACL submode.

> [!tip] Preferred editing workflow
> Enter named ACL configuration mode - even for a numbered ACL - to gain sequence numbers, individual ACE deletion, and easy insertion.

## Editing ACLs

### Delete an individual ACE

Display the ACL to find the sequence number:

```cisco
R1# show ip access-lists BLOCK_HTTPS
Extended IP access list BLOCK_HTTPS
    10 deny tcp 192.168.1.0 0.0.0.255 host 10.0.1.100 eq 443
    20 permit ip any any
```

Then remove only that sequence:

```cisco
R1(config)# ip access-list extended BLOCK_HTTPS
R1(config-ext-nacl)# no 10
```

### Insert a new ACE

Specify a sequence number between existing entries:

```cisco
R1(config)# ip access-list extended BLOCK_HTTPS
R1(config-ext-nacl)# 15 deny tcp 192.168.2.0 0.0.0.255 host 10.0.1.100 eq 443
```

The entry is inserted between sequence 10 and sequence 20.

### Resequence an ACL

If there are no useful gaps, renumber the entire ACL:

```cisco
Router(config)# ip access-list resequence <acl-id> <starting-sequence> <increment>
```

Example:

```cisco
R1(config)# ip access-list resequence 199 5 10
```

The sequence numbers become `5, 15, 25, 35, 45...`.

> [!danger] Classic numbered ACL deletion
> In global configuration mode, a command beginning with `no access-list 1 ...` deletes the **entire numbered ACL 1**, even if the rest of an ACE is typed. It does not remove only that matching line. Enter ACL submode and use `no <sequence-number>` for surgical edits.

## Extended ACL syntax

The complete CCNA-level ordering is:

```cisco
{permit | deny} <protocol> <source-ip> [source-wildcard] [source-port-condition] <destination-ip> [destination-wildcard] [destination-port-condition]
```

For TCP or UDP:

```cisco
{permit | deny} {tcp | udp} <source> [operator source-port] <destination> [operator destination-port]
```

> [!abstract] Memorize the order
> **Action -> protocol -> source address -> source port -> destination address -> destination port**

### Address forms

| Intent | Syntax |
|---|---|
| One host | `host 192.168.1.10` |
| One host, explicit wildcard | `192.168.1.10 0.0.0.0` |
| One `/24` network | `192.168.1.0 0.0.0.255` |
| Any address | `any` |

Unlike the abbreviated standard ACL syntax, a single address in an extended ACE must use `host` or include the `0.0.0.0` wildcard mask.

### Wildcard-mask reminder

- Wildcard `0`: corresponding address bit must match.
- Wildcard `1`: corresponding address bit is ignored.
- Wildcard mask = `255.255.255.255 - subnet mask`.

| Prefix | Wildcard mask |
|---:|---|
| `/32` | `0.0.0.0` |
| `/30` | `0.0.0.3` |
| `/26` | `0.0.0.63` |
| `/24` | `0.0.0.255` |
| `/16` | `0.0.255.255` |
| `/8` | `0.255.255.255` |

## Matching the IP protocol

The protocol field identifies the IPv4 payload type. IOS accepts protocol keywords or protocol numbers.

| Protocol | Keyword | IP protocol number |
|---|---|---:|
| ICMP | `icmp` | 1 |
| TCP | `tcp` | 6 |
| UDP | `udp` | 17 |
| EIGRP | `eigrp` | 88 |
| OSPF | `ospf` | 89 |
| Any IPv4 protocol | `ip` | All |

Equivalent OSPF matches:

```cisco
deny ospf any any
deny 89 any any
```

> [!warning] `ip` is not TCP
> In ACL syntax, `ip` means any IPv4 protocol. TCP, UDP, and ICMP are separate protocols carried inside IPv4.

### Protocol-only examples

Permit all IPv4 traffic:

```cisco
permit ip any any
```

Deny all UDP traffic from `10.0.0.0/16` to one server:

```cisco
deny udp 10.0.0.0 0.0.255.255 host 192.168.1.1
```

Stop one host from pinging `192.168.0.0/24`:

```cisco
deny icmp host 172.16.1.1 192.168.0.0 0.0.0.255
```

ICMP, OSPF, and EIGRP do not use TCP or UDP port numbers.

## Matching TCP and UDP ports

Port conditions are optional and apply only when the protocol is TCP or UDP.

### Operators

| Operator | Meaning | Example |
|---|---|---|
| `eq` | Equal to | `eq 443` matches port 443 |
| `gt` | Greater than | `gt 1023` matches 1024 and higher |
| `lt` | Less than | `lt 1024` matches 0 through 1023 |
| `neq` | Not equal to | `neq 23` matches every port except 23 |
| `range` | Inclusive range | `range 20000 30000` includes both endpoints |

### Common CCNA ports

| Service | Protocol | Port(s) |
|---|---|---:|
| FTP data | TCP | 20 |
| FTP control | TCP | 21 |
| SSH | TCP | 22 |
| Telnet | TCP | 23 |
| SMTP | TCP | 25 |
| DNS | TCP/UDP | 53 |
| DHCP server | UDP | 67 |
| DHCP client | UDP | 68 |
| TFTP | UDP | 69 |
| HTTP | TCP | 80 |
| POP3 | TCP | 110 |
| SNMP agent | UDP | 161 |
| SNMP manager/trap receiver | UDP | 162 |
| HTTPS | TCP | 443 |
| Syslog | UDP | 514 |

> [!tip] Source vs. destination port
> A client usually chooses a temporary **source** port and sends to the server's well-known **destination** port. To filter access to HTTPS, place `eq 443` after the destination address.

### Destination-port example

Deny HTTP traffic from any source to `1.1.1.1`:

```cisco
deny tcp any host 1.1.1.1 eq 80
```

### Source-port and destination-port example

Permit hosts in `172.16.1.0/24` using TCP source ports above 9999 to reach every TCP port on `4.4.4.4` except Telnet:

```cisco
permit tcp 172.16.1.0 0.0.0.255 gt 9999 host 4.4.4.4 neq 23
```

The first port condition follows the source address; the second follows the destination address.

### Port-range example

Deny UDP packets with a source port from 20000 through 30000 when destined to `3.3.3.3`:

```cisco
deny udp any range 20000 30000 host 3.3.3.3
```

### HTTPS example

Permit `10.0.0.0/16` to access HTTPS on `2.2.2.2`:

```cisco
permit tcp 10.0.0.0 0.0.255.255 host 2.2.2.2 eq 443
```

> [!note] Additional match options
> IOS can also match TCP flags such as `ack`, `fin`, and `syn`, as well as TTL or DSCP values. These are not central to the CCNA ACL objectives. The TCP `established` keyword checks ACK/RST bits; it is not a full stateful firewall.

## Applying an extended ACL

Apply a numbered or named ACL under the interface:

```cisco
Router(config)# interface <interface-id>
Router(config-if)# ip access-group <acl-id> {in | out}
```

Example:

```cisco
R1(config)# interface g0/1
R1(config-if)# ip access-group BLOCK_HTTPS in
```

### Direction

- **Inbound:** Packet enters the router through the interface; ACL is checked before the routing decision.
- **Outbound:** Routing has selected the exit interface; ACL is checked before the packet leaves.

> [!example] Direction test
> A client packet entering R1 on G0/1 is inbound on G0/1. If R1 routes it through G0/0, the same packet is outbound on G0/0.

### Application limit

The CCNA rule is **one ACL per protocol, per interface, per direction**. An interface can have one IPv4 ACL inbound and another IPv4 ACL outbound. Applying another IPv4 ACL to the same interface in the same direction replaces the earlier application.

## Placement best practices

Use this workflow:

1. Translate the requirement into source, destination, protocol, and port fields.
2. Trace the packet's path through the topology.
3. Find the first router interface near the source where the policy can be applied safely.
4. Determine direction from that interface's perspective.
5. Order specific exceptions before broader rules.
6. Add an explicit permit for all remaining traffic that should pass.
7. Verify the attachment and test both permitted and denied cases.

> [!warning] Protect routing and management traffic
> A broad ACL can unintentionally block OSPF, EIGRP, SSH, DHCP, DNS, or ICMP. Consider every protocol that crosses the selected interface, not only the application mentioned in the requirement.

## Worked topology examples

The slide topology uses two client LANs behind R1 and two server LANs behind R2:

- Clients: `192.168.1.0/24` on R1 G0/1
- Clients: `192.168.2.0/24` on R1 G0/2
- SRV1: `10.0.1.100` in `10.0.1.0/24`
- SRV2: `10.0.2.100` in `10.0.2.0/24`

### Example 1: Block HTTPS to one server

Requirement: Hosts in `192.168.1.0/24` cannot use HTTPS to reach SRV1, but other traffic is allowed.

```cisco
R1(config)# ip access-list extended HTTP_SRV1
R1(config-ext-nacl)# 10 deny tcp 192.168.1.0 0.0.0.255 host 10.0.1.100 eq 443
R1(config-ext-nacl)# 20 permit ip any any
R1(config)# interface g0/1
R1(config-if)# ip access-group HTTP_SRV1 in
```

This filters the unwanted traffic as it enters R1 from the source LAN.

### Example 2: Block one client subnet from one server subnet

Requirement: `192.168.2.0/24` cannot access `10.0.2.0/24`, but other traffic is allowed.

```cisco
R1(config)# ip access-list extended BLOCK_SERVER_LAN_2
R1(config-ext-nacl)# 10 deny ip 192.168.2.0 0.0.0.255 10.0.2.0 0.0.0.255
R1(config-ext-nacl)# 20 permit ip any any
R1(config)# interface g0/2
R1(config-if)# ip access-group BLOCK_SERVER_LAN_2 in
```

Using protocol `ip` blocks all IPv4 protocols between those two subnets, not only TCP or UDP.

### Example 3: Block selected pings

Requirements:

- Neither client subnet may ping `10.0.1.0/24`.
- Neither client subnet may ping `10.0.2.0/24`.
- Other IPv4 traffic remains permitted.

A complete policy would include all four source/destination combinations:

```cisco
R1(config)# ip access-list extended BLOCK_CLIENT_ICMP
R1(config-ext-nacl)# 10 deny icmp 192.168.1.0 0.0.0.255 10.0.1.0 0.0.0.255
R1(config-ext-nacl)# 20 deny icmp 192.168.1.0 0.0.0.255 10.0.2.0 0.0.0.255
R1(config-ext-nacl)# 30 deny icmp 192.168.2.0 0.0.0.255 10.0.1.0 0.0.0.255
R1(config-ext-nacl)# 40 deny icmp 192.168.2.0 0.0.0.255 10.0.2.0 0.0.0.255
R1(config-ext-nacl)# 50 permit ip any any
R1(config)# interface g0/0
R1(config-if)# ip access-group BLOCK_CLIENT_ICMP out
```

This outbound placement on R1 G0/0 aggregates both client sources. Two separate inbound ACLs closer to each source would also be possible, but each interface would require a policy appropriate to its own source LAN.

### Example 4: Permit only PC1 to use TFTP on SRV1

PC1 is `192.168.1.1`, SRV1 is `10.0.1.100`, and TFTP uses UDP destination port 69:

```cisco
R1(config)# ip access-list extended 103
R1(config-ext-nacl)# 10 permit udp host 192.168.1.1 host 10.0.1.100 eq tftp
R1(config-ext-nacl)# 20 deny udp any host 10.0.1.100 eq tftp
R1(config-ext-nacl)# 30 permit ip any any
R1(config)# interface g0/0
R1(config-if)# ip access-group 103 out
```

- Sequence 10 permits PC1's TFTP requests.
- Sequence 20 blocks TFTP from every other source.
- Sequence 30 allows other IPv4 traffic.

## Verification commands

```cisco
Router# show access-lists
Router# show ip access-lists
Router# show ip access-lists BLOCK_HTTPS
Router# show ip interface g0/1
Router# show running-config | include access-list
Router# show running-config | section ip access-list
Router# show running-config interface g0/1
```

| Command | What to verify |
|---|---|
| `show ip access-lists` | ACE order, sequence numbers, protocols, addresses, ports, and counters |
| `show ip interface` | Inbound/outbound ACL attached to each interface |
| `show running-config \| section ip access-list` | Named ACL configuration and remarks |
| `show running-config interface` | Exact ACL identifier and direction on an interface |

For a controlled test, optionally clear counters first:

```cisco
Router# clear access-list counters BLOCK_HTTPS
```

Then generate both permitted and denied traffic and confirm that the expected ACE counters increase.

### Troubleshooting checklist

1. Is the correct ACL attached to the expected interface?
2. Is the direction correct for the tested packet?
3. Is the transport protocol correct (`tcp` vs. `udp`)?
4. Are source and destination addresses in the correct positions?
5. Are wildcard masks correct?
6. Is the port condition after the correct address?
7. Does a broader earlier ACE shadow the intended ACE?
8. Is an explicit permit present for other legitimate traffic?
9. Does the packet follow the path assumed by the design?
10. Which match counter changes during the test?

## Common mistakes

- Using UDP for HTTP or HTTPS instead of TCP
- Using TCP for TFTP instead of UDP
- Placing a server's well-known port after the source address instead of the destination address
- Reversing the source and destination networks
- Omitting `host` or `0.0.0.0` for a single address in an extended ACE
- Using a subnet mask instead of a wildcard mask
- Writing `permit tcp any any` when all remaining IPv4 traffic should be permitted
- Forgetting the implicit `deny ip any any`
- Placing `permit ip any any` before the deny statements
- Applying the ACL outbound on the source-facing interface when the tested packet enters that interface inbound
- Placing an extended ACL unnecessarily far from the source
- Blocking OSPF protocol 89 or EIGRP protocol 88 unintentionally
- Confusing an IP protocol number with a TCP/UDP port number
- Forgetting that ACL fields use logical AND
- Expecting multiple ACLs in the same interface direction to merge
- Deleting an entire numbered ACL while trying to remove one global-config ACE
- Assuming a basic ACL is stateful or automatically permits return traffic

## CCNA exam tips

> [!example] High-value facts
> - Extended numbered ranges: **100-199 and 2000-2699**
> - Entry order: **action, protocol, source, source port, destination, destination port**
> - Protocol numbers: **ICMP 1, TCP 6, UDP 17, EIGRP 88, OSPF 89**
> - TFTP: **UDP 69**
> - HTTP/HTTPS: **TCP 80/443**
> - DNS: **TCP and UDP 53**
> - First matching ACE wins
> - All specified fields in an ACE must match
> - No match means implicit `deny ip any any`
> - Extended ACLs are generally placed close to the source
> - Use `ip access-list resequence <acl-id> <start> <increment>`

### Slide quiz review

1. **ACL 103** is correct for allowing only PC1 to use TFTP on SRV1: it uses UDP, places `eq tftp` after the destination, explicitly denies other TFTP sources, and permits other IP traffic.
2. `no access-list 1 deny 10.0.2.0 0.0.0.255` in global configuration mode deletes **the entire ACL 1**.
3. Changing ACL 199 from sequence numbers `1,2,3,4,5` to `5,15,25,35,45` uses `ip access-list resequence 199 5 10`.
4. To prevent R1 from forwarding OSPF packets **out** G0/2, deny protocol **89** with ACL 112 applied **outbound**.
5. To block HTTP and HTTPS from `192.168.1.0/24` to `10.0.2.0/24`, change the protocol from UDP to **TCP** and apply the ACL **inbound on G0/1** near the source.

> [!question] Exam trap: protocol vs. port
> OSPF's `89` is an **IP protocol number**. HTTP's `80` is a **TCP port number**. They appear in different parts of an extended ACE.

> [!question] Exam trap: TFTP
> TFTP uses **UDP destination port 69**. An ACE using TCP or placing port 69 after the source address will not match normal client requests as intended.

## Flashcards

> [!question]- 1. What can an extended IPv4 ACL match that a standard ACL cannot?
> Destination IPv4 address, IP protocol, and TCP/UDP source or destination ports.

> [!question]- 2. What are the extended numbered ACL ranges?
> `100-199` and `2000-2699`.

> [!question]- 3. In what order are the main extended ACL fields written?
> Action, protocol, source address, source port, destination address, destination port.

> [!question]- 4. How are multiple match fields within one ACE combined?
> With logical AND; every specified field must match.

> [!question]- 5. What happens after the first matching ACE?
> Its action is taken immediately and lower entries are ignored.

> [!question]- 6. What is the implicit final entry in an extended IPv4 ACL?
> `deny ip any any`.

> [!question]- 7. Where should an extended ACL generally be placed?
> As close to the source as practical.

> [!question]- 8. What does the protocol keyword `ip` match?
> Every IPv4 protocol, including TCP, UDP, ICMP, OSPF, and EIGRP.

> [!question]- 9. What are the IP protocol numbers for ICMP, TCP, and UDP?
> ICMP 1, TCP 6, and UDP 17.

> [!question]- 10. What are the IP protocol numbers for EIGRP and OSPF?
> EIGRP 88 and OSPF 89.

> [!question]- 11. Which protocol and port does HTTP use?
> TCP port 80.

> [!question]- 12. Which protocol and port does HTTPS use?
> TCP port 443.

> [!question]- 13. Which protocol and port does TFTP use?
> UDP port 69.

> [!question]- 14. Where is a server's well-known port usually placed in an ACE?
> After the destination address as a destination-port condition.

> [!question]- 15. What do `eq`, `gt`, `lt`, `neq`, and `range` mean?
> Equal, greater than, less than, not equal, and inclusive range.

> [!question]- 16. What does `range 20000 30000` match?
> Ports 20000 through 30000, including both endpoints.

> [!question]- 17. How do you match one host in an extended ACL?
> Use `host <address>` or `<address> 0.0.0.0`.

> [!question]- 18. How do you enter numbered extended ACL 100 in ACL submode?
> `ip access-list extended 100`.

> [!question]- 19. How do you remove sequence 20 from an ACL?
> Enter the ACL's configuration mode and issue `no 20`.

> [!question]- 20. What does `ip access-list resequence 199 5 10` do?
> Renumbers ACL 199 starting at 5 and adds 10 for each following ACE: 5, 15, 25, and so on.

> [!question]- 21. Why is `no access-list 1 deny ...` dangerous in global configuration mode?
> It deletes the entire numbered ACL 1 rather than only that ACE.

> [!question]- 22. What interface command applies ACL 100 inbound?
> `ip access-group 100 in`.

> [!question]- 23. When is an inbound ACL evaluated?
> As the packet enters the interface, before the routing decision.

> [!question]- 24. Are basic router ACLs stateful?
> No. Packets are evaluated independently; return traffic must also be permitted where applicable.

## Quick reference

```cisco
! Named extended ACL
ip access-list extended WEB_POLICY
 10 deny tcp 192.168.1.0 0.0.0.255 host 10.0.1.100 eq 80
 20 deny tcp 192.168.1.0 0.0.0.255 host 10.0.1.100 eq 443
 30 permit ip any any

! Apply near the source
interface g0/1
 ip access-group WEB_POLICY in

! Edit and resequence
ip access-list extended WEB_POLICY
 no 20
 20 deny tcp 192.168.1.0 0.0.0.255 host 10.0.1.100 eq 443
exit
ip access-list resequence WEB_POLICY 10 10

! Verify
show ip access-lists WEB_POLICY
show ip interface g0/1
show running-config interface g0/1
```

## Related notes

- [Standard Access Control Lists (ACLs)](<Standard Access Control Lists (ACLs).md>)
- IPv4 Subnetting
- [OSPF Part 1 - Fundamentals, Areas, and Basic Configuration](<../OSPF/OSPF Part 1 - Fundamentals, Areas, and Basic Configuration.md>)
