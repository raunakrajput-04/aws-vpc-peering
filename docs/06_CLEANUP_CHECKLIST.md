# 06. Cleanup Checklist & Cost Control

Following Page 14 of the EWB Cloud Labs workbook, AWS resources left running (such as EC2 instances, EBS volumes, and public IPv4 addresses) incur ongoing charges. Follow this checklist to ensure complete teardown.

---

## Teardown Order of Operations

To prevent dependency deadlock in AWS, delete resources in the exact reverse order of creation:

```
[1. EC2 Instances] 
       ↓ (Wait for termination)
[2. VPC Peering Connection] 
       ↓ 
[3. Security Groups] 
       ↓ 
[4. Custom Route Tables] 
       ↓ 
[5. Internet Gateway (Detach & Delete)] 
       ↓ 
[6. Subnets] 
       ↓ 
[7. VPCs]
```

---

## Step-by-Step Cleanup Guide

### Option A: Automated Cleanup (Recommended)
If you used the automated Python script:
```bash
py -3 scripts/cleanup_aws.py
```
Type `yes` when prompted. The script automatically handles dependency ordering.

---

### Option B: Manual Console Cleanup

#### 1. Compute & Storage Teardown
* Open **EC2 Console** > **Instances**.
* Select `ewb-bastion`, `ewb-app-a`, and `ewb-app-b`.
* Click **Instance state** > **Terminate instance**.
* Go to **Volumes** (under Elastic Block Store). Verify no orphaned volumes remain in `available` state.
* Go to **Elastic IPs** (under Network & Security). Release any Elastic IPs if created.

#### 2. VPC Peering Teardown
* Go to **VPC Console** > **Peering connections**.
* Select `ewb-a-b-peer` > Click **Actions** > **Delete VPC peering connection**.
* Check the box to delete associated route table entries automatically > Confirm.

#### 3. Security Groups Teardown
* Wait for EC2 instances to reach `terminated` state (network interfaces released).
* Go to **Security Groups**.
* Select `ewb-sg-bastion`, `ewb-sg-app-a`, and `ewb-sg-app-b`.
* Click **Actions** > **Delete security groups**.

#### 4. Route Tables & Internet Gateway
* Go to **Route tables**. Select `ewb-rt-a-public`, `ewb-rt-a-private`, `ewb-rt-b-private` > **Delete route table**.
* Go to **Internet gateways**. Select `ewb-igw-a` > **Actions** > **Detach from VPC** > **Delete internet gateway**.

#### 5. Subnets & VPCs
* Go to **Subnets**. Select `ewb-a-public`, `ewb-a-private`, `ewb-b-private` > **Delete subnet**.
* Go to **Your VPCs**. Select `ewb-vpc-a` and `ewb-vpc-b` > **Actions** > **Delete VPC**. Type `delete` to confirm.

---

## 📸 Final Cleanup Evidence Required for Report (10 Marks)
Capture a screenshot of:
1. **EC2 Console:** Showing instances in `Terminated` state.
2. **VPC Console:** Showing no active VPCs or peering connections tagged with `Project=EWB-VPC-Peering`.
