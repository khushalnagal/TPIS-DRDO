# pipeline/scorer.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import json
from langchain_ollama import OllamaLLM
from pydantic import BaseModel, Field
from config import LLM_MODEL

# ── LLM Instance ────────────────────────────────────────
llm = OllamaLLM(model=LLM_MODEL)


# ── Pydantic Score Model ─────────────────────────────────
class ReportScore(BaseModel):
    technical_depth: int = Field(ge=0, le=100)
    clarity: int = Field(ge=0, le=100)
    methodology: int = Field(ge=0, le=100)
    results: int = Field(ge=0, le=100)
    references: int = Field(ge=0, le=100)
    total: float = Field(ge=0, le=100)
    feedback: str


# ── Scoring Prompt ───────────────────────────────────────
SCORING_PROMPT = """You are an expert evaluator at DRDO reviewing a trainee research report.
Score the report on the following 5 dimensions. Return ONLY a valid JSON object.

SCORING DIMENSIONS:
1. technical_depth (0-100): Domain knowledge, equations, algorithms, concepts
2. clarity (0-100): Logical flow, headings, writing quality, abstract
3. methodology (0-100): Experimental design, dataset choices, reproducibility
4. results (0-100): Data interpretation, charts, conclusions, critical analysis
5. references (0-100): Citation quality, relevance, recency

REPORT TEXT:
{report_text}

Return ONLY this JSON format, nothing else:
{{
    "technical_depth": <score 0-100>,
    "clarity": <score 0-100>,
    "methodology": <score 0-100>,
    "results": <score 0-100>,
    "references": <score 0-100>,
    "feedback": "<2-3 sentences of constructive feedback>"
}}"""


# ── Score Calculator ─────────────────────────────────────
def calculate_total(scores: dict) -> float:
    """Calculate weighted total score."""
    weights = {
        "technical_depth": 0.25,
        "clarity": 0.20,
        "methodology": 0.20,
        "results": 0.25,
        "references": 0.10
    }
    total = sum(scores[dim] * weights[dim] for dim in weights)
    return round(total, 2)


# ── JSON Parser ──────────────────────────────────────────
def parse_score_response(response: str) -> dict:
    """
    Extracts JSON from LLM response.
    Handles missing closing brace and extra text.
    """
    # Find the JSON block
    start = response.find("{")
    end = response.rfind("}")
    
    if start == -1:
        raise ValueError("No JSON found in LLM response")
    
    # If closing brace missing, add it
    if end == -1 or end < start:
        json_str = response[start:] + "\n}"
    else:
        json_str = response[start:end + 1]
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # Last resort — add closing brace and try again
        json_str = response[start:] + "\n}"
        return json.loads(json_str)

# ── Main Scorer ──────────────────────────────────────────
def score_report(report_text: str, filename: str = "unknown") -> dict:
    """
    Scores a report across 5 dimensions.
    Returns a dictionary with scores + feedback.

    This is the integration point with db_writer.py.
    """
    print(f"  Scoring: {filename}")

    # Truncate if too long for context window
    max_chars = 3000
    if len(report_text) > max_chars:
        report_text = report_text[:max_chars] + "\n...[truncated]"

    # Build prompt
    prompt = SCORING_PROMPT.format(report_text=report_text)

    # Call LLM
    response = llm.invoke(prompt)
    

    # Parse JSON response
    raw_scores = parse_score_response(response)

    # Calculate weighted total
    total = calculate_total(raw_scores)

    # Build final score dict — this is what db_writer.py receives
    scores = {
        "technical_depth": raw_scores["technical_depth"],
        "clarity": raw_scores["clarity"],
        "methodology": raw_scores["methodology"],
        "results": raw_scores["results"],
        "references": raw_scores["references"],
        "total": total,
        "feedback": raw_scores["feedback"]
    }

    # Validate with Pydantic
    ReportScore(**scores)

    return scores


# ── Test ─────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing scorer...\n")

    sample_report = """
    Title: CNN-Based Target Detection in Radar Signals

    Abstract:
    This report presents a deep learning approach to radar target detection
    using Convolutional Neural Networks trained on DRDO radar signal data.

    Methodology:
    We collected 5000 radar signal samples from DRDO test range.
    80% training, 20% testing split was used. A 4-layer CNN with batch
    normalization and dropout was trained for 50 epochs using Adam optimizer
    with learning rate 0.001. Data augmentation included random noise injection.

    Results:
    The CNN achieved 91.3% detection accuracy vs 78.2% for CFAR baseline.
    False positive rate reduced by 34%. ROC-AUC score was 0.967.
    Confusion matrix shows strong performance across all target classes.

    Conclusion:
    Deep learning significantly outperforms traditional signal processing
    for radar target detection. Real-time deployment is feasible on GPU hardware.

    References:
    1. LeCun et al. (1998) - Gradient based learning
    2. Wen et al. (2020) - Deep learning for radar
    3. Richards (2014) - Radar Signal Processing fundamentals
    4. Skolnik (2008) - Introduction to Radar Systems
    """

    print("Scoring sample DRDO report...")
    print("-" * 50)

    scores = score_report(sample_report, filename="sample_report.pdf")

    print("\n" + "=" * 50)
    print("SCORE RESULTS:")
    print("=" * 50)
    print(f"  Technical Depth : {scores['technical_depth']}/100  (weight: 25%)")
    print(f"  Clarity         : {scores['clarity']}/100  (weight: 20%)")
    print(f"  Methodology     : {scores['methodology']}/100  (weight: 20%)")
    print(f"  Results         : {scores['results']}/100  (weight: 25%)")
    print(f"  References      : {scores['references']}/100  (weight: 10%)")
    print(f"  {'─'*40}")
    print(f"  TOTAL SCORE     : {scores['total']}/100")
    print(f"\nFeedback:")
    print(f"  {scores['feedback']}")
    print(f"\n✅ Scorer works!")
    print(f"\nThis dict goes to db_writer.py:")
    print(scores)