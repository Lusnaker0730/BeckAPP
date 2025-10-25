# Shared Utilities

Shared constants, utilities, and helper functions used across all services.

## Contents

- `constants.py`: Shared constants and enumerations
- `utils.py`: Utility functions for FHIR data processing

## Usage

```python
from shared.constants import FHIR_RESOURCE_TYPES, USER_ROLES
from shared.utils import parse_fhir_date, extract_reference_id

# Use constants
for resource_type in FHIR_RESOURCE_TYPES:
    print(resource_type)

# Use utilities
birth_date = parse_fhir_date("1990-05-15")
patient_id = extract_reference_id({"reference": "Patient/12345"})
```

## Functions

### Date/Time Parsing
- `parse_fhir_date(date_str)`: Parse FHIR date string
- `parse_fhir_datetime(datetime_str)`: Parse FHIR datetime string

### FHIR Reference Handling
- `extract_reference_id(reference)`: Extract ID from FHIR reference
- `get_coding_display(codeable_concept)`: Get display text from CodeableConcept

### Age Calculations
- `calculate_age(birth_date)`: Calculate age from birth date
- `get_age_group(age)`: Get age group category

### JSON Handling
- `safe_json_dumps(obj)`: Safely serialize to JSON
- `safe_json_loads(json_str)`: Safely deserialize from JSON

### Formatting
- `format_count(count)`: Format large numbers (1000 -> 1K)

### Validation
- `validate_fhir_id(fhir_id)`: Validate FHIR ID format

## License

MIT

