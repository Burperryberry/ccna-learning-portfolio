---
tags: [ccna, wireshark, packet-analysis]
---

# CCNA Capture Workflow

Use the **CCNA** Wireshark profile. It contains focused display and capture filters without changing the default profile.

## Repeatable capture method

1. Write one sentence predicting the packets you expect.
2. Select the active interface (normally Wi-Fi on the MacBook Air).
3. Apply a narrow capture filter only when the traffic is easy to generate again.
4. Start capturing, generate the traffic, then stop within 10–20 seconds.
5. Apply a display filter and inspect Ethernet, IP, transport, and application fields in order.
6. Record the field values that prove or disprove your prediction.
7. Save only useful, non-sensitive captures. Avoid capturing passwords, tokens, or unrelated personal traffic.

## DNS practical — Day 38

### Prediction

Before capturing, predict which transport protocol, destination port, query type, and response fields you expect.

### Capture

Use the capture filter `port 53`, start the capture, and run these in Terminal one at a time:

```bash
dig example.com A
dig example.com AAAA
dig example.com NS
dig gmail.com MX
dig -x 1.1.1.1
dig +tcp example.com A
```

`example.com` is reserved for documentation. The other queries request only public DNS data.

### Display filters

```text
dns
dns.flags.response == 0
dns.flags.response == 1
dns.qry.type == 1
dns.qry.type == 28
dns.qry.type == 15
dns.qry.type == 12
udp.port == 53 || tcp.port == 53
dns.flags.rcode != 0
```

### Questions to answer from packets

1. Which flags distinguish the query from the response?
2. Where do the transaction IDs match?
3. What name and record type appear in the Questions section?
4. What answer, TTL, and authoritative/additional information were returned?
5. Why did the `+tcp` lookup use a connection handshake while the others normally did not?
6. What would an NXDOMAIN response look like?

## CCNA filter shelf

| Topic | Display filter |
|---|---|
| ARP | `arp` |
| ICMP / ICMPv6 | `icmp || icmpv6` |
| DNS | `dns` |
| DHCPv4 | `bootp` |
| TCP handshake/reset | `tcp.flags.syn == 1 || tcp.flags.reset == 1` |
| VLAN tags | `vlan` |
| Spanning Tree | `stp` |
| CDP / LLDP | `cdp || lldp` |
| OSPF | `ospf` |
| NTP | `ntp` |
| SSH | `tcp.port == 22` |
| FTP / TFTP | `ftp || ftp-data || tftp` |

## Capture journal

For every important capture, create a note from Lab Reflection and record:

- the hypothesis;
- how traffic was generated;
- the display filter;
- two or three decisive packet fields;
- the conclusion and one failure scenario.
