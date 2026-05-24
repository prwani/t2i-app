# Skills

Phase 5 adds three skills under `skills/`. Each skill has a `SKILL.md`, references, and scripts that import `t2i_core`.

## t2i-generation

Use for image generation and editing workflows.

```bash
python skills/t2i-generation/scripts/generate.py --scenario text --prompt "A product hero image" --model gpt-image-2 --output hero.png
```

## t2i-evaluation

Use for image quality and prompt-adherence scoring.

```bash
python skills/t2i-evaluation/scripts/evaluate.py --image hero.png --prompt "A product hero image" --layers embedding,rubric,judge
```

## t2i-design-assets

Use for end-to-end image asset workflows such as best-of-N ranking and multi-platform packages.

```bash
python skills/t2i-design-assets/scripts/create_assets.py --workflow best-of-n --prompt "A product hero image" --n 3
```

## Design principle

Skills remain thin wrappers. Shared logic belongs in `t2i_core`.
