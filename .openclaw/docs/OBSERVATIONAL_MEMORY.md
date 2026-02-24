# OpenClaw Observational Memory (PAOM)

**Based on Mastra's Observational Memory**

A text-based memory system that compresses context into structured observations
with emoji prioritization and multi-date temporal tracking.

---

## 🎯 Overview

Pi-Agent Observational Memory (PAOM) is a three-agent memory system for AI assistants:

- **Observer**: Extracts observations from message history when it exceeds threshold
- **Reflector**: Condenses observations when they exceed threshold
- **Actor**: Main agent sees observations + recent unobserved messages

### Key Features

- ✅ **Text-based**: No vector/graph DB needed
- ✅ **Emoji prioritization**: 🔴 (critical), 🟡 (important), 🟢 (info)
- ✅ **Temporal tracking**: Observation date, referenced date, relative time
- ✅ **Prompt caching**: Stable context window for full cache hits
- ✅ **Threshold-based**: Automatic compression when limits reached

---

## 📊 Performance

Based on Mastra's benchmarks:

| Metric | Score |
|--------|-------|
| LongMemEval (gpt-5-mini) | 94.87% |
| LongMemEval (gpt-4o) | 84.23% |
| LongMemEval (Gemini 3 Pro) | 93.27% |

+12.8% accuracy improvement over full context!

---

## 🚀 Usage

### Installation

```bash
# Initialize Observational Memory (V2.4)
cd openclaw-memory-template
bash scripts/init-observational-memory.sh
```

### Configuration

```python
from openclaw.observational_memory import ObservationConfig

config = ObservationConfig(
    observation_threshold=30000,  # 30k tokens default
    reflection_threshold=40000,   # 40k tokens default
    observer_temperature=0.3,      # LLM temperature for extraction
    reflector_temperature=0.0,      # Condensation temperature
    db_path=".openclaw/observational_memory.db"  # Custom path
)
```

### Basic Commands

```python
from openclaw.observational_memory import ObservationalMemory

# Initialize
om = ObservationalMemory()

# Observe new messages
record = om.process_messages(thread_id, messages)

# Get context
context = om.get_context(thread_id)

# Get stats
stats = om.get_stats(thread_id)

# Force reflection
result = om.force_reflection(thread_id)
```

### Integration with ALMA

```python
from openclaw.observational_memory import ObservationalMemory
from openclaw.alma import get_consensus

# Initialize both systems
om = ObservationalMemory()
alma = get_consensus()

# Process messages
record = om.process_messages(thread_id, messages)

# Get weights
weights = alma.get_weights(['StrategyA', 'StrategyB'])

# Build unified context
context = f"""
{om.get_context(thread_id)}

## Strategy Weights
{format_weights(weights)}
"""
```

---

## 📁 Structure

```
.openclaw/observational_memory/
├── __init__.py              # Main PAOM system
├── types.py                  # Configuration and data types
├── token_counter.py          # Token counting
├── observer_agent.py         # Observation extraction
└── reflector_agent.py        # Observation condensation
```

---

## 🔧 Configuration

### Thresholds

| Setting | Default | Description |
|----------|-----------|-------------|
| Observation | 30k tokens | Trigger Observer when messages exceed this |
| Reflection | 40k tokens | Trigger Reflector when observations exceed this |

---

## 📈 Performance

| Metric | Value |
|--------|-------|
| Compression Ratio | 4:1 to 13:1 |
| LongMemEval Accuracy | 94.87% (gpt-5-mini) |
| Token Efficiency | ~50% faster (prompt caching) |

---

## 🚨 Best Practices

1. **Use appropriate threshold**: Adjust based on conversation volume
2. **Monitor token usage**: Avoid context window overflow
3. **Regular reflections**: Clean old observations
4. **Integrate with ALMA**: Use unified memory system
5. **Track performance**: Enable meta-learning improvements

---

## 📚 Full Documentation

See [`.openclaw/memory/__init__.py`](../memory/) for complete memory system docs.

---

## 📚 References

- [Mastra Observational Memory Blog](https://mastra.ai/blog/observational-memory)
- [Mastra GitHub](https://github.com/mastra-ai/mastra/tree/main/packages/memory/src/processors/observational-memory)
- [LongMemEval Benchmark](https://arxiv.org/abs/2410.10813)

---

🐺📿 **Observational Memory**

Context compression meets temporal intelligence
