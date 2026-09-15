# Expert Feedback: Single-Factor Principles (2026-07-06)

## Source
External quant expert reviewed the 10-round `self_funded_reinvestment_quality` iteration history and gave five corrections. These are now hard rules in the framework.

## 1. Threshold Correction
Old thresholds were too strict for single-factor discovery:
- Old: RankICmean > 0.03 (3%), RankICIR > 1.5, lsret > 15%
- **New**: RankICmean > 0.015 (1.5%), RankICIR > 1.5, lsret > 4%

Rationale: Raw single factors rarely achieve 3% ICmean and 15% lsret simultaneously. The new thresholds are realistic for standalone factors that can add value in multifactor combination context.

## 2. Single-Factor Rule (Core Change)
**Factor must be a true single factor, not a multi-factor combination.**

Allowed:
- FCF = OCF - CapEx (single economic meaning: free cash flow)
- Cash profit margin = OCF / NetProfit (single meaning: cash generation per unit profit)
- Asset turnover = Revenue / TotalAssets (single meaning: capital efficiency)

Not allowed:
- zscore(OCF_surprise) + zscore(CapEx_surprise) - penalty(DebtRatio)
  → This is three factors combined with arbitrary coefficients (why 1, 0.5, 0.4? no economic basis)

Judgment test: Can you summarize the factor with a single economically meaningful name? If yes → single factor. If you need "zscore of X plus zscore of Y minus penalty of Z" → it's a multi-factor combination.

## 3. First-Principles Starting Point
Before every round, dvcoder must say "从第一性原理出发" (start from first principles).
This forces thinking from economic meaning rather than carrying forward previous round's wrong assumptions or reusing canned patterns from external reports.

## 4. Gate/Reward Minimization
Gates and rewards are derived from historical data → cannot guarantee future validity.

**Default: OFF.** Exception only when economic meaning *requires* it:
- Example: Cash profit margin = OCF / NetProfit. If both numerator and denominator are negative, the ratio is positive — this is an economic contradiction, must be gated.

If the economic rationale for a gate is unclear → don't add it.

## 5. Evaluator Three-Question Mandate
Every evaluator review MUST ask:
1. Does this factor have clear economic meaning? (not just "code runs")
2. Is this a single factor, not a multi-factor combination?
3. Is this based on historically-tuned ratios/gates/rewards? (gates require economic justification)
