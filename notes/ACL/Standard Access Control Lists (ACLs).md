---
title: Standard Access Control Lists (ACLs)
aliases:
  - Standard ACLs
  - IPv4 ACLs
  - Access Control Lists
tags:
  - ccna
  - acl
  - security
  - ipv4
source: Day 34 Slides - Standard ACLs
date: 2026-08-17
---

# Standard Access Control Lists (ACLs)

## Overview

An **access control list (ACL)** is an ordered set of rules that tells a router or multilayer switch which packets to **permit** or **deny**. An individual rule is an **access control entry (ACE)**.

From a security perspective, ACLs act as packet filters. Depending on the ACL type, they can examine source and destination IP addresses, IP protocols, and Layer 4 port numbers. This note focuses on **standard IPv4 ACLs**, which match only the packet's **source IPv4 address**.

> [!abstract] CCNA core idea
> Build the ACL globally, order its ACEs from specific to general, include any required permits, and then apply it to the correct interface in the correct direction.

> [!tip] Related topic
> Standard ACLs make decisions using only the source address. See [Extended ACLs](<Extended Access Control Lists (ACLs).md>) when filtering must consider a destination, protocol, or TCP/UDP port.

## ACL concepts

- **ACL:** The complete ordered list of filtering rules.
- **ACE:** One `permit`, `deny`, or `remark` entry inside an ACL.
- **Permit:** Allow a matching packet to continue through normal router processing.
- **Deny:** Drop a matching packet.
- **Source:** The address of the device that created the packet.
- **Destination:** The address the packet is trying to reach.
- **Wildcard mask:** Identifies which source-address bits must match and which bits can vary.
- **Inbound ACL:** Checks packets entering an interface.
- **Outbound ACL:** Checks packets leaving an interface.

ACLs can be used for more than basic security filtering, including identifying traffic for features such as Network Address Translation, policy-based routing, and quality of service. The action associated with a match depends on the feature using the ACL. When an ACL is applied with `ip access-group`, it filters packets.

## ACL processing logic

The router processes an ACL as follows:

1. The packet reaches an interface where an ACL is applied in the packet's direction.
2. The router compares the packet to the first ACE.
3. If it matches, the router immediately performs that ACE's action and stops checking the ACL.
4. If it does not match, the router checks the next ACE.
5. If no configured ACE matches, the packet reaches the implicit deny and is dropped.

```text
Packet enters ACL
      |
      v
Check first ACE -- match --> permit or deny; stop
      |
   no match
      v
Check next ACE  -- match --> permit or deny; stop
      |
   no match
      v
Continue downward
      |
   no match
      v
Implicit deny --> drop
```

> [!important] First match wins
> ACLs do **not** use longest-prefix match or choose the most specific matching ACE. The first matching entry wins, so rule order is part of the policy.

### Ordering example

This order blocks the entire `192.168.0.0/16`, including `192.168.1.0/24`. The later permit is never reached for that subnet:

```cisco
access-list 1 deny 192.168.0.0 0.0.255.255
access-list 1 permit 192.168.1.0 0.0.0.255
```

To permit `192.168.1.0/24` as an exception, put the specific permit first:

```cisco
access-list 1 permit 192.168.1.0 0.0.0.255
access-list 1 deny 192.168.0.0 0.0.255.255
access-list 1 permit any
```

## Implicit deny

Every IPv4 ACL ends with an invisible rule equivalent to:

```cisco
deny any
```

This entry cannot be removed. Any packet that fails to match a configured ACE is dropped.

> [!warning] The classic outage
> An ACL containing only deny statements blocks everything: the listed sources match an explicit deny, and all other sources reach the implicit deny. Add an explicit permit for traffic that must continue.

For example:

```cisco
access-list 10 deny 192.168.50.0 0.0.0.255
access-list 10 permit any
```

The first ACE blocks `192.168.50.0/24`; the second allows every other source.

## Standard vs. extended ACLs

| Feature | Standard IPv4 ACL | Extended IPv4 ACL |
|---|---|---|
| Matches source IP | Yes | Yes |
| Matches destination IP | No | Yes |
| Matches protocol | No | Yes, such as IP, TCP, UDP, ICMP, OSPF |
| Matches source/destination port | No | Yes, for TCP/UDP |
| Number ranges | `1-99`, `1300-1999` | `100-199`, `2000-2699` |
| General placement | Close to the destination | Close to the source |
| Best use | Broadly control which sources reach a destination area | Precisely control traffic by source, destination, protocol, and service |

