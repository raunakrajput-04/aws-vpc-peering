# 02. Manual AWS Management Console Walkthrough

Follow this step-by-step console guide to build the lab in your AWS account and capture all required checkpoints.

---

## Step 1: Create Key Pair
1. Navigate to **EC2 Console** > **Key Pairs** (under Network & Security).
2. Click **Create key pair**.
3. Name: `ewb-lab`.
4. Key pair type: **RSA**.
5. Private key file format: **.pem**.
6. Click **Create key pair** and save `ewb-lab.pem` to your local `~/.ssh/` folder.
   > **Important:** Never upload or copy this private key onto any EC2 instance.

---

## Step 2: Build VPC A & Subnets
1. Open the **VPC Console** > **Your VPCs** > Click **Create VPC**.
2. Select **VPC only** (do not select "VPC and more" so you retain total control).
   * Name tag: `ewb-vpc-a`
   * IPv4 CIDR block: `10.10.0.0/16`
   * IPv6 CIDR block: `No IPv6 CIDR block`
   * Tenancy: `Default`
3. Click **Create VPC**.
4. Go to **Subnets** > **Create subnet**:
   * Select VPC: `ewb-vpc-a`
   * **Subnet 1:**
     * Subnet name: `ewb-a-public`
     * Availability Zone: Choose your preferred AZ (e.g., `ap-south-1a`)
     * IPv4 CIDR block: `10.10.1.0/24`
   * Click **Add new subnet**
   * **Subnet 2:**
     * Subnet name: `ewb-a-private`
     * Availability Zone: Same AZ as above (e.g., `ap-south-1a`)
     * IPv4 CIDR block: `10.10.2.0/24`
   * Click **Create subnet**.
5. Select `ewb-a-public` > **Actions** > **Edit subnet settings** > check **Enable auto-assign public IPv4 address** > Click **Save**.

---

## Step 3: Attach Internet Gateway to VPC A
1. Go to **Internet gateways** > Click **Create internet gateway**.
2. Name tag: `ewb-igw-a` > Click **Create internet gateway**.
3. Select `ewb-igw-a` > **Actions** > **Attach to VPC**.
4. Select `ewb-vpc-a` > Click **Attach internet gateway**.

---

## Step 4: Route Tables for VPC A
1. Go to **Route tables** > Click **Create route table**.
   * Name: `ewb-rt-a-public`
   * VPC: `ewb-vpc-a`
   * Click **Create route table**.
2. Under **Subnet associations** tab > Click **Edit subnet associations**:
   * Check `ewb-a-public` > Click **Save associations**.
3. Under **Routes** tab > Click **Edit routes**:
   * Click **Add route**:
     * Destination: `0.0.0.0/0`
     * Target: **Internet Gateway** > Select `ewb-igw-a`
   * Click **Save changes**.

4. Create Private Route Table:
   * Click **Create route table**.
   * Name: `ewb-rt-a-private`
   * VPC: `ewb-vpc-a`
   * Click **Create route table**.
5. Under **Subnet associations** > Edit > select `ewb-a-private` > Save.
   *(Leave routes as local for now; peering route will be added after peering is established).*

> 📸 **Checkpoint 01:** Capture a screenshot showing the two subnet associations and route tables for VPC A.

---

## Step 5: Build VPC B & Subnet
1. In **VPC Console** > **Your VPCs** > Click **Create VPC**.
   * Name tag: `ewb-vpc-b`
   * IPv4 CIDR block: `10.20.0.0/16`
   * Tenancy: `Default`
   * Click **Create VPC**.
2. Go to **Subnets** > Click **Create subnet**:
   * VPC: `ewb-vpc-b`
   * Subnet name: `ewb-b-private`
   * Availability Zone: Choose the same AZ as VPC A
   * IPv4 CIDR block: `10.20.1.0/24`
   * Click **Create subnet**.
3. Go to **Route tables** > Click **Create route table**:
   * Name: `ewb-rt-b-private`
   * VPC: `ewb-vpc-b`
   * Click **Create route table**.
4. Under **Subnet associations** > select `ewb-b-private` > Save.
   *(VPC B has NO Internet Gateway).*

---

## Step 6: Create Security Groups

### SG 1: `ewb-sg-bastion` (in VPC A)
1. Go to **Security Groups** > **Create security group**.
   * Name: `ewb-sg-bastion`
   * Description: `Bastion SG in VPC A`
   * VPC: `ewb-vpc-a`
