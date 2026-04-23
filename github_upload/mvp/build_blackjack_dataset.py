from collections import Counter
from pathlib import Path
import random
import sys
from typing import Iterable, List, Sequence, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from blackjack_engine import format_for_gpt, is_bust, recommend_action


RANKS: List[str] = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
NON_TEN_RANKS = {"A", "2", "3", "4", "5", "6", "7", "8", "9"}
TWO_DECK_LIMITS = {rank: 8 for rank in NON_TEN_RANKS}
TWO_DECK_LIMITS.update({"10": 8, "J": 8, "Q": 8, "K": 8})

MAX_PLAYER_CARDS = 4
OUTPUT_PATH = SCRIPT_DIR / "data" / "train.txt"
RANDOM_SEED = 1337
OPENING_HAND_SAMPLE_LIMIT = 60
LATER_HAND_SAMPLE_LIMIT = 16
LATER_HAND_ATTEMPTS_MULTIPLIER = 10
VARIANTS_PER_STATE = 3

ANCHOR_STATES: List[Tuple[Tuple[str, ...], str]] = [
    (("8", "8"), "6"),
    (("10", "6"), "7"),
    (("A", "7"), "9"),
    (("9", "9"), "7"),
    (("10", "2"), "4"),
    (("A", "6"), "3"),
    (("10", "10"), "10"),
    (("10", "5"), "10"),
    (("9", "7"), "10"),
    (("10", "3"), "6"),
    (("A", "5"), "4"),
    (("A", "8"), "6"),
    (("9", "2"), "5"),
]


TIER_PROMPTS = {
    "Table Coach": {
        "mode": "classical",
        "response_label": "Coach Call",
    },
    "EV Edge": {
        "mode": "expected_value",
        "response_label": "Coach Call",
    },
    "Bankroll Desk": {
        "mode": "bankroll",
        "response_label": "Bankroll Lens",
    },
}


def format_best_ev(best_ev) -> str:
    if best_ev is None:
        return "N/A"
    return f"{best_ev:+.3f}"


def format_margin(ev_margin) -> str:
    if ev_margin is None:
        return "N/A"
    return f"{ev_margin:+.3f}"


def cards_within_two_decks(cards: Sequence[str]) -> bool:
    counts = Counter(cards)
    return all(counts[rank] <= TWO_DECK_LIMITS[rank] for rank in counts)


def canonical_hand(cards: Iterable[str]) -> Tuple[str, ...]:
    return tuple(sorted(cards, key=lambda rank: (RANKS.index(rank), rank)))


def valid_state(player_cards: Sequence[str], dealer_card: str) -> bool:
    all_cards = list(player_cards) + [dealer_card]
    return cards_within_two_decks(all_cards)


def tiered_response(result: dict, tier_name: str) -> str:
    coach = result.get("coach", {})
    action = result["recommended_action"]
    best_ev = result.get("best_ev")
    ev_margin = result.get("ev_margin")
    explanation = result["explanation"]
    math_reason = coach.get("math") or coach.get("decision_summary") or explanation
    decision_summary = coach.get("decision_summary") or explanation
    teaching_tip = coach.get("teaching_tip") or explanation
    common_mistake = coach.get("common_mistake") or explanation

    if tier_name == "Table Coach":
        variants = [
            coach.get("beginner") or explanation,
            f"{action}, because {decision_summary.lower()}",
            f"{action} is the clean table play here. {teaching_tip}",
            f"Stick with {action}. {common_mistake} {teaching_tip}",
        ]
        return random.choice([variant for variant in variants if variant])

    if tier_name == "EV Edge":
        if best_ev is None:
            return math_reason
        variants = [
            (
                f"{math_reason} The best play is worth {format_best_ev(best_ev)} units per original bet. "
                f"The edge over the next-best option is {format_margin(ev_margin)} units."
            ),
            (
                f"Expected value view: {action} leads the board at {format_best_ev(best_ev)} units. "
                f"The separation from the runner-up is {format_margin(ev_margin)} units, so the math is fairly clear."
            ),
            (
                f"The EV model prefers {action}. It grades this choice at {format_best_ev(best_ev)} units per original bet, "
                f"with a margin of {format_margin(ev_margin)} over the next-best line."
            ),
            (
                f"{action} is the financially strongest play. {math_reason} "
                f"On the model, that comes out to {format_best_ev(best_ev)} units with a {format_margin(ev_margin)} unit cushion."
            ),
        ]
        return random.choice(variants)

    pressure = "thin" if best_ev is not None and best_ev <= 0 else "positive"
    if best_ev is None:
        variants = [
            (
                f"{action} is the bankroll-aware play. This is a {pressure} spot, so the job is to stay disciplined "
                "and avoid letting variance force bad betting decisions."
            ),
            (
                f"Bankroll lens: {action} keeps the hand aligned with long-run discipline. "
                "Without a strong edge, stake control matters just as much as the move itself."
            ),
        ]
        return random.choice(variants)

    variants = [
        (
            f"{action} is the bankroll-aware play. This is a {pressure} edge at {format_best_ev(best_ev)} units per original bet, "
            "so profit comes from pairing the right move with disciplined bet sizing and enough bankroll to survive variance."
        ),
        (
            f"Bankroll lens: {action} is the correct line, but the money is made only if the stake stays controlled. "
            f"The hand is worth {format_best_ev(best_ev)} units, which means sizing discipline is part of the edge."
        ),
        (
            f"{action} protects the bankroll better than the alternatives. At {format_best_ev(best_ev)} units of expectation, "
            "this is the kind of edge that compounds only when the player avoids oversized bets."
        ),
        (
            f"For bankroll play, {action} is the right decision. The model values the hand at {format_best_ev(best_ev)} units per original bet, "
            "so long-run profit depends on surviving variance long enough for that edge to repeat."
        ),
    ]
    return random.choice(variants)


