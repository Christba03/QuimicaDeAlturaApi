import re

import structlog

logger = structlog.get_logger()


class IntentClassifier:
    """
    Rule-based intent classifier for user messages about medicinal plants.

    Classifies messages into intents such as plant_query, symptom_query,
    compound_query, preparation_query, safety_query, and general_info.

    In production, this can be enhanced with a fine-tuned ML classifier
    or delegated to the LLM for zero-shot classification.
    """

    INTENT_PATTERNS = {
        "plant_query": {
            "es": [
                r"\bplanta\b", r"\bhierba\b", r"\byerba\b", r"\bflor\b",
                r"\braiz\b", r"\bhoja\b", r"\bcorteza\b", r"\bfruto\b",
                r"\barbol\b", r"\barnica\b", r"\bchamomila\b", r"\bmanzanilla\b",
                r"\bepazote\b", r"\bdamiana\b", r"\bvaleriana\b",
                r"\bcuachalalate\b", r"\bmuicle\b", r"\btila\b",
                r"\bque es\b.*\bplanta\b", r"\bconoces\b.*\bplanta\b",
            ],
            "en": [
                r"\bplant\b", r"\bherb\b", r"\bflower\b", r"\broot\b",
                r"\bleaf\b", r"\bbark\b", r"\bfruit\b", r"\btree\b",
                r"\bwhat is\b.*\bplant\b", r"\btell me about\b.*\bplant\b",
            ],
        },
        "symptom_query": {
            "es": [
                r"\bdolor\b", r"\bfiebre\b", r"\btos\b", r"\bgripe\b",
                r"\bestomago\b", r"\bcabeza\b", r"\binflamacion\b",
                r"\binfeccion\b", r"\binsomnio\b", r"\bansiedad\b",
                r"\bestres\b", r"\bdigestion\b", r"\bnausea\b",
                r"\bsintoma\b", r"\bpadecimiento\b", r"\benfermedad\b",
                r"\bme duele\b", r"\btengo\b.*\bdolor\b",
                r"\bque tomo para\b", r"\bque me recomiendas para\b",
            ],
            "en": [
                r"\bpain\b", r"\bfever\b", r"\bcough\b", r"\bcold\b",
                r"\bstomach\b", r"\bheadache\b", r"\binflammation\b",
                r"\binfection\b", r"\binsomnia\b", r"\banxiety\b",
                r"\bstress\b", r"\bdigestion\b", r"\bnausea\b",
                r"\bsymptom\b", r"\bailment\b", r"\bdisease\b",
                r"\bi have\b.*\bpain\b", r"\bwhat should i take\b",
            ],
        },
        "compound_query": {
            "es": [
                r"\bcompuesto\b", r"\bquimico\b", r"\bmolecula\b",
                r"\balcaloide\b", r"\bflavonoide\b", r"\bterpeno\b",
                r"\baceite esencial\b", r"\bprincipio activo\b",
                r"\bfitoquimico\b", r"\bextracto\b",
            ],
            "en": [
                r"\bcompound\b", r"\bchemical\b", r"\bmolecule\b",
                r"\balkaloid\b", r"\bflavonoid\b", r"\bterpene\b",
                r"\bessential oil\b", r"\bactive ingredient\b",
                r"\bphytochemical\b", r"\bextract\b",
            ],
        },
        "preparation_query": {
            "es": [
                r"\bpreparar\b", r"\bpreparacion\b", r"\bte\b",
                r"\binfusion\b", r"\btintura\b", r"\bcocimiento\b",
                r"\bdecoccion\b", r"\bpomada\b", r"\bcataplasma\b",
                r"\bcomo se usa\b", r"\bcomo se toma\b",
                r"\bdosis\b", r"\bcantidad\b", r"\breceta\b",
            ],
            "en": [
                r"\bprepare\b", r"\bpreparation\b", r"\btea\b",
                r"\binfusion\b", r"\btincture\b", r"\bdecoction\b",
                r"\bpoultice\b", r"\bointment\b",
                r"\bhow to use\b", r"\bhow to take\b",
                r"\bdosage\b", r"\brecipe\b",
            ],
        },
        "safety_query": {
            "es": [
                r"\bseguridad\b", r"\bcontraindicacion\b", r"\bpeligro\b",
                r"\btoxico\b", r"\bveneno\b", r"\befecto secundario\b",
                r"\balergia\b", r"\bembarazo\b", r"\blactancia\b",
                r"\binteraccion\b", r"\bes seguro\b", r"\bpuedo tomar\b",
                r"\briesgo\b",
            ],
            "en": [
                r"\bsafety\b", r"\bcontraindication\b", r"\bdanger\b",
                r"\btoxic\b", r"\bpoison\b", r"\bside effect\b",
                r"\ballergy\b", r"\bpregnancy\b", r"\bbreastfeeding\b",
                r"\binteraction\b", r"\bis it safe\b", r"\bcan i take\b",
                r"\brisk\b",
            ],
        },
    }

    async def classify(self, message: str, language: str = "es") -> str:
        """
        Classify the intent of a user message.

        Args:
            message: The user message text.
            language: Language code ('es' or 'en').

        Returns:
            Intent string (e.g., 'plant_query', 'symptom_query', 'general_info').
        """
        message_lower = message.lower().strip()
        scores: dict[str, int] = {}

        for intent, lang_patterns in self.INTENT_PATTERNS.items():
            patterns = lang_patterns.get(language, lang_patterns.get("es", []))
            match_count = 0
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    match_count += 1
            if match_count > 0:
                scores[intent] = match_count

        if not scores:
            logger.info("No intent matched, defaulting to general_info", message=message[:100])
            return "general_info"

        best_intent = max(scores, key=scores.get)
        logger.info(
            "Intent classified",
            intent=best_intent,
            score=scores[best_intent],
            all_scores=scores,
        )
        return best_intent
