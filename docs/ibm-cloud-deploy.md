# IBM Cloud Deployment Guide

## Plan A: IBM Cloud Code Engine (preferred)

### Prerequisites
- IBM Cloud account with Code Engine and Container Registry access
- `ibmcloud` CLI installed with `code-engine` and `container-registry` plugins
- Docker installed locally
- `.env` file with all required environment variables

### Steps

```bash
# 1. Log in
ibmcloud login --apikey $IBMCLOUD_API_KEY -r us-south
ibmcloud target -g Default

# 2. Set up container registry namespace
ibmcloud cr namespace-add vidyaplan
ibmcloud cr login

# 3. Build and push the production image
docker build -f Dockerfile.prod -t us.icr.io/vidyaplan/app:latest .
docker push us.icr.io/vidyaplan/app:latest

# 4. Create Code Engine project
ibmcloud ce project create --name vidyaplan

# 5. Create secrets from environment variables (never bake into image)
ibmcloud ce secret create --name vidyaplan-env \
  --from-env-file .env

# 6. Deploy the application (min-scale 1 = no cold start during demo)
ibmcloud ce application create \
  --name vidyaplan-app \
  --image us.icr.io/vidyaplan/app:latest \
  --min-scale 1 \
  --max-scale 3 \
  --port 8000 \
  --env-from-secret vidyaplan-env \
  --registry-secret vidyaplan-registry

# 7. Get the public URL
ibmcloud ce application get --name vidyaplan-app --output url
```

### Verify deployment
```bash
# Health check
curl https://<your-url>/health

# Run a plan
curl -X POST https://<your-url>/api/plan \
  -H "Content-Type: application/json" \
  -d '{"budget": 5000000, "cohort_only": true}'
```

---

## Plan B: IBM Cloud VM with docker-compose (fallback)

If Code Engine is unavailable, deploy to a small IBM Cloud Virtual Server.

### Steps

1. Create a Virtual Server Instance (VSI) in IBM Cloud (2 vCPU, 4 GB RAM minimum)
2. SSH in, install Docker and docker-compose
3. Clone the repo and copy `.env`
4. Run:

```bash
docker compose -f docker-compose.prod.yml up -d
```

5. Set up a public IP or floating IP for the VSI
6. Configure firewall rules to allow port 8000

---

## Database

**Local/Plan B:** SQLite (included in the app container, no external DB needed for demo)

**Production:** If your IBM Cloud account includes IBM Databases for MySQL:
1. Provision a MySQL 8 instance
2. Update `DATABASE_URL` in your secrets to the MySQL connection string
3. Run migrations: `python -m app.db.migrate`

---

## Environment Variables (Code Engine Secrets)

```
WATSONX_API_KEY=<ibm-cloud-api-key>
WATSONX_URL=https://us-south.ml.cloud.ibm.com
WATSONX_PROJECT_ID=<project-id>
WATSONX_MODEL_ID=ibm/granite-13b-instruct-v2
DATABASE_URL=sqlite+aiosqlite:///./vidyaplan.db
LLM_TIMEOUT_SECONDS=20
STRESS_SCENARIOS=300
CORS_ORIGINS=https://<your-code-engine-url>
```

**Never commit secrets to git.** Use Code Engine secrets or VM `.env` file.
