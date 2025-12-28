import json
import boto3
import os
import time
import logging
import re
#Adding structured logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create a S3 Client
s3 = boto3.client("s3")
RAG_BUCKET="serverless-ai-chatbot-rag"

#Create a Bedrock client
bedrock = boto3.client(
    service_name="bedrock-runtime",
    region_name=os.environ.get("AWS_REGION", "us-east-1")
)

MODEL_ID="anthropic.claude-3-haiku-20240307-v1:0"

#Adding Stopword filtering
STOPWORDS = {
            "what", "is", "the", "a", "an", "how", "why", "explain",
            "tell", "me", "about", "does", "do", "of", "to", "in"
}
'''This is the earlier S3-based rag implementation
#load Documents from S3 
def load_documents():
    response = s3.list_objects_v2(Bucket=RAG_BUCKET)
    documents = []

    for obj in response.get("Contents", []):
        key=obj["Key"]
        file_obj = s3.get_object(Bucket=RAG_BUCKET, Key=key)
        text = file_obj['Body'].read().decode('utf-8')
        documents.append({
            "key": key,
            "text": text
        })
    return documents
'''
#Chunk based RAG implementation
def load_documents():
    response = s3.list_objects_v2(Bucket=RAG_BUCKET)
    chunks=[]
    for obj in response.get("Contents", []):
        key = obj["Key"]
        file_obj = s3.get_object(Bucket=RAG_BUCKET, Key=key)
        text = file_obj['Body'].read().decode('utf-8')

        paragraphs = [p.strip() for p in text.split("\n") if len(p.strip())>40]

        for para in paragraphs:
            chunks.append({
                "source": key,
                "text": para
            })
    return chunks                  

# Keyword based retrieval    
def extract_keywords(text):
    words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
    return [word for word in words if word not in STOPWORDS]

MIN_SCORE = 1
GENERIC_TERMS = {"aws","services","cloud","service"}

'''
# My earlier simple keyword matching retrieval
def retrieve_context(user_prompt, documents, top_k=2):
    keywords = extract_keywords(user_prompt)
    scored_docs = []
    
    for doc in documents:
        score = sum(1 for word in keywords if word in doc["text"].lower() and not word in GENERIC_TERMS)
        filename = doc["key"].lower()
        if any(word in filename for word in keywords):
            score += 2  # Boost score if keyword is in filename

        #Minimum relevance threshold. This will filter out weak matches liek just "aws" & keeps omly docs with real semantic overlap.
        if score >= MIN_SCORE:
            scored_docs.append({
                "score": score,
                "key":doc["key"],
                "text":doc["text"]
            })

    scored_docs.sort(reverse=True, key=lambda x: x["score"])

    top_docs = scored_docs[:top_k]
    context_text = "\n\n".join(d["text"] for d in top_docs)
    sources = [d["key"] for d in top_docs]

    return context_text,sources
'''
def retrieve_context(user_prompt, chunks, top_k=3):
    keywords = extract_keywords(user_prompt)
    scored_chunks = []

    for chunk in chunks:
        score = sum(
            1 for word in keywords
            if word in chunk["text"].lower()
            and word not in GENERIC_TERMS
        )

        filename = chunk["source"].lower()
        if any(word in filename for word in keywords):
            score += 3  # filename relevance boost

        if score >= MIN_SCORE:
            scored_chunks.append({
                "score": score,
                "text": chunk["text"],
                "source": chunk["source"]
            })

    scored_chunks.sort(key=lambda x: x["score"], reverse=True)

    top_chunks = scored_chunks[:top_k]

    context_text = "\n\n".join(c["text"] for c in top_chunks)
    sources = list({c["source"] for c in top_chunks})

    return context_text, sources


