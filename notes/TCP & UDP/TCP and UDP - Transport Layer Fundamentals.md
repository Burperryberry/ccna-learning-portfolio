---
title: "TCP and UDP - Transport Layer Fundamentals"
aliases:
  - TCP and UDP
  - Comparing TCP and UDP
  - Transport Layer Fundamentals
tags:
  - ccna
  - tcp
  - udp
  - transport-layer
  - port-numbers
  - osi-model
source: "CCNA 200-301 Day 30 - TCP and UDP"
date: 2026-08-03
---

# TCP and UDP - Transport Layer Fundamentals

## Summary

The **Transport layer (Layer 4)** provides end-to-end communication between applications running on different hosts. It uses **port numbers** to identify applications and keep multiple conversations separate.

The two major Transport-layer protocols are:

- **TCP (Transmission Control Protocol)** - connection-oriented and reliable; provides sequencing, acknowledgments, retransmission, and flow control.
- **UDP (User Datagram Protocol)** - connectionless and best-effort; has less overhead but does not provide TCP's reliability mechanisms.

> [!important] Core distinction
> **TCP prioritizes reliable, ordered delivery. UDP prioritizes low overhead and timely delivery.** The application determines which behavior it needs.

---

## Functions of the Transport layer

Layer 4 provides transparent transfer of data between end hosts and may provide these services to applications:

- Reliable data transfer
- Error recovery
- Data sequencing
- Flow control
- Layer 4 addressing with port numbers
- Session multiplexing

TCP provides the reliability, sequencing, and flow-control services. UDP does not.

### Layer 4 encapsulation

- TCP places a **TCP header** in front of application data, creating a **TCP segment**.
- UDP places a **UDP header** in front of application data, creating a **UDP datagram**.
- The Layer 4 unit is then encapsulated inside a Layer 3 packet and a Layer 2 frame.

```text
Ethernet header | IP header | TCP/UDP header | Application data | Ethernet trailer
```

---

## Port numbers and session multiplexing

A port number identifies an application or service. These are logical Layer 4 numbers, not physical switch or router interfaces.

### Source and destination ports

When a client connects to a server:

- The **destination port** identifies the server application.
- The **source port** is normally selected dynamically by the client and helps identify that particular session.

Example HTTP request:

```text
Client -> Server
TCP source port:      50000
TCP destination port: 80
```

The server reverses those values in its reply:

```text
Server -> Client
TCP source port:      80
TCP destination port: 50000
```

Two clients can connect to the same server port because their sessions use different combinations of addresses and port numbers.

> [!note] Session multiplexing
> Port numbers allow one device to maintain many simultaneous application conversations. A session is distinguished by the protocol plus the source and destination IP addresses and port numbers.

### IANA port ranges

| Range | Name | Typical purpose |
|---|---|---|
| `0-1023` | Well-known | Common server services |
| `1024-49151` | Registered | Registered applications and services |
| `49152-65535` | Ephemeral / private / dynamic | Temporary client source ports |

Port fields are **16 bits**, so values range from `0` through `65535`.

---

## TCP - Transmission Control Protocol

TCP is **connection-oriented**. The hosts establish a connection before exchanging application data.

TCP provides:

- Connection establishment
- Reliable delivery
- Acknowledgments
- Retransmission of missing data
- Sequencing and ordered delivery
- Flow control

### Important TCP header fields

| Field | Purpose |
|---|---|
| Source port | Identifies the sending application session |
| Destination port | Identifies the receiving application |
| Sequence number | Identifies the position of data in the byte stream |
| Acknowledgment number | Indicates the next sequence number or byte expected |
| Flags | Control connection establishment, acknowledgment, and termination |
| Window size | Advertises how much data the receiver can currently accept |
| Checksum | Detects corruption in the TCP segment |

The minimum TCP header is **20 bytes**. Options can make it larger.

### Common TCP flags in these slides

- **SYN** - synchronizes sequence numbers and starts a connection
- **ACK** - indicates that the acknowledgment field is valid
- **FIN** - requests an orderly connection termination

---

## TCP three-way handshake

TCP establishes a connection with three messages:

1. **SYN** - the client requests a connection and supplies its initial sequence number.
2. **SYN-ACK** - the server acknowledges the client and supplies its own initial sequence number.
3. **ACK** - the client acknowledges the server.

```text
Client                         Server
  | ----------- SYN ----------> |
  | <-------- SYN-ACK ---------- |
  | ----------- ACK ----------> |
  |       Connection ready       |
```

> [!tip] Memory cue
> To open: **SYN, SYN-ACK, ACK**.

---

## TCP four-way termination

Each direction of a TCP conversation is closed independently, so a normal termination uses four messages:

1. One host sends **FIN**.
2. The other host sends **ACK**.
3. The other host sends its own **FIN**.
4. The first host sends the final **ACK**.

```text
Host A                         Host B
  | ----------- FIN ----------> |
  | <----------- ACK ---------- |
  | <----------- FIN ---------- |
  | ----------- ACK ----------> |
```

> [!tip] Memory cue
> To close normally: **FIN, ACK, FIN, ACK**.

---

## Sequencing and acknowledgments

Each host selects an initial sequence number. Sequence numbers allow the receiver to:

- Put data back in the correct order
- Recognize missing data
- Recognize duplicate data

TCP uses **forward acknowledgment**. The acknowledgment number tells the sender what the receiver expects next.

For the simplified one-unit examples in the slides:

```text
Received sequence number: 27
Acknowledgment number:     28
```

In real TCP communication, sequence numbers track **bytes**, so the acknowledgment normally advances by the amount of data received. SYN and FIN also consume one sequence number.

---

## Reliability and retransmission

