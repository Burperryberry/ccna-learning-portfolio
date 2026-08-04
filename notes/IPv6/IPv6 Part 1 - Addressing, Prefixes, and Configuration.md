---
title: "IPv6 Part 1 - Addressing, Prefixes, and Configuration"
aliases:
  - IPv6 Part 1
  - IPv6 Addressing Fundamentals
  - IPv6 Address Configuration
tags:
  - ccna
  - ipv6
  - hexadecimal
  - ipv6-addressing
  - ipv6-prefixes
  - routing
source: "CCNA 200-301 Day 31 - IPv6 Part 1"
date: 2026-08-03
---

# IPv6 Part 1 - Addressing, Prefixes, and Configuration

## Summary

IPv6 is the long-term replacement for IPv4. It uses **128-bit addresses**, written as eight groups of hexadecimal digits, to provide an enormous address space.

For the CCNA, know how to:

- Convert between binary and hexadecimal
- Recognize the structure of an IPv6 address
- Shorten and expand IPv6 addresses correctly
- Find an IPv6 network prefix at any prefix length
- Configure IPv6 addresses on Cisco router interfaces
- Enable IPv6 routing with `ipv6 unicast-routing`
- Verify global unicast and link-local addresses

> [!important] Core idea
> An IPv6 address contains **128 bits**, normally written as **eight 16-bit hextets**. Each hexadecimal digit represents exactly four bits.

---

## What happened to IPv5?

An experimental protocol called **Internet Stream Protocol** used the value `5` in the IP header's Version field. It was developed in the late 1970s but was never introduced for general public use.

It was not formally called IPv5, but because version number `5` had already been used, the successor to IPv4 was named **IPv6**.

---

## Hexadecimal review

IPv6 uses hexadecimal because it represents long binary values more compactly.

| Number system | Base | Prefix | Symbols |
|---|---:|---|---|
| Binary | 2 | `0b` | `0-1` |
| Decimal | 10 | `0d` | `0-9` |
| Hexadecimal | 16 | `0x` | `0-9`, `A-F` |

### Four-bit conversion table

| Decimal | Binary | Hex | Decimal | Binary | Hex |
|---:|---|---|---:|---|---|
| 0 | `0000` | `0` | 8 | `1000` | `8` |
| 1 | `0001` | `1` | 9 | `1001` | `9` |
| 2 | `0010` | `2` | 10 | `1010` | `A` |
| 3 | `0011` | `3` | 11 | `1011` | `B` |
| 4 | `0100` | `4` | 12 | `1100` | `C` |
| 5 | `0101` | `5` | 13 | `1101` | `D` |
| 6 | `0110` | `6` | 14 | `1110` | `E` |
| 7 | `0111` | `7` | 15 | `1111` | `F` |

### Binary to hexadecimal

1. Split the binary number into groups of four bits.
2. Convert each group to one hexadecimal digit.

Examples:

```text
1101 1011 = D B = 0xDB
0010 1111 = 2 F = 0x2F
1000 0001 = 8 1 = 0x81
```

### Hexadecimal to binary

Convert each hexadecimal digit into exactly four bits:

```text
0xEC = 1110 1100
0x2B = 0010 1011
0xD7 = 1101 0111
```

> [!tip] Memory cue
> **One hex digit = four bits. Four hex digits = one 16-bit IPv6 hextet.**

---

## Why IPv6?

The primary reason for IPv6 is IPv4 address exhaustion.

- IPv4 has `2^32` addresses: **4,294,967,296**.
- IPv6 has `2^128` addresses: **340,282,366,920,938,463,463,374,607,431,768,211,456**.

VLSM, private IPv4 addresses, and NAT extended the life of IPv4, but they do not create a larger public IPv4 address space. IPv6 is the long-term solution.

IANA distributes address space to **Regional Internet Registries (RIRs)**, which allocate it within their regions. IPv4 exhaustion occurred at different times in different RIR regions.

---

## IPv6 address structure

An IPv6 address is written as eight groups of four hexadecimal digits:

```text
2001:0DB8:5917:EABD:6562:17EA:C92D:59BD
```

Terminology:

- Each group is commonly called a **hextet**. The slides also use **quartet**.
- Each hextet contains 16 bits.
- Eight hextets contain 128 bits.
- Colons separate the hextets.
- IPv6 prefix length uses slash notation, such as `/64`.

```text
8 hextets x 16 bits = 128 bits
32 hexadecimal digits x 4 bits = 128 bits
```

---

## Shortening IPv6 addresses

IPv6 has two shortening rules.

### Rule 1: Remove leading zeros

Leading zeros within any hextet can be removed.

```text
2001:0DB8:000A:001B:20A1:0020:0080:34BD
2001:DB8:A:1B:20A1:20:80:34BD
```

