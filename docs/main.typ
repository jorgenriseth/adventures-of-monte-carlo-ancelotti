#set page(paper: "a4", margin: 2.5cm)
#set text(font: "Linux Libertine", size: 11pt)
#set heading(numbering: "1.1")

#align(center)[
  #text(16pt, weight: "bold")[Mathematical Formulation of the Fantasy Premier League ILP] \
  #v(0.5cm)
  #text(12pt)[Rolling Horizon Integer Linear Program]
]

#v(1cm)

= Sets and Indices
- $I$: Set of all available players, indexed by $i$.
- $T$: Set of gameweeks in the optimization horizon, indexed by $t in {1, ..., N}$.
- $C$: Set of real-world Premier League clubs, indexed by $c$. Let $I_c subset I$ denote the subset of players belonging to club $c$.
- $P$: Set of positional categories $p in {1, 2, 3, 4}$ (representing GK, DEF, MID, FWD). Let $I_p subset I$ denote the subset of players in position $p$.

= Parameters (Constants)
- $E_(i,t) in RR_(>=0)$: Expected points of player $i$ in gameweek $t$.
- $P_(i,t) in ZZ_(>=0)$: Market price of player $i$ at week $t$ (scaled by 10).
- $x_(i,0) in {0, 1}$: Initial squad state (1 if owned at $t=0$).
- $V_(i,0) in ZZ_(>=0)$: Initial book value (purchase price) of owned players at $t=0$.
- $B_0 in ZZ_(>=0)$: Starting bank balance at $t=0$.
- $S_0 in ZZ_(>=0)$: Number of rolled-over free transfers available at $t=0$.
- $S_max in ZZ_(>=0)$: Maximum number of free transfers that can be banked (e.g., 5).
- $L_p in ZZ_(>=0)$: Roster limit for position $p$ in the 15-man squad ($L_1=2, L_2=5, L_3=5, L_4=3$).
- $F_(p, min), F_(p, max) in ZZ_(>=0)$: Min/max pitch formation limits for position $p$ in the starting XI:
  - Goalkeepers ($p=1$): $F_(1, min) = 1, F_(1, max) = 1$
  - Defenders ($p=2$): $F_(2, min) = 3, F_(2, max) = 5$
  - Midfielders ($p=3$): $F_(3, min) = 2, F_(3, max) = 5$
  - Forwards ($p=4$): $F_(4, min) = 1, F_(4, max) = 3$
- $M in ZZ_(>=0)$: A sufficiently large constant for Big-M bounds (e.g., 150).

= Decision Variables

*Binary Variables ${0, 1}$*
- $x_(i,t)$: 1 if player $i$ is in the 15-man squad at the end of week $t$.
- $y_(i,t)$: 1 if player $i$ is selected in the starting XI for week $t$.
- $c_(i,t)$: 1 if player $i$ is designated as Captain in week $t$.
- $u_(i,t)$: 1 if player $i$ is transferred in (bought) during week $t$.
- $v_(i,t)$: 1 if player $i$ is transferred out (sold) during week $t$.
- $z_(i,t)$: 1 if player $i$ is sold at a strictly positive profit (tax indicator).

*Integer Variables $ZZ$*
- $V_(i,t) >= 0$: The current Book Value of player $i$ held in the squad.
- $delta_(i,t)$: The isolated price difference (Profit/Loss) triggered upon the sale of player $i$.
- $tau_(i,t) >= 0$: The exact 50% FPL tax deducted upon sale.
- $B_t >= 0$: The total bank balance available at the end of week $t$.
- $K_t >= 0$: Total number of transfers made in week $t$.
- $H_t >= 0$: Number of penalty hits taken in week $t$ (costs -4 points each).
- $S_t >= 0$: Number of free transfers saved and rolled over into week $t+1$.
- $w_t >= 0$: Number of wasted / discarded free transfers in week $t$.

#pagebreak()

= Objective Function
The objective is to maximize the total Expected Value of the starting XI ($y_(i,t)$) plus the captain bonus ($c_(i,t)$) across the entire horizon, minus point penalties for transfer hits ($H_t$).

$ "Maximize" quad Z = sum_(t in T) sum_(i in I) E_(i,t) (y_(i,t) + c_(i,t)) - sum_(t in T) (4 dot H_t) $

= Constraints

