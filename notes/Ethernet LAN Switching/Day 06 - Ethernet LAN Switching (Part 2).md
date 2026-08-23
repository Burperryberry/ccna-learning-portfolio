---
title: "Day 06 - Ethernet LAN Switching (Part 2)"
course: "CCNA 200-301"
topic: "Ethernet LAN Switching"
source: "Jeremy's IT Lab - Day 6"
tags:
  - ccna
  - ethernet
  - switching
  - layer2
  - arp
  - icmp
  - mac-address-table
---

# Day 06 - Ethernet LAN Switching (Part 2)

## Big Picture

This lesson connects Ethernet switching to the protocols a host uses before and during local communication:

- Ethernet frames must meet a **64-byte minimum size** from the Destination MAC field through the FCS.
- The Ethernet header plus trailer is **18 bytes**, so the minimum payload is **46 bytes**.
- **ARP (Address Resolution Protocol)** discovers the MAC address associated with a known IPv4 address.
- An **ARP Request** is broadcast; an **ARP Reply** is unicast.
- **Ping** tests reachability and round-trip time with ICMP Echo Request and Echo Reply messages.
- Switches learn source MAC addresses while ARP and ping traffic cross the LAN.
- Cisco switches display learned forwarding information with `show mac address-table`.

> [!abstract] CCNA core idea
> A host first resolves an IPv4 address to a MAC address with ARP. The switches learn from each frame's **source MAC**, then forward or flood based on the **destination MAC**.

> [!tip] Part 1 connection
> Review [Day 05 - Ethernet LAN Switching (Part 1)](<Day 05 - Ethernet LAN Switching (Part 1).md>) for Ethernet fields, MAC addresses, source-MAC learning, known unicast forwarding, unknown unicast flooding, and dynamic MAC aging.

---

## 1. Ethernet Frame Size Review

The lesson separates these fields as follows:

```text
Preamble | SFD | Destination | Source | Type | Payload | FCS
 7 bytes   1       6 bytes    6 bytes   2      variable   4
                   \________ Ethernet header ________/   trailer
```

The **Preamble and SFD are usually not considered part of the Ethernet header**. Therefore:

| Component | Size |
|---|---:|
| Destination MAC | 6 bytes |
| Source MAC | 6 bytes |
| Type | 2 bytes |
| Ethernet header | 14 bytes |
| FCS trailer | 4 bytes |
| Header + trailer | **18 bytes** |

> [!important] Two common totals
> - Header only: **14 bytes**
> - Header + FCS trailer: **18 bytes**
>
> Preamble and SFD add another 8 bytes on the physical medium but are normally excluded from the Ethernet frame-size calculation used in this lesson.

### Minimum Ethernet frame and payload

The minimum Ethernet frame size is **64 bytes**:

```text
64-byte minimum frame - 18-byte header/trailer = 46-byte minimum payload
```

| Item | Minimum size |
|---|---:|
| Ethernet frame: header + payload + trailer | 64 bytes |
| Ethernet payload | 46 bytes |

If the encapsulated packet is smaller than 46 bytes, Ethernet adds **padding bytes** until the payload reaches 46 bytes.

```text
34-byte packet + 12 bytes of padding = 46-byte Ethernet payload
14-byte header + 46-byte payload + 4-byte FCS = 64-byte frame
```

> [!warning] Exam trap
> Padding is part of the Ethernet payload area used to meet the minimum size. It is not the FCS, and it does not mean the higher-layer message itself consists of zeroes.

### Why a capture may show 60 bytes

Packet captures commonly do not include the 4-byte FCS because the network interface removes it before handing the frame to the capture software. A minimum Ethernet frame can therefore appear as **60 captured bytes** even though its on-the-wire frame size is 64 bytes when the FCS is included.

---

## 2. Address Resolution Protocol (ARP)

**ARP stands for Address Resolution Protocol.** It discovers the Layer 2 address - the MAC address - associated with a known Layer 3 IPv4 address.

```text
Known:   IPv4 address
Needed:  MAC address for the local Ethernet frame
Method:  ARP Request -> ARP Reply
```

ARP uses two messages:

