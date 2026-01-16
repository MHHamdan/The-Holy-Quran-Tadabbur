"""
AI Verification Assistant.

Uses LLM to assist with content verification by:
1. Analyzing flagged content for issues
2. Suggesting corrections
3. Providing confidence scores
4. Generating verification reports

Arabic: مساعد التحقق بالذكاء الاصطناعي
"""
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field, asdict
from enum import Enum

from app.rag.llm_provider import get_llm, BaseLLM, LLMResponse
from app.core.config import settings

logger = logging.getLogger(__name__)


class IssueCategory(str, Enum):
    """Categories of potential issues."""
    FACTUAL_ERROR = "factual_error"
    WEAK_EVIDENCE = "weak_evidence"
    TRANSLATION_ISSUE = "translation_issue"
    INCOMPLETE_INFO = "incomplete_info"
    FORMATTING = "formatting"
    NO_ISSUE = "no_issue"


@dataclass
class AIAnalysisResult:
    """Result of AI-assisted content analysis."""
    confidence: float  # 0.0-1.0
    issues_found: List[str] = field(default_factory=list)
    issue_category: IssueCategory = IssueCategory.NO_ISSUE
    suggestion: str = ""
    suggestion_ar: str = ""
    evidence_assessment: str = ""
    evidence_assessment_ar: str = ""
    recommended_action: str = ""  # approve, revise, reject, escalate
    analysis_details: Dict[str, Any] = field(default_factory=dict)
    raw_response: str = ""
    latency_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        result = asdict(self)
        result['issue_category'] = self.issue_category.value
        return result


