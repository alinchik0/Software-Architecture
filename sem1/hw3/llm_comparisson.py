from flask import Flask, request, jsonify
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
import torch

app = Flask(__name__)

# --------------------------
# Basic small model for baseline
# --------------------------
basic_model = pipeline(
    "text-generation",
    model="distilgpt2",
    max_length=100,
    do_sample=True,
    temperature=0.7
)

# --------------------------
# Load lightweight models
# --------------------------
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

# --------------------------
# Phi-2 model (NEW)
# --------------------------
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

print("Loading Phi-2...")
phi2_tokenizer = AutoTokenizer.from_pretrained("microsoft/phi-2")

phi2_model = AutoModelForCausalLM.from_pretrained(
    "microsoft/phi-2",
    dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    device_map="auto"   # работает только после установки accelerate
)


def generate_phi2(prompt: str):
    inputs = phi2_tokenizer(prompt, return_tensors="pt").to(phi2_model.device)
    outputs = phi2_model.generate(
        **inputs,
        max_length=200,
        temperature=0.7,
        do_sample=True
    )
    text = phi2_tokenizer.decode(outputs[0], skip_special_tokens=True)
    return text


# --------------------------
# ROUTES
# --------------------------
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


@app.route("/generate/phi2", methods=["POST"])
def generate_phi2_api():
    data = request.get_json()
    prompt = data.get("prompt", "")
    result = generate_phi2(prompt)

    # удаляем повторяющийся prompt
    if result.startswith(prompt):
        result = result[len(prompt):].strip()

    return jsonify({"model": "phi2", "response": result})


if __name__ == "__main__":
    app.run(port=5002)