| Message | Ethernet delivery | Purpose |
|---|---|---|
| ARP Request | Broadcast | Ask all hosts which device owns a particular IPv4 address |
| ARP Reply | Unicast | Tell the requester the owner's MAC address |

> [!important] Memorize this pair
> **ARP Request = broadcast. ARP Reply = unicast.**

### Broadcast MAC address

An ARP Request uses the destination MAC address:

```text
FFFF.FFFF.FFFF
```

This is the Ethernet **broadcast MAC address**. Switches flood a broadcast frame out every interface in the same VLAN except the interface on which the frame arrived.

### ARP scope

ARP resolves addresses on the local IPv4 link. For a destination in the same subnet, the sender resolves the destination host's MAC address. For a remote destination, the sender resolves the MAC address of its default gateway, not the remote host's MAC address.

> [!note]
> ARP maps IPv4 addresses to MAC addresses. IPv6 uses Neighbor Discovery rather than ARP.

---

## 3. Worked ARP Example: PC1 to PC3

The slide topology places four PCs in `192.168.1.0/24` across two switches:

```text
PC1 .1                                            .3 PC3
MAC ...9D00 -- G0/0 SW1 G0/2 ---- G0/2 SW2 G0/0 -- MAC ...3900
                 G0/1                  G0/1
PC2 .2                                            .4 PC4
MAC ...6200                                      MAC ...0A00
```

PC1 wants to send traffic to PC3:

```text
Source IP:      192.168.1.1
Destination IP: 192.168.1.3
Source MAC:     0C2F.B011.9D00
Destination MAC: unknown
```

Because PC1 knows PC3's IPv4 address but not its MAC address, PC1 performs ARP before sending the intended unicast traffic.

### Step 1: PC1 creates an ARP Request

```text
ARP REQUEST
Sender IP:        192.168.1.1
Target IP:        192.168.1.3
Sender MAC:       0C2F.B011.9D00
Ethernet Dst MAC: FFFF.FFFF.FFFF
```

The request means: **Who has `192.168.1.3`? Tell `192.168.1.1`.**

### Step 2: SW1 receives the request

SW1 learns the source MAC from the incoming frame:

| SW1 learned MAC | Interface |
|---|---|
| `0C2F.B011.9D00` | `G0/0` |

Because the destination is broadcast, SW1 floods the frame out all other ports in the VLAN, including the link toward SW2. PC2 receives the request but discards it because it does not own `192.168.1.3`.

### Step 3: SW2 receives the request

SW2 learns PC1's source MAC on the inter-switch link:

| SW2 learned MAC | Interface |
|---|---|
| `0C2F.B011.9D00` | `G0/2` |

SW2 floods the request out its other ports. PC4 discards it; PC3 recognizes its own IPv4 address as the target.

### Step 4: PC3 creates an ARP Reply

PC3 replies directly to PC1:

```text
ARP REPLY
Sender IP:        192.168.1.3
Target IP:        192.168.1.1
Source MAC:       0C2F.B06A.3900
Destination MAC:  0C2F.B011.9D00
```

The reply is a **unicast** frame because PC3 learned PC1's address information from the request.

### Step 5: SW2 learns and forwards

SW2 learns PC3's source MAC:

| SW2 MAC | Interface |
|---|---|
| `0C2F.B011.9D00` | `G0/2` |
| `0C2F.B06A.3900` | `G0/0` |

PC1's MAC is already known on `G0/2`, so SW2 forwards the reply only toward SW1. It does not flood the known unicast frame.

### Step 6: SW1 learns and forwards

SW1 learns PC3's source MAC on the inter-switch link:

| SW1 MAC | Interface |
|---|---|
| `0C2F.B011.9D00` | `G0/0` |
| `0C2F.B06A.3900` | `G0/2` |

SW1 already knows PC1 is on `G0/0`, so it forwards the reply only to PC1.

### Final result

PC1 now has the IP-to-MAC mapping needed to build the original unicast frame:

```text
Source IP:        192.168.1.1
Destination IP:   192.168.1.3
Source MAC:       0C2F.B011.9D00
Destination MAC:  0C2F.B06A.3900
```

Both switches also learned the path to PC1 and PC3 from the source MAC addresses of the ARP exchange.

