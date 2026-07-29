---
title: "EIGRP Terminology and Unequal-Cost Load Balancing"
aliases:
  - EIGRP Terms
  - EIGRP Feasibility Condition
  - EIGRP Variance
tags:
  - ccna
  - routing
  - eigrp
  - feasible-distance
  - reported-distance
  - successor
  - feasible-successor
  - variance
  - unequal-cost-load-balancing
source: "CCNA 200-301 Day 25 Extra - EIGRP Terms"
date: 2026-07-27
---

# EIGRP Terminology and Unequal-Cost Load Balancing

## Summary

EIGRP identifies the best path as the **successor** and can keep qualifying backup paths as **feasible successors**. A backup path must satisfy the **feasibility condition** before EIGRP can trust it as loop-free.

The `variance` command can then allow feasible successors with higher metrics to join the routing table for unequal-cost load balancing.

> [!important] The two tests are separate
> A path must first pass the **feasibility condition** to become a feasible successor. It must then fall within the configured **variance multiplier** to be used for unequal-cost load balancing.

---

## EIGRP metric

By default, EIGRP calculates its composite metric using:

- The bandwidth of the **slowest link** in the path
- The combined delay of **all links** in the path

The full metric formula uses K-values:

```text
([K1 * bandwidth
  + (K2 * bandwidth) / (256 - load)
  + K3 * delay]
  * [K5 / (reliability + K4)])
  * 256
```

The default K-values are:

```text
K1 = 1
K2 = 0
K3 = 1
K4 = 0
K5 = 0
```

With the defaults, bandwidth and delay are the active metric components. The slides simplify the idea as:

```text
EIGRP metric = bandwidth + delay
```

Conceptually:

```text
slowest-path bandwidth + total path delay
```

> [!note]
> The displayed EIGRP metric is a calculated composite value. The important CCNA point is that the lowest metric wins and that bandwidth and delay are used by default.

---

## Core EIGRP terminology

### Feasible distance

**Feasible Distance (FD)** is the local router's total EIGRP metric to reach the destination through a particular path.

Think:

```text
What does the entire route cost from me to the destination?
```

The successor's feasible distance is the best metric currently known for that destination.

### Reported distance

**Reported Distance (RD)**, also called **Advertised Distance (AD)**, is the neighbor's metric from itself to the destination.

Think:

```text
How far does my neighbor say it is from the destination?
```

Do not confuse EIGRP's advertised distance with **administrative distance**. They share the abbreviation AD in some materials but describe different values:

- EIGRP advertised distance = the neighbor's metric to the destination
- Administrative distance = the trust ranking of a route source, such as EIGRP internal AD 90

### Successor

The **successor** is the path with the lowest feasible distance.

It is:

- The best route to the destination
- Installed in the IP routing table
- Used to forward traffic

### Feasible successor

A **feasible successor** is an alternate path that:

- Is not currently the best path
- Passes the feasibility condition
- Is considered a safe, loop-free backup

A route is not a feasible successor merely because it is the second-best metric. It must satisfy the feasibility condition.

---

## The feasibility condition

An alternate route becomes a feasible successor when:

```text
Alternate route's RD < successor route's FD
```

Or:

```text
Neighbor's reported distance < my best total distance
```

### Why this protects against loops

If a neighbor reports that it is closer to the destination than the local router's current best total distance, EIGRP can safely treat that neighbor as progressing toward the destination rather than looping traffic back.

### Memory aid

```text
RD < successor FD
```

Say it as:

> The neighbor must claim a distance lower than my current best distance.

The comparison uses:

- The alternate route's **reported distance**
- The current successor's **feasible distance**

It does not compare the alternate route's full feasible distance against the successor FD.

---

## Numeric example from the slides

EIGRP knows two paths to `192.168.4.0/24`:

```text
P 192.168.4.0/24, 1 successors, FD is 28672
  via 10.0.12.2 (28672/28416), GigabitEthernet0/0
  via 10.0.13.2 (30976/28416), FastEthernet1/0
```

For EIGRP topology entries:

```text
(feasible distance / reported distance)
```

### Path through `10.0.12.2`

```text
FD = 28672
RD = 28416
```

This is the successor because it has the lowest total metric.

### Path through `10.0.13.2`

```text
FD = 30976
RD = 28416
```

Test the alternate path against the successor:

```text
Alternate RD < successor FD
28416       < 28672
```

The condition is true, so the path through `10.0.13.2` is a **feasible successor**.

> [!important]
> The alternate path's full FD is 30976, which is higher than the successor's 28672. That is acceptable. The feasibility test uses the alternate path's RD of 28416.

---

## Successor versus feasible successor

| Term | Meaning | Installed by default? |
|---|---|---|
| Successor | Best path with the lowest FD | Yes |
| Feasible successor | Loop-free alternate that passes `RD < successor FD` | No, unless it is equal-cost or selected by variance |

