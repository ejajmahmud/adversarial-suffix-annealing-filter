"""Core Adversarial Suffix Annealing Filter implementation."""
import math
import re
from dataclasses import dataclass
from typing import List, Tuple

@dataclass
class FilterResult:
    is_adversarial: bool
    clean_text: str
    stripped_suffix: str
    perplexity_score: float
    reason: str

class SuffixAnnealingFilter:
    """Detects and strips high-entropy gibberish suffixes produced by gradient-based attacks."""
    
    def __init__(self, entropy_threshold: float = 3.0, min_suffix_len: int = 10):
        self.entropy_threshold = entropy_threshold
        self.min_suffix_len = min_suffix_len

    def calculate_char_entropy(self, s: str) -> float:
        if not s:
            return 0.0
        counts = {}
        for c in s:
            counts[c] = counts.get(c, 0) + 1
        entropy = 0.0
        tot = len(s)
        for c, count in counts.items():
            p = count / tot
            entropy -= p * math.log2(p)
        return round(entropy, 3)

    def analyze_and_strip(self, prompt: str) -> FilterResult:
        words = prompt.split()
        if len(words) < 3:
            return FilterResult(False, prompt, "", 0.0, "Prompt too short for suffix analysis")

        # Evaluate last 25% of tokens
        cut_idx = max(1, int(len(words) * 0.75))
        prefix = " ".join(words[:cut_idx])
        suffix = " ".join(words[cut_idx:])

        # Check for repetitive punctuation or random consonant clusters typical of GCG
        punct_ratio = len(re.findall(r"[^a-zA-Z0-9\s]", suffix)) / max(1, len(suffix))
        entropy = self.calculate_char_entropy(suffix)
        
        # Check dictionary-like word ratio
        has_gibberish = bool(re.search(r"\b[bcdfghjklmnpqrstvwxyz]{6,}\b", suffix.lower()))

        is_adv = False
        reason = "Clean text"
        if len(suffix) >= self.min_suffix_len:
            if (punct_ratio > 0.25 and entropy > 2.5) or has_gibberish:
                is_adv = True
                reason = "Detected GCG attack signature (high punctuation entropy or dense consonant gibberish)"

        if is_adv:
            return FilterResult(
                is_adversarial=True,
                clean_text=prefix,
                stripped_suffix=suffix,
                perplexity_score=entropy,
                reason=reason
            )

        return FilterResult(False, prompt, "", entropy, "Normal natural language profile")
