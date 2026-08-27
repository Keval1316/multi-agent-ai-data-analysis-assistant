from typing import Tuple, List
from backend.app.models.understanding import DatasetUnderstanding
from backend.app.models.statistics import StatisticalAnalysisResult
from backend.app.models.sql import SQLAnalysisResult
from backend.app.models.patterns import PatternDetectionResult
from backend.app.models.quality import QualityReport
from backend.app.models.insights import InsightCollection, InsightItem
from backend.app.models.critic import CriticReviewResult
from backend.app.agents.generate_insights import InsightGenerationAgent
from backend.app.agents.critic_review import CriticReviewAgent
from backend.app.core.logging import logger


class InsightRevisionOrchestrator:
    """Orchestrates generation, critic verification, and iterative revision with a hard cap of 2 loops."""

    MAX_REVISIONS = 2

    @classmethod
    def run_generation_and_critic_loop(
        cls,
        understanding: DatasetUnderstanding,
        statistics: StatisticalAnalysisResult,
        sql_results: SQLAnalysisResult,
        patterns: PatternDetectionResult,
        quality: QualityReport
    ) -> Tuple[InsightCollection, CriticReviewResult, int]:
        logger.info(f"Starting Insight Generation and Critic Loop for dataset '{statistics.dataset_id}'")

        # 1. Initial Generation
        current_insights = InsightGenerationAgent.generate(
            understanding=understanding,
            statistics=statistics,
            sql_results=sql_results,
            patterns=patterns,
            quality=quality
        )

        # 2. Initial Critic Review
        current_review = CriticReviewAgent.review(
            insights=current_insights,
            statistics=statistics,
            sql_results=sql_results,
            patterns=patterns
        )

        revision_count = 0

        # 3. Revision Loop (Max 2 iterations)
        while not current_review.approved and revision_count < cls.MAX_REVISIONS:
            revision_count += 1
            logger.warning(
                f"Critic rejected insights (Revision {revision_count}/{cls.MAX_REVISIONS}). "
                f"Issues flagged: {len(current_review.unsupported_claims)}. Re-generating..."
            )

            # Construct structured feedback text
            feedback_parts = [f"General Feedback: {current_review.feedback}"]
            if current_review.unsupported_claims:
                feedback_parts.append("Unsupported Claims:")
                for uc in current_review.unsupported_claims:
                    feedback_parts.append(f"- [Insight {uc.insight_id}] '{uc.claim_text}': {uc.reason} (Fact: {uc.ground_truth_fact or 'Not verified'})")
            if current_review.required_corrections:
                feedback_parts.append("Required Corrections:")
                for rc in current_review.required_corrections:
                    feedback_parts.append(f"- {rc}")

            revision_prompt = "\n".join(feedback_parts)

            # Re-generate with critic feedback
            current_insights = InsightGenerationAgent.generate(
                understanding=understanding,
                statistics=statistics,
                sql_results=sql_results,
                patterns=patterns,
                quality=quality,
                revision_critique=revision_prompt
            )

            # Re-audit
            current_review = CriticReviewAgent.review(
                insights=current_insights,
                statistics=statistics,
                sql_results=sql_results,
                patterns=patterns
            )

        # 4. Final Fallback if still unapproved after max revisions
        if not current_review.approved:
            logger.warning(f"Exceeded max revisions ({cls.MAX_REVISIONS}). Pruning unverified claims and attaching caveat.")
            flagged_ids = {uc.insight_id for uc in current_review.unsupported_claims}

            pruned_insights: List[InsightItem] = []
            for ins in current_insights.insights:
                if ins.id in flagged_ids:
                    # Downgrade confidence and append caveat
                    ins.confidence = "Caveat"
                    ins.finding = f"{ins.finding} (Note: Claim subject to statistical data limitation caveat)."
                pruned_insights.append(ins)

            current_insights.insights = pruned_insights
            current_insights.overall_confidence_rating = "Caveat"

        logger.info(
            f"Insight and Critic loop finished after {revision_count} revision(s). "
            f"Final Status: Approved={current_review.approved}, Total Insights={len(current_insights.insights)}"
        )

        return current_insights, current_review, revision_count