### Why placement differs

A standard ACL cannot distinguish among destinations. If it is placed near the source, it may block that source from every destination beyond the interface, not only the intended destination. Placing it near the destination limits unwanted side effects.

An extended ACL can identify the exact destination and service, so placing it near the source stops unwanted traffic before it consumes network bandwidth.

> [!note]
> These are placement guidelines, not absolute laws. The correct placement is the location and direction that enforce the requirement without blocking valid traffic.

## Numbered vs. named ACLs

Numbered and named ACLs can perform the same filtering. Their main difference is how the ACL is identified and maintained.

| Feature | Numbered ACL | Named ACL |
|---|---|---|
| Identifier | Number, such as `10` | Descriptive name, such as `BLOCK_GUESTS` |
| Indicates ACL type | Number range identifies type | `standard` or `extended` keyword identifies type |
| Readability | Lower | Higher |
| Editing | Awkward with classic global syntax; modern IOS supports named ACL mode for a numbered list | Sequence-based editing is straightforward |
| Interface application | `ip access-group 10 in` | `ip access-group BLOCK_GUESTS in` |

> [!tip] Operational preference
> Named ACLs are easier to recognize in configurations and troubleshooting output. Sequence numbers leave gaps so new ACEs can be inserted later.

### Standard numbered ranges

- Original range: `1-99`
- Expanded range: `1300-1999`

## Wildcard masks

A wildcard mask is the inverse of a subnet mask:

- A wildcard bit of **0** means the corresponding address bit **must match**.
- A wildcard bit of **1** means the corresponding address bit is **ignored**.

> [!abstract] Memory aid
> **0 = check; 1 = ignore.**

### Calculate a wildcard mask

Subtract each subnet-mask octet from 255:

```text
Subnet mask:   255.255.255.0
Subtract from: 255.255.255.255
Wildcard mask:   0.  0.  0.255
```

### Common wildcard masks

| Prefix | Subnet mask | Wildcard mask | Example source expression |
|---:|---|---|---|
| `/32` | `255.255.255.255` | `0.0.0.0` | `192.168.1.10 0.0.0.0` |
| `/30` | `255.255.255.252` | `0.0.0.3` | `10.0.0.0 0.0.0.3` |
| `/26` | `255.255.255.192` | `0.0.0.63` | `192.168.1.64 0.0.0.63` |
| `/24` | `255.255.255.0` | `0.0.0.255` | `192.168.1.0 0.0.0.255` |
| `/16` | `255.255.0.0` | `0.0.255.255` | `172.16.0.0 0.0.255.255` |
| `/8` | `255.0.0.0` | `0.255.255.255` | `10.0.0.0 0.255.255.255` |

### `host` and `any` shortcuts

These pairs are equivalent:

```cisco
access-list 1 deny 192.168.1.10 0.0.0.0
access-list 1 deny host 192.168.1.10
```

```cisco
access-list 1 permit 0.0.0.0 255.255.255.255
access-list 1 permit any
```

When a single IP address is entered without a wildcard mask in a standard ACL, IOS treats it as a host match.

> [!warning]
> Do not enter a subnet mask where IOS expects a wildcard mask. For `192.168.1.0/24`, use `0.0.0.255`, not `255.255.255.0`.

## Configuration syntax

### Standard numbered ACL

```cisco
Router(config)# access-list <1-99 | 1300-1999> {permit | deny} <source> <wildcard-mask>
Router(config)# access-list <number> remark <description>
```

Examples:

```cisco
R1(config)# access-list 10 remark BLOCK ACCOUNTING SUBNET
R1(config)# access-list 10 deny 192.168.50.0 0.0.0.255
R1(config)# access-list 10 permit any
```

```cisco
R1(config)# access-list 11 deny host 192.168.1.10
R1(config)# access-list 11 permit any
```

### Standard named ACL

```cisco
Router(config)# ip access-list standard <acl-name>
Router(config-std-nacl)# [sequence-number] {permit | deny} <source> <wildcard-mask>
Router(config-std-nacl)# [sequence-number] remark <description>
```

