"""
LLM utilities for Saathi AI pipeline.
Handles HuggingFace integration with fallback responses.
"""

import os
import logging
from typing import Dict, Any, Optional
from django.conf import settings

logger = logging.getLogger(__name__)

# Fallback responses for when API keys are not available
FALLBACK_RESPONSES = {
    'greeting': [
        "Hello! I'm Saathi, your mental wellness companion. I'm here to listen and support you. How are you feeling today?",
        "Hi there! I'm glad you're here. I'm Saathi, and I'm here to provide a safe space for you to share what's on your mind.",
        "Welcome! I'm Saathi, your AI wellness companion. I'm here to support your mental health journey. What would you like to talk about?",
    ],
    'crisis_support': [
        "I'm really concerned about what you're sharing. Your safety is the most important thing right now. Please reach out to:\n\n🆘 **Crisis Text Line**: Text HOME to 741741\n📞 **National Suicide Prevention Lifeline**: 988\n🏥 **Emergency Services**: 911\n\nYou don't have to go through this alone. There are people who want to help.",
        "Thank you for trusting me with these difficult feelings. Right now, I want to connect you with immediate support:\n\n• **Crisis Text Line**: Text HOME to 741741\n• **National Suicide Prevention Lifeline**: 988\n• **Campus Counseling**: Contact your university's counseling center\n\nYour life has value, and there are people trained to help you through this.",
    ],
    'supportive': [
        "It sounds like you're going through a challenging time. Thank you for sharing that with me. Sometimes just talking about our feelings can help us process them better.",
        "I hear you, and I want you to know that your feelings are valid. It's okay to not be okay sometimes. What's one small thing that usually helps you feel a bit better?",
        "That sounds really difficult. I'm glad you felt comfortable enough to share that with me. Remember, you're not alone in this journey.",
    ],
    'anxiety_support': [
        "Anxiety can feel overwhelming, but you're taking a positive step by talking about it. Have you tried any breathing exercises or grounding techniques that help you?",
        "It's understandable to feel anxious, especially with everything you have going on. Let's focus on what you can control right now. What's one thing you can do today for yourself?",
    ],
    'academic_stress': [
        "Academic pressure is really common among college students, and it sounds like you're dealing with a lot. What's the most stressful part of your academic life right now?",
        "College can be incredibly demanding. It's important to remember that your worth isn't determined by your grades. How are you taking care of yourself during this busy time?",
    ],
    'general_support': [
        "Thank you for sharing that with me. It takes courage to open up about how you're feeling. What's something that's been on your mind lately?",
        "I'm here to listen and support you. Everyone's mental health journey looks different, and I'm glad you're taking steps to care for yours.",
    ]
}


