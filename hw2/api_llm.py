from flask import Flask, request, jsonify
from transformers import pipeline

app = Flask(__name__)


basic_model = pipeline(
    "text-generation",
    model="distilgpt2",
    max_length=100,
    do_sample=True,
    temperature=0.7
)


models = {
    "distilgpt2_pipeline": pipeline(
        "text-generation",
        model="distilgpt2",
        max_length=150
    ),
    "gpt_neo_125m": pipeline(
        "text-generation",
        model="EleutherAI/gpt-neo-125M",
        max_length=150
    ),
    "tiny_llama": pipeline(
        "text-generation",
        model="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        max_length=200
    ),
}


@app.route("/")
def home():
    return "LLM Multi-Model API работает!"


@app.route("/generate/basic", methods=["POST"])
def generate_basic():
    data = request.get_json()
    prompt = data.get("prompt", "")

    result = basic_model(prompt)[0]["generated_text"]

    if result.startswith(prompt):
        result = result[len(prompt):].strip()

    return jsonify({"model": "distilgpt2_basic", "response": result})



@app.route("/generate/distilgpt2", methods=["POST"])
def generate_distilgpt2():
    data = request.get_json()
    prompt = data.get("prompt", "")
    result = models["distilgpt2_pipeline"](prompt)[0]["generated_text"]
    return jsonify({"model": "distilgpt2_pipeline", "response": result})



@app.route("/generate/gptneo", methods=["POST"])
def generate_gptneo():
    data = request.get_json()
    prompt = data.get("prompt", "")
    result = models["gpt_neo_125m"](prompt)[0]["generated_text"]
    return jsonify({"model": "gpt_neo_125m", "response": result})



@app.route("/generate/tinyllama", methods=["POST"])
def generate_tinyllama():
    data = request.get_json()
    prompt = data.get("prompt", "")
    result = models["tiny_llama"](prompt)[0]["generated_text"]
    return jsonify({"model": "tiny_llama", "response": result})


if __name__ == "__main__":
    app.run(port=5002)