The feasible successor is immediately useful as a backup. If the successor fails, EIGRP may promote the feasible successor without first searching the network for a new route.

---

## Equal-cost load balancing

By default, EIGRP's variance is 1:

```text
EIGRP maximum metric variance 1
```

Variance 1 allows only paths with the same metric as the successor to be installed together. This is Equal-Cost Multi-Path load balancing.

In the example:

```text
Successor FD         = 28672
Feasible successor FD = 30976
```

Because `30976` is not equal to `28672`, only the successor is installed when variance is 1.

---

## Unequal-cost load balancing

EIGRP is the only IGP covered in the course that can perform unequal-cost load balancing.

Configure the variance multiplier under the EIGRP process:

```cisco
router eigrp 100
 variance 2
```

IOS accepts a variance value from 1 through 128:

```text
variance 1-128
```

### Variance rule

A feasible successor is eligible for load balancing when:

```text
Feasible successor FD <= successor FD * variance
```

The slides phrase this as feasible-successor routes with an FD up to the multiplied successor FD.

### Example with variance 2

```text
Successor FD * variance
28672 * 2 = 57344
```

Now compare the feasible successor:

```text
30976 <= 57344
```

The path qualifies, so both routes can be installed:

```text
D 192.168.4.0/24 [90/28672] via 10.0.12.2
                    [90/30976] via 10.0.13.2
```

The routes have different metrics, which confirms that EIGRP is performing unequal-cost load balancing.

---

## Variance never overrides the feasibility condition

EIGRP performs unequal-cost load balancing only across **feasible successor** routes.

The complete logic is:

```text
1. Is the route a feasible successor?
   Alternate RD < successor FD

2. Is its FD inside the variance range?
   Alternate FD <= successor FD * variance

3. If both are true, it can be installed for load balancing.
```

If an alternate route fails the feasibility condition, EIGRP will not use it for load balancing regardless of how high the variance is configured.

> [!warning]
> Increasing variance does not turn every alternate route into a load-balancing path. Feasibility is always checked first.

---

## Decision flow

```text
Find the route with the lowest FD
            |
            v
     Make it the successor
            |
            v
For each alternate, is RD < successor FD?
       |                     |
      No                    Yes
       |                     |
Not a feasible         Feasible successor
successor                    |
                             v
             Is alternate FD within variance?
                    |                |
                   No               Yes
                    |                |
              Backup only      Install for load
                                balancing
```

---

## Verification

### View the EIGRP topology table

```cisco
show ip eigrp topology
```

Look for:

- Destination prefix
- Number of successors
- Successor FD
- Each path's `(FD/RD)` pair
- Paths that pass the feasibility condition

### View protocol settings

```cisco
show ip protocols
```

Look for:

```text
EIGRP maximum metric variance 1
```

After configuring `variance 2`, verify that the displayed variance changes.

### View installed routes

```cisco
show ip route
```

If unequal-cost load balancing is active, the EIGRP route can list multiple next hops with different metrics.

---

## Worked checklist

When asked whether an alternate EIGRP route will be used:

1. Identify the successor and write down its FD.
2. Write down the alternate path's RD.
3. Test `alternate RD < successor FD`.
4. If false, stop: the route can never be selected by variance.
5. If true, the route is a feasible successor.
6. Multiply the successor FD by the configured variance.
7. Compare the alternate FD with that result.
8. If the alternate FD is within the range, it can join the routing table.

### Applied to the slide values

```text
Successor FD = 28672
Alternate FD = 30976
Alternate RD = 28416
Variance     = 2
```

Feasibility:

```text
28416 < 28672 = true
```

Variance:

```text
28672 * 2 = 57344
30976 <= 57344 = true
```

Result:

```text
The alternate is a feasible successor and can be used for
unequal-cost load balancing.
```

---

## Exam takeaways

- EIGRP uses bandwidth and delay in its metric by default.
- Feasible distance is the local router's total metric to a destination.
- Reported distance is the neighbor's metric to that destination.
- Reported distance is also called advertised distance.
- The successor is the best route with the lowest feasible distance.
- A feasible successor is a loop-free alternate route that passes the feasibility condition.
- The feasibility condition is `alternate RD < successor FD`.
- Default variance 1 permits only equal-cost load balancing.
- Variance multiplies the successor FD to define the eligible metric range.
- A route must be a feasible successor before variance can select it.
- A high variance never overrides the feasibility condition.
- Multiple installed `D` routes with different metrics indicate EIGRP unequal-cost load balancing.

## Related notes

- [RIP & EIGRP - Configuration and Concepts](<RIP & EIGRP - Configuration and Concepts.md>)
- [Dynamic Routing - Fundamentals](<../Dynamic Routing/Dynamic Routing - Fundamentals.md>)
