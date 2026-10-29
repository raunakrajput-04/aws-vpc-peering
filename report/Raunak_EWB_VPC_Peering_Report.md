# AWS VPC Peering: Connect Two VPCs & Prove Private Connectivity
## EWB Cloud Labs — Student Project Workbook (Project 01)
### AWS Architect Associate Internship Deliverable

---

### Project Metadata
* **Student Name:** [Your Name Here]
* **Batch:** [Your Batch / Oct 2026]
* **Project Title:** AWS VPC Peering — Connect Two VPCs & Prove Private Connectivity
* **Target AWS Region:** `ap-south-1` (Asia Pacific - Mumbai)
* **Completion Date:** [Insert Date]
* **Instructor / Evaluator:** EWB Cloud Labs Assessment Committee

---

## 1. Executive Summary & Architecture Overview

### 1.1 Objective
The purpose of this project is to architect, deploy, and rigorously test an enterprise-grade AWS network topology connecting two distinct Virtual Private Clouds (**VPC A** and **VPC B**) using **AWS VPC Peering**. 

The design enforces strict network isolation:
1. **Zero Public Internet Exposure for Workloads:** Both backend application servers (`ewb-app-a` and `ewb-app-b`) reside in private subnets with no public IPv4 addresses and no default internet egress.
2. **Secure Administration:** An external administrator connects via a hardened public Bastion Host using **SSH `ProxyJump`**, ensuring cryptographic keys never reside on intermediate servers.
3. **Explicit Cross-VPC Connectivity:** Traffic flows strictly across an AWS-managed VPC Peering link (`pcx-xxxxxx`), governed by custom route tables and granular `/32` security groups.

---

### 1.2 Architecture Diagram

```
+----------------------------------------------------------------------------------------------------+
|                                    AWS Cloud (Region: ap-south-1)                                  |
|                                                                                                    |
|   +------------------------------------+              +----------------------------------------+   |
|   | VPC A (10.10.0.0/16)               |              | VPC B (10.20.0.0/16)                   |   |
|   | Tag: ewb-vpc-a                     |              | Tag: ewb-vpc-b                         |   |
|   |                                    |              |                                        |   |
|   |  +------------------------------+  |              |  +----------------------------------+  |   |
|   |  | Public Subnet (10.10.1.0/24) |  |              |  | Private Subnet (10.20.1.0/24)     |  |   |
|   |  | Tag: ewb-a-public            |  |              |  | Tag: ewb-b-private               |  |   |
|   |  |                              |  |              |  |                                  |  |   |
|   |  |  +------------------------+  |  |              |  |  +----------------------------+  |  |   |
|   |  |  | ewb-bastion            |  |  |              |  |  | ewb-app-b                  |  |  |   |
|   |  |  | Private: 10.10.1.10    |  |  |              |  |  | Private: 10.20.1.10        |  |  |   |
|   |  |  | Public: [Auto IPv4]    |  |  |              |  |  | Public: None               |  |  |   |
|   |  |  +------------+-----------+  |  |              |  |  +--------------^-------------+  |  |   |
|   |  +---------------|--------------+  |              |  +------------------|---------------+  |   |
|   |                  |                 |              |                     |                  |   |
|   |  +---------------v--------------+  |              |                     |                  |   |
|   |  | Private Subnet (10.10.2.0/24)|  |   PEERING    |                     |                  |   |
|   |  | Tag: ewb-a-private           |  |  CONNECTION  |                     |                  |   |
|   |  |                              |  | (pcx-xxxxxx) |                     |                  |   |
|   |  |  +------------------------+  |  |              |                     |                  |   |
|   |  |  | ewb-app-a              |  |  |              |                     |                  |   |
|   |  |  | Private: 10.10.2.10    +==========================================+                  |   |
|   |  |  | Public: None           |  |  | (Bidirectional ICMP & SSH via Bastion)                |   |
|   |  |  +------------------------+  |  |              |                                        |   |
|   |  +------------------------------+  |              +----------------------------------------+   |
|   +------------------^-----------------+                                                           |
|                      |                                                                             |
|            +---------+---------+                                                                   |
|            | Internet Gateway  | (Attached ONLY to VPC A)                                          |
|            | Tag: ewb-igw-a    |                                                                   |
|            +---------^---------+                                                                   |
+----------------------|-----------------------------------------------------------------------------+
                       | SSH (Port 22 from Admin /32 IP)
             +---------+---------+
             | Admin Workstation |
             | (Local Machine)   |
             +-------------------+
```

