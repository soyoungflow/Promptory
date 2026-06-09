import os

_model = None
_tokenizer = None


def is_model_loaded() -> bool:
    return _model is not None

# EC2 t3.micro/small(2GB) — B안: EXAONE-0.8B + float32 대신 float16으로 메모리 절약
# 한국어 OSS instruct (프로젝트 기본). EC2 2GB는 스왑 필수·느림 → 발표는 mock 권장.
_DEFAULT_MODEL = 'LGAI-EXAONE/EXAONE-3.5-2.4B-Instruct'


def get_model():
    global _model, _tokenizer
    if _model is None:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        model_name = os.getenv('HF_MODEL_NAME', _DEFAULT_MODEL)
        dtype_name = os.getenv('HF_TORCH_DTYPE', 'float16').lower()
        torch_dtype = torch.float16 if dtype_name == 'float16' else torch.float32

        _tokenizer = AutoTokenizer.from_pretrained(
            model_name, trust_remote_code=True, use_fast=False,
        )
        _model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch_dtype,
            low_cpu_mem_usage=True,
            device_map='cpu',
            trust_remote_code=True,
        )
        _model.eval()
    return _model, _tokenizer


def generate(prompt: str, max_new_tokens: int = 384) -> str:
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
