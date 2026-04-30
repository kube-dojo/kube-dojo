# Tier 3 Review — Chapter 58: The Math of Noise

Reviewer: Codex (gpt-5.5)
Date: 2026-04-30
Reviewing: tier3-proposal.md by Claude (claude-opus-4-7)

## Element 8 — Inline parenthetical definition
Author verdict: SKIPPED — Tooltip component is not available; `<abbr>` would modify prose and violate bit-identity.
Reviewer verdict: APPROVE
I approve the skip. The spec keeps Element 8 skipped until a non-destructive tooltip component exists, and this chapter's Tier 1 glossary already covers the terms a reader needs without altering verified prose.

## Element 9 — Pull-quote
Author verdict: SKIPPED — Math sidebar plus chapter authorial voice carry the load; proposed primary-source candidates would be ornamental or repetitive.
Reviewer verdict: APPROVE
I approve the skip. I checked the most plausible revival paths: Sohl-Dickstein's forward/reverse-process framing, Ho et al.'s DDPM sample-quality/noise-prediction framing, Dhariwal and Nichol's "beat GANs" claim, Rombach et al.'s latent-space compute argument, and Stability AI's 2022 release/consumer-GPU framing. Each is already doing work in the prose or Tier 2 aids.

Do not revive the Dhariwal/Nichol title because the chapter already names it verbatim. Do not revive the Stability AI 4,000-A100 or VRAM sentences because the chapter already states those release facts in the surrounding Stable Diffusion section. A pull-quote here would create emphasis without adding provenance, limitation, or interpretive force that the chapter lacks.

## Element 10 — Plain-reading aside
Author verdict: SKIPPED — Math sidebar carries the symbolic load; prose body is conceptual rather than formula-dense.
Reviewer verdict: APPROVE
I approve the skip. The dense symbolic material is isolated in the Tier 2 math sidebar, and the prose explains diffusion, guidance, and latent diffusion in ordinary language. Adding `:::tip[Plain reading]` asides would mostly paraphrase already readable paragraphs.

## Summary
- Approved: Element 8 skip; Element 9 skip; Element 10 skip
- Rejected: None
- Revised: None
- Revived: None

## Math sidebar verification
The six equations are structurally correct against the named primary sources, with one required prose correction in the classifier-free guidance bullet.

- **Forward diffusion one step:** Correct. Ho et al. 2020 §2 Eq. 2 defines $q(x_t \mid x_{t-1}) = \mathcal{N}(x_t;\sqrt{1-\beta_t}x_{t-1},\beta_t I)$.
- **Closed-form forward:** Correct. Ho et al. 2020 §2 Eq. 4 uses $\alpha_t = 1-\beta_t$, $\bar{\alpha}_t=\prod_{s=1}^{t}\alpha_s$, and $q(x_t\mid x_0)=\mathcal{N}(x_t;\sqrt{\bar{\alpha}_t}x_0,(1-\bar{\alpha}_t)I)$.
- **$L_{\text{simple}}$:** Correct. Ho et al. 2020 Eq. 14 is the unweighted MSE on $\epsilon-\epsilon_\theta(\sqrt{\bar{\alpha}_t}x_0+\sqrt{1-\bar{\alpha}_t}\epsilon,t)$ with $t$ sampled uniformly.
- **DDPM reverse step:** Correct. Algorithm 2 / Eq. 11 gives the ancestral update with $\frac{1}{\sqrt{\alpha_t}}\left(x_t-\frac{\beta_t}{\sqrt{1-\bar{\alpha}_t}}\epsilon_\theta(x_t,t)\right)+\sigma_t z$, using $z=0$ at $t=1$.
- **Classifier-free guidance:** Formula sign and coefficients are correct against Ho & Salimans 2022 Eq. 6: $\tilde{\epsilon}_\theta=(1+w)\epsilon_\theta(\cdot,c)-w\epsilon_\theta(\cdot,\emptyset)$. The explanatory sentence is wrong: in this parameterization, $w=0$ recovers the ordinary conditional prediction, not the unconditional model. Replace that clause with: `$w = 0$ recovers ordinary conditional sampling; larger $w$ extrapolates away from the unconditional estimate, pushing harder toward the condition at the cost of diversity.`
- **Latent-diffusion wrap:** Correct. Rombach et al. §3 trains a perceptual autoencoder, freezes it, runs the diffusion model in the lower-dimensional latent space, and decodes generated latents back to image space. The chapter's $x_0 \to z_0=\mathcal{E}(x_0)$, latent-chain, and $\hat{z}_0 \to \hat{x}_0=\mathcal{D}(\hat{z}_0)$ description matches that design.
