# Research report: Does grounding answers in peer-reviewed literature improve accuracy?

*Generated automatically on 2026-11-04 by the Autonomous Multimodal Scientific Discovery Agent. Status: complete.*

## Objective
Research question: Does grounding answers in peer-reviewed literature improve accuracy?

Hypothesis: Grounding answers in peer-reviewed sources raises answer accuracy [1][2].

Evidence base: 2 cited source(s).

## Methods
- Experiment: Eight runs per condition on the same question set.
- Execution: completed successfully after 2 attempt(s).
- Statistical analysis: Welch two-sample t-test (two-sided, alpha = 0.05).
- Holm-Bonferroni correction was applied across 2 analyses.
- Sample sizes: Accuracy: grounded vs ungrounded: grounded = 8, ungrounded = 8; Latency: grounded vs ungrounded (seconds): grounded = 6, ungrounded = 6.

## Findings
- Accuracy: grounded vs ungrounded: Welch two-sample t-test, t = 7.64, p < 0.0001, Holm-adjusted p < 0.0001, Cohen's d = 3.8188 (large), 95% CI [0.036, 0.064] for mean(grounded) - mean(ungrounded). grounded has the higher mean (difference 0.05). Statistically significant at alpha = 0.05.
- Latency: grounded vs ungrounded (seconds): Welch two-sample t-test, t = 0.784, p = 0.4510, Holm-adjusted p = 0.4510, Cohen's d = 0.4529 (small), 95% CI [-0.1227, 0.256] for mean(grounded) - mean(ungrounded). grounded has the higher mean (difference 0.06667). Not statistically significant at alpha = 0.05; this does not show that there is no effect.
- Automated figure analysis, Figure 3 of [2]: hallucination rate falls as retrieval depth increases

## Conclusion
Statistically significant results were obtained for: Accuracy: grounded vs ungrounded. No statistically significant result was found for: Latency: grounded vs ungrounded (seconds). This does not show that there is no effect. Significance alone does not establish that the hypothesis is correct; the direction and size of each effect should be checked against it.

## Limitations
- A p-value is not the probability that the hypothesis is true, and p below alpha does not guarantee the effect is real or important.
- Small sample (smallest group has 6 values): low power and unstable estimates. Treat this result as preliminary.
- This report was generated automatically from the experiment outputs and retrieved literature and should be reviewed by a person before it is relied on.

## References
[1] Lewis, Perez, Piktus et al. (2020). Retrieval-augmented generation for knowledge-intensive NLP tasks. NeurIPS. https://doi.org/10.5555/3495724.3496517
[2] Ji, Lee (2023). Survey of hallucination in natural language generation. ACM Computing Surveys. https://doi.org/10.1145/3571730
