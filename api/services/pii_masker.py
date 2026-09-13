from collections import defaultdict
from functools import lru_cache

import spacy
from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_analyzer.predefined_recognizers import (
    InAadhaarRecognizer,
    InPanRecognizer,
    InPassportRecognizer,
    InVoterRecognizer,
    PhoneRecognizer,
)

# Keep transaction facts such as currency, amounts, and rates. 
PII_ENTITIES = [
    "PERSON",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "CREDIT_CARD",
    "IN_AADHAAR",
    "IN_PAN",
    "IN_PASSPORT",
    "IN_VOTER",
    "IN_BANK_ACCOUNT",
    "IN_UPI",
]


@lru_cache(maxsize=1)
def get_analyzer() -> AnalyzerEngine:
    if not spacy.util.is_package("en_core_web_sm"):
        raise RuntimeError("Install the en_core_web_sm spaCy model")

    provider = NlpEngineProvider(
        nlp_configuration={
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
        }
    )
    analyzer = AnalyzerEngine(
        nlp_engine=provider.create_engine(), supported_languages=["en"]
    )

    for recognizer in (
        InAadhaarRecognizer(),
        InPanRecognizer(),
        InPassportRecognizer(),
        InVoterRecognizer(),
    ):
        analyzer.registry.add_recognizer(recognizer)

    # PhoneRecognizer defaults to several countries; adding India specific recognizer
    analyzer.registry.remove_recognizer("PhoneRecognizer")
    analyzer.registry.add_recognizer(PhoneRecognizer(supported_regions=["IN"]))

    analyzer.registry.add_recognizer(
        PatternRecognizer(
            supported_entity="IN_UPI",
            name="IndianUpiRecognizer",
            patterns=[Pattern("upi_like_address", r"(?<![\w.+-])[a-zA-Z0-9._-]{2,256}@[a-zA-Z][a-zA-Z0-9.-]{1,63}\b", 0.6)],
        )
    )
    analyzer.registry.add_recognizer(
        PatternRecognizer(
            supported_entity="IN_BANK_ACCOUNT",
            name="IndianBankAccountRecognizer",
            patterns=[Pattern("labelled_bank_account", r"(?i)\b(?:bank\s+account|account\s+(?:number|no\.?)|a/c)\s*(?:is\s*)?[:#-]?\s*\d(?:[ -]?\d){7,17}\b", 0.85)],
        )
    )
    # Whisper may produce a checksum-invalid Aadhaar; a labelled candidate should
    # still be masked rather than leaked.
    analyzer.registry.add_recognizer(
        PatternRecognizer(
            supported_entity="IN_AADHAAR",
            name="LabelledAadhaarFallbackRecognizer",
            patterns=[Pattern("labelled_aadhaar_candidate", r"(?i)\b(?:aadhaar|aadhar|adhar|uidai)\s*(?:card\s*)?(?:number|no\.?)?\s*(?:is\s*)?[:#-]?\s*\d(?:[ -]?\d){11}\b", 0.85)],
        )
    )
    return analyzer


def mask_pii(text: str) -> str:
    results = get_analyzer().analyze(
        text=text, language="en", entities=PII_ENTITIES, score_threshold=0.4
    )
    spans = []
    for result in sorted(results, key=lambda item: (item.start, -item.end)):
        if spans and result.start < spans[-1][1]:
            spans[-1] = (spans[-1][0], max(spans[-1][1], result.end), spans[-1][2])
        else:
            spans.append((result.start, result.end, result.entity_type))

    counters = defaultdict(int)
    placeholders = {}
    output, cursor = [], 0
    for start, end, entity in spans:
        original = text[start:end]
        key = (entity, original.casefold())
        if key not in placeholders:
            counters[entity] += 1
            placeholders[key] = f"[{entity}_{counters[entity]}]"
        output.extend((text[cursor:start], placeholders[key]))
        cursor = end
    output.append(text[cursor:])
    return "".join(output)
