# Launch template + ASG: 2+ t3.micro across private subnets (2 AZs)

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "state"
    values = ["available"]
  }
}

locals {
  user_data = templatefile("${path.module}/user-data.sh", {
    repo_url   = var.app_repo_url
    branch     = var.app_repo_branch
    table_name = aws_dynamodb_table.items.name
    aws_region = var.aws_region
  })
}

resource "aws_launch_template" "app" {
  name_prefix   = "${var.project_name}-"
  image_id      = data.aws_ami.ubuntu.id
  instance_type = "t3.micro"

  vpc_security_group_ids = [aws_security_group.app.id]
  iam_instance_profile {
    name = aws_iam_instance_profile.app.name
  }

  user_data = base64encode(local.user_data)

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "${var.project_name}-app"
    }
  }

  tags = {
    Name = "${var.project_name}-lt"
  }
}

resource "aws_autoscaling_group" "app" {
  name                = "${var.project_name}-asg"
  vpc_zone_identifier = aws_subnet.private[*].id
  target_group_arns   = [aws_lb_target_group.app.arn]
  health_check_type   = "ELB"
  health_check_grace_period = 120

  min_size         = 2
  max_size         = 4
  desired_capacity = 2

  launch_template {
    id      = aws_launch_template.app.id
    version = "$Latest"
  }

  tag {
    key                 = "Name"
    value               = "${var.project_name}-app"
    propagate_at_launch = true
  }

  instance_refresh {
    strategy = "Rolling"
  }
}
