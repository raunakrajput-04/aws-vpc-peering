# 05. Viva & Interview Defense Guide

This document contains deep, architect-level explanations for the four viva questions asked on Page 12 of the EWB Cloud Labs workbook, plus key networking principles required to defend your project.

---

## Question 1: Why is the return route needed?

### In-Depth Answer:
Network communication operates as a **two-way conversation** (bidirectional packet exchange):
1. When `App-A` (`10.10.2.10`) sends an ICMP Echo Request or TCP SYN packet to `App-B` (`10.20.1.10`), the route table associated with `App-A` (`ewb-rt-a-private`) inspects the destination IP `10.20.1.10`. Finding the matching CIDR prefix `10.20.0.0/16`, it forwards the frame across the peering connection (`pcx-xxxxxx`).
2. When the packet arrives at `App-B`, the operating system generates an **ICMP Echo Reply** (or TCP SYN-ACK). In this reply packet:
   * **Source IP:** `10.20.1.10`
   * **Destination IP:** `10.10.2.10`
3. AWS VPC routing is **hop-by-hop and stateless**. VPC B's virtual router consults `App-B`'s route table (`ewb-rt-b-private`) to determine how to reach destination `10.10.2.10`.
4. If `ewb-rt-b-private` does not contain an explicit entry for `10.10.0.0/16 -> pcx-xxxxxx`, the router has no valid path and immediately **drops the reply packet (black-holes it)**.

> **Key takeaway:** A peering connection is only a layer-3 pipeline. Traffic cannot flow unless both the forward route AND the return route are explicitly programmed in the respective route tables.

---

## Question 2: Why is the App-B SSH source the bastion private IP?

### In-Depth Answer:
When connecting via SSH from your laptop using `ProxyJump`:
1. Your laptop initiates a standard SSH connection to the Bastion host's public IP on port 22 (`Admin Laptop -> Internet Gateway -> ewb-bastion`).
2. Inside this connection, the SSH client uses the `-W` flag / channel forwarding mechanism. The Bastion host opens a fresh, local TCP connection from its private network interface (`10.10.1.10`) targeted at App-B's private IP (`10.20.1.10:22`).
3. From the perspective of AWS networking and the operating system kernel on `App-B`:
   * The incoming IP packet's **Layer 3 Source IPv4 header contains `10.10.1.10`** (the Bastion's private IP), NOT your laptop's external public IP.
4. Because the Bastion is in a peered VPC and routes across `pcx-xxxxxx`, App-B's security group (`ewb-sg-app-b`) must whitelist the exact sender of that TCP packet: `10.10.1.10/32`.

---

## Question 3: Why does Active peering not guarantee a successful ping?

### In-Depth Answer:
An **Active** status on an AWS VPC Peering connection simply means that:
* The requester VPC sent an invitation.
* The accepter VPC approved the handshake.
* The physical/virtual point-to-point link has been provisioned by the AWS Hyperplane/SDN infrastructure.

However, end-to-end packet delivery depends on **four independent layers of configuration**, all of which must be correctly aligned:
1. **Routing Layer (Route Tables):** Both VPCs must have explicit route table entries pointing to the peering connection ID (`pcx-xxxxxx`). Without these, packets are discarded at the VPC router.
2. **Firewall Layer 1 (Security Groups):** SGs are stateful firewalls at the ENI (instance) level. The destination instance's SG must explicitly allow inbound ICMP (Echo Request) from the sender's IP.
3. **Firewall Layer 2 (Network ACLs):** Subnet-level stateless firewalls must allow inbound ICMP and outbound ephemeral/reply traffic.
4. **Operating System Layer:** The target EC2 instance's OS kernel must be running, the network interface active, and internal firewalls (e.g., `iptables` or `nftables`) must not drop ICMP.

---

## Question 4: Can VPC B use VPC A's internet gateway over peering?

### In-Depth Answer:
**No. AWS VPC Peering is strictly non-transitive and does NOT support edge-to-edge routing or transit routing.**

### Architectural Reasons:
1. **Non-Transitivity:** VPC Peering only connects two endpoints directly: `VPC A <--> VPC B`. Traffic cannot "hop" through VPC A to reach a third entity (such as the Internet Gateway, a Virtual Private Gateway, a Direct Connect circuit, or a third VPC C).
2. **AWS Routing Limitation:** An Internet Gateway attached to VPC A can only route packets whose source IP belongs to VPC A's CIDR (`10.10.0.0/16`). It will reject or drop packets originating from VPC B (`10.20.0.0/16`).
3. **Enterprise Alternative:** If VPC B requires centralized outbound internet egress through VPC A, an architect must deploy:
   * **AWS Transit Gateway (TGW)** with centralized NAT Gateways, OR
   * A proxy server (e.g., Squid / Envoy / NAT instance) residing in VPC A that terminates connections and performs Source NAT (SNAT).

---

## 5. Summary Cheat Sheet for Viva

| Principle | VPC Peering Behavior |
| :--- | :--- |
| **Transitivity** | **Non-transitive** (A-B + A-C != B-C) |
| **Bandwidth Limits** | No aggregate bandwidth limit; scales to EC2 instance limits |
| **Latency** | Single-digit millisecond latency; no single-point-of-failure bottleneck |
| **Encryption** | Encrypted in transit across AWS backbone without traversing public internet |
| **Cross-Account / Region** | Fully supported across different AWS accounts and regions |
