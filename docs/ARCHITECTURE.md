# Architecture: FastAPI + React CRUD with DynamoDB and Terraform

This document explains how the application and infrastructure fit together so you can learn and modify them.

---

## 1. High-level diagram and traffic flow

```
User (browser)
    → Internet
    → Application Load Balancer (ALB) on port 80
    → Nginx on EC2 (port 80) in private subnet
    → Gunicorn/FastAPI on 127.0.0.1:8000 (same EC2)
    → DynamoDB (AWS managed, multi-AZ)
```

- The **ALB** is the only component that receives traffic from the internet. It forwards requests to EC2 instances in **private subnets**.
- Each **EC2** instance runs **Nginx** (listening on port 80) and **Gunicorn** (listening on 127.0.0.1:8000). Nginx serves the React static files and proxies `/items` and `/health` to FastAPI.
- **DynamoDB** is used as the database. It is serverless and replicated across multiple Availability Zones by AWS; no database server runs on EC2.

---

## 2. Nginx on EC2

**Why use a reverse proxy?**

- **Single entry point**: The ALB talks to Nginx on port 80 only. The app (Gunicorn) does not need to be exposed to the network.
- **Static files**: Nginx serves the built React app (HTML, JS, CSS) efficiently from disk (`/var/www/app`).
- **API proxy**: Requests to `/items` and `/health` are proxied to `http://127.0.0.1:8000`, so the browser still talks to one origin.

**Config (see `terraform/nginx-app.conf`):**

- `location /items` and `location /health`: `proxy_pass http://127.0.0.1:8000` with headers like `Host`, `X-Real-IP`, `X-Forwarded-For`.
- `location /`: `try_files $uri $uri/ /index.html` so that client-side routes (e.g. `/some/route`) serve `index.html` and the React router can handle them.

Gunicorn binds only to **127.0.0.1:8000**, so it is not reachable from outside the instance.

---

## 3. VPC and networking

**What is a VPC?**  
A Virtual Private Cloud is your own isolated network in AWS. Nothing in it is reachable from the internet unless you explicitly attach an Internet Gateway or a NAT Gateway and configure route tables.

**Why two kinds of subnets?**

- **Public subnets** have a route to the **Internet Gateway** (IGW). Resources here can have a public IP and be reached from the internet. We put the **ALB** and **NAT Gateways** here. The ALB is the only thing that needs to accept traffic from the internet.
- **Private subnets** do *not* have a route to the IGW. Instances here get no public IP and cannot be reached directly from the internet. They *can* reach the internet (for package installs, Git clone, etc.) via a **NAT Gateway** in a public subnet. We put **EC2 (app)** only in private subnets.

**Why two Availability Zones (AZs)?**  
For failover: if one AZ has an outage, the other can still serve traffic. The ALB distributes traffic across instances in both AZs, and the ASG keeps at least two instances running (one per AZ when possible).

**Route tables (summary):**

- Public subnet → route `0.0.0.0/0` to IGW.
- Private subnet (per AZ) → route `0.0.0.0/0` to the NAT Gateway in that AZ.

---

## 4. Security groups

- **ALB security group**: Allows inbound **port 80** from `0.0.0.0/0` (internet). Allows all outbound.
- **App (EC2) security group**: Allows inbound **port 80** only from the ALB security group. So only the ALB can talk to Nginx; no one can hit EC2 directly on port 80. Allows all outbound (for DynamoDB, package installs, etc.).

This follows **least privilege**: the app tier is not exposed to the internet.

---

## 5. DynamoDB

**Table design:**  
One table, e.g. `items-crud-dev-items`, with **partition key** `id` (string). Each item has `id`, `name`, `description`, `created_at`.

**How the backend uses it (boto3):**

- **Create**: `put_item` with a new UUID and timestamp.
- **Read one**: `get_item` with `Key={"id": item_id}`.
- **List**: `scan` with optional `Limit` and `ExclusiveStartKey` for pagination.
- **Update**: `update_item` with `UpdateExpression` for `name` and `description`.
- **Delete**: `delete_item` with `Key={"id": item_id}`.

**Credentials:**  
On EC2, the app uses the **IAM instance profile**. The profile allows `dynamodb:GetItem`, `PutItem`, `UpdateItem`, `DeleteItem`, `Scan`, etc. on this table. There are **no access keys** in the code; the SDK picks up temporary credentials from the instance metadata.

---

## 6. Failover and resilience

- **ALB**: Performs health checks on `/health` (proxied by Nginx to FastAPI). If an instance fails, the ALB stops sending traffic to it.
- **Auto Scaling Group (ASG)**: Keeps **min 2** instances (t3.micro) across the private subnets. If an instance is terminated or unhealthy, the ASG launches a replacement. Instances are spread across AZs when possible.
- **DynamoDB**: Replicated across multiple AZs by AWS; no action needed for failover.

---

## 7. Terraform walkthrough

**What each file does:**

- **main.tf**: Provider (AWS), backend (local state), variables (region, project name, `app_repo_url`, etc.).
- **vpc.tf**: VPC, public/private subnets in 2 AZs, Internet Gateway, NAT Gateways, route tables and associations.
- **security_groups.tf**: ALB SG (80 from internet), app SG (80 from ALB only).
- **dynamodb.tf**: One DynamoDB table with partition key `id`, pay-per-request, point-in-time recovery.
- **iam.tf**: IAM role for EC2 and policy for DynamoDB access; instance profile attached to the launch template.
- **alb.tf**: Application Load Balancer, target group (port 80), HTTP listener, health check on `/health`.
- **asg.tf**: Launch template (Ubuntu, t3.micro, user data to install Nginx + Python + Node, clone repo, build frontend, run Nginx and Gunicorn); ASG with min 2, max 4, desired 2 in private subnets.
- **outputs.tf**: ALB DNS name, table name, VPC and subnet IDs.

**Order of resources:**  
VPC → subnets → NAT → security groups → IAM → DynamoDB → ALB → launch template → ASG. Dependencies are expressed in Terraform; `terraform apply` creates them in the right order.

**How to run:**

1. Copy `terraform/terraform.tfvars.example` to `terraform/terraform.tfvars` and set `app_repo_url` to your Git repo (must be cloneable from EC2).
2. From the `terraform/` directory:
   - `terraform init`
   - `terraform plan`
   - `terraform apply`
3. After apply, use `terraform output alb_url` to get the app URL. Open it in a browser; the React UI will call the same origin for `/items` (Nginx proxies to FastAPI).

---

## 8. Deploy and test

1. **Push your code** to the repo you set in `app_repo_url` (backend, frontend, and `terraform/nginx-app.conf`).
2. **Apply Terraform** as above. Wait for the ASG to launch instances and for the ALB health checks to pass (can take a few minutes).
3. **Open the ALB URL** in a browser. You should see the Items CRUD UI. Create, list, edit, and delete items; they are stored in DynamoDB.
4. **Logs**: On an EC2 instance, app logs are written to `/var/log/app.log` (Gunicorn). You can SSH (e.g. via Session Manager or a bastion) to inspect them. For production, add the CloudWatch agent to ship logs to CloudWatch.

---

## Next steps (optional)

- **HTTPS**: Request an ACM certificate, add an HTTPS listener on the ALB (port 443), and redirect HTTP to HTTPS.
- **Docker/ECR**: Build an image that includes Nginx + built frontend + FastAPI, push to ECR, and change the launch template user data to pull and run the image instead of cloning and building.
- **CloudWatch**: Install the CloudWatch agent on the instances to send logs and metrics to CloudWatch.
