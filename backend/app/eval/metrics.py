"""
Pure Python metrics computation for policy findings evaluation.
Matches predicted findings to expected ground-truth findings using entry code + span overlap.
Computes overall and per-category Precision, Recall, F1, and error listings.
"""

from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from app.eval.schema import ExpectedFinding, EvalDocument


def spans_overlap(start1: int, end1: int, start2: int, end2: int) -> bool:
    """Returns True if [start1, end1) and [start2, end2) overlap by at least 1 character."""
    return max(start1, start2) < min(end1, end2)


def finding_matches(
    pred: Dict[str, Any],
    exp: ExpectedFinding,
    require_verdict_match: bool = False,
) -> bool:
    """
    Core matching criterion:
    1. Entry codes match (case-insensitive)
    2. Character spans overlap
    3. If require_verdict_match is True and exp has a verdict, verdicts must match
    """
    pred_code = (pred.get("cited_entry_code") or "").strip().upper()
    exp_code = exp.entry_code.strip().upper()

    if pred_code != exp_code:
        return False

    pred_start = int(pred.get("span_start", 0))
    pred_end = int(pred.get("span_end", 0))

    if not spans_overlap(pred_start, pred_end, exp.span_start, exp.span_end):
        return False

    if require_verdict_match and exp.verdict:
        pred_verdict = (pred.get("claim_verdict") or "").strip().lower()
        if pred_verdict != exp.verdict.strip().lower():
            return False

    return True


@dataclass
class MetricSummary:
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0

    def compute(self) -> None:
        if self.true_positives + self.false_positives > 0:
            self.precision = self.true_positives / (self.true_positives + self.false_positives)
        else:
            self.precision = 1.0 if self.false_negatives == 0 else 0.0

        if self.true_positives + self.false_negatives > 0:
            self.recall = self.true_positives / (self.true_positives + self.false_negatives)
        else:
            self.recall = 1.0

        if self.precision + self.recall > 0:
            self.f1 = 2 * (self.precision * self.recall) / (self.precision + self.recall)
        else:
            self.f1 = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tp": self.true_positives,
            "fp": self.false_positives,
            "fn": self.false_negatives,
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1": round(self.f1, 4),
        }


@dataclass
class EvalReport:
    total_documents: int = 0
    clean_documents: int = 0
    clean_documents_passed: int = 0
    overall: MetricSummary = field(default_factory=MetricSummary)
    by_issue_type: Dict[str, MetricSummary] = field(default_factory=dict)
    by_claim_verdict: Dict[str, MetricSummary] = field(default_factory=dict)
    false_positives: List[Dict[str, Any]] = field(default_factory=list)
    false_negatives: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": {
                "total_documents": self.total_documents,
                "clean_documents": self.clean_documents,
                "clean_documents_passed": self.clean_documents_passed,
                "clean_pass_rate": round(
                    self.clean_documents_passed / max(1, self.clean_documents), 4
                ) if self.clean_documents else 1.0,
                "overall": self.overall.to_dict(),
            },
            "by_issue_type": {k: v.to_dict() for k, v in self.by_issue_type.items()},
            "by_claim_verdict": {k: v.to_dict() for k, v in self.by_claim_verdict.items()},
            "false_positives_count": len(self.false_positives),
            "false_negatives_count": len(self.false_negatives),
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives,
        }


def compute_eval_metrics(
    eval_docs: List[EvalDocument],
    predictions_by_doc_id: Dict[str, List[Dict[str, Any]]],
    require_verdict_match: bool = False,
) -> EvalReport:
    """
    Evaluates predictions across all documents in eval_docs.
    Returns an EvalReport with overall and segmented metrics.
    """
    report = EvalReport(total_documents=len(eval_docs))

    # Track by issue_type and verdict
    issue_type_summaries: Dict[str, MetricSummary] = {}
    verdict_summaries: Dict[str, MetricSummary] = {}

    for doc in eval_docs:
        expected_list = doc.expected_findings
        predicted_list = predictions_by_doc_id.get(doc.id, [])

        if doc.is_clean:
            report.clean_documents += 1
            if len(predicted_list) == 0:
                report.clean_documents_passed += 1

        matched_pred_indices: Set[int] = set()
        matched_exp_indices: Set[int] = set()

        # Greedy 1-to-1 matching
        for exp_idx, exp in enumerate(expected_list):
            for pred_idx, pred in enumerate(predicted_list):
                if pred_idx in matched_pred_indices:
                    continue
                if finding_matches(pred, exp, require_verdict_match=require_verdict_match):
                    matched_exp_indices.add(exp_idx)
                    matched_pred_indices.add(pred_idx)
                    break

        # Count TPs, FPs, FNs for this doc
        doc_tp = len(matched_exp_indices)
        report.overall.true_positives += doc_tp

        # False negatives (expected but missed)
        for exp_idx, exp in enumerate(expected_list):
            itype = exp.issue_type
            if itype not in issue_type_summaries:
                issue_type_summaries[itype] = MetricSummary()

            if exp.verdict:
                vkey = exp.verdict
                if vkey not in verdict_summaries:
                    verdict_summaries[vkey] = MetricSummary()

            if exp_idx in matched_exp_indices:
                issue_type_summaries[itype].true_positives += 1
                if exp.verdict:
                    verdict_summaries[exp.verdict].true_positives += 1
            else:
                report.overall.false_negatives += 1
                issue_type_summaries[itype].false_negatives += 1
                if exp.verdict:
                    verdict_summaries[exp.verdict].false_negatives += 1
                report.false_negatives.append({
                    "document_id": doc.id,
                    "channel": doc.channel,
                    "entry_code": exp.entry_code,
                    "issue_type": exp.issue_type,
                    "excerpt": exp.excerpt,
                    "span": [exp.span_start, exp.span_end],
                    "verdict": exp.verdict,
                })

        # False positives (predicted but not expected)
        for pred_idx, pred in enumerate(predicted_list):
            if pred_idx not in matched_pred_indices:
                report.overall.false_positives += 1
                itype = pred.get("issue_type", "unknown")
                if itype not in issue_type_summaries:
                    issue_type_summaries[itype] = MetricSummary()
                issue_type_summaries[itype].false_positives += 1

                p_verdict = pred.get("claim_verdict")
                if p_verdict:
                    if p_verdict not in verdict_summaries:
                        verdict_summaries[p_verdict] = MetricSummary()
                    verdict_summaries[p_verdict].false_positives += 1

                report.false_positives.append({
                    "document_id": doc.id,
                    "channel": doc.channel,
                    "cited_entry_code": pred.get("cited_entry_code"),
                    "issue_type": pred.get("issue_type"),
                    "excerpt": pred.get("excerpt"),
                    "span": [pred.get("span_start"), pred.get("span_end")],
                    "claim_verdict": pred.get("claim_verdict"),
                    "explanation": pred.get("explanation"),
                })

    # Compute summaries
    report.overall.compute()

    for s in issue_type_summaries.values():
        s.compute()
    report.by_issue_type = issue_type_summaries

    for s in verdict_summaries.values():
        s.compute()
    report.by_claim_verdict = verdict_summaries

    return report
