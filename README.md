# AWS VPC Peering: Connect Two VPCs & Prove Private Connectivity
### EWB Cloud Labs — Student Project Workbook (Project 01)
**Course:** AWS Architect Associate | **Evaluation:** 100 Marks

---

## 📌 Project Overview
This repository contains the complete implementation, automation scripts, Terraform code, testing suites, viva defense answers, and submission report generator for **AWS VPC Peering: Connect Two VPCs & Prove Private Connectivity**.

### The Mission
* **VPC A (`10.10.0.0/16`)**: Contains a public subnet with a Bastion host (`10.10.1.10`) and a private subnet with backend workload `App-A` (`10.10.2.10`).
* **VPC B (`10.20.0.0/16`)**: Contains a private subnet with isolated backend workload `App-B` (`10.20.1.10`) with **zero direct internet access**.
* **AWS VPC Peering (`ewb-a-b-peer`)**: Connects VPC A and VPC B privately over the AWS backbone network.
* **Security & Access**: Granular `/32` security group rules and end-to-end SSH administration via **`ProxyJump`** without ever exposing private workloads or copying private keys to remote instances.

---

## 🏗️ Architecture Blueprint

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
|   |  |  [ ewb-bastion ]             |  |              |  |  [ ewb-app-b ]                   |  |   |
|   |  |  Private: 10.10.1.10         |  |              |  |  Private: 10.20.1.10             |  |   |
|   |  |  Public: Auto-assigned       |  |              |  |  Public: None (Isolated)         |  |   |
|   |  +--------------+---------------+  |              |  +------------------^---------------+  |   |
|   |                 |                  |              |                     |                  |   |
|   |  +--------------v---------------+  |  PEERING     |                     |                  |   |
|   |  | Private Subnet (10.10.2.0/24)|  | CONNECTION   |                     |                  |   |
|   |  | [ ewb-app-a ]                |  | (pcx-xxxxxx) |                     |                  |   |
|   |  | Private: 10.10.2.10          +=======================================+                  |   |
|   |  | Public: None                 |  | (Bidirectional ICMP & SSH ProxyJump)                  |   |
|   |  +------------------------------+  |              +----------------------------------------+   |
|   +-----------------^------------------+                                                           |
|                     |                                                                              |
|           [ Internet Gateway ] (VPC A only)                                                        |
+---------------------|------------------------------------------------------------------------------+
                      | SSH TCP:22 (from Admin /32 IP)
            [ Admin Workstation ]
```

---

## 📂 Repository Structure

```
AWS Internship Project/
│
├── README.md                                  # Project overview and master manual
│
├── docs/                                      # Step-by-Step Documentation & Rubric Guides
│   ├── 01_ARCHITECTURE_AND_IP_PLAN.md         # Network plan & non-overlapping CIDRs
│   ├── 02_MANUAL_AWS_CONSOLE_WALKTHROUGH.md   # Exact AWS console instructions & checkpoints
│   ├── 03_SSH_PROXYJUMP_CONFIGURATION.md      # Secure SSH ProxyJump guide & key security
│   ├── 04_TESTING_AND_VALIDATION_SUITE.md     # Acceptance tests 01 to 05 + controlled failure
│   ├── 05_VIVA_AND_INTERVIEW_DEFENSE.md       # Complete answers to all 4 viva questions
│   └── 06_CLEANUP_CHECKLIST.md                # Cost control & teardown instructions
│
├── terraform/                                 # Infrastructure as Code (Terraform)
│   ├── provider.tf                            # AWS provider configuration
│   ├── variables.tf                           # Configurable variables & tags
│   ├── main.tf                                # VPCs, Subnets, IGW, Route tables
│   ├── peering.tf                             # VPC Peering connection
│   ├── security_groups.tf                     # Least-privilege /32 security groups
│   ├── compute.tf                             # EC2 instances with static IPs
│   ├── outputs.tf                             # Resource IDs and SSH snippet
│   └── terraform.tfvars.example               # Example variables file
│
├── scripts/                                   # Automation Scripts
│   ├── deploy_aws.py                          # 1-Click Python Boto3 provisioning
│   ├── cleanup_aws.py                         # 1-Click teardown & resource cleanup
│   ├── setup_ssh_config.ps1                   # Windows PowerShell SSH setup
│   └── setup_ssh_config.sh                    # Linux / macOS / WSL SSH setup
│
└── report/                                    # Internship Submission Deliverables (100 Marks)
    ├── YourName_EWB_VPC_Peering_Report.md     # Full technical markdown report
    ├── generate_html_report.py                # Compiles report into print-ready HTML
    └── YourName_EWB_VPC_Peering_Report.html   # Standalone HTML report (Print to PDF)