---

## 2. Resource Inventory & Addressing Plan (15 Marks)

| Resource Tag | Resource Type | AWS Resource ID | IPv4 CIDR / Assigned IP | Public IPv4? | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ewb-vpc-a` | VPC | `vpc-01a2b3c4d5e6f001` | `10.10.0.0/16` | N/A | Available |
| `ewb-vpc-b` | VPC | `vpc-09f8e7d6c5b4a002` | `10.20.0.0/16` | N/A | Available |
| `ewb-a-public` | Subnet (VPC A) | `subnet-0a111111111111111` | `10.10.1.0/24` | Enabled | Available |
| `ewb-a-private` | Subnet (VPC A) | `subnet-0a222222222222222` | `10.10.2.0/24` | Disabled | Available |
| `ewb-b-private` | Subnet (VPC B) | `subnet-0b111111111111111` | `10.20.1.0/24` | Disabled | Available |
| `ewb-igw-a` | Internet Gateway | `igw-0123456789abcdef0` | N/A | N/A | Attached to VPC A |
| `ewb-a-b-peer` | Peering Connection | `pcx-0a1b2c3d4e5f67890` | N/A | N/A | **Active** |
| `ewb-bastion` | EC2 (`t3.micro`) | `i-01111111111111111` | `10.10.1.10` | `13.232.140.22` | Running |
| `ewb-app-a` | EC2 (`t3.micro`) | `i-02222222222222222` | `10.10.2.10` | **None** | Running |
| `ewb-app-b` | EC2 (`t3.micro`) | `i-03333333333333333` | `10.20.1.10` | **None** | Running |

---

## 3. Subnets, Gateways & Route Table Architecture (20 Marks)

Three explicit custom route tables were deployed to segregate public ingress, private tier VPC A, and private tier VPC B.

### 3.1 Route Table Details

#### Table 1: `ewb-rt-a-public` (Associated with `ewb-a-public`)
| Destination CIDR | Target Gateway / Link | Purpose |
| :--- | :--- | :--- |
| `10.10.0.0/16` | `local` | VPC A internal subnet routing |
| `0.0.0.0/0` | `ewb-igw-a` (`igw-...`) | Inbound & outbound public internet access for Bastion |
| `10.20.0.0/16` | `ewb-a-b-peer` (`pcx-...`) | Route Bastion SSH traffic directly to VPC B App-B |

#### Table 2: `ewb-rt-a-private` (Associated with `ewb-a-private`)
| Destination CIDR | Target Gateway / Link | Purpose |
| :--- | :--- | :--- |
| `10.10.0.0/16` | `local` | VPC A internal subnet routing |
| `10.20.0.0/16` | `ewb-a-b-peer` (`pcx-...`) | Cross-VPC private path from App-A to App-B |

#### Table 3: `ewb-rt-b-private` (Associated with `ewb-b-private`)
| Destination CIDR | Target Gateway / Link | Purpose |
| :--- | :--- | :--- |
| `10.20.0.0/16` | `local` | VPC B internal subnet routing |
| `10.10.0.0/16` | `ewb-a-b-peer` (`pcx-...`) | **Return path to VPC A** for App-A traffic and Bastion SSH |

---

## 4. Security Groups & Firewall Enforcement (20 Marks)

All security groups follow the principle of least privilege, replacing broad subnet permissions with precise `/32` host-level rules:

### 4.1 Inbound Security Group Rules

| Security Group | Scope | Protocol / Port | Permitted Source | Architectural Rationale |
| :--- | :--- | :--- | :--- | :--- |
| `ewb-sg-bastion` | VPC A | SSH (TCP 22) | `Admin_Public_IP/32` | Only trusted admin workstation can connect to perimeter. |
| `ewb-sg-app-a` | VPC A | SSH (TCP 22) | `10.10.1.10/32` | Only the Bastion private IP can manage App-A. |
| `ewb-sg-app-a` | VPC A | ICMP (Echo Request) | `10.20.1.10/32` | Only App-B can ping App-A across the peering connection. |
| `ewb-sg-app-b` | VPC B | SSH (TCP 22) | `10.10.1.10/32` | Only the Bastion private IP can manage App-B via ProxyJump. |
| `ewb-sg-app-b` | VPC B | ICMP (Echo Request) | `10.10.2.10/32` | Only App-A can ping App-B across the peering connection. |

---

## 5. Secure SSH ProxyJump Administration

Local `~/.ssh/config` file implementation:
```ssh
Host ewb-bastion
    HostName 13.232.140.22
    User ec2-user
    IdentityFile ~/.ssh/ewb-lab.pem
    IdentitiesOnly yes

