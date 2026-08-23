---
title: "Day 05 - Ethernet LAN Switching (Part 1)"
course: "CCNA 200-301"
topic: "Ethernet LAN Switching"
source: "Jeremy's IT Lab - Day 5"
tags:
  - ccna
  - ethernet
  - switching
  - layer2
  - mac-address
---
 
# Day 05 - Ethernet LAN Switching (Part 1)

## Big Picture
Ethernet LAN switching is primarily a **Layer 2 (Data Link)** topic. The key ideas are:

- Ethernet frames carry Layer 3 packets across a local link.
- Layer 2 devices use **MAC addresses** to identify the sender and receiver of an Ethernet frame.
- Switches automatically learn where devices are located by examining the **source MAC address** of received frames.
- A switch either **forwards** a known unicast frame or **floods** an unknown unicast frame.

---

## 1. OSI Model Refresher

### Layer 1 - Physical Layer
The Physical Layer defines the physical characteristics of the medium used to transfer data between devices.

Examples include:
- Voltage levels
- Maximum transmission distances
- Physical connectors
- Cable specifications

At Layer 1, digital bits are converted into electrical signals for wired connections or radio signals for wireless connections.

### Layer 2 - Data Link Layer
The Data Link Layer:
- Provides **node-to-node connectivity** and data transfer.
- Defines how data is formatted for transmission over the physical medium.
- Detects and may correct Physical Layer errors.
- Uses **Layer 2 addressing**, separate from Layer 3 addressing.
- Is the layer at which Ethernet switches operate.

> [!important] CCNA Focus
> Switches operate at **Layer 2** and make forwarding decisions using **MAC addresses**.

---

## 2. Protocol Data Units (PDUs)

As data is encapsulated, each layer adds information.

| Layer | PDU |
|---|---|
| Upper layers | Data |
| Layer 4 | Segment |
| Layer 3 | Packet |
| Layer 2 | Frame |

At Layer 2, the packet receives an **L2 header** and an **L2 trailer**, producing an Ethernet frame.

---

## 3. Ethernet Frame Structure

The Ethernet frame fields covered in this lesson are:

| Field | Length | Purpose |
|---|---:|---|
| Preamble | 7 bytes | Synchronizes the receiver's clock |
| SFD | 1 byte | Marks the end of the preamble and beginning of the rest of the frame |
| Destination MAC | 6 bytes | Identifies the receiving device |
| Source MAC | 6 bytes | Identifies the sending device |
| Type / Length | 2 bytes | Indicates the encapsulated protocol or payload length |
| FCS | 4 bytes | Detects corrupted data using CRC |

The slide totals these header/trailer fields as **26 bytes** when the Preamble and SFD are included in the count presented in the lesson.

### Preamble
- Length: **7 bytes / 56 bits**
- Pattern: `10101010` repeated seven times
- Allows receiving devices to synchronize their receiver clocks

### Start Frame Delimiter (SFD)
- Length: **1 byte / 8 bits**
- Pattern: `10101011`
- Marks the end of the preamble and the beginning of the rest of the frame

> [!warning] Exam Trap
> **Preamble** provides receiver clock synchronization. The **SFD** marks where the actual frame begins after the preamble.

### Destination and Source MAC Fields
Both are **6 bytes / 48 bits**.

- **Destination MAC** = intended receiver
- **Source MAC** = sender

A switch uses the **source MAC address** to learn entries for its MAC address table.

### Type / Length Field
Length: **2 bytes / 16 bits**.

According to the lesson:
- Value **1500 or less** = length of the encapsulated packet in bytes
- Value **1536 or greater** = type of encapsulated packet

Common EtherType values:
- IPv4 = `0x0800`
- IPv6 = `0x86DD`

### Frame Check Sequence (FCS)
- Length: **4 bytes / 32 bits**
- Detects corrupted data
- Uses **CRC (Cyclic Redundancy Check)**

---

## 4. MAC Addresses

A MAC address is a **6-byte / 48-bit physical address** assigned to a device.

The lesson describes it as:
- Also called a **Burned-In Address (BIA)**
- Globally unique
- Written as **12 hexadecimal characters**

Example:

`E8BA.7011.2874`

### MAC Address Structure

A MAC address is split into two 24-bit halves:

1. **OUI - Organizationally Unique Identifier**
   - First 3 bytes / 24 bits
   - Assigned to the company that makes the device

2. **Device-specific portion**
   - Last 3 bytes / 24 bits
   - Unique to that particular device

For `E8BA.7011.2874`, the OUI is:

`E8BA.70`

---

## 5. Hexadecimal Refresher

Hexadecimal uses 16 symbols:

`0 1 2 3 4 5 6 7 8 9 A B C D E F`

Where:
- A = 10
- B = 11
- C = 12
- D = 13
- E = 14
- F = 15

MAC addresses are represented in hexadecimal because 48 binary bits can be written much more compactly as 12 hexadecimal characters.

---

## 6. How a Switch Learns MAC Addresses

A switch builds a **MAC address table** dynamically.

### Core Rule
When a frame enters a switch, the switch looks at the **source MAC address** and associates it with the interface on which the frame arrived.

