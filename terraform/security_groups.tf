################################################################################
# Security Groups
################################################################################

# 1. Bastion Host Security Group (VPC A)
resource "aws_security_group" "sg_bastion" {
  name        = "ewb-sg-bastion"
  description = "Security group for public Bastion host in VPC A"
  vpc_id      = aws_vpc.vpc_a.id

  # Inbound: SSH only from Administrator's public IP
  ingress {
    description = "SSH from Administrator Workstation"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }

  # Outbound: All traffic allowed
  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "ewb-sg-bastion"
  }
}

# 2. App-A Security Group (VPC A)
resource "aws_security_group" "sg_app_a" {
  name        = "ewb-sg-app-a"
  description = "Security group for private App-A workload in VPC A"
  vpc_id      = aws_vpc.vpc_a.id

  # Inbound: SSH only from Bastion private IP (10.10.1.10/32)
  ingress {
    description = "SSH administration via Bastion"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["10.10.1.10/32"]
  }

  # Inbound: ICMP Echo Request from App-B (10.20.1.10/32)
  ingress {
    description = "ICMP Echo Request from App-B over Peering"
    from_port   = 8 # ICMP Type 8 (Echo Request)
    to_port     = 0 # ICMP Code 0
    protocol    = "icmp"
    cidr_blocks = ["10.20.1.10/32"]
  }

  # Outbound: All traffic allowed
  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "ewb-sg-app-a"
  }
}

# 3. App-B Security Group (VPC B)
resource "aws_security_group" "sg_app_b" {
  name        = "ewb-sg-app-b"
  description = "Security group for private App-B workload in VPC B"
  vpc_id      = aws_vpc.vpc_b.id

  # Inbound: SSH only from Bastion private IP (10.10.1.10/32)
  ingress {
    description = "SSH administration via Bastion"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["10.10.1.10/32"]
  }

  # Inbound: ICMP Echo Request from App-A (10.10.2.10/32)
  ingress {
    description = "ICMP Echo Request from App-A over Peering"
    from_port   = 8 # ICMP Type 8 (Echo Request)
    to_port     = 0 # ICMP Code 0
    protocol    = "icmp"
    cidr_blocks = ["10.10.2.10/32"]
  }

  # Outbound: All traffic allowed
  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "ewb-sg-app-b"
  }
}