Do not remove trailing zeros that change the hextet's value.

### Rule 2: Replace consecutive all-zero hextets with `::`

One consecutive run of all-zero hextets can be replaced by a double colon.

```text
2001:0DB8:0000:0000:0000:0000:0080:34BD
2001:DB8::80:34BD
```

### `::` can be used only once

The double colon may appear only once in an IPv6 address. If it appeared twice, the reader could not determine how many zero hextets each `::` represents.

Invalid:

```text
2001::20A1::34BD
```

Valid:

```text
2001::20A1:0:0:34BD
```

> [!important]
> Remove leading zeros anywhere, but compress an all-zero sequence with `::` only once. By convention, compress the longest sequence of zero hextets.

### Shortening examples

| Full address | Shortened address |
|---|---|
| `2000:AB78:0020:01BF:ED89:0000:0000:0001` | `2000:AB78:20:1BF:ED89::1` |
| `FE80:0000:0000:0000:0002:0000:0000:FBE8` | `FE80::2:0:0:FBE8` |
| `AE89:2100:01AC:00F0:0000:0000:0000:020F` | `AE89:2100:1AC:F0::20F` |
| `2001:0DB8:8B00:1000:0002:0BC0:0D07:0099` | `2001:DB8:8B00:1000:2:BC0:D07:99` |
| `2001:0DB8:0000:0000:0000:0000:0000:1000` | `2001:DB8::1000` |

---

## Expanding shortened IPv6 addresses

To expand an address:

1. Count the explicitly written hextets.
2. Replace `::` with enough `0000` hextets to make eight total.
3. Add leading zeros until each hextet has four digits.

Example:

```text
Short: FE80::2:0:0:FBE8

Five hextets are written, so :: represents three zero hextets.

Full:  FE80:0000:0000:0000:0002:0000:0000:FBE8
```

Additional examples:

| Shortened address | Full address |
|---|---|
| `FE80::1010:2FC:0:9` | `FE80:0000:0000:0000:1010:02FC:0000:0009` |
| `2001:DB8:1:B23:2309::C1` | `2001:0DB8:0001:0B23:2309:0000:0000:00C1` |
| `FD00::1000:689:9000:CDF` | `FD00:0000:0000:0000:1000:0689:9000:0CDF` |
| `FF02::2` | `FF02:0000:0000:0000:0000:0000:0000:0002` |
| `::1` | `0000:0000:0000:0000:0000:0000:0000:0001` |

---

## IPv6 prefixes

The prefix length tells how many leftmost bits belong to the network portion.

Typical global unicast allocation:

```text
| 48-bit global routing prefix | 16-bit subnet ID | 64-bit interface ID |
```

- An enterprise commonly receives a `/48` from its ISP.
- IPv6 LAN subnets commonly use `/64`.
- The enterprise can use the 16 bits between `/48` and `/64` to create subnets.
- The remaining 64 bits identify an interface within the subnet.

Example:

```text
Host address: 2001:0DB8:8B00:0001:0000:0000:0000:0001/64
Prefix:       2001:DB8:8B00:1::/64
```

### Finding a prefix on a hextet boundary

For `/16`, `/32`, `/48`, or `/64`, keep the complete network hextets and set all host hextets to zero.

```text
2001:0DB8:8B00:0001:0000:0000:0000:0001/64
2001:DB8:8B00:1::/64
```

### Finding a prefix inside a hextet

If the prefix does not end on a 16-bit boundary:

1. Keep every complete network hextet.
2. Convert the affected hexadecimal digit or hextet to binary.
3. Preserve only the network bits.
4. Set all remaining host bits to zero.
5. Convert the result back to hexadecimal.

Example `/56`:

```text
Host:   300D:00F2:0B34:2100:0000:0000:1200:0001/56
Prefix: 300D:F2:B34:2100::/56
```

The first 56 bits are the first three hextets plus the first two hex digits of the fourth hextet.

Example `/93`:

```text
Host:   2001:0DB8:8B00:0001:FB89:017B:0020:0011/93
Prefix: 2001:DB8:8B00:1:FB89:178::/93
```

Only the first 13 bits of the sixth hextet belong to the prefix; the remaining bits are zeroed.

### Prefix practice from the slides

| Host address | Network prefix |
|---|---|
| `FE80:0000:0000:0000:4C2C:E2ED:6A89:2A27/9` | `FE80::/9` |
| `2001:0DB8:0001:0B23:BA89:0020:0000:00C1/64` | `2001:DB8:1:B23::/64` |
| `2001:0DB8:0BAD:CAFE:1300:0689:9000:0CDF/71` | `2001:DB8:BAD:CAFE:1200::/71` |
| `2001:0DB8:0000:FEED:0DAD:018F:6001:0DA3/62` | `2001:DB8:0:FEEC::/62` |
| `2001:0DB8:9BAD:BABE:0DE8:AB78:2301:0010/63` | `2001:DB8:9BAD:BABE::/63` |

