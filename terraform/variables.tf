variable "aws_region" {
  description = "The AWS Region where resources will be provisioned."
  type        = string
  default     = "ap-south-1" # Mumbai Region (as suggested in EWB workbook)
}

variable "project_tag" {
  description = "Project name tag required by EWB workbook."
  type        = string
  default     = "EWB-VPC-Peering"
}

variable "student_name" {
  description = "Your student name for resource tagging."
  type        = string
  default     = "Student"
}

variable "key_pair_name" {
  description = "EC2 key pair name for SSH access."
  type        = string
  default     = "ewb-lab"
}

variable "instance_type" {
  description = "EC2 instance type (Free Tier eligible)."
  type        = string
  default     = "t3.micro"
}

variable "my_ip" {
  description = "Your local public IPv4 address in CIDR format (/32) for bastion SSH access."
  type        = string
  default     = "0.0.0.0/0" # Strongly recommended to replace with your public IP /32 (e.g. 203.0.113.25/32)
}
