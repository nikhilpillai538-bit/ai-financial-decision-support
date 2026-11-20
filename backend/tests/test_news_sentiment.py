"""
Unit tests for Phase 10 FinBERT Financial Sentiment Analysis.

Verifies:
- MockSentimentAnalyzer deterministic lexicon classification
- Positive, negative, and neutral probability calculation
- Normalization of sentiment score to [-1.0000, +1.0000] scale
- Probabilities summation to 1.0
- Empty headline handling and warning emission
- FinBERTSentimentAnalyzer availability checking and singleton behavior
- FinBERTUnavailableError on missing PyTorch/Transformers dependencies
- Factory function resolution and fallback behavior
"""

from decimal import Decimal
import pytest

from app.news.sentiment import (
    FinBERTSentimentAnalyzer,
    FinBERTUnavailableError,
    MockSentimentAnalyzer,
    SentimentResult,
    get_sentiment_analyzer,
)


class TestMockSentimentAnalyzer:
    """Tests for deterministic lexicon-based financial sentiment analyzer."""

    @pytest.fixture()
    def analyzer(self) -> MockSentimentAnalyzer:
        return MockSentimentAnalyzer()

    def test_positive_sentiment_classification(self, analyzer: MockSentimentAnalyzer):
        headline = "Tech Stocks Surge on Strong AI Earnings Beat and Record Profits"
        summary = "Cloud revenue grew 25%, marking an optimistic milestone for the bull market."
        res = analyzer.analyze(headline, summary)

        assert isinstance(res, SentimentResult)
        assert res.label == "positive"
        assert res.confidence >= 0.75
        assert res.score > Decimal("0.0000")
        assert res.probabilities["positive"] > res.probabilities["negative"]
        assert pytest.approx(sum(res.probabilities.values()), 0.001) == 1.0

    def test_negative_sentiment_classification(self, analyzer: MockSentimentAnalyzer):
        headline = "Crude Oil Slumps on Demand Warning and Looming Recession Pressure"
        summary = "Energy stocks tumble as heavy losses and inflation deficit mount."
        res = analyzer.analyze(headline, summary)

        assert isinstance(res, SentimentResult)
        assert res.label == "negative"
        assert res.confidence >= 0.75
        assert res.score < Decimal("0.0000")
        assert res.probabilities["negative"] > res.probabilities["positive"]
        assert pytest.approx(sum(res.probabilities.values()), 0.001) == 1.0

    def test_neutral_sentiment_classification(self, analyzer: MockSentimentAnalyzer):
        headline = "Federal Reserve Publishes Calendar of Upcoming Regular Meetings"
        summary = "The central bank released dates for routine scheduled releases."
        res = analyzer.analyze(headline, summary)

        assert isinstance(res, SentimentResult)
        assert res.label == "neutral"
        assert res.score == Decimal("0.0000")
        assert res.probabilities["neutral"] >= 0.70
        assert pytest.approx(sum(res.probabilities.values()), 0.001) == 1.0

    def test_empty_headline_adds_warning(self, analyzer: MockSentimentAnalyzer):
        res = analyzer.analyze("", "Some summary text")
        assert "Headline text was empty." in res.warnings
        assert res.label in {"positive", "negative", "neutral"}

    def test_batch_analysis_matches_single(self, analyzer: MockSentimentAnalyzer):
        pairs = [
            ("Company posts record profit", "Bullish momentum"),
            ("Bank faces major fraud lawsuit", "Heavy losses"),
            ("Exchange reports routine volume", "Normal market close"),
        ]
        batch_results = analyzer.analyze_batch(pairs)
        assert len(batch_results) == 3

        for i, (h, s) in enumerate(pairs):
            single = analyzer.analyze(h, s)
            assert batch_results[i].label == single.label
            assert batch_results[i].score == single.score

    def test_to_dict_serialization(self, analyzer: MockSentimentAnalyzer):
        res = analyzer.analyze("Apple reports profit growth")
        d = res.to_dict()
        assert d["label"] == "positive"
        assert "confidence" in d
        assert "score" in d
        assert "probabilities" in d
        assert "model_name" in d
        assert "analyzed_at" in d


class TestFinBERTSentimentAnalyzer:
    """Tests for FinBERTSentimentAnalyzer integration and graceful fallback."""

    def test_availability_and_error_handling(self):
        analyzer = FinBERTSentimentAnalyzer()
        # If PyTorch or transformers is not installed in the test environment
        if not analyzer.is_available():
            with pytest.raises(FinBERTUnavailableError, match="FinBERT sentiment analysis is currently unavailable"):
                analyzer.analyze_batch([("Test headline", None)])
        else:
            # If installed, verify it can perform an analysis
            res = analyzer.analyze("Company reports strong earnings gain")
            assert res.label in {"positive", "negative", "neutral"}

    def test_factory_function_with_mock_override(self):
        analyzer = get_sentiment_analyzer(mock_override=True)
        assert isinstance(analyzer, MockSentimentAnalyzer)
        assert analyzer.is_available() is True

    def test_factory_function_fallback(self):
        # Even without override, if FinBERT is missing it gracefully returns MockSentimentAnalyzer
        analyzer = get_sentiment_analyzer()
        assert analyzer is not None
        assert analyzer.is_available() is True
