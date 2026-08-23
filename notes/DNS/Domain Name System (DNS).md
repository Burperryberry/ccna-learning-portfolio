---
tags: [ccna, dns, ip-services, day-38]
topic: DNS
course-day: 38
blueprint-domain: 4.0 IP Services
status: learning
---

# Domain Name System (DNS)

## One-sentence purpose

DNS is a distributed, hierarchical naming system that maps human-readable names to resource records such as IPv4 and IPv6 addresses.

## CCNA essentials

- A **stub resolver** on the client sends a recursive query to its configured DNS resolver.
- A **recursive resolver** obtains or retrieves the answer on the client's behalf and caches it for the record's TTL.
- **Root servers** direct the resolver toward the correct top-level-domain servers.
- **TLD servers** direct it toward the authoritative servers for the requested domain.
- An **authoritative server** holds the zone data and returns authoritative answers.
- DNS normally uses **UDP port 53** for ordinary queries and responses.
- DNS can use **TCP port 53** for cases such as responses requiring TCP, explicit TCP queries, and zone transfers.
- Caching reduces latency and load. The **TTL** tells a cache how long a record may be retained.

## Resolution flow

1. An application asks the local resolver for a name.
2. The client checks local information/cache, then queries its configured recursive resolver.
3. If the resolver has a valid cached answer, it returns it immediately.
4. Otherwise, the resolver follows referrals through root, TLD, and authoritative name servers.
5. The authoritative answer returns to the resolver, which caches it according to TTL and replies to the client.

The client typically requests recursion from its resolver. The resolver's work across the DNS hierarchy is commonly described as iterative because each referral points it toward the next server.

## Record types

| Type | Purpose | Memory cue |
|---|---|---|
| A | Name to IPv4 address | **A**ddress (IPv4) |
| AAAA | Name to IPv6 address | Four times the address space label |
| CNAME | Alias to canonical name | **C**anonical name |
| MX | Mail exchanger for a domain | **M**ail e**x**changer |
| NS | Authoritative name server for a zone | **N**ame **s**erver |
| PTR | Address to name, used for reverse lookups | **P**oin**t**e**r** back to a name |
| SOA | Zone authority and administrative parameters | **S**tart **o**f **a**uthority |
| TXT | Arbitrary text; often used for verification and email-policy data | Text |

## Message fields to recognize

- **Transaction ID:** matches a response to its query.
- **QR flag:** `0` for a query and `1` for a response.
- **Opcode:** type of DNS operation; a standard query is normally `0`.
- **AA:** the answer is authoritative.
- **TC:** the message was truncated; retrying over TCP may be necessary.
- **RD:** the client requests recursion.
- **RA:** the server says recursion is available.
- **RCODE:** response result, such as no error or NXDOMAIN.
- **Question/Answer counts:** identify the number of records in each section.

## Cisco IOS configuration and verification

```text
! Configure DNS servers for the device itself
ip name-server 192.0.2.53

! Allow hostname lookups (normally enabled by default)
ip domain lookup

! Configure a domain name; also used when creating RSA keys for SSH
ip domain name example.com

! Add a static host mapping
ip host server1 192.0.2.10

! Verify configured DNS-related settings
show running-config | include domain|name-server|ip host
show hosts
```

`no ip domain lookup` prevents unwanted DNS lookups after mistyped IOS commands, but it also disables hostname resolution by the device. Know the tradeoff rather than applying it blindly.

## macOS verification

```bash
dig example.com A
dig example.com AAAA
dig example.com NS
dig gmail.com MX
dig -x 1.1.1.1
dig +tcp example.com A
```

Use [the Day 38 DNS practical](<../Wireshark/CCNA Capture Workflow.md#dns-practical--day-38>) to correlate each command with packets.

## Failure patterns

| Symptom | Possible cause | First checks |
|---|---|---|
| IP connectivity works but names fail | Wrong/unreachable resolver or DNS failure | Verify configured resolver, ping its IP, then query it directly |
| One name returns an old address | Cached record or stale authoritative data | Inspect TTL and compare resolvers/authoritative answer |
| Name does not exist | Typo or NXDOMAIN response | Check RCODE and queried name |
| Large response fails over UDP | Truncation, firewall, or TCP/53 blocked | Check TC flag and test the same query with TCP |
| Reverse lookup fails | Missing/incorrect PTR record or reverse zone | Query with `dig -x` and inspect authority |

## Security connection

- DNS cache poisoning attempts to place false mappings into a resolver cache.
- DNS tunneling can encode command-and-control or exfiltrated data in queries/responses.
- Filtering only UDP/53 is incomplete because valid DNS also uses TCP/53.
- Encrypted DNS changes visibility, but the CCNA foundation is understanding conventional DNS roles and message flow first.

## Retrieval check

Answer these without looking above:

1. What is the difference between recursive and iterative resolution?
2. Put root, TLD, and authoritative servers in lookup order.
3. Which records provide IPv4, IPv6, aliases, mail servers, name servers, and reverse mappings?
4. Why does TTL matter?
5. Which flags identify query/response, recursion, authority, truncation, and the response result?
6. Why might DNS use TCP instead of UDP?
7. If pinging an IP works but pinging a hostname fails, where do you investigate first?

## Definition of done

- [ ] Explain the resolution flow in under two minutes.
- [ ] Identify A, AAAA, CNAME, MX, NS, PTR, and SOA from memory.
- [ ] Complete and interpret the DNS capture.
- [ ] Explain one caching failure and one transport-related failure.
- [ ] Create flashcards only for missed or slow answers.
