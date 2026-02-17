import re

import structlog

logger = structlog.get_logger()


class EntityExtractor:
    """
    Extracts entities from user messages related to Mexican medicinal plants.

    Identifies plant names, symptoms, compounds, body parts, and preparation types.
    In production, this can be enhanced with a NER model or LLM-based extraction.
    """

    PLANT_NAMES = {
        "es": [
            "arnica", "manzanilla", "chamomila", "epazote", "damiana",
            "valeriana", "cuachalalate", "muicle", "tila", "toronjil",
            "hierba del cancer", "gordolobo", "estafiate", "ruda",
            "sabila", "aloe vera", "nopal", "calendula", "romero",
            "albahaca", "hierbabuena", "menta", "oregano", "tomillo",
            "lavanda", "pasiflora", "flor de manita", "zapote blanco",
            "guayaba", "bugambilia", "cola de caballo", "diente de leon",
            "uña de gato", "sangre de drago", "gobernadora",
            "yerba santa", "pirul", "ajenjo", "boldo", "cempasuchil",
            "chaya", "moringa", "neem", "stevia", "te de limon",
        ],
        "en": [
            "arnica", "chamomile", "epazote", "damiana", "valerian",
            "cuachalalate", "muicle", "linden", "aloe vera", "nopal",
            "calendula", "rosemary", "basil", "spearmint", "mint",
            "oregano", "thyme", "lavender", "passionflower",
            "guava", "bougainvillea", "horsetail", "dandelion",
            "cat's claw", "dragon's blood", "creosote bush",
            "yerba santa", "wormwood", "boldo", "marigold",
            "moringa", "neem", "stevia", "lemongrass",
        ],
    }

    SYMPTOM_TERMS = {
        "es": [
            "dolor de cabeza", "dolor de estomago", "dolor muscular",
            "fiebre", "tos", "gripe", "resfriado", "nausea", "vomito",
            "diarrea", "estreñimiento", "insomnio", "ansiedad", "estres",
            "inflamacion", "infeccion", "alergia", "colicos", "gastritis",
            "diabetes", "hipertension", "presion alta", "colesterol",
            "artritis", "reumatismo", "herida", "quemadura", "irritacion",
            "dermatitis", "hongos", "acne",
        ],
        "en": [
            "headache", "stomachache", "muscle pain", "fever", "cough",
            "flu", "cold", "nausea", "vomiting", "diarrhea", "constipation",
            "insomnia", "anxiety", "stress", "inflammation", "infection",
            "allergy", "cramps", "gastritis", "diabetes", "hypertension",
            "high blood pressure", "cholesterol", "arthritis", "rheumatism",
            "wound", "burn", "irritation", "dermatitis", "fungus", "acne",
        ],
    }

    COMPOUND_TERMS = {
        "es": [
            "alcaloide", "flavonoide", "terpeno", "tanino", "saponina",
            "aceite esencial", "curcumina", "quercetina", "kaempferol",
            "acido rosmarinico", "timol", "carvacrol", "mentol",
            "eucaliptol", "limoneno", "linalool", "beta-caroteno",
        ],
        "en": [
            "alkaloid", "flavonoid", "terpene", "tannin", "saponin",
            "essential oil", "curcumin", "quercetin", "kaempferol",
            "rosmarinic acid", "thymol", "carvacrol", "menthol",
            "eucalyptol", "limonene", "linalool", "beta-carotene",
        ],
    }

    PREPARATION_TYPES = {
        "es": [
            "te", "infusion", "decoccion", "tintura", "extracto",
            "pomada", "cataplasma", "aceite", "jarabe", "capsula",
            "polvo", "compresa", "baño", "vapor", "inhalacion",
        ],
        "en": [
            "tea", "infusion", "decoction", "tincture", "extract",
            "ointment", "poultice", "oil", "syrup", "capsule",
            "powder", "compress", "bath", "steam", "inhalation",
        ],
    }

    async def extract(self, message: str, language: str = "es") -> list[dict]:
        """
        Extract entities from a user message.

        Args:
            message: The user's message text.
            language: Language code ('es' or 'en').

        Returns:
            List of entity dicts with 'type', 'value', and 'start'/'end' positions.
        """
        message_lower = message.lower()
        entities = []

        # Extract plant names
        plant_names = self.PLANT_NAMES.get(language, self.PLANT_NAMES["es"])
        for plant in plant_names:
            pattern = rf"\b{re.escape(plant)}\b"
            for match in re.finditer(pattern, message_lower):
                entities.append(
                    {
                        "type": "plant",
                        "value": plant,
                        "start": match.start(),
                        "end": match.end(),
                    }
                )

        # Extract symptoms
        symptoms = self.SYMPTOM_TERMS.get(language, self.SYMPTOM_TERMS["es"])
        for symptom in symptoms:
            pattern = rf"\b{re.escape(symptom)}\b"
            for match in re.finditer(pattern, message_lower):
                entities.append(
                    {
                        "type": "symptom",
                        "value": symptom,
                        "start": match.start(),
                        "end": match.end(),
                    }
                )

        # Extract compounds
        compounds = self.COMPOUND_TERMS.get(language, self.COMPOUND_TERMS["es"])
        for compound in compounds:
            pattern = rf"\b{re.escape(compound)}\b"
            for match in re.finditer(pattern, message_lower):
                entities.append(
                    {
                        "type": "compound",
                        "value": compound,
                        "start": match.start(),
                        "end": match.end(),
                    }
                )

        # Extract preparation types
        preparations = self.PREPARATION_TYPES.get(language, self.PREPARATION_TYPES["es"])
        for prep in preparations:
            pattern = rf"\b{re.escape(prep)}\b"
            for match in re.finditer(pattern, message_lower):
                entities.append(
                    {
                        "type": "preparation",
                        "value": prep,
                        "start": match.start(),
                        "end": match.end(),
                    }
                )

        # Sort by position in text
        entities.sort(key=lambda e: e["start"])

        logger.info(
            "Entities extracted",
            count=len(entities),
            types=[e["type"] for e in entities],
        )
        return entities
