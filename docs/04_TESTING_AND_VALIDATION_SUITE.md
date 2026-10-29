# 04. Testing and Validation Suite

This document defines the acceptance criteria and exact command sequence required to validate the AWS VPC Peering architecture.

---

## Acceptance Test Matrix (From Page 11 of Workbook)

| Test ID | Test Name | Execution Location & Command | Expected Result | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- |
| **01** | **Baseline (Pre-Peering)** | `ssh ewb-app-a`<br>`ping -c 4 10.20.1.10` | 100% packet loss (0 replies) | Proves VPCs are completely isolated by default before peering. |
| **02** | **Forward Path** | `ssh ewb-app-a`<br>`ping -c 4 10.20.1.10` | 4 replies; 0% packet loss | Proves VPC A can route packets to VPC B across peering link. |
| **03** | **Reverse Path** | `ssh ewb-app-b`<br>`ping -c 4 10.10.2.10` | 4 replies; 0% packet loss | Proves VPC B can route return & outbound packets to VPC A. |
| **04** | **Private SSH** | Local Laptop:<br>`ssh ewb-app-b` | Shell prompt on App-B | Proves ProxyJump routing via Bastion across peering. |
| **05** | **Public Isolation** | AWS Console / CLI Details | Public IPv4 is null/empty | Proves App-A & App-B are not exposed to internet. |

---

## Detailed Step-by-Step Execution

### Test 01: Baseline Negative Test (Before Peering Routes)
Before adding the routes pointing to `pcx-xxxxxx`, connect to App-A and test connectivity to App-B:

```bash
# On your local machine:
ssh ewb-app-a

# Inside App-A:
hostname
hostname -I
ping -c 4 10.20.1.10
```

**Expected Terminal Output:**
```
PING 10.20.1.10 (10.20.1.10) 56(84) bytes of data.

--- 10.20.1.10 ping statistics ---
4 packets transmitted, 0 received, 100% packet loss, time 3072ms
```
> 📸 **Capture Screenshot 01:** Save this output showing 100% packet loss as proof of initial network isolation.

---

### Test 02: Forward Path Reachability Test (After Route Addition)
Once peering routes are added to `ewb-rt-a-private` and `ewb-rt-b-private`:

```bash
# Inside App-A:
ping -c 4 10.20.1.10
```

**Expected Terminal Output:**
```
PING 10.20.1.10 (10.20.1.10) 56(84) bytes of data.
64 bytes from 10.20.1.10: icmp_seq=1 ttl=255 time=0.812 ms
64 bytes from 10.20.1.10: icmp_seq=2 ttl=255 time=0.745 ms
64 bytes from 10.20.1.10: icmp_seq=3 ttl=255 time=0.760 ms
64 bytes from 10.20.1.10: icmp_seq=4 ttl=255 time=0.732 ms

--- 10.20.1.10 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 3065ms
rtt min/avg/max/mdev = 0.732/0.762/0.812/0.030 ms
```
> 📸 **Capture Screenshot 02:** Save terminal output showing 0% packet loss from App-A to App-B.

---

### Test 03: Reverse Path Reachability Test
Connect to App-B and test connectivity back to App-A:

```bash
# On local machine:
ssh ewb-app-b

# Inside App-B:
hostname
hostname -I
ping -c 4 10.10.2.10
```

**Expected Terminal Output:**
```
PING 10.10.2.10 (10.10.2.10) 56(84) bytes of data.
64 bytes from 10.10.2.10: icmp_seq=1 ttl=255 time=0.789 ms
64 bytes from 10.10.2.10: icmp_seq=2 ttl=255 time=0.751 ms
64 bytes from 10.10.2.10: icmp_seq=3 ttl=255 time=0.748 ms
64 bytes from 10.10.2.10: icmp_seq=4 ttl=255 time=0.763 ms

--- 10.10.2.10 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 3068ms
rtt min/avg/max/mdev = 0.748/0.762/0.789/0.016 ms
```
> 📸 **Capture Screenshot 03:** Save terminal output showing 0% packet loss from App-B to App-A.

---

### Test 04: Controlled Failure & Recovery Experiment
This test proves that security groups actively filter traffic even when routing is intact.

1. **Simulate Failure:**
   * Go to AWS EC2 Console > **Security Groups** > Select `ewb-sg-app-b`.
   * Click **Edit inbound rules**.
   * Delete or temporarily disable the **Custom ICMP - IPv4 Echo request** rule from `10.10.2.10/32`.
   * Click **Save rules**.
2. **Execute Test from App-A:**
   ```bash
   ssh ewb-app-a
   ping -c 4 10.20.1.10
   ```
   *Result:* Ping hangs and reports **100% packet loss**.
   > 📸 **Capture Screenshot 04A:** Controlled failure proof.
3. **Simulate Recovery:**
   * Re-add the rule to `ewb-sg-app-b`:
     * Type: `Custom ICMP - IPv4` | Protocol: `ICMP` | Port range: `Echo Request` | Source: `10.10.2.10/32`
   * Click **Save rules**.
4. **Re-execute Test from App-A:**
   ```bash
   ping -c 4 10.20.1.10
   ```
   *Result:* Ping immediately succeeds with **0% packet loss**.
   > 📸 **Capture Screenshot 04B:** Recovery proof.
