# UniSkill V2.2 - "Universal Skill" Edition

> **Inner Sage, Outer King**: Hard logic inside (10,855 golden cases), Beautiful UI outside (Jinja2 templates)

## Core Features

| Feature | Description |
|---------|-------------|
| State Machine Engine | Auto-routing by convergence threshold (0.7→cloud, 0.3→local) |
| Jinja2 Templates | Sea-Glass frosted glass design, Industrial Blue + Graphite Gray |
| Thinking Fingerprint | 0.8s animation showing retrieval trace |
| Asset Dashboard | 10,855 golden cases visualization |
| Streaming Render | Compatible with 2C 2G environment |

## Quick Start

```python
from core_v2.x_styler_v2 import XStylerV2

styler = XStylerV2()

# Render decision card
html = styler.render_decision_card(
    convergence=0.85,
    model="qwen3.5-plus",
    intent="task_execution",
    content="Result content..."
)
```

## Convergence Thresholds

| Threshold | Status | Route |
|-----------|--------|-------|
| >= 0.7 | READY | qwen3.5-plus (cloud) |
| 0.4 - 0.7 | PROBING | glm-5 (clarification) |
| < 0.3 | CRITICAL | local model (fallback) |

## Architecture

```
core_v2/
├── state_machine.py       # State Machine Engine
├── x_styler_v2.py         # Sea-Glass Renderer
├── templates/             # Jinja2 Templates
│   ├── decision_card.html
│   ├── socratic_probe.html
│   ├── thinking_trace.html
│   ├── asset_dashboard.html
│   └── error_card.html
└── example_v2.py          # Usage Examples
```

## Installation

```bash
pip install jinja2 psutil
```

## Color Scheme

| Color | Usage | Hex |
|-------|-------|-----|
| Industrial Blue | Router Module | #1e3a8a |
| Success Green | Sandbox + High Convergence | #17BF63 |
| Warning Orange | Medium Convergence | #FFAD1F |
| Error Red | Low Convergence / Failed | #E0245E |
| Graphite Gray | Dashboard Background | #1f2937 |

## Unique Features (No Competitors)

1. **Convergence Detection** - Industry first, auto-route by intent clarity
2. **Socratic Questioning** - 5W2H auto-clarification for vague requests
3. **Thinking Fingerprint** - Visual thinking process animation
4. **Golden Dataset** - 10,855 built-in cases for instant retrieval
5. **Low-Spec Compatible** - Runs on 2C 2G servers

## Workflow

```
User Input
    ↓
Intent Parsing → Convergence Detection
    ↓
Local Skill Match? ──Yes──→ Execute Local Skill
    ↓ No
ClawHub Search? ──Yes──→ Install & Execute
    ↓ No
Hybrid Model Router (Cloud/Local)
    ↓ Failed
Fallback to Local Model
```

## Source Priority

| Source | Priority | Status |
|--------|----------|--------|
| Local Skills | 1st (40%) | Enabled |
| ClawHub | 2nd (5%) | Enabled |
| Hybrid Model Router | 3rd (50%) | Enabled |
| Fallback | 4th (5%) | Auto |

## Version History

| Version | Date | Changes |
|---------|------|---------|
| V2.2.0 | 2026-03-28 | Jinja2 templates + State machine + Thinking fingerprint + Asset dashboard |
| V2.1.0 | 2026-03-27 | Convergence detection + Socratic questioning |
| V2.0.0 | 2026-03-22 | Hybrid retrieval architecture |

## License

MIT License - Open Source

## Author

OpenClaw Team

## Links

- Website: https://openclaw.ai
- Docs: https://docs.openclaw.ai
- GitHub: https://github.com/openclaw/openclaw
- ClawHub: https://clawhub.com