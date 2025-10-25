"""
Shared utility functions
"""

from datetime import datetime, date
from typing import Any, Optional
import json


def parse_fhir_date(date_str: Optional[str]) -> Optional[date]:
    """Parse FHIR date string to Python date"""
    if not date_str:
        return None
    
    try:
        # FHIR date format: YYYY-MM-DD
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_fhir_datetime(datetime_str: Optional[str]) -> Optional[datetime]:
    """Parse FHIR datetime string to Python datetime"""
    if not datetime_str:
        return None
    
    try:
        # Remove 'Z' and parse
        clean_str = datetime_str.replace('Z', '+00:00')
        return datetime.fromisoformat(clean_str)
    except (ValueError, AttributeError):
        return None


def extract_reference_id(reference: Optional[dict]) -> Optional[str]:
    """Extract ID from FHIR reference"""
    if not reference or not isinstance(reference, dict):
        return None
    
    ref = reference.get("reference", "")
    if "/" in ref:
        return ref.split("/")[-1]
    return ref


def get_coding_display(codeable_concept: Optional[dict]) -> Optional[str]:
    """Get display text from CodeableConcept"""
    if not codeable_concept or not isinstance(codeable_concept, dict):
        return None
    
    # Try text field first
    if "text" in codeable_concept:
        return codeable_concept["text"]
    
    # Try first coding display
    codings = codeable_concept.get("coding", [])
    if codings and len(codings) > 0:
        return codings[0].get("display")
    
    return None


def calculate_age(birth_date: date) -> int:
    """Calculate age from birth date"""
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))


def get_age_group(age: int) -> str:
    """Get age group from age"""
    if age < 18:
        return "0-18"
    elif age < 36:
        return "19-35"
    elif age < 51:
        return "36-50"
    elif age < 66:
        return "51-65"
    else:
        return "65+"


def safe_json_dumps(obj: Any, default: Any = str) -> str:
    """Safely dump object to JSON string"""
    try:
        return json.dumps(obj, default=default)
    except (TypeError, ValueError):
        return "{}"


def safe_json_loads(json_str: Optional[str]) -> Any:
    """Safely load JSON string to object"""
    if not json_str:
        return None
    
    try:
        return json.loads(json_str)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None


def format_count(count: int) -> str:
    """Format large numbers with K, M, B suffixes"""
    if count >= 1_000_000_000:
        return f"{count / 1_000_000_000:.1f}B"
    elif count >= 1_000_000:
        return f"{count / 1_000_000:.1f}M"
    elif count >= 1_000:
        return f"{count / 1_000:.1f}K"
    else:
        return str(count)


def validate_fhir_id(fhir_id: str) -> bool:
    """Validate FHIR ID format"""
    if not fhir_id or not isinstance(fhir_id, str):
        return False
    
    # FHIR IDs should be 1-64 characters, [A-Za-z0-9\-\.]{1,64}
    import re
    pattern = r'^[A-Za-z0-9\-\.]{1,64}$'
    return bool(re.match(pattern, fhir_id))

