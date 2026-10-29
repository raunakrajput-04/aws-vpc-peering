output "vpc_a_id" {
  description = "VPC A ID"
  value       = aws_vpc.vpc_a.id
}

output "vpc_b_id" {
  description = "VPC B ID"
  value       = aws_vpc.vpc_b.id
}

output "peering_connection_id" {
  description = "VPC Peering Connection ID (pcx-...)"
  value       = aws_vpc_peering_connection.peering.id
}

output "bastion_public_ip" {
  description = "Bastion Host Public IPv4 address"
  value       = aws_instance.bastion.public_ip
}

output "bastion_private_ip" {
  description = "Bastion Host Private IPv4 address"
  value       = aws_instance.bastion.private_ip
}

output "app_a_private_ip" {
  description = "App-A Private IPv4 address (No Public IP)"
  value       = aws_instance.app_a.private_ip
}

output "app_b_private_ip" {
  description = "App-B Private IPv4 address (No Public IP)"
  value       = aws_instance.app_b.private_ip
}

output "ssh_config_snippet" {
  description = "Convenient SSH configuration block for your ~/.ssh/config file"
  value       = <<-EOT
    Host ewb-bastion
      HostName ${aws_instance.bastion.public_ip}
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
  EOT
}
