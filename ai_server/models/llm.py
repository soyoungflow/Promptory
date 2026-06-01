import os

_model = None
_tokenizer = None


def get_model():
    global _model, _tokenizer
    if _model is None:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        model_name = os.getenv('HF_MODEL_NAME', 'LGAI-EXAONE/EXAONE-3.5-2.4B-Instruct')
        _tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        _model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float32,
            device_map='cpu',
            trust_remote_code=True,
        )
    return _model, _tokenizer


def generate(prompt: str, max_new_tokens: int = 512) -> str:
    model, tokenizer = get_model()
    messages = [{'role': 'user', 'content': prompt}]
    inputs = tokenizer.apply_chat_template(
        messages, return_tensors='pt', add_generation_prompt=True,
    )
    import torch

    with torch.no_grad():
        outputs = model.generate(
            inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
        )
    return tokenizer.decode(outputs[0][inputs.shape[1]:], skip_special_tokens=True)
