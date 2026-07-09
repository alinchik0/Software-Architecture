import logging
from fastapi import APIRouter
from pydantic import BaseModel
from orchestrator.graph import build_graph
from shared.observability import get_tracer


logger = logging.getLogger(__name__)

tracer = get_tracer(__name__)

router = APIRouter()

graph = build_graph()


class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
def chat(req: ChatRequest):
    with tracer.start_as_current_span("api_chat") as span:
        logger.info("api_request", extra={"user_input":req.message})

        try:
            span.set_attribute("user_input", req.message)
            print(req.message)
            result = graph.invoke({
                "input": req.message
            })

            response = result.get("output", "")

            logger.info("api_response", extra={"bot_response":response})

            span.set_attribute("response", response)
            return {"response": str(response)}

        except Exception as e:
            logger.error("api_error", extra={"error_details":str(e)})
            return {"response": f"Error: {str(e)}"}