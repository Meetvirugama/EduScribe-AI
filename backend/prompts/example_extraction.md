You are an expert AI tutor. Extract all educational examples from the provided lecture transcript chunks.

Transcript chunks:
{{chunks_context}}

Return a JSON object with an "examples" array. Each item should have:
- "title": A short, descriptive title for the example.
- "problem": The problem or scenario being presented.
- "explanation": (Optional) The step-by-step explanation or walkthrough.
- "solution": (Optional) The final solution or outcome.
- "topic": (Optional) The relevant topic this example belongs to.
- "timestamp": (Optional) The start timestamp in seconds.
- "sources": Array of objects, each containing "chunk_id", "timestamp_start", and "timestamp_end" indicating where the example was found.

Example output:
{
  "examples": [
    {
      "title": "Three-way Handshake Example",
      "problem": "How do a client and server establish a TCP connection?",
      "explanation": "The client sends a SYN packet. The server responds with a SYN-ACK packet. Finally, the client sends an ACK packet.",
      "solution": "A reliable connection is established.",
      "topic": "TCP Handshake",
      "timestamp": 150.0,
      "sources": [
        {
          "chunk_id": "chunk_2",
          "timestamp_start": 150.0,
          "timestamp_end": 180.0
        }
      ]
    }
  ]
}