Example:

```cisco
R1(config)# ip access-list standard BLOCK_BOB
R1(config-std-nacl)# 5 remark BLOCK BOB FROM ACCOUNTING
R1(config-std-nacl)# 10 deny host 192.168.50.10
R1(config-std-nacl)# 20 permit any
```

### Sequence numbers and editing

IOS normally assigns sequence numbers in increments of 10. Gaps allow insertion without rebuilding the ACL:

```cisco
R1(config)# ip access-list standard BLOCK_BOB
R1(config-std-nacl)# 15 deny host 192.168.50.11
R1(config-std-nacl)# no 10
```

The new ACE is inserted between sequence 10 and 20, and `no 10` removes only sequence 10.

To edit a numbered ACL using sequence-aware ACL mode on modern IOS:

```cisco
R1(config)# ip access-list standard 10
R1(config-std-nacl)# 15 deny host 192.168.50.11
```

> [!danger] Deleting numbered ACLs
> In classic global configuration mode, `no access-list 10` deletes the **entire ACL 10**, not one ACE. Verify the command context before pressing Enter.

## Applying an ACL to an interface

Creating an ACL does not filter traffic by itself. Apply it under an interface:

```cisco
Router(config)# interface <interface-id>
Router(config-if)# ip access-group <acl-number-or-name> {in | out}
```

Example:

```cisco
R1(config)# interface g0/2
R1(config-if)# ip access-group 10 out
```

To remove the application without deleting the ACL:

```cisco
R1(config-if)# no ip access-group 10 out
```

### Inbound vs. outbound

Direction is always described from the router interface's perspective.

| Direction | When the ACL is checked | Mental model |
|---|---|---|
| **Inbound** | After the frame enters the interface and before the router makes the routing decision | Traffic coming **into** the router through that interface |
| **Outbound** | After the routing decision selects the exit interface and before the frame leaves | Traffic going **out of** the router through that interface |

The same packet can be checked by an inbound ACL on its ingress interface and an outbound ACL on its egress interface.

> [!example] Direction test
> Ask: “At this interface, is the packet entering the router or leaving it?” Do not decide direction based on where the client or server appears in a diagram.

### How many ACLs can be applied?

The CCNA rule is **one ACL per protocol, per interface, per direction**.

For IPv4 on `G0/0`, one IPv4 ACL can be inbound and a different IPv4 ACL can be outbound. Applying another IPv4 ACL in the same direction replaces the previous application; the ACLs are not combined automatically.

## Placement best practices

### Standard ACL placement

Place a standard ACL **as close to the destination as practical** because it cannot distinguish among different destinations.

### Extended ACL placement

Place an extended ACL **as close to the source as practical** because it can precisely identify the unwanted destination and service.

### Placement checklist

1. Write the traffic requirement in plain language.
2. Identify the packet's source and intended destination.
3. Draw the path through the routers.
4. Mark candidate ingress and egress interfaces.
5. Choose the location that filters the intended traffic without affecting other destinations.
6. Determine `in` or `out` from the selected interface's perspective.
7. Confirm that a required `permit` prevents the implicit deny from blocking legitimate traffic.

## Worked examples

### Example 1: Permit one host, deny the rest of its subnet

Requirement:

- PC1 (`192.168.1.1`) may reach `192.168.2.0/24`.
- Other hosts in `192.168.1.0/24` may not reach that destination.
- Other source networks should remain permitted.

Because this is a standard ACL, place it near the destination - outbound on the interface leading to `192.168.2.0/24`:

```cisco
R1(config)# access-list 1 remark ONLY PC1 MAY REACH 192.168.2.0/24
R1(config)# access-list 1 permit host 192.168.1.1
R1(config)# access-list 1 deny 192.168.1.0 0.0.0.255
R1(config)# access-list 1 permit any
R1(config)# interface g0/2
R1(config-if)# ip access-group 1 out
```

Why order matters:

- PC1 matches the host permit and stops.
- Other `192.168.1.0/24` hosts miss the host ACE and match the subnet deny.
- All other sources match `permit any`.

### Example 2: Named ACL protecting one server LAN

Requirement: Block `192.168.1.0/24` from the `10.0.2.0/24` server LAN while permitting other sources.

