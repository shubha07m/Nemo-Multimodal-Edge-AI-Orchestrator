# 🐠 Nemo's Vision: Edge Multimodal Agent

> **"A privacy-first, dual-spectrum autonomous agent running locally on Raspberry Pi 4B."**

![Nemo Multimodal Edge AI](https://github.com/shubha07m/Nemo-Multimodal-Edge-AI-Orchestrator/blob/005a6c3f677434225c85037e5131ec40e4a8817a/nemo_test.jpg)


**Nemo's Vision** is an experiment in **multimodal orchestration on the edge**. It combines real-time object detection, small language models (SLMs), and text-to-speech (TTS) into a single autonomous loop, running entirely on a standard Raspberry Pi 4B (8GB).

Unlike cloud-based solutions, Nemo processes dual video streams and generates contextual narration entirely on-device without any external accelerators (no Hailo, no Coral, no GPU). To achieve near real-time performance on a Cortex-A72 CPU, we moved away from monolithic Vision Language Models (VLMs) in favor of a modular, orchestrated pipeline.

*(The Interface: Simultaneous RGB and NoIR streams with bounding box inference, feeding into a generated narrative.)*

### 🧠 The Architecture: Why Modular Wins on Edge

We initially experimented with lightweight **Vision Language Models (VLMs)** like **Moondream2** and **NanoLlava**. While impressive, running a VLM on the Pi's CPU resulted in high latency (inference >10s), destroying the sense of presence.

To solve this, we decoupled **Vision** from **Reasoning**:

1. **Vision (The "Eyes"):** **Ultralytics YOLO26 (Small)**.
* *Evolution:* We upgraded from **YOLO11s** to the newly released **YOLO26s**. The new NMS-free architecture provides slightly better detection accuracy at similar speeds on the CPU, delivering structured data (labels + bounding box coordinates) instantly.


2. **Reasoning (The "Brain"):** **Qwen 2.5 (0.5B)** via Ollama.
* *Why:* By feeding the structured YOLO data into a tiny but capable SLM, we get descriptive scene understanding ("The teddy bear is *in front of* the book") with a fraction of the compute cost of a full VLM.


3. **Speech (The "Voice"):** **KittenTTS**.
* *Why:* Ultra-low latency synthesis that fits within the remaining CPU cycles.



### 🚦 "Traffic Light" Orchestration (The Secret Sauce)

Running three neural networks simultaneously on a Raspberry Pi CPU is a recipe for deadlock. As seen in our resource logs, the system frequently hits **97-98% CPU utilization**.

*(High CPU contention requires strict thread management to maintain stability.)*

To manage this, we engineered a custom **"Traffic Light" Service Orchestrator**:

* **State Management:** A shared, thread-safe state object acts as the central nervous system.
* **Sequential Locking:** The system utilizes a semaphore-style lock. When the **Narrator** (LLM) needs to "think," it signals the **Vision** service to throttle down (sleep), freeing up critical CPU cycles for inference. Once the thought is generated, the Vision service wakes up while the TTS service takes over.
* **Result:** A fluid, non-blocking experience that feels "alive" despite the hardware operating at its absolute limit.
* **Efficiency:** Through careful memory management and quantization, the entire stack (Dual Camera Streams + YOLO26s + Qwen 2.5 + TTS + Web Server) stays well within **2GB of RAM**, leaving plenty of headroom on the 8GB board.

### 🛠️ Tech Stack

* **Hardware:** Raspberry Pi 4B (8GB RAM, Cortex-A72 CPU). No external accelerators.
* **Vision:** Ultralytics **YOLO26s** (ONNX Runtime for CPU acceleration).
* **LLM:** **Qwen 2.5:0.5b** (Quantized via Ollama).
* **TTS:** **KittenTTS** (Real-time synthesis).
* **Backend:** Python (Flask), Threading, OpenCV.