class AIVerificationAssistant:
    """
    AI-powered verification assistant.

    Analyzes flagged content and provides recommendations.
    Uses structured prompts to ensure consistent, grounded analysis.
    """

    # System prompt for verification analysis
    SYSTEM_PROMPT = """You are a scholarly AI assistant for verifying Islamic/Quranic content.
Your role is to analyze flagged content for accuracy, completeness, and proper sourcing.

CRITICAL RULES:
1. You must NEVER invent or fabricate Islamic rulings, hadith, or tafsir
2. All claims must be grounded in provided evidence
3. If evidence is insufficient, clearly state uncertainty
4. Respect scholarly consensus (ijma') on core matters
5. Be objective and avoid sectarian bias

When analyzing content, evaluate:
- Factual accuracy against known Islamic sources
- Quality of evidence/citations
- Translation accuracy (Arabic/English)
- Completeness of information
- Potential for misunderstanding

Respond in JSON format with:
{
  "confidence": 0.0-1.0,
  "issues_found": ["list of specific issues"],
  "issue_category": "factual_error|weak_evidence|translation_issue|incomplete_info|formatting|no_issue",
  "suggestion": "English suggestion for correction",
  "suggestion_ar": "Arabic suggestion for correction",
  "evidence_assessment": "Assessment of evidence quality in English",
  "evidence_assessment_ar": "Assessment of evidence quality in Arabic",
  "recommended_action": "approve|revise|reject|escalate",
  "analysis_details": {"additional": "structured data"}
}"""

    # Prompt template for content analysis
    ANALYSIS_PROMPT = """Analyze the following flagged content for verification:

**Entity Type:** {entity_type}
**Entity ID:** {entity_id}
**Flag Type:** {flag_type}
**Flag Reason:** {flag_reason}

**Content to Verify:**
```json
{content}
```

**Evidence/Context (if available):**
{evidence}

Please analyze this content and provide your assessment in the specified JSON format.
Focus particularly on the flagged issue ({flag_type}) while also noting any other concerns."""

    def __init__(self, llm: BaseLLM = None):
        """Initialize with optional LLM instance."""
        self.llm = llm

    def _get_llm(self) -> BaseLLM:
        """Get or create LLM instance."""
        if self.llm is None:
            self.llm = get_llm()
        return self.llm

    async def analyze_content(
        self,
        entity_type: str,
        entity_id: str,
        flag_type: str,
        flag_reason: str,
        content: Dict[str, Any],
        evidence: str = None,
    ) -> AIAnalysisResult:
        """
        Analyze flagged content using AI.

        Args:
            entity_type: Type of entity (concept, story, etc.)
            entity_id: ID of the entity
            flag_type: Type of flag raised
            flag_reason: Reason for flagging
            content: Content snapshot to analyze
            evidence: Additional evidence/context

        Returns:
            AIAnalysisResult with analysis and recommendations
        """
        if not settings.feature_ai_verification:
            logger.info("AI verification disabled, returning default result")
            return AIAnalysisResult(
                confidence=0.0,
                suggestion="AI verification is disabled",
                suggestion_ar="التحقق بالذكاء الاصطناعي معطل",
                recommended_action="escalate",
            )

        llm = self._get_llm()

        # Format the analysis prompt
        user_message = self.ANALYSIS_PROMPT.format(
            entity_type=entity_type,
            entity_id=entity_id,
            flag_type=flag_type,
            flag_reason=flag_reason or "No specific reason provided",
            content=json.dumps(content, ensure_ascii=False, indent=2),
            evidence=evidence or "No additional evidence provided",
        )

        try:
            response = await llm.generate(
                system_prompt=self.SYSTEM_PROMPT,
                user_message=user_message,
                max_tokens=1500,
                temperature=0.2,  # Lower temperature for consistent analysis
            )

            # Parse the JSON response
            result = self._parse_response(response)
            result.latency_ms = response.latency_ms
            result.raw_response = response.content

            logger.info(
                f"AI analysis complete for {entity_type}:{entity_id} - "
                f"confidence: {result.confidence:.2f}, action: {result.recommended_action}"
            )

            return result

        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return AIAnalysisResult(
                confidence=0.0,
                issues_found=[f"Analysis error: {str(e)}"],
                issue_category=IssueCategory.NO_ISSUE,
                suggestion="Unable to analyze - manual review required",
                suggestion_ar="تعذر التحليل - مطلوب مراجعة يدوية",
                recommended_action="escalate",
            )

    def _parse_response(self, response: LLMResponse) -> AIAnalysisResult:
        """Parse LLM response into structured result."""
        try:
            # Extract JSON from response
            content = response.content.strip()

            # Handle markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            data = json.loads(content)

            # Map issue category
            issue_cat_str = data.get("issue_category", "no_issue")
            try:
                issue_category = IssueCategory(issue_cat_str)
            except ValueError:
                issue_category = IssueCategory.NO_ISSUE

            return AIAnalysisResult(
                confidence=float(data.get("confidence", 0.5)),
                issues_found=data.get("issues_found", []),
                issue_category=issue_category,
                suggestion=data.get("suggestion", ""),
                suggestion_ar=data.get("suggestion_ar", ""),
                evidence_assessment=data.get("evidence_assessment", ""),
                evidence_assessment_ar=data.get("evidence_assessment_ar", ""),
                recommended_action=data.get("recommended_action", "escalate"),
                analysis_details=data.get("analysis_details", {}),
            )

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse AI response as JSON: {e}")
            # Return a default result with the raw response
            return AIAnalysisResult(
                confidence=0.3,
                issues_found=["Unable to parse AI response"],
                suggestion=response.content[:500],
                recommended_action="escalate",
            )

    async def suggest_correction(
        self,
        entity_type: str,
        content: Dict[str, Any],
        issue_description: str,
    ) -> Dict[str, Any]:
        """
        Generate a suggested correction for flagged content.

        Args:
            entity_type: Type of entity
            content: Current content
            issue_description: Description of the issue

        Returns:
            Dict with suggested corrections
        """
        if not settings.feature_ai_verification:
            return {"error": "AI verification disabled"}

        llm = self._get_llm()

        prompt = f"""Given the following {entity_type} content and the identified issue,
suggest a specific correction:

**Current Content:**
```json
{json.dumps(content, ensure_ascii=False, indent=2)}
```

**Issue:**
{issue_description}

Provide your correction as a JSON object with the same structure as the input,
but with corrected values. Include only the fields that need to be changed.
Also provide:
- "explanation": why this correction is needed
- "explanation_ar": Arabic explanation
- "confidence": how confident you are in this correction (0.0-1.0)"""

        try:
            response = await llm.generate(
                system_prompt=self.SYSTEM_PROMPT,
                user_message=prompt,
                max_tokens=1000,
                temperature=0.2,
            )

            # Parse JSON from response
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            return json.loads(content)

        except Exception as e:
            logger.error(f"Failed to generate correction: {e}")
            return {
                "error": str(e),
                "suggestion": "Manual correction required",
            }

    async def verify_evidence(
        self,
        claim: str,
        evidence_refs: List[str],
        evidence_text: str = None,
    ) -> Dict[str, Any]:
        """
        Verify if evidence supports a claim.

        Args:
            claim: The claim to verify
            evidence_refs: List of evidence references (ayah, hadith, etc.)
            evidence_text: Optional full text of evidence

        Returns:
            Dict with verification result
        """
        if not settings.feature_ai_verification:
            return {
                "verified": False,
                "reason": "AI verification disabled",
            }

        llm = self._get_llm()

        prompt = f"""Evaluate whether the following evidence supports the claim:

**Claim:**
{claim}

**Evidence References:**
{', '.join(evidence_refs)}

**Evidence Text (if available):**
{evidence_text or 'Not provided'}

Respond in JSON format:
{{
  "verified": true/false,
  "confidence": 0.0-1.0,
  "support_level": "strong|moderate|weak|none",
  "reasoning": "Explanation in English",
  "reasoning_ar": "Explanation in Arabic",
  "missing_evidence": ["list of additional evidence needed, if any"]
}}"""

        try:
            response = await llm.generate(
                system_prompt=self.SYSTEM_PROMPT,
                user_message=prompt,
                max_tokens=800,
                temperature=0.2,
            )

            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            return json.loads(content)

        except Exception as e:
            logger.error(f"Evidence verification failed: {e}")
            return {
                "verified": False,
                "confidence": 0.0,
                "reason": f"Verification error: {str(e)}",
            }

    async def health_check(self) -> Dict[str, Any]:
        """Check if AI verification is available."""
        if not settings.feature_ai_verification:
            return {
                "available": False,
                "reason": "AI verification disabled in settings",
            }

        try:
            llm = self._get_llm()
            is_healthy = await llm.health_check()
            return {
                "available": is_healthy,
                "provider": type(llm).__name__,
            }
        except Exception as e:
            return {
                "available": False,
                "reason": str(e),
            }


# Singleton instance
_ai_assistant: Optional[AIVerificationAssistant] = None


def get_ai_assistant() -> AIVerificationAssistant:
    """Get the AI verification assistant singleton."""
    global _ai_assistant
    if _ai_assistant is None:
        _ai_assistant = AIVerificationAssistant()
    return _ai_assistant
