#!/usr/bin/env python3
"""
Automated AWS VPC Peering Deployment Script
Course: AWS Architect Associate (EWB Cloud Labs)
Project: AWS VPC Peering - Connect Two VPCs & Prove Private Connectivity

This script programmatically provisions the complete architecture using boto3:
- VPC A (10.10.0.0/16) with Public Subnet (10.10.1.0/24) and Private Subnet (10.10.2.0/24)
- VPC B (10.20.0.0/16) with Private Subnet (10.20.1.0/24)
- Internet Gateway attached to VPC A
- 3 Custom Route Tables with explicit subnet associations
- VPC Peering Connection (ewb-a-b-peer) auto-requested & accepted
- Bidirectional Routes across Peering connection
- 3 Strict Security Groups (/32 rules)
- 3 EC2 Instances (ewb-bastion, ewb-app-a, ewb-app-b) with fixed private IPs
"""

import sys
import time

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    print("[-] Error: 'boto3' is not installed.")
    print("    Install it via: py -3 -m pip install boto3")
    sys.exit(1)

# Configuration Parameters (Customize if needed)
REGION = "ap-south-1"  # Mumbai Region
KEY_NAME = "ewb-lab"
STUDENT_NAME = "Student"
PROJECT_TAG = "EWB-VPC-Peering"
MY_PUBLIC_IP = "0.0.0.0/0"  # Replace with "YOUR_IP/32" for strict bastion access

TAGS = [
    {"Key": "Project", "Value": PROJECT_TAG},
    {"Key": "Student", "Value": STUDENT_NAME}
]

def get_tag_spec(resource_type, name):
    tags = list(TAGS)
    tags.append({"Key": "Name", "Value": name})
    return [{"ResourceType": resource_type, "Tags": tags}]

