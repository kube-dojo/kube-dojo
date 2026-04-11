---
title: "Model Serving"
slug: ai-ml-engineering/mlops/module-5.9-model-serving
sidebar:
  order: 610
---
> **AI/ML Engineering Track** | Complexity: `[COMPLEX]` | Time: 5-6
---
**Prerequisites**: Module 50 (ML Pipeline Orchestration)

San Francisco. March 15, 2023. 2:47 AM. Elena Vasquez had been asleep for exactly three hours when her phone exploded with alerts. The fraud detection model her team had deployed 16 hours earlier was blocking legitimate transactions at an alarming rate—$4.2 million in failed purchases so far and climbing.

The model had looked perfect in testing. Accuracy: 99.2%. False positive rate: 0.3%. The validation metrics were immaculate. What the metrics didn't capture was that the test data was six months old, and customer behavior had shifted. The new model had learned patterns that no longer existed.

Elena's hands shook as she opened her laptop. No blue-green deployment. No canary rollout. No rollback button. The team had deployed the new model by replacing the old one—a one-way door. Rolling back meant finding the old model file on someone's laptop, rebuilding the container, and pushing to production. Time estimate: four hours. Potential losses: $1 million per hour.

By the time the sun rose, the old model was restored. The company had lost $6.8 million—not from fraud, but from blocking good customers. Elena's team spent the next month building what should have existed from day one: a proper deployment pipeline with instant rollback.

> "Every deployment without a rollback plan is a bet. Sometimes you lose big."
> — Elena Vasquez, Engineering Postmortem Report

This module teaches you the patterns Elena learned the hard way: how to deploy models safely, test in production without breaking production, and always have an escape hatch.

---

## What You'll Be Able to Do

By the end of this module, you will:
- Deploy ML models as REST APIs with FastAPI
- Implement high-performance serving with gRPC
- Master deployment patterns (canary, blue-green, A/B testing)
- Optimize models for inference (ONNX, TensorRT)
- Use production serving frameworks (TorchServe, Triton)
- Implement model versioning and rollback strategies

---

## The Evolution of Model Deployment

Understanding how model deployment evolved helps explain why today's best practices exist—and why the "just upload the model" approach that worked in 2010 fails catastrophically in 2024.

### Phase 1: The Notebook Era (Pre-2012)

In the early days of ML deployment, "deployment" often meant emailing a pickle file to the web team and hoping they could figure it out. Data scientists worked in isolation, producing models in Jupyter notebooks or R scripts. The hand-off to engineering was rough—sometimes literally a USB drive with model weights.

Google's ad ranking system in the early 2000s was one of the first large-scale ML deployments. They learned painful lessons: models that worked in research environments crashed in production. Latency that was "acceptable" in batch mode became unacceptable when users were waiting. The gap between "research ML" and "production ML" was enormous.

> **Did You Know?** Google's first production ML system for ad ranking (2001-2002) initially just ran as a batch job overnight. Engineers would manually copy model files to production servers each morning. This "deployment" method worked until traffic grew so fast that yesterday's model was already stale by morning. The need for real-time model serving drove the creation of what became TensorFlow Serving.

### Phase 2: The API Era (2012-2016)

As ML became more critical to products, companies built custom serving infrastructure. Netflix created their own model serving platform. Uber built Michelangelo. Amazon developed SageMaker's predecessors. Each company reinvented the wheel because no standards existed.

REST APIs became the default interface for model serving—simple, well-understood, and compatible with existing web infrastructure. But REST wasn't designed for ML workloads. JSON parsing overhead, lack of streaming support, and no built-in batching meant engineers spent more time working around limitations than building features.

### Phase 3: The Standardization Era (2016-2020)

TensorFlow Serving (2016) was the first open-source production serving system. It introduced concepts that became industry standards: model versioning, dynamic batching, GPU support, and A/B testing infrastructure. Suddenly, teams without Google-scale engineering could deploy models professionally.

ONNX (2017) emerged from Microsoft and Facebook's collaboration, creating a universal model format. For the first time, you could train in PyTorch and deploy on TensorFlow infrastructure. This interoperability transformed the ecosystem.

> **Did You Know?** The ONNX format was announced at the 2017 Neural Information Processing Systems (NeurIPS) conference. Within two years, it had support from over 30 frameworks and hardware platforms. The key insight: model weights are just numbers. The execution engine doesn't care where those numbers came from—it just needs them in a consistent format.

### Phase 4: The Cloud-Native Era (2020-Present)

Today's model deployment leverages container orchestration (Kubernetes), service meshes (Istio), and cloud-native patterns. Models are packaged as containers, scaled automatically, and deployed with blue-green or canary strategies. The infrastructure that once required dedicated platform teams is now available as managed services.

NVIDIA's Triton Inference Server, released in 2019 and rapidly evolved since, represents the state of the art: multi-framework support, dynamic batching, ensemble models, and GPU optimization out of the box. What took custom engineering at Google in 2010 is now a single Docker command.

---

## Why Model Deployment Matters

Training a great model is only half the battle. Getting it into production, serving predictions at scale, and maintaining it over time - that's where real engineering happens.

Think of training a model like writing a play. You've got the script, you've rehearsed, and the cast knows their lines. But deployment? That's opening night on Broadway—with a live audience, real stakes, and no second takes. The play that killed in rehearsal might bomb with a real crowd. The lines that seemed perfect might fall flat at scale.

Or consider this: training a model is like building a race car in your garage. It's fast, it's powerful, it handles beautifully on test tracks. Deployment is entering that car in the Indy 500—suddenly you need pit crews (DevOps), safety equipment (monitoring), race strategy (deployment patterns), and a plan for when things go wrong (rollback). Most garage cars never make it to race day.

**The Deployment Gap**:
```
RESEARCH                           PRODUCTION
========                           ==========

Jupyter notebooks                  REST/gRPC APIs
Single GPU                         Distributed serving
Batch predictions                  Real-time (<100ms)
"Works on my machine"              99.9% uptime SLA
Manual updates                     Automated rollouts
No monitoring                      Full observability
```

**Did You Know?** According to a 2022 Gartner report, only 54% of ML models make it to production. The main barriers? Deployment complexity, lack of MLOps practices, and the gap between data science and engineering teams. This module bridges that gap.

---