2. **Inbound rules**:
   * Type: `SSH` | Protocol: `TCP` | Port: `22` | Source: Select `My IP` (or enter `YourPublicIP/32`)
3. Click **Create security group**.

### SG 2: `ewb-sg-app-a` (in VPC A)
1. Click **Create security group**.
   * Name: `ewb-sg-app-a`
   * Description: `App-A SG in VPC A`
   * VPC: `ewb-vpc-a`
2. **Inbound rules**:
   * Rule 1: Type: `SSH` | Port: `22` | Source: `Custom` > `10.10.1.10/32` (Bastion private IP)
   * Rule 2: Type: `Custom ICMP - IPv4` | Protocol: `ICMP` | Port range: `Echo Request` (Type 8, Code 0) | Source: `Custom` > `10.20.1.10/32` (App-B private IP)
3. Click **Create security group**.

### SG 3: `ewb-sg-app-b` (in VPC B)
1. Click **Create security group**.
   * Name: `ewb-sg-app-b`
   * Description: `App-B SG in VPC B`
   * VPC: `ewb-vpc-b`
2. **Inbound rules**:
   * Rule 1: Type: `SSH` | Port: `22` | Source: `Custom` > `10.10.1.10/32` (Bastion private IP)
   * Rule 2: Type: `Custom ICMP - IPv4` | Protocol: `ICMP` | Port range: `Echo Request` (Type 8, Code 0) | Source: `Custom` > `10.10.2.10/32` (App-A private IP)
3. Click **Create security group**.

---

## Step 7: Launch EC2 Instances

### Instance 1: `ewb-bastion`
* **AMI:** Amazon Linux 2023
* **Instance Type:** `t3.micro`
* **Key pair:** `ewb-lab`
* **Network Settings (Edit):**
  * VPC: `ewb-vpc-a`
  * Subnet: `ewb-a-public`
  * Auto-assign public IP: **Enable**
  * Firewall (security groups): Select existing > `ewb-sg-bastion`
  * **Advanced network settings:** Primary IP: `10.10.1.10`
* Click **Launch instance**.

### Instance 2: `ewb-app-a`
* **AMI:** Amazon Linux 2023 | **Type:** `t3.micro` | **Key pair:** `ewb-lab`
* **Network Settings (Edit):**
  * VPC: `ewb-vpc-a`
  * Subnet: `ewb-a-private`
  * Auto-assign public IP: **Disable**
  * Security group: `ewb-sg-app-a`
  * **Advanced network settings:** Primary IP: `10.10.2.10`
* Click **Launch instance**.

### Instance 3: `ewb-app-b`
* **AMI:** Amazon Linux 2023 | **Type:** `t3.micro` | **Key pair:** `ewb-lab`
* **Network Settings (Edit):**
  * VPC: `ewb-vpc-b`
  * Subnet: `ewb-b-private`
  * Auto-assign public IP: **Disable**
  * Security group: `ewb-sg-app-b`
  * **Advanced network settings:** Primary IP: `10.20.1.10`
* Click **Launch instance**.

> 📸 **Checkpoint 02:** Record instance IDs and verify App-A and App-B have **NO Public IPv4 address**.

---

## Step 8: Create & Accept VPC Peering Connection
1. In **VPC Console** > **Peering connections** > Click **Create peering connection**.
   * Name: `ewb-a-b-peer`
   * VPC ID (Requester): Select `ewb-vpc-a`
   * Select **My account** & **This Region**
   * VPC ID (Accepter): Select `ewb-vpc-b`
2. Click **Create peering connection**.
3. Select `ewb-a-b-peer` > **Actions** > **Accept request** > Confirm.
4. Verify status changes to **Active**.

> 📸 **Checkpoint 03:** Capture a screenshot showing the peering connection status as **Active** with requester and accepter VPC IDs.

---

## Step 9: Update Route Tables for Peering
Open each route table, click **Routes** > **Edit routes** > **Add route**:

1. **Table `ewb-rt-a-public`:**
   * Destination: `10.20.0.0/16` | Target: **Peering Connection** (`ewb-a-b-peer`)
2. **Table `ewb-rt-a-private`:**
   * Destination: `10.20.0.0/16` | Target: **Peering Connection** (`ewb-a-b-peer`)
3. **Table `ewb-rt-b-private`:**
   * Destination: `10.10.0.0/16` | Target: **Peering Connection** (`ewb-a-b-peer`)

> 📸 **Checkpoint 04:** Capture screenshots of routes for all 3 route tables showing the peering target.
