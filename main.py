import os
from typing import TypedDict, List, Optional
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv

load_dotenv()

class Plan(BaseModel):
    blog_title: str = Field(description="The catchy title of the blog post")
    sections: List[str] = Field(description="List of section headings and brief bullet points to cover")

class Review(BaseModel):
    is_approved: bool = Field(description="True if the draft accurately follows the outline, False otherwise")
    feedback: str = Field(description="Actionable feedback on what needs to be fixed if rejected")



# Defining state
class State(TypedDict):
    topic: str
    audience: str
    plan: Optional[Plan]
    draft: str
    feedback: str
    is_approved: bool
    iterations: int


llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7) 


def plan_blog(state: State) -> dict:
    pass

def draft_blog(state: State) -> dict:
    pass

def evaluate_blog(state: State) -> dict:
    pass

def optimize_blog(state: State) -> dict:
    pass

def route_evaluation(state: State) -> str:
    pass


g = StateGraph(State)

g.add_node("plan_blog", plan_blog)
g.add_node("draft_blog", draft_blog)
g.add_node("evaluate_blog", evaluate_blog)
g.add_node("optimize_blog", optimize_blog)

g.add_edge(START, "plan_blog")
g.add_edge("plan_blog", "draft_blog")
g.add_edge("draft_blog", "evaluate_blog")

g.add_conditional_edges(
    "evaluate_blog", 
    route_evaluation, 
    {
        "approved": END,
        "needs_improvement": "optimize_blog"
    }
)

g.add_edge("optimize_blog", "evaluate_blog")

app = g.compile()


if __name__ == "__main__":
    print("Blog writing agent is on work ")
    
    topic_input = input("Enter the blog topic: ")
    audience_input = input("Enter the target audience: ")
    
    initial_state = {
        "topic": topic_input,
        "audience": audience_input,
        "draft": "",
        "feedback": "",
        "is_approved": False,
        "iterations": 0
    }
    
   