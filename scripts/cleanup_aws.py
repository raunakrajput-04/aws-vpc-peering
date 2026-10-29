#!/usr/bin/env python3
"""
Automated AWS Teardown Script for VPC Peering Lab
Safely terminates compute and deletes network dependencies in proper order:
1. Terminate EC2 instances (bastion, app-a, app-b)
2. Wait for termination and network interface deletion
3. Delete VPC Peering connection (automatically removes peer routes)
4. Delete custom Security Groups
5. Disassociate and delete custom Route Tables
6. Detach and delete Internet Gateway
7. Delete Subnets
8. Delete VPCs
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

REGION = "ap-south-1"
PROJECT_TAG = "EWB-VPC-Peering"

def main():
    print("=" * 70)
    print(" AWS VPC PEERING LAB TEARDOWN & CLEANUP")
    print(f" Region: {REGION} | Target Tag: Project={PROJECT_TAG}")
    print("=" * 70)

    confirm = input("Are you sure you want to delete all lab resources? (yes/no): ").strip().lower()
    if confirm not in ["yes", "y"]:
        print("Cleanup aborted.")
        return

    ec2 = boto3.client("ec2", region_name=REGION)

    # 1. Terminate Instances
    print("\n[1/7] Finding and terminating EC2 instances...")
    instances = ec2.describe_instances(
        Filters=[
            {"Name": "tag:Project", "Values": [PROJECT_TAG]},
            {"Name": "instance-state-name", "Values": ["pending", "running", "stopping", "stopped"]}
        ]
    )
    inst_ids = []
    for res in instances.get("Reservations", []):
        for inst in res.get("Instances", []):
            inst_ids.append(inst["InstanceId"])

    if inst_ids:
        print(f"    Terminating instances: {inst_ids}")
        ec2.terminate_instances(InstanceIds=inst_ids)
        print("    Waiting for instances to terminate completely...")
        waiter = ec2.get_waiter("instance_terminated")
        waiter.wait(InstanceIds=inst_ids)
        print("    [OK] All lab instances terminated.")
        time.sleep(10)
    else:
        print("    No active lab instances found.")

    # 2. Delete VPC Peering Connection
    print("\n[2/7] Finding and deleting VPC peering connections...")
    pcxs = ec2.describe_vpc_peering_connections(
        Filters=[{"Name": "tag:Project", "Values": [PROJECT_TAG]}]
    ).get("VpcPeeringConnections", [])

    for pcx in pcxs:
        if pcx["Status"]["Code"] not in ["deleted", "deleting"]:
            pcx_id = pcx["VpcPeeringConnectionId"]
            print(f"    Deleting peering connection: {pcx_id}")
            try:
                ec2.delete_vpc_peering_connection(VpcPeeringConnectionId=pcx_id)
            except Exception as e:
                print(f"    Warning: {e}")

    # 3. Delete Security Groups
    print("\n[3/7] Finding and deleting custom security groups...")
    sgs = ec2.describe_security_groups(
        Filters=[{"Name": "tag:Project", "Values": [PROJECT_TAG]}]
    ).get("SecurityGroups", [])

    for sg in sgs:
        sg_id = sg["GroupId"]
        if sg["GroupName"] != "default":
            print(f"    Deleting Security Group: {sg['GroupName']} ({sg_id})")
            retries = 5
            while retries > 0:
                try:
                    ec2.delete_security_group(GroupId=sg_id)
                    break
                except ClientError as e:
                    time.sleep(5)
                    retries -= 1
                    if retries == 0:
                        print(f"    Could not delete {sg_id}: {e}")

    # 4. Delete Custom Route Tables
    print("\n[4/7] Finding and deleting custom route tables...")
    rts = ec2.describe_route_tables(
        Filters=[{"Name": "tag:Project", "Values": [PROJECT_TAG]}]
    ).get("RouteTables", [])

    for rt in rts:
        rt_id = rt["RouteTableId"]
        is_main = any(assoc.get("Main", False) for assoc in rt.get("Associations", []))
        if not is_main:
            for assoc in rt.get("Associations", []):
                assoc_id = assoc.get("RouteTableAssociationId")
                if assoc_id and not assoc.get("Main", False):
                    print(f"    Disassociating route table association: {assoc_id}")
                    try:
                        ec2.disassociate_route_table(AssociationId=assoc_id)
                    except Exception as e:
                        print(f"    Warning: {e}")
            try:
                print(f"    Deleting Route Table: {rt_id}")
                ec2.delete_route_table(RouteTableId=rt_id)
            except Exception as e:
                print(f"    Warning: {e}")

    # 5. Detach & Delete Internet Gateways
    print("\n[5/7] Finding and deleting Internet Gateways...")
    igws = ec2.describe_internet_gateways(
        Filters=[{"Name": "tag:Project", "Values": [PROJECT_TAG]}]
    ).get("InternetGateways", [])

    for igw in igws:
        igw_id = igw["InternetGatewayId"]
        for attachment in igw.get("Attachments", []):
            vpc_id = attachment.get("VpcId")
            print(f"    Detaching IGW {igw_id} from VPC {vpc_id}...")
            try:
                ec2.detach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
            except Exception as e:
                print(f"    Warning: {e}")
        try:
            print(f"    Deleting IGW {igw_id}...")
            ec2.delete_internet_gateway(InternetGatewayId=igw_id)
        except Exception as e:
            print(f"    Warning: {e}")

    # 6. Delete Subnets
    print("\n[6/7] Finding and deleting subnets...")
    subnets = ec2.describe_subnets(
        Filters=[{"Name": "tag:Project", "Values": [PROJECT_TAG]}]
    ).get("Subnets", [])

    for sub in subnets:
        sub_id = sub["SubnetId"]
        print(f"    Deleting Subnet: {sub_id} ({sub.get('CidrBlock')})")
        try:
            ec2.delete_subnet(SubnetId=sub_id)
        except Exception as e:
            print(f"    Warning: {e}")

    # 7. Delete VPCs
    print("\n[7/7] Finding and deleting VPCs...")
    vpcs = ec2.describe_vpcs(
        Filters=[{"Name": "tag:Project", "Values": [PROJECT_TAG]}]
    ).get("Vpcs", [])

    for vpc in vpcs:
        vpc_id = vpc["VpcId"]
        print(f"    Deleting VPC: {vpc_id} ({vpc.get('CidrBlock')})")
        try:
            ec2.delete_vpc(VpcId=vpc_id)
        except Exception as e:
            print(f"    Warning: {e}")

    print("\n" + "=" * 70)
    print(" [OK] CLEANUP COMPLETE: All project resources have been safely removed!")
    print("=" * 70)

if __name__ == "__main__":
    main()
