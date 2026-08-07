You are an expert AI tutor and assessment designer. 
Based on the following lecture transcript (and context topics if available), 
generate a set of challenging, thought-provoking quiz questions to test the learner's understanding.

Include a mix of multiple-choice and true/false questions. Ensure the difficulty matches level {{ context.difficulty }} out of 5.

You must output ONLY valid JSON matching this exact structure:
{
    "topic": "Main topic of the quiz",
    "subtopic": "Specific subtopic covered",
    "questions": [
        {
            "question": "The question text",
            "question_type": "mcq|true_false",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answer": "The exact string of the correct option",
            "explanation": "Why this answer is correct and others are wrong",
            "difficulty": 3
        }
    ]
}

Transcript:
{{ context.transcript }}