def lambda_handler(event, context):
    try:
        #Track request lifecycle
        start_time = time.time()
        request_id = context.aws_request_id
        #1. Parse input
        body = json.loads(event.get("body", "{}"))
        user_prompt = body.get("prompt","").strip()
        #Early Exit for trivial prompts. This will lead to faster response, zero cost & no bedrock call if invoked.
        normalized_prompt = user_prompt.lower().strip()
        GREETING = ["hi", "hello", "hey", "what's up", "How are you?"]
        if any(normalized_prompt.startswith(greet) for greet in GREETING):
            #Logging early exits
            logger.info({
                "request_id": request_id,
                "event": "Early exit",
                "reason": "Unnecessary greeting",
                "prompt_length": len(user_prompt)
            })
            return response(200,{
                "response":"Hello! Ask me a Technical question."
            })

        if not user_prompt:
            return response(400, {"error":"Prompt is required."})
        
        #2. Hard Safety limits
        if len(user_prompt) > 500:
            return response(400, {"error":"Prompt is too long."})
        #Dynamic Token Control
        if len(user_prompt) < 50:
            max_tokens = 120
        else:
            max_tokens = 180

        #RAG Implementation
        #documents = load_documents()
        chunks = load_documents()
        #context, sources = retrieve_context(user_prompt, documents)
        context, sources = retrieve_context(user_prompt, chunks)

        #Logging to check if the retrieval is working properly
        logger.info({
        "event": "chunk_retrieval_debug",
        "num_chunks": len(chunks),
        "matched_chunks": len(context.split("\n\n")) if context else 0,
        "sources": sources
        })

        if not context:
            logger.info({
                "request_id": request_id,
                "event": "rag_no_context"
            })
            return response(200, {
                "prompt": user_prompt,
                "response": "I don't know based on the provided context."
            })
        #3. Build Claude request
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "system": (
                "You are a concise technical assistant."
                "Answer using the provided context ."
                "If the answer is not in the context, say you don't know.\n\n"
                f"Context:\n{context}"
                #"Avoid unnecesary details."
                #"Answer in 2-3 sentences maximum."
                #"Avoid unnecesary details."
            ),
            "max_tokens": max_tokens, #COST CONTROL Earlier this was set explicitly as 200, now changed it to max_tokens
            "temperature": 0.3, #Change from 0.5 to 0.3
            "messages": [
                
                #{
                 #   "role": "system",
                 #   "content": ("You are a concise technical assistant."
                #                "Answer in 2-3 sentences maximum."
                 #               "Avoid unnecesary details."
                #    )
                #},
                 #Commenting this out as this is OPENAI style system prompt, not needed for Claude
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        }
        #Log before calling Bedrock
        logger.info({
            "request_id": request_id,
            "event": "bedrock_call",
            "prompt_length": len(user_prompt),
            "max_tokens": max_tokens
        })

        #4. Call Bedrock Claude model
        result = bedrock.invoke_model(
            modelId = MODEL_ID,
            contentType = "application/json",
            accept = "application/json",
            body = json.dumps(payload)
        )
        
        response_body = json.loads(result['body'].read())

        ai_text = response_body["content"][0]["text"]

        #If the context contains the answer then only provide the sources
        answer_text = ai_text.lower()

        NO_ANSWER_PATTERNS = [
            "not mentioned",
            "not contain",
            "don't know",
            "do not have enough information"
        ]

        used_sources = sources
        if any(p in answer_text for p in NO_ANSWER_PATTERNS):
            used_sources = []

        #log retrieval behavior
        logger.info({
            "request_id": request_id,
            "event": "rag_retrieval",
            "context_found  ": bool(context),
            "context_length": len(context)
        })

        #log latency
        latency_ms = int((time.time() - start_time) * 1000)
        logger.info({
            "request_id": request_id,
            "event": "request_complete",
            "latency_ms": latency_ms
        })

        return response(200, {
            "prompt": user_prompt,
            "response": ai_text,
            "rag_used": bool(used_sources),
            "sources": used_sources,
            "latency_ms": latency_ms
        })
    
    except Exception as e:
        logger.error({
            "reques_id":request_id,
            "event":"unhandled_exception",
            "error":str(e)
        })
        return response(500,{
            "error":"Internal Server Error",
            "message":"Something went wrong while processing your request."
        })
    
def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token"
        },
        "body": json.dumps(body)
    }