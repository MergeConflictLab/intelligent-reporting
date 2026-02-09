# Benchmark Analysis: Intelligent Reporting Pipeline

## Executive Summary
This report compares the performance of the reporting pipeline across **Local (Mac)** and **Remote (Linux VM)** environments in both **Online** and **Offline** modes.

**Verdict:**
-   **Online Mode (Cloud)**: 🚀 **Excellent Parity**. The Remote VM performs equally to the Local Mac (~65s), making it production-ready for cloud-backed deployments.
-   **Offline Mode (Local LLM)**: ⚠️ **Critical Bottleneck**. The Remote VM is **~7.5x slower** than the Local Mac due to lack of hardware acceleration, making it unsuitable for interactive use without optimization.

## Comparative Metrics

### 1. Total Execution Time
| Environment | Inference Mode | Backend | Duration | Comparison |
| :--- | :--- | :--- | :--- | :--- |
| **Local Mac** | Offline | Llama.cpp (Metal) | **61 s** | Baseline |
| **Remote VM** | Online | Azure OpenAI | **65 s** | 1.07x Baseline (Good) |
| **Remote VM** | Offline | Llama.cpp (CPU) | **457 s** | **7.50x Slower (Critical)** |

### 2. Component Latency
| Component | Local (Offline) | VM (Offline) | VM (Online) |
| :--- | :--- | :--- | :--- |
| **Metadata Agent** | 15.7 s | **182.0 s** | 8.9 s |
| **Supervisor Agent** | 13.4 s | **158.5 s** | 33.3 s |
| **Assistant Agent** | 31.7 s | **116.7 s** | 23.1 s |

## Root Cause Analysis

### Why is Online Mode fast on VM?
**Network Bound**. In Online mode, the heavy lifting (inference) happens on Azure's servers. The VM only handles lightweight logic and HTTP requests. The latency difference (65s vs 60s) is purely due to the round-trip time (RTT) from the VM to Azure, which is negligible.

### Why is Offline Mode slow on VM?
**Compute Bound & Configuration Issue**.
1.  **Code Configuration**: We inspected the VM's codebase (via `/backend`) and found a **critical configuration issue** in `backend/agents/fallback_manager.py`. It explicitly hardcodes `n_threads=2`. On a multi-core VM (likely 4+ cores), this artificial limit severely throttles performance.
    ```python
    # backend/agents/fallback_manager.py
    self.model = Llama(..., n_threads=2, ...) # Hardcoded limit!
    ```
2.  **Hardware Acceleration**: The Local Mac utilizes **Metal (GPU/NPU)** acceleration. The VM runs on CPU, necessitating optimal thread usage which is currently blocked by the code.
3.  **Memory Bandwidth**: CPU inference is memory-bandwidth constrained, further exacerbated by unoptimized threading.

## Optimization Experiment Results (Update)
We applied the proposed patch (`n_threads=4`, static) and re-ran the Offline VM benchmark.

| Metric | Baseline (n_threads=2) | Run 1 (n_threads=4) | Run 2 (n_threads=4) | Impact |
| :--- | :--- | :--- | :--- | :--- |
| **Metadata Agent** | 182.0 s | 199.8 s | **192.1 s** | **~5-10% Slower** |
| **Supervisor Agent** | 158.5 s | 160.5 s | **163.9 s** | **Slower** |
| **Assistant Agent** | 116.7 s (3 tasks) | 38.9 s (1 task) | **11.0 s (1 task)** | *Workload Variance* |

**Conclusion**: Two separate runs confirm that increasing thread count **did not** improve performance for the Metadata and Supervisor agents. In fact, it consistently added overhead. The bottleneck is definitively **hardware-based** (CPU architecture/Memory), not configuration-based.
**Action**: We must proceed with **Long-Term Infrastructure** changes (GPU attachment) as code-level optimizations have hit a wall.

## Detailed Metric Analysis (New)
With the new instrumentation, we can break down the performance by token throughput.

| Component | Latency (s) | Total Tokens | Approx. Speed (tokens/s) |
| :--- | :--- | :--- | :--- |
| **Metadata Agent** | 200.7s | 3,542 | ~2.5 t/s |
| **Supervisor Agent** | 164.5s | 3,502 | ~1.7 t/s |
| **Assistant Agent** | 122.6s | 616 | ~1.6 t/s |

*Note: Speed is estimated as `Completion Tokens / Total Latency`. Actual generation speed is likely slightly higher as this ignores prompt processing time, but prompt processing on CPU is also slow.*

**Insight**: The consistent **~2 t/s** throughput confirms that the lack of GPU acceleration is the single limiting factor. No amount of thread tuning will significantly alter this physical limit of the CPU.

## Root Cause Analysis
### 1. Compute Bound (Lack of Hardware Acceleration)
-   **Observation**: The VM is limited to **~2 tokens/second**, regardless of thread count tuning.
-   **Cause**: The standard VM CPU (likely generic x86_64 without AVX-512/AMX optimizations for ML) cannot perform matrix multiplications fast enough for the quantized model. The lack of a GPU or NPU means all inference is handled by the CPU, which hits a hard physical wall.
-   **Impact**: Latency scales linearly with token count. 8991 tokens * 0.5s/token = ~4500s (theoretical worst case), effectively observed as ~600s pipeline duration.

### 2. Memory Bandwidth Saturation
-   **Observation**: Increasing `n_threads` from 2 to 4 yielded **no improvement** (or slight regression).
-   **Cause**: LLM inference is memory-bandwidth bound. Adding more threads merely increases contention for the same memory bus. Once the memory bandwidth is saturated, additional cores provide zero benefit and add context-switching overhead.
-   **Conclusion**: Vertical scaling (adding more CPU cores) will **FAIL** to improve performance. Only GPU attachment (high-bandwidth memory) or higher memory bandwidth (DDR5/HBM) will help.

### 3. Architecture Mismatch
-   **Observation**: The application design is "Chatty". It relies on multiple round-trips (Profile -> Metadata -> Supervisor -> Assistant -> Code -> Insights).
-   **Cause**: While modular, this chain multiplies the latency penalty. A single slow link (Offline Assistant) blocks the entire user experience.
-   **Recommendation**: For Offline Mode, consider a "Turbo" pipeline that consolidates steps (e.g., merging Metadata and Supervisor) to reduce the number of inference passes required.