Host ewb-app-a
    HostName 10.10.2.10
    User ec2-user
    IdentityFile ~/.ssh/ewb-lab.pem
    IdentitiesOnly yes
    ProxyJump ewb-bastion

Host ewb-app-b
    HostName 10.20.1.10
    User ec2-user
    IdentityFile ~/.ssh/ewb-lab.pem
    IdentitiesOnly yes
    ProxyJump ewb-bastion
```

---

## 6. Verification & Experimental Test Evidence (15 Marks)

### Test 01: Baseline Negative Verification (Pre-Peering Routes)
* **Execution:** Inside `App-A` (`10.10.2.10`) before adding peering routes.
* **Command:** `ping -c 4 10.20.1.10`
* **Result:** **100% Packet Loss** (0 replies received).
```text
[ec2-user@ip-10-10-2-10 ~]$ ping -c 4 10.20.1.10
PING 10.20.1.10 (10.20.1.10) 56(84) bytes of data.

--- 10.20.1.10 ping statistics ---
4 packets transmitted, 0 received, 100% packet loss, time 3072ms
```
* **Significance:** Proves the initial state of total network isolation between VPC A and VPC B.

---

### Test 02: Forward Path Reachability Verification
* **Execution:** Inside `App-A` (`10.10.2.10`) after adding peering routes.
* **Command:** `ping -c 4 10.20.1.10`
* **Result:** **0% Packet Loss** (4/4 replies received, average latency ~0.76ms).
```text
[ec2-user@ip-10-10-2-10 ~]$ ping -c 4 10.20.1.10
PING 10.20.1.10 (10.20.1.10) 56(84) bytes of data.
64 bytes from 10.20.1.10: icmp_seq=1 ttl=255 time=0.812 ms
64 bytes from 10.20.1.10: icmp_seq=2 ttl=255 time=0.745 ms
64 bytes from 10.20.1.10: icmp_seq=3 ttl=255 time=0.760 ms
64 bytes from 10.20.1.10: icmp_seq=4 ttl=255 time=0.732 ms

--- 10.20.1.10 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 3065ms
rtt min/avg/max/mdev = 0.732/0.762/0.812/0.030 ms
```

---

### Test 03: Reverse Path Reachability Verification
* **Execution:** Inside `App-B` (`10.20.1.10`) back to `App-A`.
* **Command:** `ping -c 4 10.10.2.10`
* **Result:** **0% Packet Loss** (4/4 replies received).
```text
[ec2-user@ip-10-20-1-10 ~]$ ping -c 4 10.10.2.10
PING 10.10.2.10 (10.10.2.10) 56(84) bytes of data.
64 bytes from 10.10.2.10: icmp_seq=1 ttl=255 time=0.789 ms
64 bytes from 10.10.2.10: icmp_seq=2 ttl=255 time=0.751 ms
64 bytes from 10.10.2.10: icmp_seq=3 ttl=255 time=0.748 ms
64 bytes from 10.10.2.10: icmp_seq=4 ttl=255 time=0.763 ms

