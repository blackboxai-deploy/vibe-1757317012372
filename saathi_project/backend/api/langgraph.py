"""
LangGraph-style AI pipeline for Saathi mental wellness conversations.
Implements: Moderator -> Crisis -> Memory/RAG -> Therapist -> Postprocess
"""

import logging
from typing import Dict, Any, List, Optional
from .llm_utils import get_llm_service
from .models import UserProfile, UserMemory, Conversation, CrisisEvent
import json
import re

logger = logging.getLogger(__name__)


class SaathiAIPipeline:
    """Main AI pipeline orchestrating the conversation flow."""
    
    def __init__(self):
        self.llm_service = get_llm_service()
    
    def process_conversation(
        self, 
        uid: str, 
        message: str, 
        history: List[Dict] = None, 
        context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Main pipeline processing a user conversation.
        Returns structured response with crisis detection, memory updates, etc.
        """
        
        try:
            # Initialize pipeline state
            pipeline_state = {
                'uid': uid,
                'user_message': message,
                'history': history or [],
                'context': context or {},
                'crisis_detected': False,
                'memory_updates': {},
                'suggested_coping': [],
                'escalation': None,
                'ai_response': '',
                'processing_steps': []
            }
            
            # Step 1: Moderator - Input validation and safety
            pipeline_state = self._moderator_step(pipeline_state)
            
            # Step 2: Crisis Detection - Check for immediate safety concerns
            pipeline_state = self._crisis_detection_step(pipeline_state)
            
            # If crisis detected, short-circuit to crisis response
            if pipeline_state['crisis_detected']:
                pipeline_state = self._crisis_response_step(pipeline_state)
                return self._format_final_response(pipeline_state)
            
            # Step 3: Memory/RAG - Retrieve relevant context and memories
            pipeline_state = self._memory_rag_step(pipeline_state)
            
            # Step 4: Therapist - Generate therapeutic response
            pipeline_state = self._therapist_step(pipeline_state)
            
            # Step 5: Postprocess - Extract memory updates and coping strategies
            pipeline_state = self._postprocess_step(pipeline_state)
            
            return self._format_final_response(pipeline_state)
            
        except Exception as e:
            logger.error(f"Pipeline processing error: {e}")
            return {
                'reply': "I'm experiencing some technical difficulties right now. Please try again, or if you're in crisis, please contact emergency services or call 988.",
                'crisis': False,
                'suggested_coping': [],
                'memory_update': {},
                'escalation': None,
                'error': str(e)
            }
    
    def _moderator_step(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Step 1: Moderate input for safety and appropriateness."""
        
        state['processing_steps'].append('moderator')
        
        message = state['user_message']
        
        # Basic content moderation
        inappropriate_patterns = [
            r'\b(fuck|shit|damn)\b',  # Allow mild profanity in mental health context
        ]
        
        # Check for spam or nonsensical input
        if len(message.strip()) < 3:
            state['moderation_flag'] = 'too_short'
        elif len(message) > 2000:
            state['moderation_flag'] = 'too_long'
            state['user_message'] = message[:2000] + "..."
        
        # Mark as processed
        state['moderated'] = True
        
        return state
    
    def _crisis_detection_step(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Step 2: Detect crisis situations requiring immediate intervention."""
        
        state['processing_steps'].append('crisis_detection')
        
        # Use LLM service crisis detection
        crisis_analysis = self.llm_service.detect_crisis(state['user_message'])
        
        if crisis_analysis['crisis_detected']:
            state['crisis_detected'] = True
            state['crisis_type'] = crisis_analysis['crisis_type']
            state['crisis_severity'] = crisis_analysis['severity_score']
            state['crisis_keywords'] = crisis_analysis['matched_keywords']
            state['immediate_intervention'] = crisis_analysis['immediate_intervention']
            
            logger.warning(f"Crisis detected for user {state['uid']}: {crisis_analysis['crisis_type']}")
        
        return state
    
    def _crisis_response_step(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Generate immediate crisis response and log the event."""
        
        state['processing_steps'].append('crisis_response')
        
        # Generate crisis-appropriate response
        crisis_prompt = f"""
        URGENT: The user has indicated they may be in crisis. Their message: "{state['user_message']}"
        
        Respond with:
        1. Immediate validation and concern
        2. Crisis resources (988, Crisis Text Line, Emergency services)
        3. Gentle encouragement to reach out for help
        4. Brief message that their life has value
        
        Keep response under 200 words, warm but urgent.
        """
        
        state['ai_response'] = self.llm_service.generate_response(
            crisis_prompt, 
            context={'crisis': True}
        )
        
        # Set escalation information
        state['escalation'] = {
            'type': 'crisis',
            'resources': [
                {'name': 'Crisis Text Line', 'contact': 'Text HOME to 741741'},
                {'name': 'National Suicide Prevention Lifeline', 'contact': '988'},
                {'name': 'Emergency Services', 'contact': '911'},
            ],
            'immediate': state.get('immediate_intervention', False)
        }
        
        # Log crisis event (this would be saved to database in the view)
        state['crisis_log'] = {
            'crisis_type': state['crisis_type'],
            'severity_score': state['crisis_severity'],
            'trigger_keywords': state['crisis_keywords']
        }
        
        return state
    
    def _memory_rag_step(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Step 3: Retrieve relevant memories and context using RAG."""
        
        state['processing_steps'].append('memory_rag')
        
        try:
            # Get user profile and memories
            user_profile = UserProfile.objects.filter(uid=state['uid']).first()
            
            if user_profile:
                # Retrieve recent memories
                memories = UserMemory.objects.filter(
                    user_profile=user_profile
                ).order_by('-updated_at')[:10]
                
                state['user_memories'] = {}
                for memory in memories:
                    category = memory.memory_type
                    if category not in state['user_memories']:
                        state['user_memories'][category] = {}
                    state['user_memories'][category][memory.key] = memory.value
                
                # Retrieve recent conversations for context
                recent_conversations = Conversation.objects.filter(
                    user_profile=user_profile
                ).order_by('-created_at')[:3]
                
                state['conversation_context'] = []
                for conv in recent_conversations:
                    state['conversation_context'].append({
                        'user': conv.user_message[:200],
                        'ai': conv.ai_response[:200]
                    })
            
            # TODO: Implement RAG document retrieval here
            # This would query the FAISS/Chroma index for relevant documents
            state['rag_documents'] = []
            
        except Exception as e:
            logger.error(f"Memory/RAG retrieval error: {e}")
            state['user_memories'] = {}
            state['conversation_context'] = []
            state['rag_documents'] = []
        
        return state
    
    def _therapist_step(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Step 4: Generate therapeutic response with context."""
        
        state['processing_steps'].append('therapist')
        
        # Build therapeutic prompt with full context
        therapist_prompt = self._build_therapist_prompt(state)
        
        # Generate response using LLM
        context_data = {
            'user_memories': state.get('user_memories', {}),
            'conversation_history': state.get('conversation_context', []),
            'screening_results': state.get('context', {}).get('screening_results'),
        }
        
        state['ai_response'] = self.llm_service.generate_response(
            therapist_prompt, 
            context=context_data,
            max_tokens=400,
            temperature=0.8
        )
        
        return state
    
    def _build_therapist_prompt(self, state: Dict[str, Any]) -> str:
        """Build comprehensive therapist prompt with context and examples."""
        
        # Base therapeutic system prompt with few-shot examples
        system_prompt = """You are Saathi, a compassionate AI mental wellness companion for college students. 

Core principles:
- Be warm, empathetic, and genuinely curious about the user's experience
- Use reflective listening and ask thoughtful follow-up questions
- Provide practical coping strategies appropriate for college students
- Normalize struggles while encouraging growth and resilience
- Remember and reference previous conversations naturally
- Always prioritize user safety and well-being

Example conversations:

User: "I've been really stressed about my midterm exams. I can't sleep and I feel like I'm going to fail everything."

Saathi: "That sounds incredibly overwhelming, especially when it's affecting your sleep too. Exam stress is so common among college students, but that doesn't make what you're feeling any less valid. When you think about the exams, what specifically worries you the most? Is it the material itself, time management, or maybe something else?"

---

User: "I had a panic attack in class yesterday and I'm embarrassed. I don't want to go back."

Saathi: "I'm really glad you felt safe enough to share that with me. Panic attacks can be frightening and exhausting, and it's completely understandable to feel embarrassed, even though you have nothing to be ashamed of. You showed incredible strength by getting through it. Have you experienced panic attacks before, or was this your first time? And how are you feeling right now as we talk about it?"

---

User: "My roommate and I got into a huge fight. I think she hates me now and I don't know what to do."

Saathi: "Roommate conflicts can feel especially intense because it's your living space too - there's no real escape. It sounds like this fight has left you feeling really uncertain about where you stand with her. Without sharing anything too personal, can you tell me what the fight was generally about? Sometimes talking through what happened can help us figure out a path forward."

---

User: "I feel like everyone else has their life figured out and I'm just pretending to know what I'm doing."

Saathi: "What you're describing sounds like imposter syndrome, and honestly, it's something I hear from college students all the time. That feeling of 'just pretending' while everyone else seems confident is so much more common than you might think. Can you tell me about a specific situation recently where you felt like you were just pretending? I'm curious about what that experience was like for you."

Now respond to the current user message with the same warmth, curiosity, and practical support."""
        
        # Add user context if available
        context_str = ""
        if state.get('user_memories'):
            memories_summary = []
            for category, items in state['user_memories'].items():
                for key, value in items.items():
                    memories_summary.append(f"{category}: {key} - {value}")
            if memories_summary:
                context_str += f"\nUser context from previous conversations:\n{'; '.join(memories_summary[:5])}"
        
        if state.get('conversation_context'):
            context_str += f"\nRecent conversation context: User has been discussing topics around {len(state['conversation_context'])} recent interactions"
        
        # Add screening context if available
        screening_context = state.get('context', {}).get('screening_results')
        if screening_context:
            context_str += f"\nRecent screening results: {screening_context}"
        
        # Build final prompt
        user_message = state['user_message']
        history_context = ""
        if state.get('history'):
            recent_history = state['history'][-2:]  # Last 2 exchanges
            history_context = "\nRecent conversation:\n"
            for exchange in recent_history:
                history_context += f"User: {exchange.get('user', '')}\nSaathi: {exchange.get('ai', '')}\n"
        
        full_prompt = f"""{system_prompt}

{context_str}
{history_context}

Current user message: "{user_message}"

Respond as Saathi with empathy, curiosity, and practical support:"""
        
        return full_prompt
    
    def _postprocess_step(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Step 5: Extract memory updates and coping strategies from response."""
        
        state['processing_steps'].append('postprocess')
        
        # Extract potential memory updates from the conversation
        memory_updates = self._extract_memory_updates(
            state['user_message'], 
            state['ai_response']
        )
        state['memory_updates'] = memory_updates
        
        # Extract coping strategies mentioned
        coping_strategies = self._extract_coping_strategies(state['ai_response'])
        state['suggested_coping'] = coping_strategies
        
        return state
    
    def _extract_memory_updates(self, user_message: str, ai_response: str) -> Dict[str, Any]:
        """Extract potential memory updates from the conversation."""
        
        memory_updates = {}
        user_lower = user_message.lower()
        
        # Extract interests/hobbies
        hobby_patterns = [
            r'i (?:like|love|enjoy) (\w+(?:\s+\w+)*)',
            r'i\'m into (\w+(?:\s+\w+)*)',
            r'my hobby is (\w+(?:\s+\w+)*)'
        ]
        
        for pattern in hobby_patterns:
            matches = re.findall(pattern, user_lower)
            for match in matches:
                if len(match) > 2:  # Avoid short words
                    memory_updates['interests'] = memory_updates.get('interests', [])
                    memory_updates['interests'].append(match)
        
        # Extract academic info
        academic_patterns = [
            r'i\'m (?:studying|majoring in) (\w+(?:\s+\w+)*)',
            r'my major is (\w+(?:\s+\w+)*)',
            r'i\'m a (\w+) major'
        ]
        
        for pattern in academic_patterns:
            matches = re.findall(pattern, user_lower)
            for match in matches:
                memory_updates['academic'] = memory_updates.get('academic', [])
                memory_updates['academic'].append(match)
        
        # Extract goals
        goal_patterns = [
            r'i want to (\w+(?:\s+\w+)*)',
            r'my goal is to (\w+(?:\s+\w+)*)',
            r'i hope to (\w+(?:\s+\w+)*)'
        ]
        
        for pattern in goal_patterns:
            matches = re.findall(pattern, user_lower)
            for match in matches:
                if len(match) > 3:
                    memory_updates['goals'] = memory_updates.get('goals', [])
                    memory_updates['goals'].append(match)
        
        return memory_updates
    
    def _extract_coping_strategies(self, ai_response: str) -> List[str]:
        """Extract coping strategies mentioned in AI response."""
        
        coping_strategies = []
        response_lower = ai_response.lower()
        
        # Common coping strategy keywords
        coping_keywords = [
            'breathing', 'meditation', 'exercise', 'journaling', 'sleep',
            'talk to someone', 'counseling', 'therapy', 'mindfulness',
            'grounding', 'relaxation', 'self-care', 'break', 'walk'
        ]
        
        for keyword in coping_keywords:
            if keyword in response_lower:
                coping_strategies.append(keyword.title())
        
        return list(set(coping_strategies))  # Remove duplicates
    
    def _format_final_response(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Format the final response for the API."""
        
        return {
            'reply': state['ai_response'],
            'crisis': state['crisis_detected'],
            'suggested_coping': state['suggested_coping'],
            'memory_update': state['memory_updates'],
            'escalation': state.get('escalation'),
            'processing_steps': state['processing_steps'],
            'crisis_log': state.get('crisis_log')
        }


# Global pipeline instance
ai_pipeline = None


def get_ai_pipeline() -> SaathiAIPipeline:
    """Get the global AI pipeline instance."""
    global ai_pipeline
    if ai_pipeline is None:
        ai_pipeline = SaathiAIPipeline()
    return ai_pipeline


def initialize_ai_pipeline():
    """Initialize the AI pipeline."""
    global ai_pipeline
    ai_pipeline = SaathiAIPipeline()
    return ai_pipeline