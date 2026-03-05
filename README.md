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

## Deploy with Terraform

1. Push this repo to a **public** Git host (or configure SSH/key so EC2 can clone it).
2. Copy `terraform/terraform.tfvars.example` to `terraform/terraform.tfvars` and set `app_repo_url` to your repo URL.
3. From `terraform/`:
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```
4. After apply, `terraform output alb_url` gives the app URL. Wait a few minutes for instances to pass health checks, then open the URL.

See **docs/ARCHITECTURE.md** for how everything fits together.