class LLMService:
    """Service class for LLM interactions with HuggingFace integration."""
    
    def __init__(self):
        self.huggingface_available = bool(settings.HUGGINGFACE_API_KEY)
        self.client = None
        
        if self.huggingface_available:
            try:
                from huggingface_hub import InferenceClient
                self.client = InferenceClient(
                    model="meta-llama/Llama-3.2-8B-Instruct",
                    token=settings.HUGGINGFACE_API_KEY,
                )
                logger.info("HuggingFace LLM service initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize HuggingFace client: {e}")
                self.huggingface_available = False
        
        if not self.huggingface_available:
            logger.info("Using fallback responses (no HuggingFace API key)")
    
    def generate_response(
        self, 
        prompt: str, 
        context: Dict[str, Any] = None,
        max_tokens: int = 500,
        temperature: float = 0.7
    ) -> str:
        """Generate AI response using HuggingFace or fallback."""
        
        if self.huggingface_available and self.client:
            try:
                return self._generate_huggingface_response(
                    prompt, context, max_tokens, temperature
                )
            except Exception as e:
                logger.error(f"HuggingFace generation failed: {e}")
                return self._get_fallback_response(prompt, context)
        else:
            return self._get_fallback_response(prompt, context)
    
    def _generate_huggingface_response(
        self, 
        prompt: str, 
        context: Dict[str, Any],
        max_tokens: int,
        temperature: float
    ) -> str:
        """Generate response using HuggingFace Inference API."""
        
        try:
            # Format the prompt for Llama-3.2-8B-Instruct
            formatted_prompt = self._format_prompt_for_llama(prompt, context)
            
            response = self.client.text_generation(
                formatted_prompt,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=True,
                return_full_text=False,
            )
            
            # Clean up the response
            return self._clean_response(response)
            
        except Exception as e:
            logger.error(f"HuggingFace API error: {e}")
            raise
    
    def _format_prompt_for_llama(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Format prompt for Llama-3.2-8B-Instruct model."""
        
        system_message = """You are Saathi, a compassionate AI mental wellness companion designed specifically for college students. You provide emotional support, active listening, and gentle guidance while maintaining appropriate boundaries.

Key guidelines:
- Be warm, empathetic, and non-judgmental
- Use a conversational, supportive tone
- Ask follow-up questions to encourage reflection
- Provide practical coping strategies when appropriate
- Always prioritize user safety - escalate crisis situations immediately
- Respect privacy and maintain confidentiality
- Acknowledge the challenges unique to college life
- Encourage professional help when needed

Remember: You are a supportive companion, not a replacement for professional therapy."""
        
        # Add context if available
        context_str = ""
        if context:
            if context.get('screening_results'):
                context_str += f"Recent screening results: {context['screening_results']}\n"
            if context.get('user_memories'):
                context_str += f"User context: {context['user_memories']}\n"
            if context.get('conversation_history'):
                context_str += f"Recent conversation: {context['conversation_history']}\n"
        
        # Format for Llama chat template
        formatted_prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

{system_message}

{context_str}<|eot_id|><|start_header_id|>user<|end_header_id|>

{prompt}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
        
        return formatted_prompt
    
    def _clean_response(self, response: str) -> str:
        """Clean up the generated response."""
        # Remove any system tokens or artifacts
        response = response.strip()
        
        # Remove common artifacts
        artifacts = [
            "<|eot_id|>", "<|end_of_text|>", "<|start_header_id|>", 
            "<|end_header_id|>", "<|begin_of_text|>"
        ]
        
        for artifact in artifacts:
            response = response.replace(artifact, "")
        
        return response.strip()
    
    def _get_fallback_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Get appropriate fallback response based on prompt analysis."""
        
        prompt_lower = prompt.lower()
        
        # Crisis keywords
        crisis_keywords = [
            'suicide', 'kill myself', 'end it all', 'not worth living',
            'better off dead', 'hurt myself', 'self harm', 'cut myself'
        ]
        
        if any(keyword in prompt_lower for keyword in crisis_keywords):
            return self._get_random_fallback('crisis_support')
        
        # Anxiety keywords
        anxiety_keywords = [
            'anxious', 'anxiety', 'panic', 'worried', 'stress', 'overwhelmed',
            'can\'t breathe', 'heart racing', 'nervous'
        ]
        
        if any(keyword in prompt_lower for keyword in anxiety_keywords):
            return self._get_random_fallback('anxiety_support')
        
        # Academic stress keywords
        academic_keywords = [
            'exam', 'test', 'grade', 'study', 'college', 'university',
            'assignment', 'homework', 'professor', 'class'
        ]
        
        if any(keyword in prompt_lower for keyword in academic_keywords):
            return self._get_random_fallback('academic_stress')
        
        # Greeting keywords
        greeting_keywords = [
            'hello', 'hi', 'hey', 'good morning', 'good afternoon', 
            'good evening', 'how are you'
        ]
        
        if any(keyword in prompt_lower for keyword in greeting_keywords):
            return self._get_random_fallback('greeting')
        
        # Default supportive response
        return self._get_random_fallback('general_support')
    
    def _get_random_fallback(self, category: str) -> str:
        """Get a random fallback response from the specified category."""
        import random
        responses = FALLBACK_RESPONSES.get(category, FALLBACK_RESPONSES['general_support'])
        return random.choice(responses)
    
    def detect_crisis(self, text: str) -> Dict[str, Any]:
        """Detect potential crisis situations in user text."""
        
        text_lower = text.lower()
        
        # Crisis indicators with severity scores
        crisis_indicators = {
            'suicidal_ideation': {
                'keywords': [
                    'kill myself', 'end my life', 'suicide', 'not worth living',
                    'better off dead', 'end it all', 'take my own life'
                ],
                'severity': 1.0
            },
            'self_harm': {
                'keywords': [
                    'hurt myself', 'cut myself', 'self harm', 'harm myself',
                    'cutting', 'burning myself'
                ],
                'severity': 0.8
            },
            'severe_depression': {
                'keywords': [
                    'hopeless', 'no point', 'nothing matters', 'can\'t go on',
                    'give up', 'worthless', 'burden'
                ],
                'severity': 0.6
            }
        }
        
        detected_crisis = None
        max_severity = 0
        matched_keywords = []
        
        for crisis_type, data in crisis_indicators.items():
            for keyword in data['keywords']:
                if keyword in text_lower:
                    if data['severity'] > max_severity:
                        max_severity = data['severity']
                        detected_crisis = crisis_type
                    matched_keywords.append(keyword)
        
        if detected_crisis:
            return {
                'crisis_detected': True,
                'crisis_type': detected_crisis,
                'severity_score': max_severity,
                'matched_keywords': matched_keywords,
                'immediate_intervention': max_severity >= 0.8
            }
        
        return {
            'crisis_detected': False,
            'crisis_type': None,
            'severity_score': 0,
            'matched_keywords': [],
            'immediate_intervention': False
        }


# Global LLM service instance
llm_service = None


def get_llm_service() -> LLMService:
    """Get the global LLM service instance."""
    global llm_service
    if llm_service is None:
        llm_service = LLMService()
    return llm_service


def initialize_llm_service():
    """Initialize the LLM service."""
    global llm_service
    llm_service = LLMService()
    return llm_service