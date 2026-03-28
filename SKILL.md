# UniSkill V2.2 - "Universal Skill" Edition

## Trigger Conditions

Automatically triggers when user requests:
- "Help me..." (multi-step tasks)
- "Analyze..." (data retrieval needed)
- "Generate..." (content creation)
- "Status report" (system check)

## Description

**Inner Sage, Outer King**: Hard logic inside (10,855 golden cases), Beautiful UI outside (Jinja2 templates).

## Core Capabilities

### V2.2 "Sea-Glass" Upgrade
- **Jinja2 Template Engine** - No more string concatenation, clean layout
- **State Machine Integration** - Real-time convergence reflection, dynamic background
- **Thinking Fingerprint** - 0.8s animation showing retrieval trace
- **Asset Dashboard** - 10,855 golden cases visualization, real-time API quota
- **Streaming Render** - 2C 2G compatible, auto-downgrade on vector DB lag

### 1. Physical Scanner
- Direct read of `core_v2/` source code
- AST parsing for real function names and logic
- No model hallucination

### 2. State Machine Engine
```python
# Convergence thresholds
CONVERGENCE_HIGH = 0.7    # High → qwen3.5-plus
CONVERGENCE_MEDIUM = 0.4  # Medium → glm-5
CONVERGENCE_LOW = 0.3     # Low → local model
```

### 3. X-Styler V2 Renderer
- Industrial Blue (#1e3a8a) + Graphite Gray (#1f2937)
- Frosted glass design
- Responsive layout (mobile-friendly)
- Triple indicators: Router + Sandbox + Align

## Execution Flow

1. Parse intent keywords
2. Calculate convergence score
3. Route to appropriate model
4. Execute in sandbox
5. Validate output quality
6. Generate HTML report

## Dependencies
- `state_machine.py` - State machine engine
- `x_styler_v2.py` - Sea-Glass renderer
- `psutil` - Hardware monitoring
- `jinja2` - Template engine

## File Structure
```
core_v2/
├── state_machine.py       # State Machine
├── x_styler_v2.py         # Sea-Glass Renderer
├── templates/             # Jinja2 Templates
│   ├── decision_card.html
│   ├── socratic_probe.html
│   ├── thinking_trace.html
│   ├── asset_dashboard.html
│   └── error_card.html
├── data/
│   └── golden_dataset.jsonl
└── static/
```

## License
MIT - Open Source

---

Beaver | Reliable, Capable, On-Duty