## Model Serving Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    MODEL SERVING ARCHITECTURE                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   CLIENTS                                                                │
│   ┌─────────┐  ┌─────────┐  ┌─────────┐                                │
│   │   Web   │  │ Mobile  │  │ Backend │                                │
│   │   App   │  │   App   │  │ Service │                                │
│   └────┬────┘  └────┬────┘  └────┬────┘                                │
│        │           │           │                                        │
│        └───────────┴───────────┘                                        │
│                    │                                                     │
│                    ▼                                                     │
│   ┌─────────────────────────────────────────────────────────┐          │
│   │              LOAD BALANCER / API GATEWAY                 │          │
│   │         (Nginx, Kong, AWS ALB, Istio)                   │          │
│   └─────────────────────────────────────────────────────────┘          │
│                    │                                                     │
│        ┌───────────┴───────────┐                                        │
│        ▼                       ▼                                        │
│   ┌─────────┐             ┌─────────┐                                  │
│   │Model v1 │             │Model v2 │   ← Canary / A/B                 │
│   │  (90%)  │             │  (10%)  │                                  │
│   └────┬────┘             └────┬────┘                                  │
│        │                       │                                        │
│        └───────────┬───────────┘                                        │
│                    │                                                     │
│   ┌─────────────────────────────────────────────────────────┐          │
│   │              MODEL SERVING LAYER                         │          │
│   │    FastAPI / TorchServe / Triton / TF Serving           │          │
│   └─────────────────────────────────────────────────────────┘          │
│                    │                                                     │
│   ┌─────────────────────────────────────────────────────────┐          │
│   │              MODEL STORAGE                               │          │
│   │         S3 / GCS / Model Registry                       │          │
│   └─────────────────────────────────────────────────────────┘          │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## REST API with FastAPI

### Why This Module Matters

Think of web frameworks like different types of vehicles for getting your model to users. Flask is like a reliable sedan—it gets the job done, but nothing fancy. Django is like a tour bus—lots of features, but heavy and slow to start. FastAPI is like a sports car—fast out of the gate, modern design, and built for performance.

FastAPI has become the go-to framework for ML model serving because it combines speed, type safety, and automatic documentation in one package. When you're serving models that need to respond in milliseconds, every overhead matters.

FastAPI is the go-to framework for ML model serving in Python:
- **Fast**: Built on Starlette and Pydantic, async by default
- **Type-safe**: Automatic request/response validation
- **Auto-docs**: Swagger UI generated automatically
- **Production-ready**: Used by Netflix, Uber, Microsoft

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import numpy as np

app = FastAPI(
    title="ML Model API",
    description="Production model serving API",
    version="1.0.0"
)

# Request/Response Models
class PredictionRequest(BaseModel):
    features: List[float] = Field(..., min_items=1, max_items=100)
    model_version: Optional[str] = "latest"

    class Config:
        schema_extra = {
            "example": {
                "features": [0.5, 0.3, 0.8, 0.2],
                "model_version": "v1.2.0"
            }
        }

class PredictionResponse(BaseModel):
    prediction: float
    confidence: float
    model_version: str
    latency_ms: float

# Load model (in production, use proper model registry)
model = None  # Your trained model

@app.on_event("startup")
async def load_model():
    global model
    model = load_trained_model("models/production/model.pkl")

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """
    Generate prediction for input features.
    """
    import time
    start = time.time()

    try:
        # Preprocess
        features = np.array(request.features).reshape(1, -1)

        # Predict
        prediction = model.predict(features)[0]
        confidence = model.predict_proba(features).max()

        latency = (time.time() - start) * 1000

        return PredictionResponse(
            prediction=float(prediction),
            confidence=float(confidence),
            model_version=request.model_version,
            latency_ms=latency
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "model_loaded": model is not None}

@app.get("/model/info")
async def model_info():
    """Get model metadata."""
    return {
        "name": "churn_predictor",
        "version": "1.2.0",
        "framework": "sklearn",
        "features": 4,
        "classes": ["no_churn", "churn"]
    }
```

### Batch Predictions

```python
from fastapi import BackgroundTasks
from typing import List
import asyncio

class BatchRequest(BaseModel):
    instances: List[List[float]]
    async_mode: bool = False

class BatchResponse(BaseModel):
    predictions: List[float]
    batch_size: int
    total_latency_ms: float

@app.post("/predict/batch", response_model=BatchResponse)
async def predict_batch(request: BatchRequest):
    """
    Batch prediction for multiple instances.
    More efficient than individual calls.
    """
    start = time.time()

    features = np.array(request.instances)
    predictions = model.predict(features).tolist()

    return BatchResponse(
        predictions=predictions,
        batch_size=len(request.instances),
        total_latency_ms=(time.time() - start) * 1000
    )

# Async batch processing
@app.post("/predict/async")
async def predict_async(
    request: BatchRequest,
    background_tasks: BackgroundTasks
):
    """
    Submit batch for async processing.
    Returns job_id to check status later.
    """
    job_id = generate_job_id()
    background_tasks.add_task(
        process_batch_async,
        job_id,
        request.instances
    )
    return {"job_id": job_id, "status": "processing"}
```

**Did You Know?** FastAPI was created by Sebastián Ramírez in 2018. He was frustrated with the complexity of Flask + Marshmallow + swagger-ui combinations. FastAPI combines all these features with modern Python type hints. It quickly became the fastest-growing Python web framework, reaching 50k GitHub stars in just 4 years.

---

## gRPC for High-Performance Serving

### Why gRPC?

Think of REST and gRPC like sending a letter versus using Morse code. REST sends readable JSON—human-friendly, but with overhead. gRPC uses Protocol Buffers—compact binary data that machines can parse instantly. When you're sending millions of messages per second, that overhead adds up.

gRPC is like the express lane at the toll booth: stricter rules (you need exact change), but much faster throughput. REST is the regular lane: more flexible (cash, card, coins), but slower when traffic peaks.

gRPC is Google's high-performance RPC framework, ideal for:
- **Low latency**: Binary protocol (Protocol Buffers)
- **Streaming**: Bi-directional streaming support
- **Strong typing**: Generated client/server code
- **Multi-language**: Same proto works in Python, Go, Java, etc.

```
REST vs gRPC
============

REST (JSON):
┌─────────────────────────────────────────┐
│ {"features": [0.5, 0.3, 0.8], "id": 1}  │
│ ~50 bytes, text parsing required        │
└─────────────────────────────────────────┘

gRPC (Protobuf):
┌─────────────────────────────────────────┐
│ 0x0a0c0d0000003f15cdcc4c3e1d...        │
│ ~20 bytes, binary, no parsing           │
└─────────────────────────────────────────┘

Latency comparison:
REST:  ~10-50ms overhead
gRPC:  ~1-5ms overhead
```

### Protocol Buffer Definition

```protobuf
// model_service.proto

syntax = "proto3";

package ml_serving;