== Squad Flow and Roster Limits
The fundamental mass-balance of the 15-man squad, ensuring mutual exclusivity of buying ($u$) and selling ($v$) the same player in the same week:
$ x_(i,t) = x_(i,t-1) + u_(i,t) - v_(i,t) quad forall i in I, t in T $
$ u_(i,t) + v_(i,t) <= 1 quad forall i in I, t in T $

15-man squad positional and club limits:
$ sum_(i in I) x_(i,t) = 15 quad forall t in T $
$ sum_(i in I_p) x_(i,t) = L_p quad forall p in P, t in T $
$ sum_(i in I_c) x_(i,t) <= 3 quad forall c in C, t in T $

== Starting XI Formation and Captaincy
Selecting 11 starters from the 15-man squad subject to pitch formation rules:
$ y_(i,t) <= x_(i,t) quad forall i in I, t in T $
$ sum_(i in I) y_(i,t) = 11 quad forall t in T $
$ F_(p, min) <= sum_(i in I_p) y_(i,t) <= F_(p, max) quad forall p in P, t in T $

Captain selection from within the starting XI:
$ c_(i,t) <= y_(i,t) quad forall i in I, t in T $
$ sum_(i in I) c_(i,t) = 1 quad forall t in T $

== Book Value Memory Isolation
This constraint locks in the purchase price, holds it flat across the player's tenure, and extracts the profit/loss into $delta_(i,t)$ the exact moment they are sold ($v_(i,t) = 1$), wiping the memory state back to 0.
$ V_(i,t) = V_(i,t-1) + P_(i,t) (u_(i,t) - v_(i,t)) + delta_(i,t) quad forall i in I, t in T $
$ 0 <= V_(i,t) <= M dot x_(i,t) quad forall i in I, t in T $
$ -M dot v_(i,t) <= delta_(i,t) <= M dot v_(i,t) quad forall i in I, t in T $

== Tax Mathematics
Linearizing the non-linear FPL tax rule $max(0, floor(delta_(i,t) / 2))$ using Big-M logic. The tax $tau_(i,t)$ must be at least half the profit, and is forced downwards by the upper bounds via the indicator $z_(i,t)$.
$ tau_(i,t) >= 0 quad forall i in I, t in T $
$ 2 dot tau_(i,t) >= delta_(i,t) - M (1 - v_(i,t)) quad forall i in I, t in T $
$ z_(i,t) <= v_(i,t) quad forall i in I, t in T $
$ tau_(i,t) <= M dot z_(i,t) quad forall i in I, t in T $
$ 2 dot tau_(i,t) <= delta_(i,t) + 1 + M (1 - z_(i,t)) quad forall i in I, t in T $

== Budget Conservation
The available bank ($B_t$) updates by subtracting new purchases, adding revenue from sales, and permanently destroying capital via the FPL tax constraint.
$
  B_t = B_(t-1) - sum_(i in I) (P_(i,t) dot u_(i,t)) + sum_(i in I) (P_(i,t) dot v_(i,t) - tau_(i,t)) quad forall t in T
$
$ B_t >= 0 quad forall t in T $

== Free Transfers, Rollover Mechanics, and Pre-Season Draft
Tracking total transfers ($K_t$), saved free transfers ($S_t$), discarded transfers ($w_t$), and penalty hits ($H_t$).

Total transfers made in week $t$:
$ K_t = sum_(i in I) u_(i,t) quad forall t in T $

Free transfer balance equation (incorporating wasted transfer slack $w_t$):
$ K_t + S_t + w_t - H_t = S_(t-1) + 1 quad forall t in T, t >= 2 $

Upper bounds and non-negativity:
$ S_t <= S_max quad forall t in T $
$ S_t >= 0, quad H_t >= 0, quad w_t >= 0 quad forall t in T $

*Pre-Season Initial Draft Condition ($t=1$):*
When running a pre-season draft ($x_(i,0) = 0$), initial squad building transfers are free:
$ H_1 = 0 $
$ S_1 = S_0 $

= Statistical Prediction Model

To generate the expected points matrix $E_(i,t)$ for the optimization horizon, we model player performance using a one-parameter scaled Negative Binomial Generalized Linear Model (GLM). Rather than learning baseline player quality from raw situational features, we treat historical averages as a known exposure (offset) and strictly isolate the multiplicative effect of the Fixture Difficulty Rating (FDR).

