# Engineering Roadmap & AI Pair-Programming Tasks (TODO)

## 📌 Autonomous Vibe-Coding Checklist

### Phase 1: Solver Optimizations
- [ ] Add support for subtraction, multiplication, and multi-term addition (e.g., $A + B + C = D$) in `cryptarithmetic_agent/solver.py`.
- [ ] Implement AC-3 (Arc Consistency Algorithm #3) preprocessing to prune unary and binary constraints before backtracking starts.
- [ ] Add benchmark script comparing naive backtracking vs MRV + LCV + Forward Checking speedup.

### Phase 2: Google ADK Agent Enhancements
- [ ] Add session persistence memory so the agent remembers past puzzles solved by the user.
- [ ] Add structured JSON streaming responses for intermediate search step visualization in UI.

### Phase 3: Frontend & Visualizer
- [ ] Add step-by-step backtracking search animation tree in `public/index.html`.
- [ ] Add dark mode toggle and copy-to-clipboard button for solutions and formulas.
- [ ] Implement mobile-responsive touch keypad for quick digit testing.
