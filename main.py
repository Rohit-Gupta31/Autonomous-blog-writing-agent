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


# Defining nodes

def plan_blog(state: State) -> dict:
    print("\nGenerating outline...")
    planner = llm.with_structured_output(Plan)
    
    messages = [
        SystemMessage(content="You are a senior technical planner. Create a structured outline for a blog post."),
        HumanMessage(content=f"""
        Topic: "{state['topic']}"
        Target Audience: "{state['audience']}"
        
        Please generate a comprehensive outline with a title and key sections to cover.
        """)
    ]
    
    plan = planner.invoke(messages)
    return {"plan": plan, "iterations": 0}

def draft_blog(state: State) -> dict:
    print("\nWriting initial draft...")
    plan = state["plan"]
    
    messages = [
        SystemMessage(content="You are an expert blog writer. Write a publish-ready blog post in Markdown based on the outline."),
        HumanMessage(content=f"""
        Topic: "{state['topic']}"
        Audience: "{state['audience']}"
        Outline Title: "{plan.blog_title}"
        
        Sections to cover:
        {plan.sections}
        
        Write the full blog post content following the exact outline.
        """)
    ]
        
    draft = llm.invoke(messages).content
    
    return {"draft": draft}

def evaluate_blog(state: State) -> dict:
    print("\nChecking draft quality...")
    reviewer = llm.with_structured_output(Review)
    
    messages = [
        SystemMessage(content="You are a strict editor. Review the draft and ensure it covers all sections from the outline."),
        HumanMessage(content=f"""
        Required Sections: 
        {state['plan'].sections}
        
        Draft to review:
        {state['draft']}
        
        Evaluate the draft and provide specific, actionable feedback if it fails to meet the requirements.
        """)
    ]
    
    review = reviewer.invoke(messages)
    
    if(review.is_approved == True):
        print("\nEditor approved the draft")
    else:
        print(f"Editor rejected the draft. Feedback: {review.feedback}")
        
    return {"is_approved": review.is_approved, "feedback": review.feedback}


def optimize_blog(state: State) -> dict:
    print("\nWorking on feedbak and rewriting the blog ...")
    
    messages = [
        SystemMessage(content="You are an expert editor who improves blog drafts based on specific feedback."),
        HumanMessage(content=f"""
        Improve the blog draft based on this feedback:
        "{state['feedback']}"
        
        Topic: "{state['topic']}"
        
        Original Draft:
        {state['draft']}
        
        Re-write the draft to incorporate the feedback perfectly while maintaining the original tone.
        """)
    ]
    
    response = llm.invoke(messages).content
    iteration = state.get("iterations", 0) + 1
    
    return {"draft": response, "iterations": iteration}


def route_evaluation(state: State) -> str:
    if state["is_approved"] or state["iterations"] >= 3: 
        return "approved"
    return "needs_improvement"



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
    print("Blog writing agnet is on work ")

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

    final_state = app.invoke(initial_state)

    print(f"Final draft\n")
    print(final_state["draft"])
  