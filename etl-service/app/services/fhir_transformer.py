import json
import logging
import os
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class FHIRTransformer:
    """Transform FHIR resources from NDJSON to structured format"""
    
    def __init__(self):
        self.transformers = {
            "Patient": self.transform_patient,
            "Condition": self.transform_condition,
            "Encounter": self.transform_encounter,
            "Observation": self.transform_observation
        }
    
    async def transform_file(self, ndjson_file: str, resource_type: str) -> Dict[str, Any]:
        """Transform an NDJSON file"""
        
        if resource_type not in self.transformers:
            raise ValueError(f"Unsupported resource type: {resource_type}")
        
        transformer = self.transformers[resource_type]
        transformed_records = []
        processed = 0
        failed = 0
        
        # Read NDJSON file line by line
        with open(ndjson_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    resource = json.loads(line.strip())
                    transformed = transformer(resource)
                    if transformed:
                        transformed_records.append(transformed)
                        processed += 1
                except Exception as e:
                    logger.error(f"Error transforming record: {e}")
                    failed += 1
        
        # Save transformed data
        output_dir = os.path.join(os.path.dirname(ndjson_file), "transformed")
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"{resource_type}.json")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(transformed_records, f, indent=2, default=str)
        
        return {
            "processed": processed,
            "failed": failed,
            "output_file": output_file
        }
    
    def transform_patient(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Patient resource"""
        
        return {
            "fhir_id": resource.get("id"),
            "identifier": resource.get("identifier"),
            "name": resource.get("name"),
            "gender": resource.get("gender"),
            "birth_date": resource.get("birthDate"),
            "address": resource.get("address"),
            "telecom": resource.get("telecom"),
            "marital_status": resource.get("maritalStatus", {}).get("text"),
            "raw_data": resource
        }
    
    def transform_condition(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Condition resource"""
        
        code = resource.get("code", {})
        code_text = code.get("text") or self._get_first_coding_display(code)
        
        return {
            "fhir_id": resource.get("id"),
            "patient_id": self._extract_reference_id(resource.get("subject")),
            "code": code,
            "code_text": code_text,
            "category": resource.get("category"),
            "clinical_status": resource.get("clinicalStatus", {}).get("text"),
            "verification_status": resource.get("verificationStatus", {}).get("text"),
            "severity": resource.get("severity", {}).get("text"),
            "onset_datetime": resource.get("onsetDateTime"),
            "recorded_date": resource.get("recordedDate"),
            "encounter_id": self._extract_reference_id(resource.get("encounter")),
            "raw_data": resource
        }
    
    def transform_encounter(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Encounter resource"""
        
        period = resource.get("period", {})
        
        return {
            "fhir_id": resource.get("id"),
            "patient_id": self._extract_reference_id(resource.get("subject")),
            "status": resource.get("status"),
            "encounter_class": resource.get("class", {}).get("code"),
            "type": resource.get("type"),
            "service_type": resource.get("serviceType", {}).get("text"),
            "priority": resource.get("priority", {}).get("text"),
            "period_start": period.get("start"),
            "period_end": period.get("end"),
            "reason_code": resource.get("reasonCode"),
            "diagnosis": resource.get("diagnosis"),
            "location": resource.get("location"),
            "raw_data": resource
        }
    
    def transform_observation(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Observation resource"""
        
        code = resource.get("code", {})
        code_text = code.get("text") or self._get_first_coding_display(code)
        
        return {
            "fhir_id": resource.get("id"),
            "patient_id": self._extract_reference_id(resource.get("subject")),
            "encounter_id": self._extract_reference_id(resource.get("encounter")),
            "status": resource.get("status"),
            "category": resource.get("category"),
            "code": code,
            "code_text": code_text,
            "value": resource.get("value"),
            "value_quantity": resource.get("valueQuantity"),
            "effective_datetime": resource.get("effectiveDateTime"),
            "issued": resource.get("issued"),
            "interpretation": resource.get("interpretation"),
            "raw_data": resource
        }
    
    def _extract_reference_id(self, reference: Dict[str, Any]) -> str:
        """Extract ID from a FHIR reference"""
        if not reference:
            return None
        
        ref = reference.get("reference", "")
        if "/" in ref:
            return ref.split("/")[-1]
        return ref
    
    def _get_first_coding_display(self, code: Dict[str, Any]) -> str:
        """Get display text from first coding in a CodeableConcept"""
        codings = code.get("coding", [])
        if codings and len(codings) > 0:
            return codings[0].get("display")
        return None