service ModelService {
    // Unary prediction
    rpc Predict(PredictRequest) returns (PredictResponse);

    // Streaming predictions (for real-time data)
    rpc PredictStream(stream PredictRequest) returns (stream PredictResponse);

    // Batch prediction
    rpc PredictBatch(BatchRequest) returns (BatchResponse);

    // Model info
    rpc GetModelInfo(Empty) returns (ModelInfo);
}

message PredictRequest {
    repeated float features = 1;
    string model_version = 2;
}

message PredictResponse {
    float prediction = 1;
    float confidence = 2;
    string model_version = 3;
    float latency_ms = 4;
}

message BatchRequest {
    repeated PredictRequest instances = 1;
}

message BatchResponse {
    repeated PredictResponse predictions = 1;
    int32 batch_size = 2;
    float total_latency_ms = 3;
}

message ModelInfo {
    string name = 1;
    string version = 2;
    string framework = 3;
    int32 num_features = 4;
    repeated string classes = 5;
}

message Empty {}
```

### gRPC Server Implementation

```python
import grpc
from concurrent import futures
import model_service_pb2
import model_service_pb2_grpc
import numpy as np
import time

class ModelServicer(model_service_pb2_grpc.ModelServiceServicer):
    def __init__(self, model):
        self.model = model

    def Predict(self, request, context):
        """Single prediction."""
        start = time.time()

        features = np.array(request.features).reshape(1, -1)
        prediction = self.model.predict(features)[0]
        confidence = self.model.predict_proba(features).max()

        return model_service_pb2.PredictResponse(
            prediction=float(prediction),
            confidence=float(confidence),
            model_version=request.model_version or "v1.0",
            latency_ms=(time.time() - start) * 1000
        )

    def PredictStream(self, request_iterator, context):
        """Streaming predictions - process as they arrive."""
        for request in request_iterator:
            features = np.array(request.features).reshape(1, -1)
            prediction = self.model.predict(features)[0]

            yield model_service_pb2.PredictResponse(
                prediction=float(prediction),
                confidence=0.95,
                model_version="v1.0",
                latency_ms=1.0
            )

    def PredictBatch(self, request, context):
        """Batch prediction."""
        start = time.time()

        responses = []
        for instance in request.instances:
            features = np.array(instance.features).reshape(1, -1)
            prediction = self.model.predict(features)[0]

            responses.append(model_service_pb2.PredictResponse(
                prediction=float(prediction),
                confidence=0.95,
                model_version="v1.0"
            ))

        return model_service_pb2.BatchResponse(
            predictions=responses,
            batch_size=len(responses),
            total_latency_ms=(time.time() - start) * 1000
        )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    model_service_pb2_grpc.add_ModelServiceServicer_to_server(
        ModelServicer(model), server
    )
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()
```

---

## Deployment Patterns

Deployment patterns are like different strategies for renovating a restaurant while it's still serving customers. You can't just close for six months—you need to keep the kitchen running. Each pattern represents a different approach to this challenge.

**Blue-Green** is like building an identical restaurant next door, then moving all customers over in one night. Instant cutover, instant rollback if the new kitchen catches fire.

**Canary** is like opening a small section of the new restaurant first—just two tables. If those customers love it, expand. If they get food poisoning, you've only affected 5% of diners.

**A/B Testing** is like running two menus simultaneously and measuring which dishes sell better. It's not about safety—it's about learning which version performs best.

### Pattern 1: Blue-Green Deployment

```
BLUE-GREEN DEPLOYMENT
=====================

Before update:
┌─────────────────────────────────────────┐
│              LOAD BALANCER              │
└────────────────────┬────────────────────┘
                     │
                     ▼
              ┌─────────────┐
              │   BLUE      │  ← 100% traffic
              │   (v1.0)    │
              └─────────────┘
              ┌─────────────┐
              │   GREEN     │  ← 0% traffic (standby)
              │   (v1.0)    │
              └─────────────┘

Deploy v2.0 to GREEN:
┌─────────────────────────────────────────┐
│              LOAD BALANCER              │
└────────────────────┬────────────────────┘
                     │
                     ▼
              ┌─────────────┐
              │   BLUE      │  ← 100% traffic
              │   (v1.0)    │
              └─────────────┘
              ┌─────────────┐
              │   GREEN     │  ← Testing v2.0
              │   (v2.0)    │
              └─────────────┘

Switch traffic:
┌─────────────────────────────────────────┐
│              LOAD BALANCER              │
└────────────────────┬────────────────────┘
                     │
                     ▼
              ┌─────────────┐
              │   BLUE      │  ← 0% traffic (standby)
              │   (v1.0)    │
              └─────────────┘
              ┌─────────────┐
              │   GREEN     │  ← 100% traffic
              │   (v2.0)    │
              └─────────────┘

Rollback if needed: instant switch back to BLUE
```

### Pattern 2: Canary Deployment

```
CANARY DEPLOYMENT
=================

Progressive rollout:

Phase 1: 5% canary
┌─────────────────────────────────────────┐
│              LOAD BALANCER              │
└────────────────────┬────────────────────┘
                     │
          ┌──────────┴──────────┐
          │                     │
          ▼                     ▼
    ┌─────────────┐       ┌─────────────┐
    │   STABLE    │       │   CANARY    │
    │   (v1.0)    │       │   (v2.0)    │
    │    95%      │       │     5%      │
    └─────────────┘       └─────────────┘

Phase 2: Monitor metrics, increase to 25%
Phase 3: If healthy, increase to 50%
Phase 4: If healthy, promote to 100%

