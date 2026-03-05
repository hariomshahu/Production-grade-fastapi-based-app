# Items CRUD — FastAPI + React + DynamoDB

Production-style CRUD app: FastAPI backend, React frontend, DynamoDB, Nginx, and Terraform for a dedicated VPC with ALB and multi-AZ EC2.

## Project layout

- **backend/** — FastAPI app (CRUD, DynamoDB, `/health`). Run with Gunicorn behind Nginx on EC2, or Uvicorn for local dev.
- **frontend/** — React (Vite + TypeScript) CRUD UI. Build output is served by Nginx in production.
- **terraform/** — VPC, public/private subnets, NAT, DynamoDB, IAM, ALB, ASG, Nginx config. User data clones repo, builds frontend, runs Nginx + Gunicorn.
- **docs/ARCHITECTURE.md** — Learning-focused description of the architecture.

## Run locally (no AWS)

1. **DynamoDB**: Use a local table or AWS table. If using AWS, set `AWS_PROFILE` or env and create a table with partition key `id` (string), or run the app with [DynamoDB Local](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.html) and point the SDK to it.

2. **Backend** (from repo root):
   ```bash
   cd backend
   pip install -r requirements.txt
   export DYNAMODB_TABLE=your-table-name   # or leave default "items"
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Frontend** (from repo root):
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   Open http://localhost:5173. Vite proxies `/items` and `/health` to the backend.

## Deploy on your own AWS account

Anyone can clone this repo and deploy the full stack (VPC, DynamoDB, ALB, EC2 with Nginx + app) into their own AWS account. You need an AWS account and credentials with permissions to create VPCs, EC2, DynamoDB, IAM, and ELB.

### 1. Clone the repo

```bash
git clone https://github.com/hariomshahu/Production-grade-fastapi-based-app.git
cd Production-grade-fastapi-based-app
```

(Or clone from your own fork if you’ve forked the repo.)

### 2. Configure AWS credentials

Ensure the AWS CLI can use your account (e.g. `aws sts get-caller-identity` works):

- **Option A:** `aws configure` and set Access Key ID and Secret for an IAM user with sufficient permissions.
- **Option B:** Environment variables `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and optionally `AWS_REGION`.
- **Option C:** `AWS_PROFILE=your-profile` if you use named profiles.

Terraform will use the same credentials.

### 3. Set Terraform variables

Create a tfvars file from the example and set at least the repo URL (and optionally region/environment):

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:

- **`app_repo_url`** — **Required.** The Git URL EC2 will clone to get the app. Use the **public** repo URL so instances can clone without SSH keys, e.g.  
  `https://github.com/hariomshahu/Production-grade-fastapi-based-app.git`  
  If you forked, use your fork’s URL. For a private repo, you must configure EC2 to clone it (e.g. deploy key or token in user data).
- **`app_repo_branch`** — Branch to checkout (default `main`).
- **`aws_region`** — AWS region for all resources (default `us-east-1`).
- **`project_name`** and **`environment`** — Used for naming resources and the DynamoDB table.

`terraform.tfvars` is gitignored; it will not be committed.

### 4. Deploy

From the `terraform/` directory:

```bash
terraform init
terraform plan    # review what will be created
terraform apply   # type "yes" when prompted, or use -auto-approve
```

Apply creates a new VPC, subnets, NAT gateways, a DynamoDB table, an Application Load Balancer, and an Auto Scaling Group of EC2 instances. User data on each instance clones the repo, installs Nginx and Python, builds the frontend, and runs the app. This can take **several minutes** (e.g. 5–10) before instances are healthy.

### 5. Open the app

After apply completes:

```bash
terraform output alb_url
```

Open that URL in a browser. If the ALB health checks haven’t passed yet, wait a minute and try again.

### 6. Clean up

To destroy all created resources and avoid ongoing cost:

```bash
cd terraform
terraform destroy
```

Confirm when prompted. This removes the VPC, EC2 instances, ALB, DynamoDB table, and related resources.

---

See **docs/ARCHITECTURE.md** for how the pieces fit together (VPC, Nginx, DynamoDB, failover).
