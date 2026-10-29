# 01. Architecture and IP Plan

## 1. Executive Summary & Mission
In an enterprise cloud ecosystem, applications frequently need to communicate privately across distinct VPCs without exposing network traffic to the public internet. This project establishes and validates a **high-security, isolated, bidirectional AWS VPC Peering connection** between:
1. **VPC A (`10.10.0.0/16`)**: Hosting an administration entry-point (Bastion Host) and an internal private microservice (`App-A`).
2. **VPC B (`10.20.0.0/16`)**: Hosting an isolated internal private workload (`App-B`) with zero direct internet access.

---

## 2. Network Topology & Architecture Diagram

```
+----------------------------------------------------------------------------------------------------+
|                                    AWS Cloud (Region: ap-south-1)                                  |
|                                                                                                    |
|   +------------------------------------+              +----------------------------------------+   |
|   | VPC A (10.10.0.0/16)               |              | VPC B (10.20.0.0/16)                   |   |
|   | Name: ewb-vpc-a                    |              | Name: ewb-vpc-b                        |   |
|   |                                    |              |                                        |   |
|   |  +------------------------------+  |              |  +----------------------------------+  |   |
|   |  | Public Subnet (10.10.1.0/24) |  |              |  | Private Subnet (10.20.1.0/24)     |  |   |
|   |  | Name: ewb-a-public           |  |              |  | Name: ewb-b-private              |  |   |
|   |  |                              |  |              |  |                                  |  |   |
|   |  |  +------------------------+  |  |              |  |  +----------------------------+  |  |   |
|   |  |  | ewb-bastion            |  |  |              |  |  | ewb-app-b                  |  |  |   |
|   |  |  | Private: 10.10.1.10    |  |  |              |  |  | Private: 10.20.1.10        |  |  |   |
|   |  |  | Public: <Elastic/Auto> |  |  |              |  |  | Public: None               |  |  |   |
|   |  |  +------------+-----------+  |  |              |  |  +--------------^-------------+  |  |   |
|   |  +---------------|--------------+  |              |  +------------------|---------------+  |   |
|   |                  |                 |              |                     |                  |   |
|   |  +---------------v--------------+  |              |                     |                  |   |
|   |  | Private Subnet (10.10.2.0/24)|  |   PEERING    |                     |                  |   |
|   |  | Name: ewb-a-private          |  |  CONNECTION  |                     |                  |   |
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
|            | Name: ewb-igw-a   |                                                                   |
|            +---------^---------+                                                                   |
+----------------------|-----------------------------------------------------------------------------+
                       | SSH (Port 22 from Admin /32 IP)
             +---------+---------+
             | Admin Workstation |
             | (Local Laptop)    |
             +-------------------+
```

---

## 3. Comprehensive IP & Resource Addressing Plan

| Resource / Tag Name | VPC Scope | Subnet / Type | IPv4 CIDR / Assigned IP | Public IPv4? | Purpose |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **ewb-vpc-a** | VPC A | N/A | `10.10.0.0/16` | N/A | Primary administration & App-A network |
| **ewb-a-public** | VPC A | Public Subnet | `10.10.1.0/24` | Yes (Auto-assign) | Ingress perimeter for bastion host |
| **ewb-a-private** | VPC A | Private Subnet | `10.10.2.0/24` | Disabled | Application A private tier |
| **ewb-vpc-b** | VPC B | N/A | `10.20.0.0/16` | N/A | Isolated secondary workload network |
| **ewb-b-private** | VPC B | Private Subnet | `10.20.1.0/24` | Disabled | Application B private tier |
| **ewb-bastion** | VPC A | ewb-a-public | `10.10.1.10` | Enabled (Auto IPv4) | SSH Jump Host (ProxyJump endpoint) |
| **ewb-app-a** | VPC A | ewb-a-private | `10.10.2.10` | Disabled (No public IP) | Workload A backend node |
| **ewb-app-b** | VPC B | ewb-b-private | `10.20.1.10` | Disabled (No public IP) | Workload B backend node |
| **ewb-igw-a** | VPC A | VPC Gateway | N/A | N/A | Route target `0.0.0.0/0` for public subnet |
| **ewb-a-b-peer** | VPC A & B | VPC Peering Link | N/A | N/A | Point-to-point private layer-3 AWS link |

---

## 4. CIDR Non-Overlap Justification
AWS VPC Peering strictly prohibits CIDR overlap:
* VPC A range: `10.10.0.0` to `10.10.255.255` (Total 65,536 addresses).
* VPC B range: `10.20.0.0` to `10.20.255.255` (Total 65,536 addresses).
* Both CIDRs are mutually exclusive RFC 1918 private subnets.
* The `/24` subnets inside each VPC are fully non-overlapping subsets:
  * Subnet A Public: `10.10.1.0/24` (Hosts 10.10.1.1 - 10.10.1.254)
  * Subnet A Private: `10.10.2.0/24` (Hosts 10.10.2.1 - 10.10.2.254)
  * Subnet B Private: `10.20.1.0/24` (Hosts 10.20.1.1 - 10.20.1.254)
