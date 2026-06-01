from prometheus_client import Counter, Histogram

agent_transformation_total = Counter(
    'agent_transformation_total',
    'Agent transformations by outcome',
    ['status', 'model_used'],
)

model_inference_duration_seconds = Histogram(
    'model_inference_duration_seconds',
    'FastAPI inference duration',
    ['model', 'task_type'],
    buckets=(0.5, 1, 2, 5, 10, 20, 30, 60, 120),
)