The receiver acknowledges successfully received TCP data. If the sender does not receive the expected acknowledgment, it retransmits the missing data.

Simplified example:

```text
Sender -> Receiver: Seq 20
Receiver -> Sender: Ack 21
Sender -> Receiver: Seq 21   (lost)
Sender -> Receiver: Seq 21   (retransmitted)
Receiver -> Sender: Ack 22
```

This acknowledgment and retransmission process provides TCP error recovery.

---

## TCP flow control and window size

Acknowledging every small segment individually would be inefficient. The **Window Size** field allows a receiver to advertise how much data the sender may transmit before another acknowledgment is required.

A **sliding window** can change dynamically:

- A larger window allows more unacknowledged data in flight and can improve throughput.
- A smaller window slows the sender when the receiver has fewer resources available.

Example with a window permitting three units:

```text
Sender -> Receiver: Seq 20
Sender -> Receiver: Seq 21
Sender -> Receiver: Seq 22
Receiver -> Sender: Ack 23
```

> [!important]
> **Acknowledgments and retransmissions provide reliability. Sequence numbers provide ordering. Window size provides flow control.**

---

## UDP - User Datagram Protocol

UDP is **connectionless**. It sends data without first establishing a session.

UDP does not provide:

- A three-way handshake
- Acknowledgments
- Protocol-level retransmission
- Sequence numbers
- Ordered delivery
- Flow control

UDP uses a small **8-byte header** containing:

- Source port
- Destination port
- Length
- Checksum

Because UDP has less overhead and no connection setup, it is useful when timeliness is more important than retransmitting old data.

Typical examples include:

- Voice over IP
- Live video
- Real-time applications
- Simple request-and-response protocols

> [!note]
> UDP itself is best-effort, but an application can add its own reliability, recovery, or sequencing mechanisms when needed.

---

## TCP versus UDP

| Feature | TCP | UDP |
|---|---|---|
| Connection style | Connection-oriented | Connectionless |
| Reliability | Reliable | Best-effort |
| Acknowledgments | Yes | No |
| Retransmission | Yes | No |
| Sequencing | Yes | No |
| Flow control | Yes | No |
| Header size | At least 20 bytes | 8 bytes |
| Overhead | Higher | Lower |
| Typical use | Downloads, file sharing, reliable application sessions | VoIP, live video, time-sensitive traffic |

Some applications can use either TCP or UDP depending on the situation. DNS is a common example.

---

## Common protocols and port numbers

### TCP

| Protocol | Port | Purpose |
|---|---:|---|
| FTP data | `20` | FTP data transfer |
| FTP control | `21` | FTP commands and control |
| SSH | `22` | Secure remote access |
| Telnet | `23` | Unencrypted remote access |
| SMTP | `25` | Sending email |
| HTTP | `80` | Web traffic |
| POP3 | `110` | Retrieving email |
| HTTPS | `443` | Secure web traffic |

### UDP

| Protocol | Port | Purpose |
|---|---:|---|
| DHCP server | `67` | Server side of DHCP |
| DHCP client | `68` | Client side of DHCP |
| TFTP | `69` | Trivial File Transfer Protocol |
| SNMP agent | `161` | SNMP queries and agent communication |
| SNMP manager | `162` | SNMP traps and notifications |
| Syslog | `514` | Logging messages |

### TCP and UDP

| Protocol | Port | Purpose |
|---|---:|---|
| DNS | `53` | Name resolution |

> [!warning]
> A port number alone is incomplete. TCP port `53` and UDP port `53` are distinct endpoints because the Transport-layer protocol is part of the session identity.

---

## Troubleshooting checklist

When an application cannot communicate, check:

1. Are the source and destination IP addresses correct?
2. Is the application using TCP or UDP?
3. Is the destination service listening on the expected port?
4. Is a firewall or ACL blocking the protocol or port?
5. For TCP, does the three-way handshake complete?
6. Are retransmissions or duplicate acknowledgments indicating packet loss?
7. Is the TCP receive window limiting throughput?
8. For UDP, does the application provide any required recovery itself?

---

## CCNA exam facts

- Transport layer = **OSI Layer 4**.
- Port numbers identify applications and multiplex sessions.
- Port numbers are 16 bits: `0-65535`.
- Well-known ports: `0-1023`.
- Registered ports: `1024-49151`.
- Ephemeral ports: `49152-65535`.
- TCP is connection-oriented, reliable, sequenced, and flow-controlled.
- UDP is connectionless and best-effort with lower overhead.
- TCP setup: SYN, SYN-ACK, ACK.
- Normal TCP teardown: FIN, ACK, FIN, ACK.
- An ACK number identifies the next data expected.
- TCP's Window Size field provides flow control.
- DNS uses both TCP and UDP port `53`.

---

## Knowledge check

1. **Which choice is a well-known port: `1010`, `2001`, `4023`, or `65000`?**  
   `1010`, because well-known ports are `0-1023`.

2. **Which range should a host normally use for a randomly selected client source port?**  
   The ephemeral/private/dynamic range, `49152-65535`.

3. **Which three features are provided by TCP but not UDP?**  
   Error recovery, flow control, and sequencing. Both protocols use Layer 4 addressing and session multiplexing.

4. **Which three listed protocols use TCP: SMTP, SNMP, HTTPS, DHCP, Syslog, or SSH?**  
   SMTP, HTTPS, and SSH.

5. **A one-unit TCP segment has sequence number 27. What acknowledgment number is expected?**  
   `28`, the next sequence value expected in the simplified example.

---

## One-sentence takeaway

TCP adds connection management, reliability, ordering, and flow control, while UDP trades those services for a smaller, faster, connectionless transport mechanism.
