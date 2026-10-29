################################################################################
# VPC Peering Connection between VPC A and VPC B
################################################################################

resource "aws_vpc_peering_connection" "peering" {
  vpc_id        = aws_vpc.vpc_a.id
  peer_vpc_id   = aws_vpc.vpc_b.id
  auto_accept   = true # Automatically accepted because both VPCs belong to the same AWS account

  tags = {
    Name = "ewb-a-b-peer"
  }
}
