---
name: answer_from_materials
category: knowledge_retrieval
triggers: ["answer", "question", "explain", "what is", "tell me about"]
parameters:
  - name: query
    type: string
    required: true
---

# Answer From Materials (RAG Skill)

Retrieves relevant study materials, generates answer with self-verification, and returns citations.

## Workflow
1. **Retrieve**: Embed query → search ChromaDB → get top-5 chunks with topics
2. **Generate**: Create draft answer STRICTLY from context (no external knowledge)
3. **Verify**: Remove unsupported claims, check factual accuracy
4. **Cite**: Map answer to source chunk IDs and topics
5. **Return**: {answer, sources: [{topic, chunk_id}], confidence}

## Constraints
- NEVER use external knowledge or training data
- If context insufficient → return "Insufficient data"
- Always attach source topics for auditability
- Confidence < 0.5 → warn user

## Output Format
```json
{
  "answer": "string",
  "sources": [
    {"topic": "string", "chunk_id": "string"}
  ],
  "confidence": 0.0-1.0
}