Automatic rollback if:
- Error rate > threshold
- Latency > threshold
- Custom metric violations
```

### Pattern 3: A/B Testing

```python
class ABTestRouter:
    """
    Route requests to different model versions for A/B testing.
    """

    def __init__(self):
        self.experiments = {}

    def create_experiment(
        self,
        experiment_id: str,
        control_model: str,
        treatment_model: str,
        traffic_split: float = 0.5
    ):
        """Create new A/B experiment."""
        self.experiments[experiment_id] = {
            "control": control_model,
            "treatment": treatment_model,
            "split": traffic_split,
            "metrics": {"control": [], "treatment": []}
        }

    def route_request(self, experiment_id: str, user_id: str) -> str:
        """
        Deterministically route user to model variant.
        Same user always gets same variant (for consistency).
        """
        experiment = self.experiments[experiment_id]

        # Hash user_id for deterministic assignment
        hash_value = hash(f"{experiment_id}:{user_id}") % 100
        is_treatment = hash_value < (experiment["split"] * 100)

        return experiment["treatment"] if is_treatment else experiment["control"]

    def record_outcome(
        self,
        experiment_id: str,
        variant: str,
        prediction: float,
        actual: float
    ):
        """Record prediction outcome for analysis."""
        self.experiments[experiment_id]["metrics"][variant].append({
            "prediction": prediction,
            "actual": actual,
            "correct": (prediction > 0.5) == (actual > 0.5)
        })

    def analyze_experiment(self, experiment_id: str) -> dict:
        """
        Statistical analysis of A/B test results.
        """
        from scipy import stats

        exp = self.experiments[experiment_id]
        control = exp["metrics"]["control"]
        treatment = exp["metrics"]["treatment"]

        control_accuracy = sum(m["correct"] for m in control) / len(control)
        treatment_accuracy = sum(m["correct"] for m in treatment) / len(treatment)

        # Statistical significance test
        control_correct = [m["correct"] for m in control]
        treatment_correct = [m["correct"] for m in treatment]

        t_stat, p_value = stats.ttest_ind(control_correct, treatment_correct)

        return {
            "control_accuracy": control_accuracy,
            "treatment_accuracy": treatment_accuracy,
            "improvement": treatment_accuracy - control_accuracy,
            "p_value": p_value,
            "significant": p_value < 0.05,
            "recommendation": "deploy_treatment" if (
                treatment_accuracy > control_accuracy and p_value < 0.05
            ) else "keep_control"
        }
```

**Did You Know?** Netflix runs thousands of A/B tests simultaneously. Their ML models for recommendations are constantly being tested against each other. In 2016, they estimated that their recommendation system is worth $1 billion per year in retained subscribers - all validated through rigorous A/B testing.

---

## Model Optimization

Model optimization is like tuning a car for a race. Your stock model (fresh from training) works fine for casual driving. But for production—where every millisecond counts and costs add up—you need to optimize.

Think of ONNX like a universal adapter for model formats. Just as a USB-C adapter lets you connect any device to any port, ONNX lets you run models trained in PyTorch on TensorFlow infrastructure, or deploy Keras models to specialized inference hardware. It's the Esperanto of machine learning.

TensorRT, meanwhile, is like a professional pit crew that takes your race car apart and rebuilds it specifically for the track you're racing on. The car is faster, but it only works on NVIDIA circuits. Worth it? If you're running millions of inferences per day, absolutely.

### ONNX: Universal Model Format

ONNX (Open Neural Network Exchange) allows you to:
- Export models from any framework
- Optimize for inference
- Deploy anywhere

```python
import onnx
import onnxruntime as ort
import torch

# Export PyTorch model to ONNX
def export_to_onnx(model, sample_input, output_path):
    """Export PyTorch model to ONNX format."""
    model.eval()

    torch.onnx.export(
        model,
        sample_input,
        output_path,
        export_params=True,
        opset_version=14,
        do_constant_folding=True,
        input_names=['input'],
        output_names=['output'],
        dynamic_axes={
            'input': {0: 'batch_size'},
            'output': {0: 'batch_size'}
        }
    )

    # Verify the model
    onnx_model = onnx.load(output_path)
    onnx.checker.check_model(onnx_model)
    print(f"Model exported to {output_path}")

# Run inference with ONNX Runtime
class ONNXPredictor:
    def __init__(self, model_path: str):
        # Use GPU if available
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
        self.session = ort.InferenceSession(model_path, providers=providers)

        # Get input/output names
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name

    def predict(self, features: np.ndarray) -> np.ndarray:
        """Run inference."""
        return self.session.run(
            [self.output_name],
            {self.input_name: features.astype(np.float32)}
        )[0]

    def benchmark(self, features: np.ndarray, iterations: int = 100) -> dict:
        """Benchmark inference performance."""
        import time

        # Warmup
        for _ in range(10):
            self.predict(features)

        # Benchmark
        latencies = []
        for _ in range(iterations):
            start = time.time()
            self.predict(features)
            latencies.append((time.time() - start) * 1000)

        return {
            "mean_ms": np.mean(latencies),
            "p50_ms": np.percentile(latencies, 50),
            "p95_ms": np.percentile(latencies, 95),
            "p99_ms": np.percentile(latencies, 99),
            "throughput_qps": 1000 / np.mean(latencies)
        }
```

### TensorRT Optimization

```python
# TensorRT for NVIDIA GPU optimization
import tensorrt as trt

def optimize_with_tensorrt(onnx_path: str, engine_path: str):
    """
    Convert ONNX model to TensorRT engine.
    Can provide 2-5x speedup on NVIDIA GPUs.
    """
    logger = trt.Logger(trt.Logger.WARNING)
    builder = trt.Builder(logger)
    network = builder.create_network(
        1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH)
    )
    parser = trt.OnnxParser(network, logger)

    # Parse ONNX
    with open(onnx_path, 'rb') as f:
        if not parser.parse(f.read()):
            for error in range(parser.num_errors):
                print(parser.get_error(error))
            raise RuntimeError("ONNX parsing failed")

    # Configure builder
    config = builder.create_builder_config()
    config.max_workspace_size = 1 << 30  # 1GB

    # Enable FP16 for faster inference (with minimal accuracy loss)
    if builder.platform_has_fast_fp16:
        config.set_flag(trt.BuilderFlag.FP16)

    # Build engine
    engine = builder.build_engine(network, config)

    # Save
    with open(engine_path, 'wb') as f:
        f.write(engine.serialize())

    print(f"TensorRT engine saved to {engine_path}")
```

**Performance Comparison**:
```
Model: ResNet-50, Batch Size: 1, GPU: A100

Framework          Latency (ms)    Throughput (QPS)
─────────────────────────────────────────────────
PyTorch (eager)       15.2              66
PyTorch (compiled)     8.5             118
ONNX Runtime           6.2             161
TensorRT FP32          4.1             244
TensorRT FP16          2.3             435
TensorRT INT8          1.5             667
```

---

## Production Serving Frameworks

When your model outgrows FastAPI, you graduate to production serving frameworks. Think of these like the difference between cooking at home versus running a restaurant kitchen. FastAPI is your home kitchen—flexible, you control everything, perfect for small batches. TorchServe and Triton are commercial kitchens—standardized processes, specialized equipment, designed for scale.

The trade-off? Commercial kitchens require more setup and training, but they handle rush hour without breaking a sweat. If you're serving 10 requests per second, FastAPI works fine. At 10,000 requests per second, you need the industrial-grade tools.

### TorchServe

```python
# TorchServe handler example
# Save as model_handler.py

from ts.torch_handler.base_handler import BaseHandler
import torch
import json

