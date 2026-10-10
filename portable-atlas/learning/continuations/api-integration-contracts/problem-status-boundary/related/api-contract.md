{
  "id": "synthetic-item-v1",
  "success_status": 200,
  "error_status": 422,
  "media_type": "application/json",
  "success_schema": {
    "type": "object", "required": ["id", "name"],
    "properties": {"id": {"type": "integer", "minimum": 1}, "name": {"type": "string", "minLength": 1}, "note": {"type": "string"}},
    "additionalProperties": true
  },
  "error_schema": {"type": "object", "required": ["error"], "properties": {"error": {"type": "object", "required": ["code", "message"], "properties": {"code": {"type": "string", "minLength": 1}, "message": {"type": "string", "minLength": 1}}}}},
  "implementation_boundary": "Handwritten checks implement only these fixed rules, not a general JSON Schema evaluator. 200/422, optional note and extra field tolerance are this API contract, not universal HTTP rules."
}
