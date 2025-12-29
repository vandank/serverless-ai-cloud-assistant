# AI Cloud Assistant — Powered by AWS Bedrock (Serverless RAG Chatbot)

A production-style, serverless AI assistant that answers AWS technical questions using **Retrieval-Augmented Generation (RAG)**.  
Built with **React (Vite) frontend** and an **AWS serverless backend** using **API Gateway + Lambda + Bedrock + S3**.

---

## What This Project Does

This app allows a user to ask technical questions in a chat UI.

When a question is submitted:
1. The request is sent from the **React UI** to an **AWS API Gateway REST API**
2. API Gateway triggers a **Python AWS Lambda**
3. Lambda loads knowledge base text files stored in **Amazon S3**
4. Lambda performs lightweight retrieval (keyword scoring + filtering) to select relevant chunks
5. Lambda sends the retrieved context + user query to **Amazon Bedrock (Claude 3 Haiku)**
6. The response is returned to the UI along with:
   - whether RAG was used
   - sources used (which `.txt` files matched)
   - end-to-end latency

If no relevant context is found, the assistant responds:
> “I don’t know based on the provided context.”

---

##  Key Features

###  RAG (Retrieval-Augmented Generation)
- Text-based knowledge base stored in **S3**
- Retrieval uses:
  - keyword extraction
  - stopword filtering
  - minimum score threshold
  - chunk-level matching (splitting docs into paragraphs)
- Response includes **Sources** (file names used)

###  API Security
- **API Key required** via `x-api-key`
- Throttling enabled via API Gateway Usage Plan to prevent abuse

###  Cost Control
- Hard prompt length limit
- Dynamic max token control (kept reasonable to reduce Bedrock cost)
- Early-exit for trivial greetings (no Bedrock call)

###  Lightweight Observability
- Structured logs with:
  - request_id
  - prompt length
  - whether RAG context was found
  - latency in ms
- Logs available in **Amazon CloudWatch Logs**

###  Modern Frontend UX
- Clean chat interface
- “Thinking…” state with spinner
- Auto-scroll behavior
- Graceful error handling (network/API failures don’t crash UI)

---

##  Architecture

**Request Flow:**

User  
→ React (Vite) UI  
→ API Gateway (REST API)  
→ AWS Lambda (Python)  
→ Amazon Bedrock (Claude 3 Haiku)  
→ Response back to UI

RAG Path:  
Lambda → Amazon S3 → retrieve relevant knowledge base chunks

Observability:  
Lambda → CloudWatch Logs

> Architecture diagram: `docs/architecture.png`

---

##  Tech Stack

### Frontend
- React (Vite)
- Fetch API
- Basic CSS styling

### Backend (AWS Serverless)
- AWS SAM (build + deploy)
- Amazon API Gateway (REST)
- AWS Lambda (Python)
- Amazon Bedrock (Claude 3 Haiku)
- Amazon S3 (RAG knowledge base)
- Amazon CloudWatch Logs (logging/latency)

---

##  Repository Structure

```bash
serverless-ai-chatbot/
│── serverless-ai-chatbot/        # Backend (AWS SAM + Lambda)
│   ├── app.py                    # Lambda handler
│   ├── template.yaml             # SAM template
│   └── ...
│
│── frontend/rag-chat-ui/         # React UI
│   ├── src/
│   ├── .env.example
│   └── ...
│
│── rag_data/                     # Local knowledge base files (synced to S3)
│   ├── aws_lambda.txt
│   ├── aws_bedrock.txt
│   ├── aws_ec2.txt
│   └── ...
│
│── docs/
│   ├── architecture.png
│   ├── ui.png
│   └── api-test.png
```

---

## Setup & Run Locally (Frontend) 
### 1. Install Dependencies
```bash
cd frontend/rag-chat-ui
npm install
```
### 2. Configure Environment
#### Create a .env file
```bash
VITE_API_KEY=your_api_key_here
```

### 3. Start dev server
```bash
npm run dev
```

---

## Deploy (Backend)
### Build + Deploy
```bash
cd serverless-ai-chatbot
sam build
sam deploy --guided
```

---

## Upload Knowledge Base to S3
#### Sync knowledge base text files into your S3 bucket

```bash
cd rag_data
aws s3 sync . s3://<your-rag-bucket-name>
```
---

### API Test
```bash
Invoke-RestMethod `
  -Uri "https://<api-id>.execute-api.us-east-1.amazonaws.com/Prod/hello/" `
  -Method POST `
  -Headers @{ "Content-Type" = "application/json"; "x-api-key" = "<YOUR_API_KEY>" } `
  -Body (@{prompt="What is AWS Lambda?"} | ConvertTo-Json)
```
---

## Known Limitations
- Retrieval is keyword-based (no embeddings yet)
- Only works well for topics included in upload .txt knowledge base
- Not a full "vector database" RAG pipeline (future upgrade)

---

## Future Improvements
- Add embedding-based retrieval (Bedrock Titan Embeddings)
- Store vectors in OpenSearch / DynamoDB / pgvector
- Add user authentication (Cognito)
- Add multi-tenant API keys & rate limits per user