> [!tip] Prefix math shortcut
> Each full hexadecimal digit represents four prefix bits. Prefix lengths divisible by four align with a hex digit; other lengths require binary work inside one digit.

---

## Configuring IPv6 on Cisco IOS

Example networks:

- G0/0: `2001:DB8:0:0::/64`
- G0/1: `2001:DB8:0:1::/64`
- G0/2: `2001:DB8:0:2::/64`

Router configuration:

```cisco
R1(config)# ipv6 unicast-routing

R1(config)# interface g0/0
R1(config-if)# ipv6 address 2001:db8:0:0::1/64
R1(config-if)# no shutdown

R1(config)# interface g0/1
R1(config-if)# ipv6 address 2001:db8:0:1::1/64
R1(config-if)# no shutdown

R1(config)# interface g0/2
R1(config-if)# ipv6 address 2001:db8:0:2::1/64
R1(config-if)# no shutdown
```

The address can be entered in shortened or full notation. IOS displays it in a shortened format.

### Enable IPv6 routing

```cisco
R1(config)# ipv6 unicast-routing
```

This global configuration command allows the router to forward IPv6 packets between interfaces.

> [!warning]
> Assigning IPv6 addresses to interfaces does not by itself enable IPv6 packet forwarding. Use `ipv6 unicast-routing` on a router.

---

## Verification and link-local addresses

Use:

```cisco
R1# show ipv6 interface brief
```

The output shows:

- Interface status
- Automatically generated or manually configured **link-local address**
- Configured global unicast address

Example pattern:

```text
GigabitEthernet0/0     [up/up]
    FE80::EF8:22FF:FE36:8500
    2001:DB8::1
GigabitEthernet0/1     [up/up]
    FE80::EF8:22FF:FE36:8501
    2001:DB8:0:1::1
```

Link-local addresses use the `FE80::/10` range and operate only on the local link. Routers do not forward link-local traffic beyond that link.

> [!note]
> Every IPv6-enabled interface needs a link-local address. It is used for important local functions such as neighbor discovery and routing-protocol neighbor relationships.

---

## Troubleshooting checklist

When IPv6 communication fails, verify:

1. Is the address written with valid hexadecimal characters only (`0-9`, `A-F`)?
2. Does the address expand to exactly eight hextets?
3. Is `::` used no more than once?
4. Is the prefix length correct for the subnet?
5. Was the host portion zeroed correctly when calculating the network prefix?
6. Is the interface `up/up`?
7. Does the interface have the expected global unicast and link-local addresses?
8. Is `ipv6 unicast-routing` enabled on the router?
9. Are neighboring devices using addresses from the correct subnet?

---

## CCNA exam facts

- IPv6 addresses are 128 bits.
- IPv6 is written as eight 16-bit hextets.
- One hexadecimal digit represents four bits.
- Leading zeros can be removed from a hextet.
- One consecutive zero run can be represented by `::`.
- `::` can appear only once in an address.
- IPv6 LANs typically use `/64`.
- An enterprise commonly receives a `/48`, leaving 16 subnet bits before `/64`.
- `ipv6 unicast-routing` enables IPv6 forwarding on a Cisco router.
- `ipv6 address ADDRESS/PREFIX` assigns an address to an interface.
- `show ipv6 interface brief` verifies interface status and IPv6 addresses.
- Link-local addresses are in `FE80::/10` and remain on the local link.
- `::1` is the IPv6 loopback address.

---

## Knowledge check

1. **Which three slide choices are valid IPv6 addresses?**  
   `2000:AB78:20:1BF:ED89::1`, `FE80:0000:0000:0000:0002:0000:0000:FBE8`, and `2001:0DB8::1000`.

   - An address containing `G` is invalid because hexadecimal ends at `F`.
   - An address with nine hextets is too long.
   - An address cannot contain two instances of `::`.

2. **Correctly shorten `2001:0DB8:0101:0B23:BA89:0020:0AB0:00C1`.**  
   `2001:DB8:101:B23:BA89:20:AB0:C1`.

3. **Which command enables a Cisco router to perform IPv6 routing?**  
   `R1(config)# ipv6 unicast-routing`.

---

## One-sentence takeaway

IPv6 uses 128-bit hexadecimal addresses that can be shortened with strict zero-compression rules, subnetted with prefix lengths, and routed on Cisco IOS after enabling `ipv6 unicast-routing`.
