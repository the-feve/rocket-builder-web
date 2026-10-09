# rocket-builder-web — working rules

- Read `HANDOFF.md` first: current state, next steps, decisions log. The plan is `docs/web_platform_spec.md`; open items are also in `geometry/report.md` and `README.md` (Status). Keep them up to date when something changes.
- **Reference design:** `src/RocketGenerator.fs` in [OS_Rocket_Builder](https://github.com/the-feve/OS_Rocket_Builder) (the latest is on the `anchor-section` branch). Port its behaviour and its "why" comments, not its dated revision history. Each `rocketgen` module names the FeatureScript functions it mirrors.
- **Units are mm.** Motor and settings data come from `geometry/rocketgen/data/*.csv` (copied from OS_Rocket_Builder `data/`); don't hard-code motor or tube numbers.
- **Don't trust OpenCascade's `is_valid` alone.** Tessellate first (`geom.meshes`), check fillets with `fillet_checked` / `try_fillet`, and keep the slice and overlap tests green. `geometry/report.md` lists the gotchas found so far; add new ones there.
- Cosmetic fillets that won't build are skipped, as in the FeatureScript's `try silent`. A part that is unsound raises `GeometryError` with a user-facing message.
- Run `python -m pytest -q` in `geometry/` before every push. It takes about a minute.
- The owner's usage budget is tight: prefer doing the work in cloud sessions, and batch changes.