> [!abstract] Full mental model
> ARP learns the **IP-to-MAC mapping** on the hosts. Ethernet switching learns the **MAC-to-port mapping** on each switch. These are different tables serving different purposes.

---

## 4. ARP Table

An ARP table stores Layer 3-to-Layer 2 mappings:

```text
IPv4 address -> MAC address
```

On Windows, macOS, and Linux, the lesson uses:

```shell
arp -a
```

Important fields in typical host output:

| Field | Meaning |
|---|---|
| Internet Address | IPv4 address - Layer 3 address |
| Physical Address | MAC address - Layer 2 address |
| Type `dynamic` | Mapping learned through ARP |
| Type `static` | Predefined/default entry rather than dynamically learned |

On a Cisco router or the VPCS environment used in the lab, the relevant command may appear as:

```cisco
PC1# show arp
```

Example conceptually:

```text
Protocol  Address       Hardware Addr   Type   Interface
Internet  192.168.1.1  0c2f.b011.9d00  ARPA   GigabitEthernet0/0
Internet  192.168.1.3  0c2f.b06a.3900  ARPA   GigabitEthernet0/0
```

> [!warning] ARP table vs. MAC address table
> A host or router ARP table maps **IPv4 addresses to MAC addresses**. A switch MAC address table maps **MAC addresses to switch ports, per VLAN**.

---

## 5. Ping and ICMP

**Ping** is a network utility that:

- Tests whether a destination is reachable
- Measures round-trip time
- Uses ICMP Echo Request and Echo Reply messages

```shell
ping 192.168.1.3
```

| ICMP message | Direction |
|---|---|
| Echo Request | Sender to target |
| Echo Reply | Target back to sender |

The request and reply are normally unicast messages aimed at specific hosts. Unlike an ARP Request, an ICMP Echo Request is not automatically sent to every device on the LAN.

### Reading ping output

The slide example sends five 100-byte ICMP Echo Requests:

```text
Sending 5, 100-byte ICMP Echos to 192.168.1.3, timeout is 2 seconds:
.!!!!
Success rate is 80 percent (4/5), round-trip min/avg/max = 20/20/22 ms
```

- `!` indicates a successful reply in Cisco-style output.
- `.` indicates a timeout.
- `4/5` means four of five requests received replies.
- `min/avg/max` reports round-trip times in milliseconds.

> [!note] Why the first ping may fail
> The first Echo Request can time out while the sender performs ARP and the switches learn the relevant MAC addresses. Later requests succeed after address resolution is complete. This is common in lab environments but is not guaranteed every time.

### Packet-capture sequence

A first ping to an uncached local neighbor often produces:

```text
1. ARP Request: Who has 192.168.1.3? Tell 192.168.1.1
2. ARP Reply:   192.168.1.3 is at 0C2F.B06A.3900
3. ICMP Echo Request
4. ICMP Echo Reply
5. Additional Echo Request/Reply pairs
```

ARP prepares the Layer 2 destination information; ICMP performs the reachability test.

---

## 6. MAC Address Table

A switch MAC address table stores forwarding information:

```text
VLAN + MAC address -> switch port
```

Use this Cisco IOS command:

```cisco
SW1# show mac address-table
```

The output fields covered in the lesson are:

| Field | Meaning |
|---|---|
| VLAN | VLAN in which the MAC address was learned |
| Mac Address | Layer 2 address |
| Type | Dynamic, static, or another entry type |
| Ports | Interface associated with the MAC address |

Example:

```text
          Mac Address Table
-------------------------------------------
Vlan    Mac Address       Type        Ports
----    -----------       --------    -----
   1    0c2f.b011.9d00    DYNAMIC     Gi0/0
   1    0c2f.b06a.3900    DYNAMIC     Gi0/2
```

Interpretation:

- PC1's MAC `0c2f.b011.9d00` is reachable through SW1 `G0/0`.
- PC3's MAC `0c2f.b06a.3900` is reachable through SW1 `G0/2`, the link toward SW2.
- `DYNAMIC` means the switch learned the address automatically from a frame's source MAC.

