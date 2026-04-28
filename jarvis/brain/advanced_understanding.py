"""
jarvis/brain/advanced_understanding.py
═══════════════════════════════════════════
Advanced understanding system for J.A.R.V.I.S. soul.

This module provides sophisticated semantic analysis and context understanding
to help Jarvis accurately identify what the user is saying and respond appropriately.
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class UnderstandingResult:
    """Result of advanced semantic analysis."""
    intent: str
    emotion: str
    confidence: float
    entities: Dict[str, str]
    context_type: str
    sarcasm_detected: bool
    implicit_request: Optional[str]

class AdvancedUnderstanding:
    """Advanced understanding system with soul-based analysis."""
    
    def __init__(self):
        self.emotion_keywords = {
            'happy': ['great', 'awesome', 'fantastic', 'love', 'amazing', 'wonderful', 'excited'],
            'frustrated': ['annoying', 'stupid', 'broken', 'useless', 'hate', 'terrible'],
            'curious': ['how', 'why', 'what', 'curious', 'interested', 'wondering'],
            'confused': ['confused', 'unclear', 'don\'t understand', 'what do you mean'],
            'playful': ['just kidding', 'joking', 'haha', 'lol', 'funny', 'sarcastic'],
            'serious': ['important', 'serious', 'focus', 'need', 'critical'],
            'grateful': ['thank', 'thanks', 'appreciate', 'grateful', 'good job'],
        }
        
        self.intent_patterns = {
            'question': [
                r'\?$', r'^(how|what|when|where|why|who|which|can|could|would|should|is|are|do|does|did)',
                r'tell me about', r'explain', r'describe'
            ],
            'command': [
                r'^(open|close|start|stop|launch|run|execute)', 
                r'^(play|pause|resume|skip)', r'^(create|make|build|write)',
                r'^(show|display|reveal)', r'^(hide|minimize|maximize)'
            ],
            'statement': [
                r'^(i think|i feel|i believe)', r'^(my name is|i am)',
                r'^(remember|forget|note)', r'^(this is|that is)'
            ],
            'greeting': [
                r'^(hi|hello|hey|good morning|good evening|good afternoon)',
                r'^(how are you|what\'s up|how\'s it going)'
            ],
            'farewell': [
                r'^(bye|goodbye|see you|later|good night)', r'^(shut down|turn off|exit)'
            ]
        }
        
        self.sarcasm_indicators = [
            'yeah right', 'sure', 'obviously', 'clearly', 'totally',
            'as if', 'whatever', 'fine', 'great', 'wonderful'
        ]
        
        self.context_keywords = {
            'technical': ['code', 'programming', 'software', 'app', 'system', 'algorithm', 'database'],
            'personal': ['i', 'me', 'my', 'name', 'feel', 'think', 'want', 'need'],
            'professional': ['work', 'project', 'task', 'deadline', 'meeting', 'team'],
            'casual': ['just', 'maybe', 'kinda', 'sorta', 'haha', 'lol'],
        }

    def analyze_user_input(self, text: str, conversation_history: List[str] = None) -> UnderstandingResult:
        """
        Perform comprehensive analysis of user input.
        
        Args:
            text: User's spoken/written input
            conversation_history: Recent conversation context
            
        Returns:
            UnderstandingResult with detailed analysis
        """
        text_lower = text.lower().strip()
        
        # Detect intent
        intent = self._detect_intent(text_lower)
        
        # Detect emotion
        emotion = self._detect_emotion(text_lower)
        
        # Extract entities
        entities = self._extract_entities(text)
        
        # Determine context type
        context_type = self._determine_context(text_lower)
        
        # Detect sarcasm
        sarcasm_detected = self._detect_sarcasm(text_lower)
        
        # Identify implicit requests
        implicit_request = self._identify_implicit_request(text_lower, intent, emotion)
        
        # Calculate confidence
        confidence = self._calculate_confidence(intent, emotion, entities)
        
        return UnderstandingResult(
            intent=intent,
            emotion=emotion,
            confidence=confidence,
            entities=entities,
            context_type=context_type,
            sarcasm_detected=sarcasm_detected,
            implicit_request=implicit_request
        )
    
    def _detect_intent(self, text: str) -> str:
        """Detect the primary intent of the user input."""
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return intent
        return 'general'
    
    def _detect_emotion(self, text: str) -> str:
        """Detect the emotional tone of the user input."""
        emotion_scores = {}
        for emotion, keywords in self.emotion_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                emotion_scores[emotion] = score
        
        if emotion_scores:
            return max(emotion_scores, key=emotion_scores.get)
        return 'neutral'
    
    def _extract_entities(self, text: str) -> Dict[str, str]:
        """Extract named entities from the text."""
        entities = {}
        
        # Extract potential names (simple heuristic)
        name_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b'
        potential_names = re.findall(name_pattern, text)
        if potential_names:
            entities['potential_names'] = ', '.join(potential_names)
        
        # Extract technical terms
        tech_words = ['python', 'javascript', 'react', 'api', 'database', 'algorithm']
        found_tech = [word for word in tech_words if word.lower() in text.lower()]
        if found_tech:
            entities['technical_terms'] = ', '.join(found_tech)
        
        # Extract time references
        time_pattern = r'\b(today|tomorrow|yesterday|morning|evening|night|now|later)\b'
        time_refs = re.findall(time_pattern, text, re.IGNORECASE)
        if time_refs:
            entities['time_references'] = ', '.join(time_refs)
        
        return entities
    
    def _determine_context(self, text: str) -> str:
        """Determine the context type of the conversation."""
        context_scores = {}
        for context, keywords in self.context_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                context_scores[context] = score
        
        if context_scores:
            return max(context_scores, key=context_scores.get)
        return 'general'
    
    def _detect_sarcasm(self, text: str) -> bool:
        """Detect if the user is being sarcastic."""
        # Simple sarcasm detection based on keywords and patterns
        sarcasm_score = sum(1 for indicator in self.sarcasm_indicators if indicator in text)
        
        # Check for contradictory statements (simple heuristic)
        positive_words = ['good', 'great', 'awesome', 'wonderful']
        negative_words = ['bad', 'terrible', 'awful', 'hate']
        
        has_positive = any(word in text for word in positive_words)
        has_negative = any(word in text for word in negative_words)
        
        # If both positive and negative words present, might be sarcasm
        contradiction = has_positive and has_negative
        
        return sarcasm_score > 0 or contradiction
    
    def _identify_implicit_request(self, text: str, intent: str, emotion: str) -> Optional[str]:
        """Identify implicit requests that aren't explicitly stated."""
        if emotion == 'frustrated' and 'broken' in text:
            return 'help_with_problem'
        
        if emotion == 'curious' and intent == 'statement':
            return 'provide_information'
        
        if emotion == 'grateful':
            return 'acknowledge_appreciation'
        
        if 'tired' in text or 'exhausted' in text:
            return 'suggest_break'
        
        return None
    
    def _calculate_confidence(self, intent: str, emotion: str, entities: Dict[str, str]) -> float:
        """Calculate confidence score for the understanding."""
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on clarity of intent
        if intent != 'general':
            confidence += 0.2
        
        # Increase confidence if emotion detected
        if emotion != 'neutral':
            confidence += 0.1
        
        # Increase confidence if entities found
        if entities:
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def generate_understanding_summary(self, result: UnderstandingResult) -> str:
        """Generate a human-readable summary of the understanding."""
        summary_parts = []
        
        if result.intent != 'general':
            summary_parts.append(f"Intent: {result.intent}")
        
        if result.emotion != 'neutral':
            summary_parts.append(f"Emotion: {result.emotion}")
        
        if result.context_type != 'general':
            summary_parts.append(f"Context: {result.context_type}")
        
        if result.sarcasm_detected:
            summary_parts.append("Sarcasm detected")
        
        if result.implicit_request:
            summary_parts.append(f"Implicit request: {result.implicit_request}")
        
        if result.entities:
            entity_list = [f"{k}: {v}" for k, v in result.entities.items()]
            summary_parts.append(f"Entities: {', '.join(entity_list)}")
        
        return " | ".join(summary_parts) if summary_parts else "General conversation"

# Global instance for use across the system
advanced_understanding = AdvancedUnderstanding()