```

---

## 🚀 Quick Start: Deployment Options

You can deploy and complete this project through three different methods:

### Option 1: Manual AWS Management Console (Recommended for Screenshots)
Follow the step-by-step console guide in [`docs/02_MANUAL_AWS_CONSOLE_WALKTHROUGH.md`](file:///c:/Users/rauna/Downloads/ANTIGRAVITY/AWS%20Internship%20Project/docs/02_MANUAL_AWS_CONSOLE_WALKTHROUGH.md) to build the infrastructure click-by-click and take screenshots for Checkpoints 01, 02, 03, and 04.

### Option 2: Automated Python Script (Fastest Setup)
1. Ensure your AWS credentials are configured (`~/.aws/credentials` or `aws configure`).
2. Run:
   ```bash
   py -3 -m pip install boto3
   py -3 scripts/deploy_aws.py
   ```
   The script provisions all VPCs, subnets, route tables, peering links, security groups, and instances in under 2 minutes.

### Option 3: Terraform Infrastructure as Code
```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Update student_name and my_ip in terraform.tfvars
terraform init
terraform apply
```

---

## 🔑 SSH Configuration & ProxyJump

1. Download your EC2 key pair `ewb-lab.pem` and place it in `~/.ssh/`.
2. Configure `~/.ssh/config` using the provided automation script:
   * **On Windows (PowerShell):**
     ```powershell
     powershell -ExecutionPolicy Bypass -File scripts\setup_ssh_config.ps1 -BastionPublicIP <YOUR_BASTION_IP>
     ```
   * **On Linux / macOS / WSL:**
     ```bash
     chmod +x scripts/setup_ssh_config.sh
     ./scripts/setup_ssh_config.sh <YOUR_BASTION_IP>
     ```
3. Test your connections:
   ```bash
   ssh ewb-bastion   # Connect to public bastion
   ssh ewb-app-a     # Jump directly to private App-A
   ssh ewb-app-b     # Jump directly to private App-B via Peering
   ```

---

## 🧪 Testing & Validation Matrix

Execute the tests detailed in [`docs/04_TESTING_AND_VALIDATION_SUITE.md`](file:///c:/Users/rauna/Downloads/ANTIGRAVITY/AWS%20Internship%20Project/docs/04_TESTING_AND_VALIDATION_SUITE.md):

| Test ID | Command | Expected Result | What It Proves |
| :--- | :--- | :--- | :--- |
| **01 (Baseline)** | `ssh ewb-app-a`<br>`ping -c 4 10.20.1.10` | 100% packet loss | Default isolation before peering routes. |
| **02 (Forward)** | `ssh ewb-app-a`<br>`ping -c 4 10.20.1.10` | 4 replies; 0% loss | Traffic routes from VPC A to VPC B. |
| **03 (Reverse)** | `ssh ewb-app-b`<br>`ping -c 4 10.10.2.10` | 4 replies; 0% loss | Traffic routes from VPC B to VPC A. |
| **04 (SSH)** | `ssh ewb-app-b` | Shell prompt on App-B | End-to-end ProxyJump over peering. |
| **05 (Controlled)** | Remove App-B ICMP rule | Ping drops; restores on rule re-add | SG acts as independent stateful firewall. |

---

## 🎓 Viva & Interview Defense Questions

Full architect-level answers are provided in [`docs/05_VIVA_AND_INTERVIEW_DEFENSE.md`](file:///c:/Users/rauna/Downloads/ANTIGRAVITY/AWS%20Internship%20Project/docs/05_VIVA_AND_INTERVIEW_DEFENSE.md):
1. **Why is the return route needed?** VPC routing is hop-by-hop and stateless. App-B needs an explicit route table entry pointing back to `10.10.0.0/16` via the peering connection to send replies.
2. **Why is the App-B SSH source the bastion private IP?** In SSH ProxyJump, the Bastion opens a local TCP connection from its private IP (`10.10.1.10`) to App-B (`10.20.1.10:22`).
3. **Why does Active peering not guarantee a successful ping?** Active status only proves SDN handshake. Packets require route table entries, security group inbound rules, NACL rules, and an active OS.
4. **Can VPC B use VPC A's internet gateway over peering?** No. VPC Peering is non-transitive. An Internet Gateway only processes traffic originating from within its attached VPC.

---

## 📄 Generating the Final PDF Submission Report

To generate your final deliverable (`YourName_EWB_VPC_Peering.pdf`):
1. Edit your name and IDs in [`report/YourName_EWB_VPC_Peering_Report.html`](file:///c:/Users/rauna/Downloads/ANTIGRAVITY/AWS%20Internship%20Project/report/YourName_EWB_VPC_Peering_Report.html) or run `py -3 report/generate_html_report.py`.
2. Double-click to open [`YourName_EWB_VPC_Peering_Report.html`](file:///c:/Users/rauna/Downloads/ANTIGRAVITY/AWS%20Internship%20Project/report/YourName_EWB_VPC_Peering_Report.html) in your browser (Google Chrome or Microsoft Edge).
3. Press **Ctrl + P** (or click the floating **Print to PDF** button).
4. Destination: **Save as PDF** > Margin: **Default** > Save as `YourName_EWB_VPC_Peering.pdf`.

---

## 🧹 Cleanup & Cost Management
When finished, cleanly delete all resources to avoid charges:
```bash
py -3 scripts/cleanup_aws.py
```
Or follow the manual teardown order in [`docs/06_CLEANUP_CHECKLIST.md`](file:///c:/Users/rauna/Downloads/ANTIGRAVITY/AWS%20Internship%20Project/docs/06_CLEANUP_CHECKLIST.md).