== Historical Baseline and The Offset
Let $Y_(i,m)$ denote the actual points scored by player $i$ in a historical match $m$. We define the player's intrinsic quality, $lambda_i$, as their historical average points per gameweek.

We assume the points follow a Negative Binomial distribution to account for overdispersion in FPL scoring:
$ Y_(i,m) tilde "NB"(mu_(i,m), alpha) $
where $mu_(i,m)$ is the expected mean and $alpha$ is the estimated dispersion parameter.

To map the baseline quality to the fixture difficulty, we utilize a log-link function. We treat $log(lambda_i)$ as a fixed offset (coefficient of $1$). Furthermore, since an FDR of 3 represents a neutral fixture that should not alter the baseline, we center the continuous FDR variable around 3:
$ log(mu_(i,m)) = log(lambda_i) + beta dot ("FDR"_(i,m) - 3) $
The model is trained on historical data to estimate a single global parameter, $beta$. Because the FDR is centered, an FDR of 3 evaluates to $exp(0) = 1$, leaving the baseline untouched.

== Cross-Season Mapping and the Cold Start Problem
To apply this model to a new season, we must resolve two data discontinuities:
+ *ID Drift:* Historical $lambda_i$ values are mapped to the new season's FPL API universe using the persistent, hidden player photographic ID (`code`), safely overriding the volatile seasonal `player_id`.
+ *New Arrivals (Cold Start):* For newly promoted or transferred players lacking a historical $lambda_i$, we impute their baseline using a Price-Position Heuristic. Let $P_i$ be the starting price of a new player in position $p$. Their baseline is imputed as the mean historical $lambda$ of all established players belonging to the same position and price bucket:
  $ lambda_i = "mean"({ lambda_j | j in I_p, P_j = P_i, lambda_j "is known" }) $

== Bias Elimination and GLM Fitting Mechanics
In models utilizing a log-link function, any $lambda_i <= 0$ results in an undefined mathematical domain. Naively applying a small constant $epsilon$ to inactive players introduces severe biases: it artificially shrinks $beta$ toward zero during training (attenuation bias) and awards fractional phantom points to non-playing assets during projection.

To eliminate these biases, we decouple the populations:
- *Training Phase:* The GLM is fitted strictly on historical records where the player recorded $>0$ minutes, ensuring $lambda_i > 0$ and isolating the true fixture impact.
- *Projection Phase:* We bypass the GLM entirely for non-playing assets.

== Expected Value Projection
The expected points matrix for the upcoming optimization horizon $T$ is defined as a piecewise function, shielding the solver from phantom points:

$
  E_(i,t) = cases(
    0 & "if" lambda_i <= 0,
    lambda_i dot exp(beta dot ("FDR"_(i,t) - 3)) & "if" lambda_i > 0
  )
$


== Bias Elimination and GLM Fitting Mechanics

In models utilizing a log-link function, the offset requires computing $log(lambda_i)$. Because FPL players can average exactly zero points (if they never play) or negative points, any $lambda_i <= 0$ results in an undefined mathematical domain.

Naively applying a small constant $epsilon$ (e.g., $lambda'_i = max(lambda_i, epsilon)$) to the entire dataset introduces two severe biases:
+ *Training Attenuation Bias:* If thousands of inactive bench players are fed into the training set with a flat $epsilon$ expected value regardless of fixture difficulty, the GLM will artificially shrink the scaling parameter $beta$ toward zero, mathematically concluding that fixtures have little impact.
+ *Prediction Bias:* During projection, the solver might incorrectly assign fractional points to "bench fodder" players, prompting the optimizer to favor them over equal-priced alternatives simply due to phantom epsilon scaling.

To eliminate these biases, we decouple the training and prediction populations:

*Training Phase (Active Matches Only):*
The GLM is fitted strictly on historical records where the player recorded $>0$ minutes. This naturally guarantees $lambda_i > 0$ and ensures $beta$ is learned exclusively from meaningful matches where fixture difficulty actually impacts performance.

*Projection Phase (Deterministic Bypass):*
During the generation of the expected points matrix, we bypass the GLM entirely for non-playing assets. The final projection is defined as a piecewise function, shielding the solver from fractional phantom points:

$
  E_(i,t) = cases(
    0 & "if" lambda_i <= 0,
    lambda_i dot exp(beta dot "FDR"_(i,t)) & "if" lambda_i > 0
  )
$