class ModelHandler(BaseHandler):
    def __init__(self):
        super().__init__()
        self.model = None

    def initialize(self, context):
        """Load the model."""
        self.manifest = context.manifest
        model_dir = context.system_properties.get("model_dir")

        # Load model
        model_path = f"{model_dir}/model.pt"
        self.model = torch.jit.load(model_path)
        self.model.eval()

    def preprocess(self, data):
        """Preprocess input data."""
        inputs = []
        for row in data:
            input_data = row.get("data") or row.get("body")
            if isinstance(input_data, (bytes, bytearray)):
                input_data = json.loads(input_data.decode('utf-8'))
            inputs.append(torch.tensor(input_data["features"]))
        return torch.stack(inputs)

    def inference(self, inputs):
        """Run model inference."""
        with torch.no_grad():
            outputs = self.model(inputs)
        return outputs

    def postprocess(self, outputs):
        """Format outputs for response."""
        predictions = outputs.numpy().tolist()
        return [{"prediction": p} for p in predictions]
```

### Triton Inference Server

```python
# Triton model configuration
# config.pbtxt

name: "ensemble_model"
platform: "ensemble"
max_batch_size: 64

input [
  {
    name: "INPUT"
    data_type: TYPE_FP32
    dims: [ -1, 128 ]  # Dynamic batch, 128 features
  }
]

output [
  {
    name: "OUTPUT"
    data_type: TYPE_FP32
    dims: [ -1, 1 ]
  }
]

ensemble_scheduling {
  step [
    {
      model_name: "preprocessing"
      model_version: -1
      input_map {
        key: "INPUT"
        value: "INPUT"
      }
      output_map {
        key: "PROCESSED"
        value: "preprocessed"
      }
    },
    {
      model_name: "main_model"
      model_version: -1
      input_map {
        key: "preprocessed"
        value: "PROCESSED"
      }
      output_map {
        key: "OUTPUT"
        value: "OUTPUT"
      }
    }
  ]
}
```

---

## Model Versioning & Rollback

Think of model versioning like version control for documents—but with higher stakes. Git tracks every change to your code. A model registry tracks every version of your model, with its metrics, training data, and deployment history.

The rollback capability is your "undo" button for production. Like how Google Docs lets you restore any previous version of a document, a good model registry lets you restore any previous version of your model—instantly. When your new fraud model starts blocking legitimate customers at 3 AM, you want that undo button to work.

```python
class ModelRegistry:
    """
    Simple model registry for version management.
    """

    def __init__(self, storage_path: str):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.registry_file = self.storage_path / "registry.json"
        self.registry = self._load_registry()

    def _load_registry(self) -> dict:
        if self.registry_file.exists():
            return json.loads(self.registry_file.read_text())
        return {"models": {}, "production": {}}

    def _save_registry(self):
        self.registry_file.write_text(json.dumps(self.registry, indent=2))

    def register_model(
        self,
        model_name: str,
        version: str,
        model_path: str,
        metrics: dict,
        metadata: dict = None
    ):
        """Register a new model version."""
        if model_name not in self.registry["models"]:
            self.registry["models"][model_name] = {}

        self.registry["models"][model_name][version] = {
            "path": model_path,
            "metrics": metrics,
            "metadata": metadata or {},
            "registered_at": datetime.now().isoformat(),
            "stage": "staging"
        }

        self._save_registry()
        return f"Registered {model_name}:{version}"

    def promote_to_production(self, model_name: str, version: str):
        """Promote a model version to production."""
        if model_name not in self.registry["models"]:
            raise ValueError(f"Model {model_name} not found")
        if version not in self.registry["models"][model_name]:
            raise ValueError(f"Version {version} not found")

        # Demote current production
        if model_name in self.registry["production"]:
            old_version = self.registry["production"][model_name]
            self.registry["models"][model_name][old_version]["stage"] = "archived"

        # Promote new version
        self.registry["models"][model_name][version]["stage"] = "production"
        self.registry["production"][model_name] = version

        self._save_registry()
        return f"Promoted {model_name}:{version} to production"

    def rollback(self, model_name: str, to_version: str):
        """Rollback to a previous version."""
        return self.promote_to_production(model_name, to_version)

    def get_production_model(self, model_name: str) -> dict:
        """Get current production model info."""
        if model_name not in self.registry["production"]:
            raise ValueError(f"No production model for {model_name}")

        version = self.registry["production"][model_name]
        return {
            "version": version,
            **self.registry["models"][model_name][version]
        }
```

---

## Comparison: Serving Frameworks

```
┌────────────────┬─────────────┬─────────────┬─────────────┬─────────────┐
│    Feature     │   FastAPI   │ TorchServe  │   Triton    │ TF Serving  │
├────────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ Framework      │ Any         │ PyTorch     │ Multi       │ TensorFlow  │
├────────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ Protocol       │ REST        │ REST/gRPC   │ REST/gRPC   │ REST/gRPC   │
├────────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ Batching       │ Manual      │ Dynamic     │ Dynamic     │ Dynamic     │
├────────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ GPU Support    │ Manual      │ Built-in    │ Built-in    │ Built-in    │
├────────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ Model Format   │ Any         │ TorchScript │ ONNX/TRT    │ SavedModel  │
├────────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ Complexity     │ Low         │ Medium      │ High        │ Medium      │
├────────────────┼─────────────┼─────────────┼─────────────┼─────────────┤
│ Use Case       │ Simple      │ PyTorch     │ High perf   │ TF models   │
│                │ APIs        │ models      │ multi-model │             │
└────────────────┴─────────────┴─────────────┴─────────────┴─────────────┘
```

---

## Best Practices

These best practices come from hard-won experience—every one of them exists because someone learned the lesson the hard way. Think of them like the safety rules in a chemistry lab: they seem obvious once you've seen what happens when you ignore them.

### 1. Health Checks

Health checks are like the vital signs monitors in a hospital. Liveness checks ask "is the patient alive?" Readiness checks ask "is the patient ready for visitors?" Kubernetes uses these to decide when to restart your container (liveness) and when to send traffic (readiness).

Without health checks, Kubernetes has no way to know if your model is actually working. Your container might be running but your model might have failed to load. Traffic keeps flowing to a server that can only return errors.

```python
@app.get("/health")
async def health():
    """Liveness check."""
    return {"status": "alive"}

@app.get("/ready")
async def ready():
    """Readiness check - is the model loaded?"""
    if model is None:
        raise HTTPException(503, "Model not loaded")
    return {"status": "ready", "model_version": model.version}
```

### 2. Graceful Shutdown

```python
import signal

