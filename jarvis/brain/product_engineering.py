"""
Jarvis Product Engineering Knowledge Module
Comprehensive knowledge base for product development, architecture, and engineering best practices.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
import re


@dataclass
class EngineeringGuidance:
    topic: str
    best_practices: List[str]
    common_pitfalls: List[str]
    code_examples: Dict[str, str]
    resources: List[str]


class ProductEngineeringKnowledge:
    """Comprehensive product engineering knowledge base for Jarvis."""
    
    def __init__(self):
        self.knowledge_base = self._build_knowledge_base()
    
    def _build_knowledge_base(self) -> Dict[str, EngineeringGuidance]:
        """Build comprehensive knowledge base across product engineering domains."""
        
        knowledge = {
            "system_design": EngineeringGuidance(
                topic="System Design & Architecture",
                best_practices=[
                    "Start with requirements before architecture",
                    "Apply SOLID principles consistently",
                    "Design for scalability from day one",
                    "Implement proper separation of concerns",
                    "Use design patterns appropriately",
                    "Consider security at every layer",
                    "Plan for monitoring and observability",
                    "Document architectural decisions"
                ],
                common_pitfalls=[
                    "Over-engineering simple problems",
                    "Ignoring non-functional requirements",
                    "Tight coupling between components",
                    "No clear data flow architecture",
                    "Missing error handling strategies",
                    "Insufficient testing strategy",
                    "No performance considerations"
                ],
                code_examples={
                    "microservices": """
# Example: Well-structured microservice
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging

app = FastAPI(title="User Service")