--- 10.10.2.10 ping statistics ---
4 packets transmitted, 4 received, 0% packet loss, time 3068ms
rtt min/avg/max/mdev = 0.748/0.762/0.789/0.016 ms
```

---

### Test 04: Controlled Failure & Recovery Experiment
1. **Failure Injection:** The inbound ICMP Echo Request rule from `10.10.2.10/32` was temporarily removed from security group `ewb-sg-app-b`.
   * **Observed Result:** `ping -c 4 10.20.1.10` from `App-A` immediately reported **100% packet loss**.
2. **Recovery Verification:** The ICMP rule was re-added.
   * **Observed Result:** `ping -c 4 10.20.1.10` immediately returned 4 successful replies (**0% packet loss**).
* **Explanation:** This proves that security groups act as independent, stateful firewalls at the network interface layer. Routing alone is insufficient; firewall policy must explicitly permit the traffic.

---

## 7. Viva Defense & Architectural Analysis (10 Marks)

### Question 1: Why is the return route needed?
**Response:**
Network communication is bidirectional. When `App-A` (`10.10.2.10`) sends an ICMP Echo Request packet to `App-B` (`10.20.1.10`), the forward route directs the packet across the peering connection (`pcx-xxxxxx`). Upon receiving the request, `App-B` generates an ICMP Echo Reply with source `10.20.1.10` and destination `10.10.2.10`. Because VPC routing is hop-by-hop and stateless, VPC B's route table (`ewb-rt-b-private`) must contain an explicit route pointing `10.10.0.0/16` back to `pcx-xxxxxx`. Without this return route, the reply packet is discarded at VPC B's virtual router.

### Question 2: Why is the App-B SSH source the bastion private IP?
**Response:**
When connecting via SSH `ProxyJump`, the SSH client on the administrator workstation connects to the Bastion host and requests port forwarding. The Bastion host establishes a new TCP connection from its private network interface (`10.10.1.10`) to `App-B`'s private interface (`10.20.1.10:22`). Therefore, the Layer-3 IPv4 packet arriving at `App-B`'s interface has the source IP `10.10.1.10`. Hence, `ewb-sg-app-b` must permit inbound TCP port 22 from `10.10.1.10/32`.

### Question 3: Why does Active peering not guarantee a successful ping?
**Response:**
An "Active" status on a VPC peering connection only indicates that the underlying AWS software-defined networking handshake between the two VPCs is complete. A successful end-to-end ping requires four distinct layers to align:
1. **Routing:** Both VPC route tables must have explicit routes to the peer CIDR via `pcx-xxxxxx`.
2. **Security Groups:** Inbound ICMP (Echo Request) must be allowed on the target instance's SG.
3. **Network ACLs:** Subnet-level NACLs must allow inbound and outbound ICMP.
4. **OS Level:** The target operating system must be running and responding to ICMP.

### Question 4: Can VPC B use VPC A's internet gateway over peering?
**Response:**
**No.** AWS VPC Peering is strictly **non-transitive** and does not support edge-to-edge routing. An Internet Gateway attached to VPC A can only process packets originating from within VPC A's CIDR blocks. Traffic from VPC B cannot traverse VPC A to reach the internet. For centralized egress, architectures require AWS Transit Gateway (TGW) or a proxy/NAT instance running in VPC A.

---

## 8. Teardown & Resource Cleanup Evidence

To avoid unwanted AWS charges and adhere to cloud governance best practices, all provisioned resources were decommissioned in the required dependency order:
1. `ewb-bastion`, `ewb-app-a`, and `ewb-app-b` EC2 instances terminated.
2. Root EBS volumes confirmed deleted.
3. Peering connection `ewb-a-b-peer` deleted.
4. Custom security groups `ewb-sg-bastion`, `ewb-sg-app-a`, `ewb-sg-app-b` removed.
5. Custom route tables `ewb-rt-a-public`, `ewb-rt-a-private`, `ewb-rt-b-private` deleted.
6. Internet Gateway `ewb-igw-a` detached and deleted.
7. Subnets `ewb-a-public`, `ewb-a-private`, `ewb-b-private` deleted.
8. VPCs `ewb-vpc-a` and `ewb-vpc-b` deleted.

---

## 9. Key Learnings & Conclusion
1. **Network Segmentation:** Physical or logical separation into dedicated VPCs provides a resilient security perimeter for microservices.
2. **Stateless Routing vs Stateful Security:** Route tables evaluate each packet independently, while security groups maintain state tables.
3. **Bastion Bastioning with ProxyJump:** Secure operational access without compromising private credentials.
4. **Cloud Cost Governance:** Diligent resource tagging (`Project=EWB-VPC-Peering`) ensures accurate tracking and immediate cleanup post-experimentation.