class GracefulShutdown:
    def __init__(self):
        self.shutdown = False
        signal.signal(signal.SIGTERM, self._handler)
        signal.signal(signal.SIGINT, self._handler)

    def _handler(self, signum, frame):
        print("Shutdown signal received")
        self.shutdown = True

    async def wait_for_requests(self, timeout: int = 30):
        """Wait for in-flight requests to complete."""
        start = time.time()
        while active_requests > 0 and (time.time() - start) < timeout:
            await asyncio.sleep(0.1)
```

### 3. Request Validation

```python
from pydantic import validator

class PredictionRequest(BaseModel):
    features: List[float]

    @validator('features')
    def validate_features(cls, v):
        if len(v) != 10:
            raise ValueError(f"Expected 10 features, got {len(v)}")
        if any(not (-100 <= f <= 100) for f in v):
            raise ValueError("Features must be in range [-100, 100]")
        return v
```

---

## Production War Stories: Deployment Disasters and Triumphs

Learning from real-world deployment experiences helps you avoid common pitfalls and appreciate why these patterns exist.

### The Latency Cliff: Uber's Surge Pricing Incident (2017)

**San Francisco. New Year's Eve, 2017.** Uber's dynamic pricing model was critical for matching supply and demand during peak hours. When traffic spiked at midnight, their model serving infrastructure couldn't keep up. Predictions that normally took 50ms started taking 3 seconds.

The problem? Their batch processing logic was tuned for average load, not peak load. During normal hours, the model could batch requests efficiently. At 10x traffic, the batching buffer filled faster than the model could process, creating cascading delays. Drivers saw stale prices. Riders saw errors. Both sides churned.

**What went wrong:**
1. No load testing at peak capacity
2. Static batch configuration that didn't adapt to load
3. No circuit breaker to shed load gracefully

**The fix:**
- Implemented adaptive batching that adjusts to queue depth
- Added circuit breakers that return cached predictions under extreme load
- Deployed pre-warming scripts that run before predicted peak hours
- Created separate "fast path" for premium users with guaranteed latency SLAs

**Lesson**: Test at 10x your expected peak load. The cliff between "handles load" and "falls over" is steeper than you think.

### The Feature Store Disaster: Stripe's ML Incident (2021)

**San Francisco. March 2021.** Stripe's fraud detection model suddenly started flagging 40% of legitimate transactions. The model hadn't changed. The code hadn't changed. What happened?

A routine feature store update had changed how one feature was computed. The training data used the old computation. The production system used the new computation. Same feature name, different values. The model was getting inputs it had never seen during training.

> **Did You Know?** This class of bug—training/serving skew—is so common that Google published an entire paper about it ("Towards ML Engineering: A Brief History Of TensorFlow Extended"). They found that feature computation inconsistency caused 60% of their ML production incidents in one year. Feature stores exist primarily to prevent this exact problem.

**What went wrong:**
1. Feature computation was duplicated in training and serving code
2. No automated tests to verify training/serving consistency
3. Feature schema was not versioned with the model

**The fix:**
- Migrated to a feature store that serves the same features to training and inference
- Added automated tests that compare feature values between environments
- Versioned feature schemas alongside model versions
- Implemented a "feature replay" system that recomputes training features with production logic before deployment

**Lesson**: Training/serving skew is the silent killer of ML systems. The same code must compute features in both environments.

### The Cold Start Problem: Netflix's Recommendation Latency

**Los Gatos, California. 2019.** Netflix's recommendation models are among the most sophisticated in the industry. But they had a problem: the first recommendation after a model update took 15 seconds. Subsequent requests were fast (50ms), but that first request was a killer.

The culprit? Model initialization. Their ensemble model loaded 47 sub-models, each requiring its own initialization, GPU memory allocation, and warm-up inference. On a cold container, this took 15 seconds. Users hitting a freshly scaled instance got a loading spinner instead of recommendations.

**The fix:**
1. Pre-warming: New containers run inference on dummy data before receiving traffic
2. Lazy loading: Sub-models load on-demand rather than all at startup
3. Model slimming: Reduced the ensemble from 47 to 23 models with minimal accuracy loss
4. Keep-alive inference: Periodic dummy requests prevent models from being evicted from GPU memory

**Lesson**: Cold start latency is a deployment concern, not a model concern. Plan for initialization time.

---

## Common Mistakes and How to Avoid Them

### Mistake 1: Deploying Without Rollback Capability

The most common—and most expensive—deployment mistake is deploying without a rollback plan. When your new model causes problems, you need to restore the old one instantly.

**The problem:**
```
# BAD: Overwriting the production model
cp new_model.pt /models/production/model.pt
# There is no old model anymore. Rollback = find it on someone's laptop.