```cisco
R2(config)# ip access-list standard TO_SERVER_LAN_2
R2(config-std-nacl)# 10 remark BLOCK 192.168.1.0/24
R2(config-std-nacl)# 20 deny 192.168.1.0 0.0.0.255
R2(config-std-nacl)# 30 permit any
R2(config)# interface g0/2
R2(config-if)# ip access-group TO_SERVER_LAN_2 out
```

The ACL is outbound on the server-facing interface, so it filters packets only after routing chooses the `10.0.2.0/24` LAN.

### Example 3: Two exceptions inside two source subnets

Requirement for access to `10.0.1.0/24`:

- Deny PC3 (`192.168.2.1`).
- Permit other hosts in `192.168.2.0/24`.
- Permit PC1 (`192.168.1.1`).
- Deny other hosts in `192.168.1.0/24`.
- Permit all other sources.

```cisco
R2(config)# ip access-list standard TO_SERVER_LAN_1
R2(config-std-nacl)# 10 deny host 192.168.2.1
R2(config-std-nacl)# 20 permit 192.168.2.0 0.0.0.255
R2(config-std-nacl)# 30 permit host 192.168.1.1
R2(config-std-nacl)# 40 deny 192.168.1.0 0.0.0.255
R2(config-std-nacl)# 50 permit any
R2(config)# interface g0/1
R2(config-if)# ip access-group TO_SERVER_LAN_1 out
```

Each host exception is listed before its broader subnet ACE.

> [!note] IOS display order
> Some IOS versions may display standard ACL `/32` host entries in a different internal order to improve processing efficiency. This applies to numbered and named standard ACLs and should not change the policy's effect. Packet Tracer may not show this behavior. Always verify the displayed ACL and test the intended traffic.

## Verification commands

```cisco
Router# show access-lists
Router# show ip access-lists
Router# show ip access-lists 10
Router# show ip interface g0/2
Router# show running-config | include access-list
Router# show running-config | section ip access-list
Router# show running-config interface g0/2
```

What each command confirms:

| Command | Verify |
|---|---|
| `show access-lists` | ACLs, ACE order, sequence numbers, and match counters |
| `show ip access-lists` | IPv4 ACL contents and counters |
| `show ip interface g0/2` | Which inbound and outbound ACLs are attached to the interface |
| `show running-config \| include access-list` | Classic numbered ACL lines |
| `show running-config \| section ip access-list` | Named ACL configuration sections |
| `show running-config interface g0/2` | Exact interface application and direction |

After verifying the configuration, generate controlled test traffic from both permitted and denied sources. Match counters should increase on the expected ACEs.

To clear counters before a test, if supported by the IOS version:

```cisco
Router# clear access-list counters 10
Router# clear access-list counters TO_SERVER_LAN_1
```

> [!tip] Troubleshooting sequence
> Check ACE order -> wildcard masks -> explicit permits -> interface -> direction -> packet path -> match counters.

## Common mistakes

- Forgetting that all ACLs end in an implicit `deny any`
- Creating the ACL but never applying it to an interface
- Applying the correct ACL to the wrong interface
- Reversing `in` and `out`
- Entering a subnet mask instead of a wildcard mask
- Putting a broad ACE before a required specific exception
- Expecting the most specific match to win instead of the first match
- Placing a standard ACL too close to the source and unintentionally blocking other destinations
- Applying several IPv4 ACLs to the same interface in the same direction and expecting IOS to merge them
- Using `no access-list <number>` when intending to remove only one ACE
- Forgetting that standard ACLs cannot match a destination, protocol, or port
- Testing only a permitted source and never confirming the deny behavior
- Assuming an ACL is stateful; basic router ACLs evaluate each packet independently
- Ignoring control-plane or management traffic that also crosses the filtered interface

## CCNA exam tips

> [!example] High-value facts
> - **Standard ACL match:** source IPv4 address only
> - **Standard numbered ranges:** `1-99` and `1300-1999`
> - **Extended numbered ranges:** `100-199` and `2000-2699`
> - **Processing:** top to bottom, first match wins
> - **No match:** implicit `deny any`, so the packet is dropped
> - **Wildcard bit:** `0` must match; `1` is ignored
> - **Standard placement:** close to the destination
> - **Extended placement:** close to the source
> - **Activation:** `ip access-group <acl> {in | out}`
> - **Limit:** one ACL per protocol, per interface, per direction

