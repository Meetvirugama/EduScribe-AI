import time
import logging
from typing import Any, Dict
from .base import BaseContentService
from .context import LectureContext
from ..llm.model_selector import TaskType
from ..llm.validation.schemas.notes import TopicsAndNotesOutput

logger = logging.getLogger(__name__)


class TopicService(BaseContentService):
    async def extract_topics(self, context: LectureContext) -> Dict[str, Any]:
        """Extracts detailed notes and topics from the transcript using chunks."""
        logger.info("Extracting topics...")
        start_time = time.time()

        empty_result = {"summary": "Failed to extract topics.", "topics": []}

        if not self.llm_manager:
            return empty_result

        video_id = context.metadata.get("video_id", "default_video")

        if not context.segments:
            chunks = [] # If no segments, chunking returns [] anyway
        else:
            chunks = self._chunk_segments_with_ocr(context, video_id, use_semantic_chunking=True)

        try:
            all_topics = []
            summaries = []

            final_provider = "unknown"
            final_model = "unknown"
            total_latency = 0.0
            total_tokens = 0

            for c in chunks:
                chunk_id = c["chunk_id"]
                transcript_text = f'[{chunk_id} | {c["start_time"]} - {c["end_time"]}]\n{c["text"]}'

                # --- STEP 2: Relevance Classification Pass ---
                import json
                from schemas.content import ChunkClassification
                
                classify_sys = (
                    "You are a content classifier. You classify video transcript chunks into one of these categories:\n"
                    "- 'technical': Genuine academic/technical content worth studying.\n"
                    "- 'administrative': Course logistics, scheduling, 'can you hear me'.\n"
                    "- 'promotional': Discounts, pricing, subscribe calls.\n"
                    "- 'filler': Jokes, tangential stories, silence.\n"
                    "Return ONLY valid JSON matching this schema: {\"classification\": \"...\", \"reasoning\": \"...\"}"
                )
                classify_user = f"Classify this transcript chunk:\n\n{c['text']}"
                
                try:
                    import asyncio
                    await asyncio.sleep(0.5)
                    
                    cls_resp = await self.llm_manager.generate(
                        task=TaskType.ROUTING,
                        messages=[
                            {"role": "system", "content": classify_sys},
                            {"role": "user", "content": classify_user}
                        ],
                        response_format={"type": "json_object"}
                    )
                    
                    cls_text = getattr(cls_resp, "text", str(cls_resp))
                    # simple regex extract if it's markdown wrapped
                    import re
                    match = re.search(r'```(?:json)?(.*?)```', cls_text, re.DOTALL)
                    if match:
                        cls_text = match.group(1).strip()
                        
                    cls_data = json.loads(cls_text)
                    classification = ChunkClassification(**cls_data)
                    
                    if classification.classification != "technical":
                        logger.info(f"Skipping chunk {chunk_id} (classified as {classification.classification}): {classification.reasoning}")
                        continue
                        
                except Exception as e:
                    logger.warning(f"Classification failed for {chunk_id}, defaulting to technical: {e}")
                
                # --- End Classification Pass ---

                messages = self._render_messages(
                    system_msg="You are an expert AI tutor that strictly outputs valid JSON.",
                    template_name="topic_extraction",
                    transcript_text=transcript_text
                )

                try:
                    await asyncio.sleep(0.5)

                    response = await self.llm_manager.generate(TaskType.DETAILED_NOTES, messages)

                    if hasattr(response,
                               "provider") and response.provider != "unknown":
                        final_provider = response.provider
                    if hasattr(response,
                               "model") and response.model != "unknown":
                        final_model = response.model
                    if hasattr(response, "latency"):
                        total_latency += response.latency
                    if hasattr(response, "total_tokens"):
                        total_tokens += response.total_tokens

                    raw_dict = self._safe_dump(response, fallback=empty_result)
                    parsed = TopicsAndNotesOutput(**raw_dict)

                    if parsed.summary:
                        summaries.append(parsed.summary)

                    for t_item in parsed.topics:
                        all_topics.append(t_item)

                except Exception as inner_exc:
                    logger.warning(
                        f"Failed to extract topics for chunk {chunk_id}: {inner_exc}")

            # --- STEP 4: Topic Deduplication / Merging Across Chunks ---
            if all_topics and hasattr(self.llm_manager, "embed"):
                try:
                    logger.info(f"Deduplicating {len(all_topics)} topics...")
                    titles = [t.title for t in all_topics]
                    emb_resp = await self.llm_manager.embed(titles)
                    
                    if "data" in emb_resp:
                        embeddings = [d["embedding"] for d in emb_resp["data"]]
                        
                        merged_topics = []
                        import math
                        def cosine_sim(a, b):
                            dot = sum(x*y for x, y in zip(a, b))
                            norm_a = math.sqrt(sum(x*x for x in a))
                            norm_b = math.sqrt(sum(y*y for y in b))
                            return dot / (norm_a * norm_b) if norm_a and norm_b else 0
                        
                        skip_indices = set()
                        for i in range(len(all_topics)):
                            if i in skip_indices:
                                continue
                            
                            current_topic = all_topics[i]
                            for j in range(i + 1, len(all_topics)):
                                if j in skip_indices:
                                    continue
                                
                                sim = cosine_sim(embeddings[i], embeddings[j])
                                if sim > 0.85:
                                    logger.info(f"Merging topic '{all_topics[j].title}' into '{current_topic.title}' (sim={sim:.2f})")
                                    current_topic.key_takeaways.extend(all_topics[j].key_takeaways)
                                    current_topic.citations.extend(all_topics[j].citations)
                                    if all_topics[j].end_time > current_topic.end_time:
                                        current_topic.end_time = all_topics[j].end_time
                                    skip_indices.add(j)
                                    
                            merged_topics.append(current_topic)
                            
                        # Cleanup merged topics
                        for mt in merged_topics:
                            mt.key_takeaways = list(dict.fromkeys(mt.key_takeaways))
                            
                            seen_ts = set()
                            unique_cit = []
                            for cit in mt.citations:
                                if cit.timestamp not in seen_ts:
                                    seen_ts.add(cit.timestamp)
                                    unique_cit.append(cit)
                            mt.citations = unique_cit
                            
                        all_topics = merged_topics
                        logger.info(f"Deduplication complete. Reduced to {len(all_topics)} topics.")
                except Exception as e:
                    logger.warning(f"Topic deduplication failed: {e}")
            # --- End Deduplication ---

            combined_summary = "\n\n".join(
                summaries) if summaries else "No summary generated."

            final_parsed = TopicsAndNotesOutput(
                summary=combined_summary,
                topics=all_topics,
                provider=final_provider,
                model=final_model,
                latency=round(total_latency, 2),
                total_tokens=total_tokens
            )

            # Save parsed topics back to context so downstream services can use
            # them
            context.topics = [t.model_dump() for t in final_parsed.topics]

            execution_time = round(time.time() - start_time, 2)

            result_dict = final_parsed.model_dump(exclude_none=True)

            return {
                "status": "success",
                "metadata": {
                    "execution_time_sec": execution_time,
                    "processed_chunks": len(chunks)
                },
                "data": result_dict
            }

        except Exception as exc:
            logger.error("TopicService: extraction failed: %s", exc)
            return empty_result
