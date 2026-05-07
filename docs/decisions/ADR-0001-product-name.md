# ADR-0001 — Product Name: Aura

## Status

Accepted (2026-05-07). Locked in `plan.md` §31.

## Context

The product needs a short, memorable, English-renderable name suitable for a Samsung EnnovateX 2026 submission addressing Indian Gen Z and Gen Alpha. The name has to survive a multilingual judging panel, a slide deck running at projector resolution, a one-line pitch hook, a tagline ("Anticipate. Act. Stay quiet."), and search engine indexing for a public GitHub repo at https://github.com/ShAuRyA-Noodle/Combobulating.

Constraints:

- Strict English (`plan.md` §5.3). No Hinglish transliteration.
- Banned word list (`plan.md` §5.3): empower, leverage, seamless, revolutionary, paradigm, etc. The name itself must not lean into hype vocabulary.
- The product is anti-anthropomorphic. It is not a chatbot, has no face, no personality, no voice. The name should not invite users to talk to it.
- The name must not collide with an existing high-profile AI assistant brand in a way that creates trademark exposure for an early-stage student project.
- The team name is `Galaxy Brain`; the product name needs to feel distinct from the team name.

Forces:

- A concrete physical metaphor lets the deck use editorial typography without illustrative crutches (see `deck_spec.md` §0 — display serif Fraunces).
- The name is a load-bearing piece of slide 1, slide 3, and the pitch opening line.

## Decision

The product name is **Aura**.

The lockup pairs `Aura` (Fraunces 96 pt) with the tagline `Anticipate. Act. Stay quiet.` (Inter Tight 22 pt). The name appears in the deck, repo README, app binary identifier (`ai.aura`), iOS bundle (`ai.aura`), Android namespace (`ai.aura`), and every doc index. Tagline runners-up are kept only for slide-deck variant testing and not as product-line names.

## Consequences

Positive:

- The name carries a soft connotation (presence, atmosphere) that pairs with "stay quiet" without anthropomorphising the system.
- Three letters, four phonemes, recognisable across South-Asian English speakers.
- Available as `ai.aura` reverse-DNS for app bundle identifiers.
- Contrasts well against `Bixby`, `Gemini`, `Siri`, and `Pixel Assistant` on the slide 5 comparison row.

Negative / costs:

- "Aura" is a common English noun; SEO will be weak in early days. Mitigated by repo and tagline pairing.
- Some existing apps and trademarks use the name in adjacent spaces (wellness apps, social-presence apps, NFT projects). Risk for a student submission is low; if the project commercialises, a trademark search and possibly a suffix (`Aura by Galaxy Brain`) becomes necessary.
- Translates well in English-language markets only. International expansion would need re-evaluation. Out of scope for the EnnovateX submission.

## Alternatives

- **Loop** — fit the closed-loop biometric wedge well, but collides directly with several developer products (Apple Loop, social-audio apps) and reads as a verb, weakening the system identity.
- **Quiet** — captured the Silence Budget ethos but read as a feature, not a product. Hard to use as a noun in the pitch ("Quiet says…"). Rejected.
- **Stillpoint** — too literary, hard to pronounce on stage, and the word reads as a meditation app rather than an intelligence layer.
- **Anchor** — strong noun, but used by the podcast platform Spotify owns, which creates avoidable confusion in the AI/assistant judging context.
- **Lull** — accurate to the silence wedge but reads as sleep-tech and lacks the agentic connotation of `Aura`.

End of ADR-0001.