> [!important] Per-switch perspective
> Each switch maintains its own MAC address table. The port associated with a remote host is normally the port leading toward the next switch, not the host's physical access port on another switch.

### Dynamic MAC aging

Dynamic entries do not remain forever. In this course, the default aging time is **5 minutes of inactivity**. New traffic from the source refreshes or relearns the entry.

---

## 7. Clearing the MAC Address Table

Cisco IOS can clear all dynamic entries or only selected dynamic entries.

### Clear all dynamic MAC addresses

```cisco
SW1# clear mac address-table dynamic
```

### Clear one dynamic MAC address

```cisco
SW1# clear mac address-table dynamic address 0c2f.b011.9d00
```

General syntax:

```cisco
clear mac address-table dynamic address <mac-address>
```

### Clear all dynamic addresses learned on one interface

```cisco
SW1# clear mac address-table dynamic interface Gi0/0
```

General syntax:

```cisco
clear mac address-table dynamic interface <interface-id>
```

### Verify after clearing

```cisco
SW1# show mac address-table
```

The switch will learn dynamic entries again when new frames arrive.

> [!danger] Syntax trap
> The correct command contains `mac address-table` with a space between `mac` and `address-table`, followed by `dynamic interface <interface-id>` when clearing a specific port.

---

## 8. Switch Forwarding Review

A switch examines the destination MAC address after learning the source MAC:

| Frame type | Destination state | Switch action |
|---|---|---|
| Broadcast | `FFFF.FFFF.FFFF` | Flood out all other ports in the VLAN |
| Unknown unicast | Unicast MAC absent from table | Flood out all other ports in the VLAN |
| Known unicast | Unicast MAC present in table | Forward only through the matching port |

> [!important] Learn and forward
> **Learn from the source MAC. Forward based on the destination MAC.**

An ARP Request demonstrates broadcast flooding. An ARP Reply demonstrates known unicast forwarding once the switches have learned the requester's source MAC.

---

## 9. Wireshark Observations

The slides use Wireshark to connect the theory to actual frames.

### IPv4/ICMP frame

The captured Ethernet II frame shows:

- Source and destination MAC addresses
- EtherType `IPv4 (0x0800)`
- An IPv4 packet carrying ICMP
- Padding bytes when the payload would otherwise be too small

### ARP frame

The ARP Reply capture shows:

- Source and destination MAC addresses
- EtherType `ARP (0x0806)`
- Address Resolution Protocol reply data
- Padding bytes to meet the Ethernet minimum payload size

### Padding in hexadecimal

Wireshark can display the padding as a series of `00` bytes near the end of the frame. Those bytes satisfy Ethernet's minimum payload requirement; they are not part of the ICMP or ARP message's meaningful data.

> [!question] Why did a 36-byte ping show zeroes at the end?
> Because the minimum Ethernet payload is 46 bytes. Ethernet added padding to the smaller packet before transmission.

---

## 10. ARP Table vs. MAC Address Table

| Characteristic | ARP table | MAC address table |
|---|---|---|
| Primary mapping | IPv4 address -> MAC address | MAC address -> switch port |
| Common owner | Host or Layer 3 device | Ethernet switch |
| Purpose | Build the correct local Ethernet destination | Forward Ethernet frames through the LAN |
| Learned from | ARP exchange | Source MAC of received frames |
| Typical host command | `arp -a` | Not applicable |
| Cisco verification | `show arp` | `show mac address-table` |
| Includes VLAN | Not as the core lookup key | Yes, MAC entries are associated with VLANs |

> [!example] Easy analogy
> The ARP table is an address book: “Which MAC belongs to this IP?” The MAC table is a building directory: “Which switch port leads to this MAC?”

---

## 11. End-to-End Decision Flow

When PC1 sends a ping to a same-subnet PC3:

```text
Does PC1 know PC3's MAC?
        |
       No
        v
Broadcast ARP Request
        |
        +--> switches learn PC1's source MAC
        +--> switches flood the broadcast
        v
PC3 sends unicast ARP Reply
        |
        +--> switches learn PC3's source MAC
        +--> switches forward toward known PC1 MAC
        v
PC1 stores PC3's IP-to-MAC mapping
        v
PC1 sends unicast ICMP Echo Request
        v
PC3 sends unicast ICMP Echo Reply
```

