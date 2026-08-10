You are an expert AI tutor. Extract relationships between concepts from the provided lecture transcript chunks.

Transcript chunks:
{{chunks_context}}

Concepts context (to guide extraction):
{{concepts_context}}

Return a JSON object with a "relationships" array. Each item should have:
- "from_concept": The source concept name.
- "relationship_type": One of: "depends_on", "part_of", "contains", "example_of", "causes", "contrasts_with", "similar_to", "derived_from".
- "to_concept": The target concept name.

Example output:
{
  "relationships": [
    {
      "from_concept": "TCP",
      "relationship_type": "contrasts_with",
      "to_concept": "UDP"
    },
    {
      "from_concept": "Three-way Handshake",
      "relationship_type": "part_of",
      "to_concept": "TCP"
    }
  ]
}