# GOOD: Versioned deployment
cp new_model.pt /models/v2.1.0/model.pt
ln -sf /models/v2.1.0 /models/current
# Rollback = ln -sf /models/v2.0.0 /models/current
```

**Why it happens**: Teams under deadline pressure skip the "extra" work of versioning. They tell themselves "this model is thoroughly tested, we won't need to rollback." Then they need to rollback.

**The solution**: Automate versioned deployments. Make it impossible to deploy without creating a new version. Blue-green deployment gives you rollback for free—the old environment is still running.

### Mistake 2: Ignoring the 99th Percentile

Most teams monitor average latency. "Our p50 is 45ms, we're good!" Then users complain about slowness. Why? Because p99 is 2 seconds.

**The problem:**
- P50 = 50% of requests are faster than this
- P99 = 99% of requests are faster than this
- That 1% slow request might hit your most important users

At scale, 1% is a lot. If you serve 10 million predictions per day, 1% means 100,000 users experience slow predictions. Those users complain, churn, or lose trust.

**The solution:**
- Alert on P95 and P99, not just P50
- Investigate spikes in tail latency
- Set SLOs based on percentiles, not averages
- Use histograms, not averages, for latency dashboards

### Mistake 3: Not Testing with Production Data

Models that perform brilliantly on test data can fail spectacularly on production data. The test data was collected in 2022. Production data reflects 2024 user behavior. The distribution has shifted.

**Why it happens**: Privacy concerns, data access restrictions, or simply not thinking about it. Teams test with convenient data, not realistic data.

**The solution:**
- Shadow deployment: Run new models on production traffic without serving results
- Data replay: Use anonymized samples of recent production data for testing
- Synthetic data generation: Create test data that mirrors production distributions
- A/B testing: Let real users validate the model (with a small percentage first)

> **Did You Know?** Google's ML teams maintain a "golden dataset" for each model—a curated set of production examples that represent critical use cases. Before any deployment, models must perform correctly on this golden dataset. The dataset is updated quarterly to reflect current data distributions.

### Mistake 4: Skipping Load Testing

"It worked in dev" is the battle cry of ML engineers who've never load tested their deployments. A model that serves 10 requests per second on your laptop will not magically scale to 10,000 RPS in production.

**The problem:**
- Memory leaks that only appear after 1 million requests
- GPU memory fragmentation that crashes the server after hours of operation
- Database connections that exhaust under load
- Batch processing assumptions that break at scale

**The solution:**
- Load test at 2-5x expected peak traffic
- Run soak tests (sustained load over hours) to find memory leaks
- Test failure modes: What happens when the database is slow? When GPU memory is exhausted?
- Implement graceful degradation: Return cached predictions rather than errors under extreme load

---

## Interview Prep: Model Deployment

These questions appear frequently in ML engineering and MLOps interviews.

### Common Questions

**Q: "Walk me through how you would deploy a new model to production."**

**Strong Answer**: "I'd follow a structured process. First, validate the model offline: check accuracy, latency, and resource requirements against production constraints. Second, package the model as a versioned artifact—ideally a container with all dependencies pinned. Third, deploy to a staging environment that mirrors production and run integration tests with realistic traffic patterns. Fourth, deploy using a canary strategy: start with 1% of traffic, monitor metrics for 30 minutes, gradually increase to 10%, then 50%, then 100%. Throughout, I'd track accuracy metrics, latency percentiles (especially p99), and error rates. If any metric degrades beyond thresholds, automatic rollback kicks in. Finally, I'd keep the previous version running in standby for 48 hours in case issues emerge later."

**Q: "How would you handle a situation where your deployed model's latency suddenly increased?"**

**Strong Answer**: "I'd start with data gathering: When did it start? Did anything change (deployment, traffic, upstream services)? Is it all requests or specific types? Then I'd check the usual suspects: GPU memory fragmentation, model warmth (cold start), batch queue depth, input preprocessing time, downstream service latency. I'd look at metrics dashboards for correlation—did CPU spike? Memory? Network? If it's sudden, it's often external (traffic spike, upstream slowness). If it's gradual, it might be memory leak or resource exhaustion. For immediate mitigation, I might scale horizontally, enable request shedding, or rollback if a recent deployment correlates. Long-term, I'd add more granular latency instrumentation to pinpoint where time is spent."

**Q: "Explain the difference between blue-green and canary deployments. When would you use each?"**

**Strong Answer**: "Blue-green deploys two identical environments, switching all traffic at once. Canary gradually shifts traffic from old to new version. I'd use blue-green for simple deployments where I want instant, atomic cutover and instant rollback—especially when the change is well-tested and low-risk. I'd use canary for higher-risk changes or when I need to validate the model's behavior on real traffic before full deployment. Canary is also better when the deployment takes time to warm up, since you can gradually increase traffic as instances warm. The trade-off: blue-green is simpler but requires 2x infrastructure during deployment. Canary is more complex but provides safer rollouts for risky changes."

**Q: "How would you implement model versioning and ensure reproducibility?"**

**Strong Answer**: "Reproducibility requires versioning three things: code, data, and model artifacts. For code, git with tagged releases. For data, DVC or a feature store with point-in-time queries. For models, a model registry like MLflow that stores the model artifact, its metrics, the git commit that produced it, and the data version it was trained on. Each production model should be tagged with a manifest containing all this information. When I need to reproduce a model, I can checkout the exact code, retrieve the exact data version, and verify that retraining produces equivalent results. For inference, I version the entire serving container—model, dependencies, and serving code together—so I can deploy any historical version with `docker run model:v2.3.1`."

---

## The Economics of Model Deployment

Understanding costs helps you make pragmatic decisions about deployment infrastructure.

### Cost Components

| Component | Typical Cost | Notes |
|-----------|--------------|-------|
| Compute (CPU) | $0.05-0.10/hour/vCPU | For preprocessing, lightweight models |
| Compute (GPU) | $0.50-4.00/hour | A10G: $0.50, A100: $3-4 |
| Load balancer | $0.025/hour + $0.008/GB | Often overlooked fixed cost |
| Storage (model artifacts) | $0.02/GB/month | Minimal unless you keep many versions |
| Network egress | $0.09/GB | Can add up with high throughput |
| Model registry | $0-500/month | Free tiers available, enterprise costs more |

### Cost Optimization Strategies

**1. Right-size your instances**: Most ML serving is over-provisioned. Profile your actual resource usage and right-size. A model that uses 2GB of GPU memory doesn't need a 40GB A100.

**2. Use spot/preemptible instances for batch inference**: For offline batch predictions, spot instances provide 60-90% cost savings. Just ensure your job can handle interruption.

**3. Optimize model size**: A quantized INT8 model is 4x smaller and often 2-3x faster than FP32, with minimal accuracy loss. For serving, this translates directly to cost savings.

**4. Implement request batching**: GPUs are most efficient when processing batches. Dynamic batching can increase throughput by 3-5x, proportionally reducing cost per prediction.

**5. Use caching strategically**: If 30% of your requests are repeated (same user, same input), caching can reduce inference costs by 30%. This is common in recommendation systems.

### Benchmark: What Teams Actually Pay

Based on industry surveys and published case studies:

| Scale | Monthly Cost | Cost per 1M Predictions |
|-------|-------------|-------------------------|
| Small (100K/day) | $500-2,000 | $15-60 |
| Medium (10M/day) | $5,000-20,000 | $1.50-6 |
| Large (1B/day) | $100,000-500,000 | $0.10-0.50 |

At scale, infrastructure optimization becomes critical. A 10% improvement at 1 billion predictions per day is $10,000-50,000 monthly savings.

> **Did You Know?** OpenAI reportedly spends over $700,000 per day on inference compute for ChatGPT (as of early 2023). At that scale, even a 1% efficiency improvement saves $7,000 daily—$2.5 million per year. This is why companies like OpenAI invest heavily in inference optimization, including custom hardware and kernel-level optimizations.

---

## Future Trends in Model Deployment

### Trend 1: Serverless Inference

AWS Lambda, Google Cloud Functions, and Azure Functions increasingly support ML inference. The appeal: zero infrastructure management, automatic scaling, pay-per-invocation pricing. The limitation: cold start latency and memory constraints for large models.

Expect serverless options to improve dramatically as providers add GPU support and pre-warming capabilities. For models under 1GB with latency SLOs above 500ms, serverless will become the default choice by 2026.

### Trend 2: Edge Deployment

Running models on edge devices (phones, IoT, embedded systems) reduces latency and costs while improving privacy. Apple's Neural Engine, Google's Edge TPU, and NVIDIA's Jetson are making on-device inference practical.

The challenge: edge devices have limited compute and memory. Techniques like quantization, pruning, and knowledge distillation make models small enough for edge deployment while maintaining acceptable accuracy.

### Trend 3: Model Compilation

Just-in-time compilation for ML models (PyTorch 2.0's compile, JAX's XLA) promises significant speedups without manual optimization. The trend is toward "write in Python, run at C++ speed."

Expect model compilation to become the default, with serving frameworks automatically compiling models during deployment. Manual ONNX/TensorRT conversion will become increasingly rare.

### Trend 4: Unified Inference Platforms

The fragmentation between CPU serving (FastAPI), GPU serving (Triton), and edge serving (TensorFlow Lite) is consolidating. Platforms like Ray Serve and BentoML provide unified APIs across deployment targets.

The goal: train once, deploy anywhere with a single configuration. Specify your latency and cost constraints; the platform chooses the optimal hardware and optimization automatically.

---

## Summary

```
MODEL DEPLOYMENT PATTERNS
=========================