class User(BaseModel):
    id: int
    name: str
    email: str

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    try:
        user = await get_user_from_db(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except Exception as e:
        logging.error(f"Error fetching user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
""",
                    "event_driven": """
# Example: Event-driven architecture
from dataclasses import dataclass
from typing import Callable, Dict
import asyncio

@dataclass
class Event:
    event_type: str
    data: dict
    timestamp: float

class EventBus:
    def __init__(self):
        self.handlers: Dict[str, List[Callable]] = {}
    
    def subscribe(self, event_type: str, handler: Callable):
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
    
    async def publish(self, event: Event):
        handlers = self.handlers.get(event.event_type, [])
        await asyncio.gather(*[handler(event) for handler in handlers])
"""
                },
                resources=[
                    "Design Patterns: Elements of Reusable Object-Oriented Software",
                    "Clean Architecture by Robert C. Martin",
                    "Building Microservices by Sam Newman",
                    "System Design Interview by Alex Xu"
                ]
            ),
            
            "product_management": EngineeringGuidance(
                topic="Product Management & Strategy",
                best_practices=[
                    "Define clear user personas and use cases",
                    "Create detailed PRDs with acceptance criteria",
                    "Prioritize features using frameworks like RICE or MoSCoW",
                    "Implement agile methodologies properly",
                    "Gather and act on user feedback systematically",
                    "Define measurable success metrics",
                    "Maintain a clear product roadmap",
                    "Balance technical debt with feature development"
                ],
                common_pitfalls=[
                    "Feature creep without clear priorities",
                    "Ignoring technical debt accumulation",
                    "No clear user value proposition",
                    "Poor stakeholder communication",
                    "Inconsistent sprint planning",
                    "No data-driven decision making",
                    "Skipping user research and validation"
                ],
                code_examples={
                    "feature_flag": """
# Example: Feature flag implementation
from functools import wraps
import os

def feature_flag(flag_name: str, default=False):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            is_enabled = os.getenv(f"FEATURE_{flag_name.upper()}", str(default)).lower() == 'true'
            if not is_enabled:
                return {"message": f"Feature {flag_name} is not enabled"}
            return func(*args, **kwargs)
        return wrapper
    return decorator

@app.get("/api/v2/advanced-analytics")
@feature_flag("advanced_analytics", default=False)
async def get_advanced_analytics():
    return {"data": "Advanced analytics data"}
"""
                },
                resources=[
                    "Inspired by Marty Cagan",
                    "The Lean Startup by Eric Ries",
                    "Hooked by Nir Eyal",
                    "Escaping the Build Trap by Melissa Perri"
                ]
            ),
            
            "devops_engineering": EngineeringGuidance(
                topic="DevOps & Infrastructure",
                best_practices=[
                    "Infrastructure as Code (IaC) with Terraform or CloudFormation",
                    "CI/CD pipelines with automated testing",
                    "Container orchestration with Kubernetes",
                    "Monitoring and logging with ELK stack or similar",
                    "Security scanning in CI/CD pipeline",
                    "Automated backup and disaster recovery",
                    "Zero-downtime deployment strategies",
                    "Performance monitoring and alerting"
                ],
                common_pitfalls=[
                    "Manual deployment processes",
                    "No automated testing in pipeline",
                    "Ignoring security in deployment",
                    "Poor monitoring and observability",
                    "No rollback strategies",
                    "Configuration management issues",
                    "Insufficient capacity planning"
                ],
                code_examples={
                    "dockerfile": """
# Example: Multi-stage Dockerfile for production
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

FROM node:18-alpine AS production
WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
""",
                    "github_actions": """
# Example: CI/CD Pipeline
name: CI/CD Pipeline
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm run test
      - run: npm run lint
      
  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to production
        run: echo "Deploying to production..."
"""
                },
                resources=[
                    "The Phoenix Project by Gene Kim",
                    "Accelerate by Nicole Forsgren",
                    "Site Reliability Engineering by Google",
                    "DevOps Handbook by Gene Kim"
                ]
            ),
            
            "software_quality": EngineeringGuidance(
                topic="Software Quality & Testing",
                best_practices=[
                    "Test-Driven Development (TDD)",
                    "Comprehensive unit testing with high coverage",
                    "Integration testing for component interactions",
                    "End-to-end testing for critical user flows",
                    "Code reviews and pair programming",
                    "Static code analysis and linting",
                    "Performance testing and optimization",
                    "Security testing and vulnerability scanning"
                ],
                common_pitfalls=[
                    "Insufficient test coverage",
                    "Testing only happy path scenarios",
                    "No automated testing in CI/CD",
                    "Ignoring performance testing",
                    "Manual testing only",
                    "No code review process",
                    "Skipping edge case testing"
                ],
                code_examples={
                    "pytest": """
# Example: Comprehensive test suite
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestUserAPI:
    def test_create_user_success(self):
        response = client.post("/users", json={
            "name": "John Doe",
            "email": "john@example.com"
        })
        assert response.status_code == 201
        assert response.json()["name"] == "John Doe"
    
    def test_create_user_duplicate_email(self):
        # Create user first
        client.post("/users", json={
            "name": "John Doe", 
            "email": "john@example.com"
        })
        
        # Try to create duplicate
        response = client.post("/users", json={
            "name": "Jane Doe",
            "email": "john@example.com"
        })
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    @pytest.mark.parametrize("invalid_email", [
        "invalid-email",
        "",
        None
    ])
    def test_create_user_invalid_email(self, invalid_email):
        response = client.post("/users", json={
            "name": "John Doe",
            "email": invalid_email
        })
        assert response.status_code == 422
"""
                },
                resources=[
                    "Clean Code by Robert C. Martin",
                    "The Pragmatic Programmer by Andy Hunt",
                    "Working Effectively with Legacy Code by Michael Feathers",
                    "Software Testing by Ron Patton"
                ]
            )
        }
        
        return knowledge
    
    def get_guidance(self, topic: str) -> Optional[EngineeringGuidance]:
        """Get engineering guidance for a specific topic."""
        return self.knowledge_base.get(topic.lower())
    
    def search_topics(self, query: str) -> List[str]:
        """Search for relevant topics based on query."""
        query_lower = query.lower()
        relevant_topics = []
        
        for topic, guidance in self.knowledge_base.items():
            # Check topic name
            if query_lower in topic.lower():
                relevant_topics.append(topic)
                continue
            
            # Check in best practices
            if any(query_lower in practice.lower() for practice in guidance.best_practices):
                relevant_topics.append(topic)
                continue
            
            # Check in common pitfalls
            if any(query_lower in pitfall.lower() for pitfall in guidance.common_pitfalls):
                relevant_topics.append(topic)
                continue
        
        return relevant_topics
    
    def get_best_practices(self, topic: str) -> List[str]:
        """Get best practices for a specific topic."""
        guidance = self.get_guidance(topic)
        return guidance.best_practices if guidance else []
    
    def get_common_pitfalls(self, topic: str) -> List[str]:
        """Get common pitfalls for a specific topic."""
        guidance = self.get_guidance(topic)
        return guidance.common_pitfalls if guidance else []
    
    def get_code_examples(self, topic: str) -> Dict[str, str]:
        """Get code examples for a specific topic."""
        guidance = self.get_guidance(topic)
        return guidance.code_examples if guidance else {}
    
    def get_resources(self, topic: str) -> List[str]:
        """Get learning resources for a specific topic."""
        guidance = self.get_guidance(topic)
        return guidance.resources if guidance else []


# Singleton instance for use across the application
product_engineering = ProductEngineeringKnowledge()
