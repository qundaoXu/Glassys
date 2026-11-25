# Glassys Notes

Focused research notes and implementation references live here. Keep the root docs index pointed at this file instead of listing each note individually.

## Research Notes

- [Crystal Toolkit Boundary Report](crystal_toolkit_boundary_report.md): short assessment of Crystal Toolkit's package boundary and whether Glassys should borrow from or depend on it.
- [Pymatgen Backend Report](pymatgen_prl_report.md): research notes on pymatgen as a possible backend for bonding, coordination environments, and symmetry analysis.
- [Coordination Polyhedra Rendering Notes](polyhedra_rendering_research.md): research notes on VESTA, pymatgen, and Crystal Toolkit polyhedra practices with implementation guidance for Glassys.
- [Camera Orientation Math](camera_orientation_math.md): concise math note on direct/reciprocal view directions, orthogonalization, and fallback anchors.
- [Naumann-Style Standard View Algorithm](naumann_standard_view_algorithm.md): implementation note for Glassys's standard preview view, including the Penfield/Naumann reference, formulas, and default fit behavior.
- [Render Depth and Transparency Sorting Review](render_depth_sorting_review_2026-07-02.md): Chinese audit of Glassys's atom, bond, unit-cell, polyhedra, and selection rendering order, depth buffer policy, and transparency risks.
- [VESTA Standard View Notes](vesta_standard_view_notes.md): research notes on VESTA-style orientation, reset views, and a proposed default view for Glassys.

## Design References

- [Backend Architecture Scan](backend_architecture_scan_2026-06-27.md): pre-refactor scan of backend module boundaries, coupling risks, and a conservative one-shot refactor plan.
- [Frontend Architecture Scan](frontend_architecture_scan_2026-06-27.md): pre-refactor scan of frontend module boundaries, highest-risk files, and a recommended first refactor slice.
- [Thermo-Nuclear Code Quality Review](thermo_nuclear_code_quality_review_2026-06-30.md): 严格中文审查报告，聚焦当前前端大文件、导出域、scene object、App 编排和合同漂移风险。
- [Three.js Best Practices 100 Tips](threejs-best-practices-100-tips.md): external 2026 Three.js performance and quality checklist, with WebGPU, batching, disposal, profiling, and TSL guidance.
- [Three.js Preview Performance Handoff](threejs_preview_performance_handoff_2026-06-27.md): 中文交接记录，说明 demand rendering 与 instanced atoms/bonds 这两个剩余预览性能问题。
- [Vercel Design Notes](vercel_design.md): Geist design reference for the light UI theme.
- [WebGPU + Three.js Migration Guide](webgpu-threejs-migration-guide.md): external 2026 migration guide covering WebGPU readiness, renderer setup, React Three Fiber integration, TSL, and fallback strategy.