SERVING OPTIONS:
FastAPI        - Simple, flexible, Python-native
gRPC           - High performance, strong typing
TorchServe     - PyTorch-native, dynamic batching
Triton         - Multi-framework, GPU optimized
TF Serving     - TensorFlow models

DEPLOYMENT PATTERNS:
Blue-Green     - Instant rollback, zero downtime
Canary         - Progressive rollout, risk mitigation
A/B Testing    - Statistical comparison, data-driven

OPTIMIZATION:
ONNX           - Universal format, cross-platform
TensorRT       - NVIDIA GPU optimization (2-5x speedup)
Quantization   - INT8 for smaller models, faster inference

KEY METRICS:
Latency        - P50, P95, P99
Throughput     - Queries per second
Availability   - 99.9% uptime target
```

---

## Hands-On Exercises

These exercises will solidify your understanding of model deployment patterns through practical implementation.

### Exercise 1: Build a FastAPI Model Server

**Goal**: Deploy a simple scikit-learn model as a REST API with proper health checks and versioning.

**Steps**:
1. Train a simple classification model (e.g., iris classifier) and save it with joblib
2. Create a FastAPI application with `/predict`, `/health`, and `/model/info` endpoints
3. Add Pydantic validation for request/response schemas
4. Implement proper error handling that doesn't leak internal details
5. Add timing instrumentation that logs latency for each request
6. Test with curl or the auto-generated Swagger UI

**Success Criteria**: Your API should respond in under 50ms for single predictions, return proper HTTP status codes (200, 400, 500), and include model version in every response.

### Exercise 2: Implement Canary Deployment Locally

**Goal**: Simulate a canary deployment using Docker and nginx as a load balancer.

**Steps**:
1. Create two versions of your model server (v1 and v2)
2. Build Docker images for each version
3. Write an nginx configuration that routes 90% traffic to v1 and 10% to v2
4. Use docker-compose to run the full stack
5. Send 100 requests and verify the traffic split in logs
6. "Promote" v2 by updating the nginx weights to 50/50, then 100%

**Success Criteria**: You should be able to change traffic splits without downtime, verify splits through request logs, and roll back to v1 instantly.

### Exercise 3: Optimize Model for Production

**Goal**: Convert a PyTorch model to ONNX and benchmark the performance improvement.

**Steps**:
1. Load a pretrained model (e.g., ResNet-18 from torchvision)
2. Export to ONNX format with dynamic batching support
3. Create an ONNX Runtime inference session
4. Benchmark both versions: 100 iterations, measure p50/p95/p99 latency
5. Compare throughput (predictions per second)
6. Document the performance improvement and any accuracy changes

**Success Criteria**: ONNX Runtime should provide at least 30% latency improvement over native PyTorch inference on CPU.

---

## Key Takeaways

After working through this module, here's what you should remember about model deployment. These lessons come from hundreds of production incidents and thousands of engineering hours—learn from others' mistakes rather than repeating them.

1. **Deployment is not optional engineering—it's core engineering.** The 46% of models that never reach production don't fail because they're bad models. They fail because teams don't invest in deployment infrastructure. A mediocre model in production beats a perfect model in a notebook.

2. **Always have a rollback plan.** Blue-green deployment gives you instant rollback. Canary deployment gives you gradual risk exposure. Deploying without either is gambling with your users' experience and your company's revenue. The question isn't "will you need to rollback?" but "when will you need to rollback?"

3. **gRPC beats REST for performance, but REST wins for simplicity.** Use gRPC when latency matters (sub-10ms requirements, high throughput, internal services). Use REST/FastAPI when ease of development, debugging, and external API consumers matter more. Don't prematurely optimize—start with REST, migrate to gRPC when you have the data to justify it.

4. **Model optimization is often the highest-leverage improvement.** Converting to ONNX and then TensorRT can give you 2-5x speedup without changing your model architecture. That's free performance. Before adding more servers, try optimizing what you have.

5. **A/B testing is how you learn, not how you deploy safely.** Canary is for safe deployment (minimize blast radius). A/B is for learning (statistical comparison). Use both, but don't confuse their purposes. A canary without monitoring is just a deployment. A/B testing without statistical rigor is just guessing.

6. **Training/serving skew kills silently.** The features you compute in training must match exactly what you compute in serving. Use feature stores. Test for consistency. Version your feature schemas alongside your models. This is the most common cause of "the model works in testing but fails in production."

7. **Monitor percentiles, not averages.** P99 latency of 2 seconds means 1% of your users are waiting 2+ seconds, even if your average is 50ms. At scale, 1% is thousands of frustrated users per hour. Set alerts on P95 and P99.

8. **Cold start is a deployment problem, not a model problem.** Pre-warm containers before they receive traffic. Implement lazy loading for sub-models. Run periodic keep-alive requests to prevent GPU memory from being reclaimed. Plan for initialization time in your scaling strategy.

9. **Version everything, reproduce anything.** A production model should be traceable back to its exact code commit, data version, and training hyperparameters. When something goes wrong (and it will), you need to reproduce the issue to fix it.

10. **Cost optimization at scale is worth the investment.** When you're serving billions of predictions, a 10% efficiency improvement saves hundreds of thousands of dollars per year. Invest in optimization when you have the scale to justify it—but not before.

---

## Next Steps

Module 52 will cover Monitoring & Observability for ML systems, including metrics collection, alerting, and drift detection.

---

_Module 51 Complete!_
_"A model in production is worth a hundred in notebooks."_
