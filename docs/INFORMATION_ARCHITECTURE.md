# Information Architecture

This site is a research dashboard built from source Markdown records. The homepage should help readers decide what to read next, not expose every generated record as a flat stream.

## Layers

1. **Research Packages**
   - Primary homepage unit.
   - One paper summary plus optional role notes from the same source directory.
   - Shows paper title, source path, role-note count, available reviewer roles, and topic tags.

2. **Problem Lenses**
   - Cross-domain entry points for recurring research questions.
   - Current lenses: Agent, UX / HCI, Evaluation, Fairness, Multimodal.
   - Built from keyword matches across canonical paper summaries.

3. **Domain Topics**
   - Conventional subject navigation such as AI, HCI, UX, NLP, ML, CV.
   - Still useful for archive-style browsing, but no longer the only mental model.

4. **Members**
   - Role pages stay secondary.
   - Member pages update only when role-note files exist.

5. **Archive**
   - Complete chronological and searchable record layer.
   - Keeps old records discoverable without making the homepage repetitive.

## Homepage Contract

- Lead with the latest research packages.
- Keep role notes attached to their paper package instead of rendering them as independent homepage cards.
- Expose problem lenses before broad archive browsing.
- Keep search broad enough to find role notes and legacy records.

## Hermes Fit

Hermes should write one paper package at a time:

```text
records/YYYY/MM/DD/HH/<paper-key>/论文总结.md
records/YYYY/MM/DD/HH/<paper-key>/<member>-能力进化.md
```

This layout gives the generator a stable grouping key and avoids duplicate homepage summaries.