def main():
    print("=" * 70)
    print(" AWS VPC PEERING AUTOMATED DEPLOYMENT")
    print(f" Target Region: {REGION} | Student: {STUDENT_NAME}")
    print("=" * 70)

    try:
        ec2 = boto3.client("ec2", region_name=REGION)
        ec2_res = boto3.resource("ec2", region_name=REGION)
    except Exception as e:
        print(f"[-] Failed to initialize AWS client: {e}")
        print("    Ensure your AWS credentials are configured via 'aws configure' or environment variables.")
        sys.exit(1)

    # 1. Create VPC A
    print("\n[+] Creating VPC A (10.10.0.0/16)...")
    vpc_a = ec2.create_vpc(
        CidrBlock="10.10.0.0/16",
        TagSpecifications=get_tag_spec("vpc", "ewb-vpc-a")
    )["Vpc"]
    vpc_a_id = vpc_a["VpcId"]
    ec2.modify_vpc_attribute(VpcId=vpc_a_id, EnableDnsHostnames={"Value": True})
    ec2.modify_vpc_attribute(VpcId=vpc_a_id, EnableDnsSupport={"Value": True})
    print(f"    VPC A Created: {vpc_a_id}")

    # 2. Create VPC B
    print("[+] Creating VPC B (10.20.0.0/16)...")
    vpc_b = ec2.create_vpc(
        CidrBlock="10.20.0.0/16",
        TagSpecifications=get_tag_spec("vpc", "ewb-vpc-b")
    )["Vpc"]
    vpc_b_id = vpc_b["VpcId"]
    ec2.modify_vpc_attribute(VpcId=vpc_b_id, EnableDnsHostnames={"Value": True})
    ec2.modify_vpc_attribute(VpcId=vpc_b_id, EnableDnsSupport={"Value": True})
    print(f"    VPC B Created: {vpc_b_id}")

    # 3. Create Subnets
    print("\n[+] Creating Subnets...")
    # ewb-a-public (10.10.1.0/24)
    sub_a_pub = ec2.create_subnet(
        VpcId=vpc_a_id,
        CidrBlock="10.10.1.0/24",
        TagSpecifications=get_tag_spec("subnet", "ewb-a-public")
    )["Subnet"]
    sub_a_pub_id = sub_a_pub["SubnetId"]
    ec2.modify_subnet_attribute(SubnetId=sub_a_pub_id, MapPublicIpOnLaunch={"Value": True})
    print(f"    Created ewb-a-public: {sub_a_pub_id} (10.10.1.0/24)")

    # ewb-a-private (10.10.2.0/24)
    sub_a_priv = ec2.create_subnet(
        VpcId=vpc_a_id,
        CidrBlock="10.10.2.0/24",
        TagSpecifications=get_tag_spec("subnet", "ewb-a-private")
    )["Subnet"]
    sub_a_priv_id = sub_a_priv["SubnetId"]
    print(f"    Created ewb-a-private: {sub_a_priv_id} (10.10.2.0/24)")

    # ewb-b-private (10.20.1.0/24)
    sub_b_priv = ec2.create_subnet(
        VpcId=vpc_b_id,
        CidrBlock="10.20.1.0/24",
        TagSpecifications=get_tag_spec("subnet", "ewb-b-private")
    )["Subnet"]
    sub_b_priv_id = sub_b_priv["SubnetId"]
    print(f"    Created ewb-b-private: {sub_b_priv_id} (10.20.1.0/24)")

    # 4. Attach Internet Gateway to VPC A
    print("\n[+] Creating and Attaching Internet Gateway to VPC A...")
    igw_a = ec2.create_internet_gateway(
        TagSpecifications=get_tag_spec("internet-gateway", "ewb-igw-a")
    )["InternetGateway"]
    igw_a_id = igw_a["InternetGatewayId"]
    ec2.attach_internet_gateway(InternetGatewayId=igw_a_id, VpcId=vpc_a_id)
    print(f"    Attached IGW {igw_a_id} to VPC A")

    # 5. Create VPC Peering Connection
    print("\n[+] Establishing VPC Peering Connection...")
    pcx = ec2.create_vpc_peering_connection(
        VpcId=vpc_a_id,
        PeerVpcId=vpc_b_id,
        TagSpecifications=get_tag_spec("vpc-peering-connection", "ewb-a-b-peer")
    )["VpcPeeringConnection"]
    pcx_id = pcx["VpcPeeringConnectionId"]
    print(f"    Peering Connection Requested: {pcx_id}")

    # Accept Peering Connection
    time.sleep(2)
    ec2.accept_vpc_peering_connection(VpcPeeringConnectionId=pcx_id)
    print(f"    Peering Connection Accepted & Active: {pcx_id}")

    # 6. Route Tables Setup
    print("\n[+] Configuring Custom Route Tables...")
    # Route table A Public
    rt_a_pub = ec2.create_route_table(
        VpcId=vpc_a_id,
        TagSpecifications=get_tag_spec("route-table", "ewb-rt-a-public")
    )["RouteTable"]["RouteTableId"]
    ec2.create_route(RouteTableId=rt_a_pub, DestinationCidrBlock="0.0.0.0/0", GatewayId=igw_a_id)
    ec2.create_route(RouteTableId=rt_a_pub, DestinationCidrBlock="10.20.0.0/16", VpcPeeringConnectionId=pcx_id)
    ec2.associate_route_table(RouteTableId=rt_a_pub, SubnetId=sub_a_pub_id)
    print(f"    Associated ewb-rt-a-public ({rt_a_pub}) with ewb-a-public")

    # Route table A Private
    rt_a_priv = ec2.create_route_table(
        VpcId=vpc_a_id,
        TagSpecifications=get_tag_spec("route-table", "ewb-rt-a-private")
    )["RouteTable"]["RouteTableId"]
    ec2.create_route(RouteTableId=rt_a_priv, DestinationCidrBlock="10.20.0.0/16", VpcPeeringConnectionId=pcx_id)
    ec2.associate_route_table(RouteTableId=rt_a_priv, SubnetId=sub_a_priv_id)
    print(f"    Associated ewb-rt-a-private ({rt_a_priv}) with ewb-a-private")

    # Route table B Private
    rt_b_priv = ec2.create_route_table(
        VpcId=vpc_b_id,
        TagSpecifications=get_tag_spec("route-table", "ewb-rt-b-private")
    )["RouteTable"]["RouteTableId"]
    ec2.create_route(RouteTableId=rt_b_priv, DestinationCidrBlock="10.10.0.0/16", VpcPeeringConnectionId=pcx_id)
    ec2.associate_route_table(RouteTableId=rt_b_priv, SubnetId=sub_b_priv_id)
    print(f"    Associated ewb-rt-b-private ({rt_b_priv}) with ewb-b-private")

    # 7. Security Groups
    print("\n[+] Creating Security Groups...")
    # ewb-sg-bastion
    sg_bastion = ec2.create_security_group(
        GroupName="ewb-sg-bastion",
        Description="Security group for Bastion Host in VPC A",
        VpcId=vpc_a_id,
        TagSpecifications=get_tag_spec("security-group", "ewb-sg-bastion")
    )["GroupId"]
    ec2.authorize_security_group_ingress(
        GroupId=sg_bastion,
        IpPermissions=[{
            "IpProtocol": "tcp", "FromPort": 22, "ToPort": 22,
            "IpRanges": [{"CidrIp": MY_PUBLIC_IP, "Description": "SSH from admin workstation"}]
        }]
    )
    print(f"    Created ewb-sg-bastion: {sg_bastion}")

    # ewb-sg-app-a
    sg_app_a = ec2.create_security_group(
        GroupName="ewb-sg-app-a",
        Description="Security group for App-A in VPC A",
        VpcId=vpc_a_id,
        TagSpecifications=get_tag_spec("security-group", "ewb-sg-app-a")
    )["GroupId"]
    ec2.authorize_security_group_ingress(
        GroupId=sg_app_a,
        IpPermissions=[
            {
                "IpProtocol": "tcp", "FromPort": 22, "ToPort": 22,
                "IpRanges": [{"CidrIp": "10.10.1.10/32", "Description": "SSH from Bastion"}]
            },
            {
                "IpProtocol": "icmp", "FromPort": 8, "ToPort": 0,
                "IpRanges": [{"CidrIp": "10.20.1.10/32", "Description": "ICMP Echo from App-B"}]
            }
        ]
    )
    print(f"    Created ewb-sg-app-a: {sg_app_a}")

    # ewb-sg-app-b
    sg_app_b = ec2.create_security_group(
        GroupName="ewb-sg-app-b",
        Description="Security group for App-B in VPC B",
        VpcId=vpc_b_id,
        TagSpecifications=get_tag_spec("security-group", "ewb-sg-app-b")
    )["GroupId"]
    ec2.authorize_security_group_ingress(
        GroupId=sg_app_b,
        IpPermissions=[
            {
                "IpProtocol": "tcp", "FromPort": 22, "ToPort": 22,
                "IpRanges": [{"CidrIp": "10.10.1.10/32", "Description": "SSH from Bastion"}]
            },
            {
                "IpProtocol": "icmp", "FromPort": 8, "ToPort": 0,
                "IpRanges": [{"CidrIp": "10.10.2.10/32", "Description": "ICMP Echo from App-A"}]
            }
        ]
    )
    print(f"    Created ewb-sg-app-b: {sg_app_b}")

    # 8. Get Latest Amazon Linux 2023 AMI
    print("\n[+] Locating Amazon Linux 2023 AMI...")
    amis = ec2.describe_images(
        Owners=["amazon"],
        Filters=[
            {"Name": "name", "Values": ["al2023-ami-2023.*-x86_64"]},
            {"Name": "state", "Values": ["available"]}
        ]
    )["Images"]
    amis.sort(key=lambda x: x["CreationDate"], reverse=True)
    ami_id = amis[0]["ImageId"]
    print(f"    Found AMI: {ami_id} ({amis[0]['Name']})")

    # 9. Launch EC2 Instances
    print("\n[+] Launching EC2 Instances with fixed IP addresses...")

    # ewb-bastion
    inst_bastion = ec2.run_instances(
        ImageId=ami_id,
        InstanceType="t3.micro",
        KeyName=KEY_NAME,
        MinCount=1, MaxCount=1,
        NetworkInterfaces=[{
            "DeviceIndex": 0,
            "SubnetId": sub_a_pub_id,
            "PrivateIpAddress": "10.10.1.10",
            "AssociatePublicIpAddress": True,
            "Groups": [sg_bastion],
            "DeleteOnTermination": True
        }],
        TagSpecifications=get_tag_spec("instance", "ewb-bastion")
    )["Instances"][0]["InstanceId"]
    print(f"    Launched ewb-bastion ({inst_bastion}) -> 10.10.1.10")

    # ewb-app-a
    inst_app_a = ec2.run_instances(
        ImageId=ami_id,
        InstanceType="t3.micro",
        KeyName=KEY_NAME,
        MinCount=1, MaxCount=1,
        NetworkInterfaces=[{
            "DeviceIndex": 0,
            "SubnetId": sub_a_priv_id,
            "PrivateIpAddress": "10.10.2.10",
            "AssociatePublicIpAddress": False,
            "Groups": [sg_app_a],
            "DeleteOnTermination": True
        }],
        TagSpecifications=get_tag_spec("instance", "ewb-app-a")
    )["Instances"][0]["InstanceId"]
    print(f"    Launched ewb-app-a ({inst_app_a}) -> 10.10.2.10 (No Public IP)")

    # ewb-app-b
    inst_app_b = ec2.run_instances(
        ImageId=ami_id,
        InstanceType="t3.micro",
        KeyName=KEY_NAME,
        MinCount=1, MaxCount=1,
        NetworkInterfaces=[{
            "DeviceIndex": 0,
            "SubnetId": sub_b_priv_id,
            "PrivateIpAddress": "10.20.1.10",
            "AssociatePublicIpAddress": False,
            "Groups": [sg_app_b],
            "DeleteOnTermination": True
        }],
        TagSpecifications=get_tag_spec("instance", "ewb-app-b")
    )["Instances"][0]["InstanceId"]
    print(f"    Launched ewb-app-b ({inst_app_b}) -> 10.20.1.10 (No Public IP)")

    print("\n[+] Waiting for Bastion public IP assignment...")
    time.sleep(5)
    bastion_desc = ec2.describe_instances(InstanceIds=[inst_bastion])["Reservations"][0]["Instances"][0]
    bastion_pub_ip = bastion_desc.get("PublicIpAddress", "Pending...")

    print("\n" + "=" * 70)
    print(" RESOURCE INVENTORY (RECORD THESE FOR YOUR REPORT)")
    print("=" * 70)
    print(f"VPC A ID:               {vpc_a_id} (10.10.0.0/16)")
    print(f"VPC B ID:               {vpc_b_id} (10.20.0.0/16)")
    print(f"Peering Connection ID:  {pcx_id} (Active)")
    print(f"Bastion Instance ID:    {inst_bastion} | Private: 10.10.1.10 | Public: {bastion_pub_ip}")
    print(f"App-A Instance ID:      {inst_app_a} | Private: 10.10.2.10 | Public: None")
    print(f"App-B Instance ID:      {inst_app_b} | Private: 10.20.1.10 | Public: None")
    print("=" * 70)

    print("\n[+] Configured ~/.ssh/config snippet:")
    print("-" * 50)
    print(f"""Host ewb-bastion
  HostName {bastion_pub_ip}
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
  ProxyJump ewb-bastion""")
    print("-" * 50)
    print("\n[OK] Deployment successfully completed!")

if __name__ == "__main__":
    main()
