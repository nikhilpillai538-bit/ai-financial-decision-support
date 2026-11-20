"""
FinBERT Financial Sentiment Analysis Service for Phase 10.

Provides classification into Positive, Negative, and Neutral classes using
Hugging Face's `ProsusAI/finbert` model when available, with a deterministic
lexicon-based Mock analyzer for automated offline testing and graceful degradation.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
import logging
import re
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("uvicorn.error")

# ---------------------------------------------------------------------------
# Sentiment Result Data Model
# ---------------------------------------------------------------------------

@dataclass
class SentimentResult:
    """Standardized output of financial sentiment inference."""
    label: str  # "positive", "negative", "neutral"
    confidence: float  # Max probability [0.0, 1.0]
    score: Decimal  # Compound score on [-1.0000, +1.0000] scale (p_pos - p_neg)
    probabilities: Dict[str, float]  # e.g. {"positive": 0.85, "neutral": 0.10, "negative": 0.05}
    model_name: str
    analyzed_field: str
    analyzed_at: datetime
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return {
            "label": self.label,
            "confidence": round(self.confidence, 4),
            "score": str(self.score),
            "probabilities": {k: round(v, 4) for k, v in self.probabilities.items()},
            "model_name": self.model_name,
            "analyzed_field": self.analyzed_field,
            "analyzed_at": self.analyzed_at.isoformat(),
            "warnings": self.warnings,
        }


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class SentimentAnalysisError(Exception):
    """Base error for sentiment analysis failures."""
    pass


class FinBERTUnavailableError(SentimentAnalysisError):
    """Raised when ProsusAI/finbert is requested but PyTorch or Transformers is absent."""
    pass


# ---------------------------------------------------------------------------
# Abstract Sentiment Analyzer
# ---------------------------------------------------------------------------

class BaseSentimentAnalyzer(ABC):
    """Abstract interface for financial sentiment analyzers."""

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if model dependencies are installed and model can run."""
        pass

    @abstractmethod
    def analyze(self, headline: str, summary: Optional[str] = None) -> SentimentResult:
        """Classify single financial news text into sentiment classes."""
        pass

    @abstractmethod
    def analyze_batch(self, texts: List[Tuple[str, Optional[str]]]) -> List[SentimentResult]:
        """Classify a batch of financial news texts."""
        pass


# ---------------------------------------------------------------------------
# Production FinBERT Analyzer (ProsusAI/finbert)
# ---------------------------------------------------------------------------

