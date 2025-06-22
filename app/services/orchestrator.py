"""
Content Generation Orchestrator for coordinating multi-platform content generation.
Manages batch processing, error handling, retry logic, and service coordination.
"""
import uuid
import time
import logging
from typing import List, Dict, Optional, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

import sys
from pathlib import Path

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

from models.platform_rules import PlatformType, get_platform_rules
from models.content import (
    VideoTranscript, PlatformContent, BatchGenerationRequest, 
    BatchGenerationResponse, ContentGenerationOptions
)
from services.content_generator import ContentGeneratorService, ContentGenerationRequest
from services.platform_agents import PlatformAgentManager
from services.transcript_processor import TranscriptProcessor, TranscriptAnalysis

logger = logging.getLogger(__name__)


@dataclass
class GenerationResult:
    """Result of content generation for a single platform."""
    platform: PlatformType
    success: bool
    content: Optional[PlatformContent] = None
    error: Optional[str] = None
    processing_time: float = 0.0
    retry_count: int = 0


class ContentOrchestrator:
    """Orchestrates content generation across multiple platforms with error handling and optimization."""
    
    def __init__(self, max_retries: int = 3, timeout_seconds: int = 30):
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        
        # Initialize services
        self.content_generator = ContentGeneratorService()
        self.platform_agents = PlatformAgentManager()
        self.transcript_processor = TranscriptProcessor()
        
        # Performance tracking
        self.generation_stats = {
            "total_requests": 0,
            "successful_generations": 0,
            "failed_generations": 0,
            "total_processing_time": 0.0,
            "platform_stats": {platform: {"success": 0, "failure": 0} for platform in PlatformType}
        }
    
    def process_transcript(self, transcript: VideoTranscript) -> Tuple[VideoTranscript, TranscriptAnalysis]:
        """Process and analyze transcript before content generation."""
        try:
            logger.info("Processing transcript for content generation")
            enhanced_transcript, analysis = self.transcript_processor.process_transcript(transcript)
            logger.info(f"Transcript processed: {analysis.word_count} words, tone: {analysis.tone}")
            return enhanced_transcript, analysis
            
        except Exception as e:
            logger.error(f"Transcript processing failed: {e}")
            # Return original transcript with basic analysis if processing fails
            basic_analysis = self.transcript_processor._create_basic_analysis(transcript.content, transcript)
            return transcript, basic_analysis
    
    def generate_content_for_platform(self, platform: PlatformType, transcript: VideoTranscript,
                                    options: Optional[ContentGenerationOptions] = None,
                                    use_specialized_agent: bool = True) -> GenerationResult:
        """Generate content for a single platform with error handling and retries."""
        start_time = time.time()
        retry_count = 0
        last_error = None
        
        # Default options
        if options is None:
            options = ContentGenerationOptions()
        
        while retry_count <= self.max_retries:
            try:
                logger.info(f"Generating content for {platform.value} (attempt {retry_count + 1})")
                
                if use_specialized_agent:
                    # Use platform-specific agent
                    content = self.platform_agents.generate_content(
                        platform=platform,
                        transcript=transcript,
                        tone=options.tone or "neutral",
                        include_emojis=options.include_emojis
                    )
                else:
                    # Use general content generator
                    request = ContentGenerationRequest(
                        transcript=transcript,
                        platform=platform,
                        tone=options.tone or "neutral",
                        include_emojis=options.include_emojis
                    )
                    content = self.content_generator.generate_content_sync(request)
                
                # Validate content meets platform requirements
                rules = get_platform_rules(platform)
                is_valid = content.validate_against_platform_rules(rules)
                
                if is_valid:
                    processing_time = time.time() - start_time
                    logger.info(f"Content generated successfully for {platform.value} in {processing_time:.2f}s")
                    
                    return GenerationResult(
                        platform=platform,
                        success=True,
                        content=content,
                        processing_time=processing_time,
                        retry_count=retry_count
                    )
                else:
                    logger.warning(f"Generated content for {platform.value} failed validation: {content.validation_notes}")
                    last_error = f"Content validation failed: {', '.join(content.validation_notes)}"
                    
            except Exception as e:
                last_error = str(e)
                logger.error(f"Content generation failed for {platform.value} (attempt {retry_count + 1}): {e}")
            
            retry_count += 1
            if retry_count <= self.max_retries:
                # Exponential backoff for retries
                wait_time = min(2 ** retry_count, 10)
                logger.info(f"Retrying {platform.value} in {wait_time} seconds...")
                time.sleep(wait_time)
        
        # All retries failed
        processing_time = time.time() - start_time
        logger.error(f"Content generation failed for {platform.value} after {self.max_retries} retries")
        
        return GenerationResult(
            platform=platform,
            success=False,
            error=last_error or "Unknown error after retries",
            processing_time=processing_time,
            retry_count=retry_count - 1
        )
    
    def generate_batch_content(self, request: BatchGenerationRequest,
                              use_specialized_agents: bool = True,
                              concurrent: bool = True) -> BatchGenerationResponse:
        """Generate content for multiple platforms in batch."""
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        logger.info(f"Starting batch generation for {len(request.platforms)} platforms (ID: {request_id})")
        
        # Process transcript first
        try:
            enhanced_transcript, analysis = self.process_transcript(request.transcript)
        except Exception as e:
            logger.error(f"Transcript processing failed: {e}")
            enhanced_transcript = request.transcript
            analysis = None
        
        # Extract options
        options = ContentGenerationOptions(**request.options) if request.options else ContentGenerationOptions()
        
        # Generate content for all platforms
        results: List[GenerationResult] = []
        
        if concurrent and len(request.platforms) > 1:
            # Concurrent generation using ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=min(len(request.platforms), 4)) as executor:
                future_to_platform = {
                    executor.submit(
                        self.generate_content_for_platform,
                        platform,
                        enhanced_transcript,
                        options,
                        use_specialized_agents
                    ): platform for platform in request.platforms
                }
                
                for future in as_completed(future_to_platform):
                    try:
                        result = future.result(timeout=self.timeout_seconds)
                        results.append(result)
                    except Exception as e:
                        platform = future_to_platform[future]
                        logger.error(f"Concurrent generation failed for {platform.value}: {e}")
                        results.append(GenerationResult(
                            platform=platform,
                            success=False,
                            error=f"Timeout or execution error: {str(e)}",
                            processing_time=self.timeout_seconds
                        ))
        else:
            # Sequential generation
            for platform in request.platforms:
                result = self.generate_content_for_platform(
                    platform, enhanced_transcript, options, use_specialized_agents
                )
                results.append(result)
        
        # Process results
        successful_content = {}
        errors = {}
        success_count = 0
        error_count = 0
        
        for result in results:
            if result.success and result.content:
                successful_content[result.platform.value] = result.content
                success_count += 1
                self.generation_stats["platform_stats"][result.platform]["success"] += 1
            else:
                errors[result.platform.value] = result.error
                error_count += 1
                self.generation_stats["platform_stats"][result.platform]["failure"] += 1
        
        # Update global stats
        total_time = time.time() - start_time
        self.generation_stats["total_requests"] += 1
        self.generation_stats["successful_generations"] += success_count
        self.generation_stats["failed_generations"] += error_count
        self.generation_stats["total_processing_time"] += total_time
        
        logger.info(f"Batch generation completed (ID: {request_id}): {success_count} successful, {error_count} failed, {total_time:.2f}s")
        
        return BatchGenerationResponse(
            request_id=request_id,
            generated_content=successful_content,
            processing_time_seconds=total_time,
            success_count=success_count,
            error_count=error_count,
            errors=errors if errors else None
        )
    
    def generate_single_platform(self, platform: PlatformType, transcript: VideoTranscript,
                                options: Optional[ContentGenerationOptions] = None) -> PlatformContent:
        """Generate content for a single platform (convenience method)."""
        batch_request = BatchGenerationRequest(
            transcript=transcript,
            platforms=[platform],
            options=options.model_dump() if options else {}
        )
        
        response = self.generate_batch_content(batch_request, concurrent=False)
        
        if response.success_count > 0:
            return response.generated_content[platform.value]
        else:
            error_msg = response.errors.get(platform.value, "Unknown error")
            raise RuntimeError(f"Content generation failed for {platform.value}: {error_msg}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for the orchestrator."""
        total_requests = self.generation_stats["total_requests"]
        if total_requests == 0:
            return {"message": "No requests processed yet"}
        
        avg_processing_time = self.generation_stats["total_processing_time"] / total_requests
        success_rate = self.generation_stats["successful_generations"] / (
            self.generation_stats["successful_generations"] + self.generation_stats["failed_generations"]
        ) if (self.generation_stats["successful_generations"] + self.generation_stats["failed_generations"]) > 0 else 0
        
        platform_performance = {}
        for platform, stats in self.generation_stats["platform_stats"].items():
            total_platform_requests = stats["success"] + stats["failure"]
            if total_platform_requests > 0:
                platform_performance[platform.value] = {
                    "success_rate": stats["success"] / total_platform_requests,
                    "total_requests": total_platform_requests,
                    "successful": stats["success"],
                    "failed": stats["failure"]
                }
        
        return {
            "total_requests": total_requests,
            "average_processing_time": avg_processing_time,
            "overall_success_rate": success_rate,
            "total_successful": self.generation_stats["successful_generations"],
            "total_failed": self.generation_stats["failed_generations"],
            "platform_performance": platform_performance
        }


# Global orchestrator instance
_content_orchestrator = None


def get_content_orchestrator() -> ContentOrchestrator:
    """Get global content orchestrator instance."""
    global _content_orchestrator
    if _content_orchestrator is None:
        _content_orchestrator = ContentOrchestrator()
    return _content_orchestrator 