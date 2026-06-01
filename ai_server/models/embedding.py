import os

_model = None


def get_embedding_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        name = os.getenv('HF_EMBEDDING_MODEL', 'jhgan/ko-sroberta-multitask')
        _model = SentenceTransformer(name)
    return _model


def embed(text: str) -> list[float]:
    model = get_embedding_model()
    return model.encode(text).tolist()
