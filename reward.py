from difflib import SequenceMatcher


def compute_reward(
    final_answer: str | int | float, expected_answer: str, n_actions: int, optimal_actions: int = 10
) -> float:
    """
    Reward in [0, 1] combining answer correctness with step-efficiency.

    Args:
        final_answer: Agent’s final answer.
        expected_answer: Ground-truth answer.
        n_actions: Number of actions the agent actually executed.
        optimal_actions: Ideal number of actions; no penalty until this point.

    Returns:
        A float ∈ [0, 1].
    """
    if n_actions <= 0:
        raise ValueError("n_actions must be ≥ 1")

    # If final_answer is not a string, convert it to string
    if not isinstance(final_answer, str):
        final_answer = str(final_answer)

    # Correctness
    sim = SequenceMatcher(None, final_answer.strip().lower(), expected_answer.strip().lower()).ratio()
    correctness = max(0.0, min(1.0, (sim - 0.70) / 0.30))  # linear ramp 0.7→1.0

    # Efficiency (penalise only extra steps
    # γ chosen so that +5 steps ⇒ ×0.5.
    extra = max(0, n_actions - optimal_actions)
    gamma = 0.5 ** (1 / 5)  # ≈ 0.87055
    efficiency = gamma**extra  # ≤ 1.0, =1.0 when extra==0

    # Combine
    reward = correctness * efficiency
    return round(reward, 6)
