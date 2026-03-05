output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer (use http://<this> to open the app)"
  value       = aws_lb.main.dns_name
}

output "alb_url" {
  description = "Full URL to the app (HTTP)"
  value       = "http://${aws_lb.main.dns_name}"
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB table for items"
  value       = aws_dynamodb_table.items.name
}

output "vpc_id" {
  description = "ID of the dedicated VPC"
  value       = aws_vpc.main.id
}

output "private_subnet_ids" {
  description = "IDs of private subnets (app EC2)"
  value       = aws_subnet.private[*].id
}

output "public_subnet_ids" {
  description = "IDs of public subnets (ALB, NAT)"
  value       = aws_subnet.public[*].id
}