This single transaction demonstrates ARP, broadcast flooding, source-MAC learning, known unicast forwarding, ICMP, the ARP table, and the MAC address table.

---

## 12. Common Mistakes

- Including the Preamble and SFD in the 14-byte Ethernet header
- Forgetting that the Ethernet header plus FCS trailer is 18 bytes
- Saying the minimum Ethernet payload is 64 bytes instead of 46 bytes
- Mistaking padding bytes for the FCS or for ICMP data
- Treating an ARP Request as unicast
- Treating an ARP Reply as broadcast
- Assuming an ICMP Echo Request is broadcast to all hosts
- Confusing `FFFF.FFFF.FFFF` with an unknown unicast address
- Thinking a switch learns from the destination MAC instead of the source MAC
- Confusing a host's ARP table with a switch's MAC address table
- Expecting every switch to associate a remote PC with that PC's access port on another switch
- Forgetting the VLAN and Type fields in `show mac address-table`
- Using the wrong command spelling, such as `mac-address-table` instead of `mac address-table`
- Forgetting the `dynamic` keyword when clearing learned entries by address or interface
- Expecting a cleared dynamic MAC entry to stay gone after the device transmits again
- Assuming the first ping must always succeed before ARP has completed

---

## 13. High-Yield CCNA Facts

> [!tip] Must Know
> - Ethernet header: **14 bytes**
> - Ethernet header + FCS trailer: **18 bytes**
> - Minimum Ethernet frame: **64 bytes**
> - Minimum Ethernet payload: **46 bytes**
> - Small payload: add **padding**
> - ARP purpose: known IPv4 address -> discover MAC address
> - ARP Request: **broadcast** to `FFFF.FFFF.FFFF`
> - ARP Reply: **unicast**
> - Ping: tests reachability and round-trip time
> - Ping messages: ICMP Echo Request and Echo Reply
> - Switch learning: source MAC + ingress interface + VLAN
> - Broadcast and unknown unicast: **flood**
> - Known unicast: **forward through one matching port**
> - `show mac address-table` fields: VLAN, MAC Address, Type, Ports
> - Dynamic MAC aging in this course: **5 minutes of inactivity**

### Slide quiz review

1. **Why does a 36-byte ping produce a series of zero bytes at the end of the Ethernet payload?**  
   They are padding bytes. The Ethernet payload must be at least 46 bytes.

2. **Which message is sent to all hosts on the local network?**  
   The ARP Request. It is broadcast because the target MAC address is not yet known. ARP Reply and ICMP Echo messages are unicast in this example.

3. **Which fields appear in `show mac address-table`?**  
   VLAN, MAC Address, Type, and Ports.

4. **Which frames does a switch flood out all interfaces except the receiving interface?**  
   Broadcast and unknown unicast frames.

5. **Which command clears all dynamic MAC addresses learned on one interface?**  
   `clear mac address-table dynamic interface <interface-id>`.

> [!question] Exam trap: 64 vs. 46
> The frame minimum is **64 bytes**; the payload minimum is **46 bytes** because 18 bytes are used by the Ethernet header and FCS trailer.

> [!question] Exam trap: two tables
> ARP answers “What MAC belongs to this IPv4 address?” The switch MAC table answers “Which port leads to this MAC in this VLAN?”

---

## 14. Flashcards

> [!question]- 1. How large is the Ethernet header when Preamble and SFD are excluded?
> 14 bytes: 6-byte destination MAC, 6-byte source MAC, and 2-byte Type field.

> [!question]- 2. How large are the Ethernet header and FCS trailer together?
> 18 bytes.

> [!question]- 3. What is the minimum Ethernet frame size covered in this lesson?
> 64 bytes for header, payload, and trailer.

> [!question]- 4. What is the minimum Ethernet payload size?
> 46 bytes.

> [!question]- 5. What happens when an Ethernet payload is smaller than 46 bytes?
> Padding bytes are added until it reaches 46 bytes.

> [!question]- 6. What does ARP stand for?
> Address Resolution Protocol.