def serialize_state(player_cards: Sequence[str], dealer_card: str) -> List[str]:
    result = recommend_action(
        player_cards=list(player_cards),
        dealer_card=dealer_card,
        can_double=True,
        can_split=True,
        dealer_hits_soft_17=False,
        deck_count=2,
    )
    base_prompt = format_for_gpt(result)
    lines = []
    for _ in range(VARIANTS_PER_STATE):
        for tier_name, tier_meta in TIER_PROMPTS.items():
            lines.append(
                f"{base_prompt} | Tier: {tier_name} | Voice: {tier_meta['mode']} | "
                f"{tier_meta['response_label']}: {tiered_response(result, tier_name)}"
            )
    return lines


def random_hand(card_count: int) -> Tuple[str, ...]:
    return canonical_hand(random.choices(RANKS, k=card_count))


def opening_states() -> List[Tuple[Tuple[str, ...], str]]:
    seen = set()
    attempts = 0
    max_attempts = OPENING_HAND_SAMPLE_LIMIT * 6

    while len(seen) < OPENING_HAND_SAMPLE_LIMIT and attempts < max_attempts:
        attempts += 1
        hand = random_hand(2)
        dealer_card = random.choice(RANKS)
        if not valid_state(hand, dealer_card):
            continue
        if len(set(hand)) == 1:
            continue
        seen.add((hand, dealer_card))

    print(f"Collected {len(seen)} sampled opening-hand states after {attempts} attempts.")
    return sorted(seen)


def later_hit_states() -> List[Tuple[Tuple[str, ...], str]]:
    sampled_states: List[Tuple[Tuple[str, ...], str]] = []

    for card_count in range(3, MAX_PLAYER_CARDS + 1):
        seen = set()
        attempts = 0
        max_attempts = LATER_HAND_SAMPLE_LIMIT * LATER_HAND_ATTEMPTS_MULTIPLIER

        while len(seen) < LATER_HAND_SAMPLE_LIMIT and attempts < max_attempts:
            attempts += 1
            hand = random_hand(card_count)
            dealer_card = random.choice(RANKS)

            if not valid_state(hand, dealer_card):
                continue

            if is_bust(list(hand)):
                continue

            seen.add((hand, dealer_card))

        sampled_states.extend(sorted(seen))
        print(
            f"Collected {len(seen)} sampled later-hand states "
            f"for {card_count}-card player hands after {attempts} attempts."
        )

    return sampled_states


def build_dataset_lines() -> List[str]:
    serialized_lines = set()

    print("Building anchor training states...")
    for player_cards, dealer_card in ANCHOR_STATES:
        serialized_lines.update(serialize_state(player_cards, dealer_card))

    print("Building opening-hand states...")
    for player_cards, dealer_card in opening_states():
        serialized_lines.update(serialize_state(player_cards, dealer_card))

    print("Building sampled later-hit states...")
    for player_cards, dealer_card in later_hit_states():
        serialized_lines.update(serialize_state(player_cards, dealer_card))

    print(f"Prepared {len(serialized_lines)} unique serialized examples.")
    return sorted(serialized_lines)


def main() -> None:
    random.seed(RANDOM_SEED)
    lines = build_dataset_lines()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(lines)} training examples to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
