# TODO: Video Transcript to Social Media Content Generator

## Project Overview
Implement functionality to generate titles and tags for multiple social media platforms given a video transcript. The system will use OpenAI's models via Pydantic AI to generate platform-specific content following each platform's content length rules and style guidelines.

**Target Platforms:** YouTube, Instagram, Facebook, TikTok, X (Twitter), LinkedIn, Twitch

**Reference:** [Pydantic AI OpenAI Models](https://ai.pydantic.dev/models/openai/)

---

## 🏗️ **Phase 1: Project Foundation & Configuration**

- [x] **Task 1.1: Environment Setup**
  - Set up OpenAI API key configuration using environment variables
  - Create `.env` file template with required API keys
  - Configure Pydantic AI with OpenAI provider
  - Test basic OpenAI connectivity
  - **Testing**: Verify API connection with a simple ping/test call

- [x] **Task 1.2: Project Structure Setup**
  - Create core application structure in `/app` directory
  - Set up FastAPI application foundation
  - Create directory structure: `/models`, `/services`, `/routers`, `/config`, `/tests`
  - **Testing**: Verify FastAPI application starts successfully

---

## 📋 **Phase 2: Data Models & Platform Definitions**

- [x] **Task 2.1: Platform Configuration Models**
  - Create Pydantic models for platform-specific rules:
    - `PlatformRules` base model
    - Platform-specific models for each platform (YouTube, Instagram, Facebook, TikTok, X, LinkedIn, Twitch)
  - Define character limits, content style guidelines, and tag requirements per platform
  - **Testing**: Validate model instantiation and field constraints

- [x] **Task 2.2: Content Generation Models**
  - Create `VideoTranscript` input model
  - Create `GeneratedContent` output model with title and tags
  - Create `PlatformContent` model for platform-specific generated content
  - **Testing**: Validate model serialization/deserialization

---

## 🎯 **Phase 3: Platform-Specific Content Rules**

- [x] **Task 3.1: YouTube Content Rules**
  - Title: Max 100 characters, engaging and SEO-friendly
  - Tags: 10-15 relevant tags, trending keywords focus
  - Content style: Educational/entertainment balance
  - **Testing**: Validate character limits and tag count constraints

- [x] **Task 3.2: Instagram Content Rules**
  - Title: Max 150 characters (for captions), visually appealing
  - Tags: 20-30 hashtags, mix of popular and niche tags
  - Content style: Visual-first, engaging, lifestyle-focused
  - **Testing**: Validate hashtag formatting and character limits

- [x] **Task 3.3: Facebook Content Rules**
  - Title: Max 255 characters, engagement-focused
  - Tags: 3-5 relevant hashtags, not hashtag-heavy
  - Content style: Community-building, shareable content
  - **Testing**: Validate content length and engagement elements

- [x] **Task 3.4: TikTok Content Rules**
  - Title: Max 150 characters, trend-aware, catchy
  - Tags: 3-5 trending hashtags, viral potential
  - Content style: Gen-Z friendly, trend-focused
  - **Testing**: Validate trend keyword integration

- [x] **Task 3.5: X (Twitter) Content Rules**
  - Title: Max 280 characters total (including hashtags)
  - Tags: 2-3 hashtags integrated into text
  - Content style: Concise, timely, conversation-starting
  - **Testing**: Validate total character count including hashtags

- [x] **Task 3.6: LinkedIn Content Rules**
  - Title: Max 210 characters, professional tone
  - Tags: 3-5 professional/industry hashtags
  - Content style: Professional, thought-leadership focused
  - **Testing**: Validate professional tone and industry relevance

- [x] **Task 3.7: Twitch Content Rules**
  - Title: Max 140 characters, gaming/streaming focused
  - Tags: Gaming categories, community-focused tags
  - Content style: Gaming community, interactive content
  - **Testing**: Validate gaming terminology and community focus

---

## 🤖 **Phase 4: AI Content Generation Service**

- [x] **Task 4.1: Base AI Service Setup**
  - Create `ContentGeneratorService` using Pydantic AI
  - Configure OpenAI model (GPT-4o)
  - Implement base prompt engineering for content generation
  - **Testing**: Test basic AI response generation

- [x] **Task 4.2: Platform-Specific AI Agents**
  - Create separate AI agents for each platform
  - Implement platform-specific prompt engineering
  - Configure response formatting for each platform's requirements
  - **Testing**: Test each agent independently with sample transcripts

- [x] **Task 4.3: Transcript Processing Service**
  - Create service to clean and prepare video transcripts
  - Implement transcript summarization for long content
  - Extract key themes and topics from transcripts
  - **Testing**: Test with various transcript lengths and qualities

---

## 🔧 **Phase 5: Core Business Logic**

- [x] **Task 5.1: Content Generation Orchestrator**
  - Create main service to coordinate platform-specific generation
  - Add retry logic and error handling
  - **Testing**: Test orchestration with multiple platform requests

- [x] **Task 5.2: Content Validation Service**
  - Implement validation for generated content against platform rules
  - Implement fallback content generation for failed validations
  - **Testing**: Test validation with edge cases and invalid content
---

## 🌐 **Phase 6: API Endpoints**

- [x] **Task 6.1: Single Platform Generation Endpoint**
  - Create POST `/generate/{platform}` endpoint
  - Implement request/response models
  - Add input validation and error handling
  - **Testing**: Test endpoint with valid/invalid inputs for each platform

- [x] **Task 6.2: Platform Rules Information Endpoint**
  - Create GET `/platforms/{platform}/rules` endpoint
  - Return platform-specific constraints and guidelines
  - **Testing**: Verify correct rule information for each platform

---

## 📊 **Phase 7: Enhanced Features**

- [ ] **Task 7.1: Content Alternatives Generator**
  - Generate multiple title/tag variations per platform
  - Implement ranking system for generated alternatives
  - **Testing**: Test alternative generation quality and diversity

- [ ] **Task 7.2: Trending Keywords Integration**
  - Integrate with trending keywords APIs (optional)
  - Update platform-specific trending considerations
  - **Testing**: Test trending keyword integration and relevance

- [ ] **Task 7.3: Content Analytics Preparation**
  - Add metadata tracking for generated content
  - Implement performance prediction scoring
  - **Testing**: Test metadata collection and scoring accuracy

---

## ✅ **Phase 8: Testing & Validation**

- [ ] **Task 8.1: Unit Tests**
  - Create comprehensive unit tests for all models
  - Test all service methods independently
  - Test platform-specific rule enforcement
  - **Testing**: Achieve >90% code coverage

- [ ] **Task 8.2: Integration Tests**
  - Test end-to-end API workflows
  - Test AI service integration with various transcript types
  - Test error handling and edge cases
  - **Testing**: Validate complete user workflows

- [ ] **Task 8.3: Performance Tests**
  - Test generation speed for single/batch requests
  - Test concurrent request handling
  - Test memory usage with large transcripts
  - **Testing**: Ensure acceptable response times (<5s per platform)

---

## 📖 **Phase 9: Documentation & Deployment**

- [ ] **Task 9.1: API Documentation**
  - Generate OpenAPI/Swagger documentation
  - Create usage examples for each endpoint
  - Document platform-specific requirements
  - **Testing**: Verify documentation accuracy with actual API

- [ ] **Task 9.2: Configuration Documentation**
  - Document environment variable requirements
  - Create deployment guide
  - Document platform rule customization options
  - **Testing**: Test deployment from documentation

---

## 🎯 **Success Criteria for Each Phase**

1. **Phase 1**: API connection established, FastAPI running
2. **Phase 2**: All models validate correctly with sample data  
3. **Phase 3**: Platform rules enforced and tested
4. **Phase 4**: AI generates relevant content for each platform
5. **Phase 5**: Content meets platform requirements consistently
6. **Phase 6**: API endpoints respond correctly with valid data
7. **Phase 7**: Enhanced features improve content quality
8. **Phase 8**: All tests pass, system handles edge cases
9. **Phase 9**: System is documented and deployable

---

## 🔍 **Independent Testing Strategy**

Each task includes specific testing criteria that can be validated independently before moving to the next task. This ensures each component works correctly in isolation and integrates properly with the overall system.

---

## 📋 **Platform-Specific Requirements Summary**

| Platform | Title Length | Tag Count | Style Focus |
|----------|-------------|-----------|-------------|
| YouTube | 100 chars | 10-15 tags | Educational/Entertainment |
| Instagram | 150 chars | 20-30 hashtags | Visual-first, Lifestyle |
| Facebook | 255 chars | 3-5 hashtags | Community-building |
| TikTok | 150 chars | 3-5 hashtags | Trend-focused, Gen-Z |
| X (Twitter) | 280 chars total | 2-3 hashtags | Concise, Timely |
| LinkedIn | 210 chars | 3-5 hashtags | Professional, Thought-leadership |
| Twitch | 140 chars | Gaming tags | Gaming community |

---

## 🚀 **Getting Started**

1. Start with Phase 1 to set up the foundation
2. Complete each task in sequence within each phase
3. Run the specified tests for each task before proceeding
4. Each phase builds upon the previous one
5. Maintain independent testability for each component

---

### How to check off tasks
Replace the empty space inside the brackets with an `x` like so: `[x]`.
> Example:  
> - [x] Install dependencies

Happy hacking! 🚀 