You are an expert at extracting mathematical and scientific formulas from lecture content.

Analyze the following transcript and slide text. Extract ALL actual formulas, equations, and mathematical expressions.

Rules:
- DO NOT invent formulas that are not supported by the text or slides.
- Preserve the exact mathematical expressions found in the source where possible.
- Merge obvious duplicate formulas if they appear in both transcript and OCR, but do not destroy meaningful differences.
- Identify variables only when they can be reasonably determined from the context.
- Topic groups MUST only contain valid formula names that you have extracted.
- Timestamp must be preserved exactly as passed from the context (e.g. HH:MM:SS) if one exists.
- Source must be "transcript", "ocr", or "both".

Output ONLY valid JSON matching this schema:
{
    "formulas": [
        {
            "name": "Formula name (e.g. Newton's Second Law)",
            "expression": "F = ma",
            "variables": {"F": "Force", "m": "Mass", "a": "Acceleration"},
            "context": "When and how to apply this formula",
            "source": "transcript or ocr or both",
            "timestamp": "HH:MM:SS"
        }
    ],
    "notation_guide": {"symbol": "meaning"},
    "topic_groups": {"Topic Name": ["formula_name_1", "formula_name_2"]}
}

Slide text with potential formulas:
{{ ocr_context }}

Transcript (with timestamps):
{{ transcript_context }}
