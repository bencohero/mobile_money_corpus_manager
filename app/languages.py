"""Central language catalog used by workshop and participant workflows."""

from dataclasses import dataclass


@dataclass(frozen=True)
class LanguageDefinition:
    code: str
    name: str


LANGUAGES = (
    LanguageDefinition("FR", "Français"),
    LanguageDefinition("MOS", "Mooré"),
    LanguageDefinition("DYU", "Dioula"),
    LanguageDefinition("FUL", "Fulfuldé"),
)
LANGUAGE_BY_CODE = {item.code: item for item in LANGUAGES}


def language_name(code: str | None) -> str:
    if not code:
        return "Langue à attribuer"
    return LANGUAGE_BY_CODE.get(code.upper(), LanguageDefinition(code, code)).name