class FinBERTSentimentAnalyzer(BaseSentimentAnalyzer):
    """
    Financial sentiment analyzer powered by ProsusAI/finbert via Hugging Face.
    Loads model once per process (singleton) and supports batch inference.
    """

    _model = None
    _tokenizer = None
    _device = "cpu"
    _load_error = None

    def __init__(self, model_name: str = "ProsusAI/finbert", device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self._ensure_loaded()

    @classmethod
    def _ensure_loaded(cls, model_name: str = "ProsusAI/finbert", device: str = "cpu"):
        if cls._model is not None:
            return

        try:
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer

            cls._tokenizer = AutoTokenizer.from_pretrained(model_name)
            cls._model = AutoModelForSequenceClassification.from_pretrained(model_name)
            cls._device = device
            if device != "cpu" and torch.cuda.is_available():
                cls._model.to(device)
            cls._model.eval()
            cls._load_error = None
            logger.info("FinBERT model '%s' loaded successfully on device '%s'.", model_name, device)
        except ImportError:
            cls._load_error = "PyTorch or HuggingFace Transformers is not installed in the environment."
            logger.warning("FinBERT unavailable: %s", cls._load_error)
        except Exception as exc:
            cls._load_error = f"Failed to load FinBERT weights: {exc}"
            logger.warning("FinBERT load failure: %s", exc)

    def is_available(self) -> bool:
        return self._model is not None and self._tokenizer is not None

    def analyze(self, headline: str, summary: Optional[str] = None) -> SentimentResult:
        results = self.analyze_batch([(headline, summary)])
        return results[0]

    def analyze_batch(self, texts: List[Tuple[str, Optional[str]]]) -> List[SentimentResult]:
        if not self.is_available():
            raise FinBERTUnavailableError(
                f"FinBERT sentiment analysis is currently unavailable: {self._load_error or 'Model not loaded'}. "
                "Install 'torch' and 'transformers' or use MockSentimentAnalyzer."
            )

        import torch
        from torch.nn.functional import softmax

        now_utc = datetime.now(timezone.utc)
        results: List[SentimentResult] = []

        # Prepare strings: "Headline - Summary"
        combined_texts = []
        warnings_list = []

        for h, s in texts:
            clean_h = (h or "").strip()
            clean_s = (s or "").strip()
            warnings = []

            if not clean_h:
                warnings.append("Headline text was empty.")
            if clean_s and len(clean_s) > 300:
                clean_s = clean_s[:297] + "..."
                warnings.append("Summary was truncated to 300 characters for inference.")

            input_text = f"{clean_h} - {clean_s}".strip(" -")
            if not input_text:
                input_text = "Market update"
                warnings.append("No text provided; analyzed placeholder.")

            combined_texts.append(input_text)
            warnings_list.append(warnings)

        # Batch tokenization
        inputs = self._tokenizer(
            combined_texts,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt",
        )
        if self._device != "cpu":
            inputs = {k: v.to(self._device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self._model(**inputs)
            probs = softmax(outputs.logits, dim=-1).cpu().numpy()

        # FinBERT class order: [positive, negative, neutral]
        labels = ["positive", "negative", "neutral"]

        for i, row in enumerate(probs):
            prob_dict = {
                "positive": float(row[0]),
                "negative": float(row[1]),
                "neutral": float(row[2]),
            }
            # Predicted class is max probability
            pred_idx = int(row.argmax())
            pred_label = labels[pred_idx]
            confidence = float(row[pred_idx])

            # Compound score: p_pos - p_neg, bounded on [-1.0000, 1.0000]
            compound = Decimal(str(round(prob_dict["positive"] - prob_dict["negative"], 4)))

            results.append(
                SentimentResult(
                    label=pred_label,
                    confidence=confidence,
                    score=compound,
                    probabilities=prob_dict,
                    model_name=self.model_name,
                    analyzed_field="headline_and_summary",
                    analyzed_at=now_utc,
                    warnings=warnings_list[i],
                )
            )

        return results


# ---------------------------------------------------------------------------
# Mock Financial Sentiment Analyzer (Testing & Offline Development)
# ---------------------------------------------------------------------------

class MockSentimentAnalyzer(BaseSentimentAnalyzer):
    """
    Deterministic financial lexicon analyzer for unit tests and offline operation.
    Requires no PyTorch/Transformers dependencies and no model downloads.
    """

    POSITIVE_KEYWORDS = [
        "surge", "surges", "gain", "gains", "jump", "jumps", "rally", "rallies",
        "profit", "profits", "profitable", "growth", "grow", "beat", "beats",
        "bull", "bullish", "expansion", "dividend", "outperform", "record",
        "upward", "optimism", "boost", "boosts", "milestone", "highs", "rebound"
    ]

    NEGATIVE_KEYWORDS = [
        "plunge", "plunges", "slump", "slumps", "drop", "drops", "fall", "falls",
        "loss", "losses", "bear", "bearish", "crash", "decline", "declines",
        "inflation", "deficit", "warn", "warning", "warns", "lawsuit", "layoff",
        "layoffs", "default", "crisis", "pressure", "fraud", "recession", "tumble"
    ]

    def is_available(self) -> bool:
        return True

    def analyze(self, headline: str, summary: Optional[str] = None) -> SentimentResult:
        results = self.analyze_batch([(headline, summary)])
        return results[0]

    def analyze_batch(self, texts: List[Tuple[str, Optional[str]]]) -> List[SentimentResult]:
        now_utc = datetime.now(timezone.utc)
        results: List[SentimentResult] = []

        for h, s in texts:
            clean_h = (h or "").strip()
            clean_s = (s or "").strip()
            warnings = []

            if not clean_h:
                warnings.append("Headline text was empty.")

            text_full = f"{clean_h} {clean_s}".lower()
            words = set(re.findall(r"\b[a-z]+\b", text_full))

            pos_matches = sum(1 for kw in self.POSITIVE_KEYWORDS if kw in words)
            neg_matches = sum(1 for kw in self.NEGATIVE_KEYWORDS if kw in words)

            if pos_matches > neg_matches:
                label = "positive"
                confidence = 0.82
                p_pos, p_neg, p_neu = 0.82, 0.08, 0.10
            elif neg_matches > pos_matches:
                label = "negative"
                confidence = 0.80
                p_pos, p_neg, p_neu = 0.08, 0.80, 0.12
            else:
                label = "neutral"
                confidence = 0.75
                p_pos, p_neg, p_neu = 0.15, 0.15, 0.70

            score = Decimal(str(round(p_pos - p_neg, 4)))

            results.append(
                SentimentResult(
                    label=label,
                    confidence=confidence,
                    score=score,
                    probabilities={"positive": p_pos, "negative": p_neg, "neutral": p_neu},
                    model_name="MockFinancialSentiment:v1.0",
                    analyzed_field="headline_and_summary",
                    analyzed_at=now_utc,
                    warnings=warnings,
                )
            )

        return results


# ---------------------------------------------------------------------------
# Sentiment Analyzer Factory
# ---------------------------------------------------------------------------

def get_sentiment_analyzer(mock_override: Optional[bool] = None) -> BaseSentimentAnalyzer:
    """Resolve and return active sentiment analyzer (FinBERT or Mock)."""
    from app.news.config import get_news_settings

    settings = get_news_settings()
    use_mock = mock_override if mock_override is not None else settings.mock_mode

    if use_mock:
        return MockSentimentAnalyzer()

    # Attempt to load FinBERT
    finbert = FinBERTSentimentAnalyzer(
        model_name=settings.finbert_model_name,
        device=settings.finbert_device,
    )
    if not finbert.is_available():
        logger.info("FinBERT dependencies missing; falling back to MockSentimentAnalyzer.")
        return MockSentimentAnalyzer()

    return finbert