Example:

If a frame arrives on `F0/1` with source MAC `AAAA.AA00.0001`, the switch learns:

| MAC Address | Interface |
|---|---|
| AAAA.AA00.0001 | F0/1 |

This is called a **dynamically learned MAC address** or **dynamic MAC address**.

> [!important] Memorize This
> **Learn from the SOURCE MAC. Forward based on the DESTINATION MAC.**

---

## 7. Unknown Unicast vs Known Unicast

### Unicast Frame
A **unicast frame** is destined for one specific target device.

### Unknown Unicast
An unknown unicast occurs when:
- The destination is a single device, but
- The destination MAC address is **not yet in the switch's MAC address table**.

The switch **floods** the frame out of all interfaces except the interface on which it was received.

Example:

PC1 sends to PC2:
- Source = `.0001`
- Destination = `.0002`
- Switch learns `.0001` on the incoming port
- If `.0002` is unknown, the frame is flooded to the other ports
- Devices that are not the destination discard the frame

### Known Unicast
A known unicast occurs when the destination MAC address is already in the switch's MAC address table.

The switch forwards the frame **only through the interface associated with the destination MAC address**.

Example table:

| MAC | Interface |
|---|---|
| `.0001` | F0/1 |
| `.0002` | F0/2 |

A frame destined for `.0001` can be forwarded directly out `F0/1`.

### Quick Decision Table

| Destination MAC Status | Switch Action |
|---|---|
| Known in MAC table | Forward out the matching interface |
| Unknown in MAC table | Flood out all interfaces except incoming interface |

---

## 8. MAC Learning Across Multiple Switches

With multiple switches, each switch builds its **own** MAC address table.

If PC1 sends a frame to PC3 through SW1 and SW2:

1. **SW1** receives the frame from PC1.
2. SW1 learns PC1's source MAC on its PC1-facing interface.
3. If PC3 is unknown, SW1 floods the frame, including toward SW2.
4. **SW2** receives the frame from SW1.
5. SW2 learns PC1's source MAC on its interface connected to SW1.
6. If PC3 is unknown to SW2, SW2 floods the frame toward its other interfaces.
7. PC3 receives the frame; other hosts discard it.
8. When PC3 replies, both switches learn PC3's MAC from the **source MAC** of the returning frame.

This is how switches gradually learn the topology of Layer 2 devices without manual configuration.

---

## 9. Dynamic MAC Address Aging

The lesson states that dynamically learned MAC addresses are removed from the MAC address table after **5 minutes of inactivity**.

This allows the switch to remove stale information and relearn a device if it moves to a different interface.

---

## 10. High-Yield CCNA Facts

> [!tip] Must Know
> - Switches operate at **Layer 2**.
> - Layer 2 PDU = **Frame**.
> - MAC address = **48 bits / 6 bytes**.
> - MAC addresses are written as **12 hexadecimal characters**.
> - OUI = **first 24 bits / first half** of a MAC address.
> - Preamble = **7 bytes**, receiver clock synchronization.
> - SFD = **1 byte**, marks the end of the preamble.
> - Destination MAC field = **6 bytes**.
> - Source MAC field = **6 bytes**.
> - Type/Length field = **2 bytes**.
> - FCS = **4 bytes**, error detection using CRC.
> - Switches learn from the **source MAC address**.
> - Switches forward based on the **destination MAC address**.
> - **Unknown unicast = flood**.
> - **Known unicast = forward only to the matching port**.
> - Dynamic MAC entries age out after **5 minutes of inactivity** in this lesson.

---

## 11. Mental Model

Think of a switch like a receptionist learning where people sit:

- A frame arrives from Bob at desk 1 -> the switch learns **Bob = Port 1**.
- The frame is addressed to Alice, but the switch does not know Alice's desk -> it asks everywhere except Bob's desk (**flood**).
- Alice replies from desk 2 -> the switch learns **Alice = Port 2**.
- Future traffic for Alice goes directly to Port 2 (**known unicast forwarding**).

The switch learns **who is behind a port by looking at who sent the frame**, not who the frame is addressed to.

---

## 12. Self-Test

1. Which Ethernet field provides receiver clock synchronization?
2. What is the purpose of the SFD?
3. How many bits are in a MAC address?
4. Which half of a MAC address contains the OUI?
5. Which Ethernet frame field does a switch use to populate its MAC address table?
6. What does a switch do with an unknown unicast frame?
7. What does a switch do with a known unicast frame?
8. What PDU name is used at Layer 2?
9. What protocol does the FCS use to detect corrupted frames?
10. After how much inactivity does the lesson say a dynamic MAC entry is removed?

### Answers
1. Preamble
2. Marks the end of the preamble and beginning of the rest of the frame
3. 48 bits
4. First 24 bits / first half
5. Source MAC address
6. Floods it out all interfaces except the incoming interface
7. Forwards it only through the interface associated with the destination MAC
8. Frame
9. CRC (Cyclic Redundancy Check)
10. 5 minutes

---

## Related Notes
- OSI Model
- Ethernet Frame
- MAC Addresses
- LAN Switching
- VLANs