> [!question]- 7. What does ARP discover?
> The Layer 2 MAC address associated with a known Layer 3 IPv4 address.

> [!question]- 8. Is an ARP Request broadcast or unicast?
> Broadcast.

> [!question]- 9. Is an ARP Reply broadcast or unicast?
> Unicast to the host that sent the request.

> [!question]- 10. What is the Ethernet broadcast MAC address?
> `FFFF.FFFF.FFFF`.

> [!question]- 11. What does a switch do with a broadcast frame?
> Floods it out all other ports in the same VLAN.

> [!question]- 12. What does a switch learn from an ARP Request?
> The requester's source MAC and the interface on which the frame arrived.

> [!question]- 13. Why can an ARP Reply normally be forwarded as known unicast?
> The switches learned the requester's source MAC while flooding the earlier ARP Request.

> [!question]- 14. What command displays a host's ARP table on Windows, macOS, and Linux?
> `arp -a`.

> [!question]- 15. What does an ARP table map?
> IPv4 addresses to MAC addresses.

> [!question]- 16. What is ping used for?
> Testing reachability and measuring round-trip time.

> [!question]- 17. Which two messages does ping use?
> ICMP Echo Request and ICMP Echo Reply.

> [!question]- 18. Are ordinary ICMP Echo Requests and Replies broadcast in this lesson?
> No, they are unicast between the specific sender and target.

> [!question]- 19. What command displays a Cisco switch's MAC address table?
> `show mac address-table`.

> [!question]- 20. Which four fields are emphasized in `show mac address-table` output?
> VLAN, MAC Address, Type, and Ports.

> [!question]- 21. What does a switch MAC address table map?
> A MAC address and VLAN to a switch port.

> [!question]- 22. What frames are flooded by a switch?
> Broadcast and unknown unicast frames.

> [!question]- 23. What happens to a known unicast frame?
> It is forwarded only through the port associated with its destination MAC.

> [!question]- 24. What command clears every dynamic MAC table entry?
> `clear mac address-table dynamic`.

> [!question]- 25. What command clears one dynamic MAC entry?
> `clear mac address-table dynamic address <mac-address>`.

> [!question]- 26. What command clears dynamic entries learned on one interface?
> `clear mac address-table dynamic interface <interface-id>`.

> [!question]- 27. Why might a minimum Ethernet frame appear as 60 bytes in Wireshark?
> The 4-byte FCS is often removed before the capture is presented.

> [!question]- 28. Which EtherType identifies IPv4?
> `0x0800`.

> [!question]- 29. Which EtherType identifies ARP?
> `0x0806`.

> [!question]- 30. After how much inactivity do dynamic MAC entries age out in this course?
> 5 minutes.

---

## Quick Reference

```cisco
! Host address resolution and reachability
arp -a
ping 192.168.1.3

! Cisco/VPCS ARP information
show arp

! Display the switch forwarding table
show mac address-table

! Clear all dynamic MAC entries
clear mac address-table dynamic

! Clear one dynamic MAC entry
clear mac address-table dynamic address 0c2f.b011.9d00

! Clear dynamic entries learned on one interface
clear mac address-table dynamic interface Gi0/0
```

```text
Ethernet minimums
-----------------
Header:                    14 bytes
Header + FCS trailer:      18 bytes
Minimum payload:           46 bytes
Minimum frame:             64 bytes

ARP Request destination:   FFFF.FFFF.FFFF (broadcast)
ARP Reply destination:     requester's MAC (unicast)

ARP table:                 IPv4 -> MAC
Switch MAC table:          VLAN + MAC -> port
```

---

## Related Notes

- [Day 05 - Ethernet LAN Switching (Part 1)](<Day 05 - Ethernet LAN Switching (Part 1).md>)
- OSI Model
- Ethernet Frame
- MAC Addresses
- IPv4 Addressing
- [VLANs Part 1 - LANs, Broadcast Domains, and Access Ports](<../VLANs/VLANs Part 1 - LANs, Broadcast Domains, and Access Ports.md>)
- [IPv6 Part 1 - Addressing, Prefixes, and Configuration](<../IPv6/IPv6 Part 1 - Addressing, Prefixes, and Configuration.md>)
