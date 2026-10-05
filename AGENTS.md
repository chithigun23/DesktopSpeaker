# Desktop Speaker project preferences

- Read and maintain `plan.md` for the schematic completion checklist, subsystem status and consolidated user style feedback. Read `ai-files/HANDOVER.md` for design decisions and evidence. The plan is an explicitly requested checklist and is permitted alongside the single handover.

- Use the installed KiCad 10.0.6 / 10.0.6-rc2 CLI. Do not use the nightly AppImage.
- Preserve reference designators and displayed values. Preserve user positions unless a requested readability change requires movement; moving obstructing components is authorized for the ordered subsystem arrangement.
- Place IC reference/value text close below the IC body, horizontally centered. Place passive and transistor reference/value text to the right of the symbol. Keep a compact, readable gap.
- Keep one component per `.kicad_sym` file in `DesktopSpeaker-kicad/kicad-library/schematic`.
- Keep footprints and 3D models as individual files in the existing `footprint` and `3d` folders. Do not create subfolders inside the three library folders.
- Use downloaded STEP models when available; check their origin and dimensions before linking them to footprints.
- Only connect sections requested by the user. USB PD, battery charging/external power, and fuel gauge/low-current power control connections are authorized. Other sections remain unconnected until requested. Do not create a PCB layout until requested.
- Use subagents for independent sourcing, BOM and library tasks, with the main conversation coordinating changes and reporting results.
- Downloads and reversible project edits are authorized. Do not repeatedly ask for permission to download datasheets or component assets.
- Record unresolved part selections and unverified stock explicitly. A partial BOM subtotal is not a complete product cost.

## Human readable schematic style

- Apply the personal `kicad-readable-schematics` skill at `/home/chithi/.codex/skills/kicad-readable-schematics/SKILL.md` for schematic capture and redraws.
- Use standard recognizable transistor graphics with verified physical pin mappings. For new KiCad 10 symbols, use native pin stacks for electrically common pads.
- Use ground symbols, oriented downward, including in child sheets.
- Use direct orthogonal wires whenever practical. Use at most one net label per connected wired section; matching labels on remote sections are acceptable when necessary.
- Avoid nonconnecting wire intersections and ambiguous junctions. Group related circuitry with clear whitespace.
- Keep child-sheet inputs on the left and outputs on the right, with appropriate port types. Port positions may be changed to align inter-sheet signals and avoid wire crossings, as explicitly requested by the user.
- IC identifiers belong below the body at its horizontal center; passive/transistor labels belong to the right. This supersedes earlier above-body text placement preferences. Reduce unnecessary page whitespace within reason, while retaining readable routing and functional grouping.
- Keep all AI helpers, exports, PDFs, datasheets, BOMs, reports and backups under `ai-files/`. Update links when moving assets. Active KiCad project/library files remain in their existing folders.
- Maintain only one handover document: `ai-files/HANDOVER.md`. Update it in place; AGENTS.md remains the project instruction file.
- When readability or connectivity verification is requested, render and inspect the schematic; compare physical pin connectivity before/after a redraw. Record inherited unfinished-section ERC findings explicitly.

## Subsystem delegation

- Keep the main chat as architecture owner and integration/review coordinator. Delegate bounded subsystem implementation to cheaper subagents with compact briefs and relevant source files rather than full conversation history.
- Prefer one hierarchical child sheet per subsystem within the main project, with agreed rail names, port directions, voltage domains and reference ranges.
- Give each agent exclusive ownership of its sheet. Only the coordinator edits root hierarchy and shared library tables; coordinate shared library file edits to avoid collisions.
- Require a short handoff covering parts/configuration, decoupling, interface assumptions, changed files and unresolved issues. Record lasting decisions in the single handover.
- Integrate and review each subsystem before advancing dependent work. Do not duplicate research already recorded in the handover.

- Arrange subsystem sheets adjacent in functional order. Align related ports for short, straight wires; move other components clear where necessary. The power row is USB_PD → Battery_Charger → Fuel_Gauge_Power.
- During sustained schematic work, refresh `ai-files/DesktopSpeaker-preview.pdf` at least every approximately 15 minutes and after substantial reviewed changes.

## Git checkpoints

- User explicitly requests ongoing `git add`, commit and push at reviewed milestones. Preserve user edits and do not force-push. Keep active project files, libraries, plan, handover, BOM, preview and useful evidence tracked; exclude execution caches/dependencies and local recovery snapshots.
- Check the existing branch/remote and review staged changes before committing. Record pushed milestones in the single handover.