### Slide quiz review

1. To permit only PC1 (`192.168.1.1`) and PC4 (`192.168.2.2`), an ACL needs those two host permits. The implicit deny blocks every other source.
2. To allow only PC3 to reach SRV2, apply the standard ACL **outbound on R2 G0/2**, the interface closest to SRV2.
3. If ACLs 40, 30, 20, and then 10 are applied outbound to the same IPv4 interface, only the final application remains. ACL 10 therefore denies `10.0.0.0/24` and permits the rest.
4. An ACL applied **inbound on R1 G0/0** does not filter traffic that leaves R1 through G0/0 toward R2. In the slide topology, all four PCs can still ping SRV2.
5. A packet that matches no configured ACE is **dropped** by the implicit deny.

> [!question] Exam trap: direction
> If traffic travels from a LAN through R1 G0/1 and leaves R1 G0/0, it is **inbound on G0/1** and **outbound on G0/0**.

> [!question] Exam trap: specificity
> A later host ACE does not override an earlier matching subnet ACE. ACLs use first-match logic, not routing-table longest-prefix logic.

## Flashcards

> [!question]- 1. What is an ACE?
> An Access Control Entry: one permit, deny, or remark rule in an ACL.

> [!question]- 2. What field does a standard IPv4 ACL inspect?
> The packet's source IPv4 address only.

> [!question]- 3. In what order are ACL entries evaluated?
> From top to bottom until the first match.

> [!question]- 4. What happens after an ACE matches?
> The router performs that ACE's action and stops processing the ACL.

> [!question]- 5. What happens when no configured ACE matches?
> The packet reaches the implicit `deny any` and is dropped.

> [!question]- 6. Can the implicit deny be removed?
> No. Permit statements must be added for traffic that should pass.

> [!question]- 7. What do wildcard bits 0 and 1 mean?
> `0` means the bit must match; `1` means the bit is ignored.

> [!question]- 8. What wildcard mask matches a `/24`?
> `0.0.0.255`.

> [!question]- 9. What wildcard mask matches one host?
> `0.0.0.0`, or use the `host` keyword.

> [!question]- 10. What does the `any` keyword represent?
> `0.0.0.0 255.255.255.255`, meaning every IPv4 source.

> [!question]- 11. What are the standard numbered ACL ranges?
> `1-99` and `1300-1999`.

> [!question]- 12. Where should a standard ACL generally be placed?
> As close to the destination as practical.

> [!question]- 13. Where should an extended ACL generally be placed?
> As close to the source as practical.

> [!question]- 14. What command applies ACL 10 inbound?
> Under the interface: `ip access-group 10 in`.

> [!question]- 15. When is an inbound ACL evaluated?
> As the packet enters the interface, before the router's routing decision.

> [!question]- 16. When is an outbound ACL evaluated?
> After the routing decision selects the exit interface and before the packet leaves.

> [!question]- 17. How many IPv4 ACLs can be applied to one interface in one direction?
> One. The broader rule is one ACL per protocol, per interface, per direction.

> [!question]- 18. Which command shows the ACLs applied to an interface?
> `show ip interface <interface-id>`.

> [!question]- 19. Why is a specific host exception placed before a subnet rule?
> Because the first matching ACE wins; the broader subnet rule would otherwise shadow the host exception.

> [!question]- 20. Are basic IPv4 ACLs stateful?
> No. They evaluate packets independently and do not automatically permit return traffic based on session state.

## Quick reference

```cisco
! Numbered standard ACL
access-list 10 deny 192.168.50.0 0.0.0.255
access-list 10 permit any

! Named standard ACL
ip access-list standard BLOCK_GUESTS
 10 deny 192.168.50.0 0.0.0.255
 20 permit any

! Apply to an interface
interface g0/1
 ip access-group BLOCK_GUESTS out

! Verify
show ip access-lists
show ip interface g0/1
show running-config interface g0/1
```

## Related notes

- [Extended ACLs](<Extended Access Control Lists (ACLs).md>)
- IPv4 Subnetting
- [VLANs Part 1 - LANs, Broadcast Domains, and Access Ports](<../VLANs/VLANs Part 1 - LANs, Broadcast Domains, and Access Ports.md>)
