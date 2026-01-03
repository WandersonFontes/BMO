import operator
from typing import Annotated, TypedDict, Dict, Any, Union
from uuid import uuid4, UUID
from langgraph.graph import StateGraph, END

# ... imports ...
from ..agents.schemas import ExecutionPlan, AgentResponse, A2AMessage, AgentState
from ..agents.researcher import ResearcherAgent
from ..agents.writer import WriterAgent
from ..agents.coder import CoderAgent
from ..agents.critic import CriticAgent
from .planner import Planner

# Registry of available agents
agents_map = {
    "researcher": ResearcherAgent(),
    "writer": WriterAgent(),
    "coder": CoderAgent(),
    "critic": CriticAgent()
}

class Supervisor:
    def __init__(self):
        self.planner = Planner()
        self.workflow = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(AgentState)

        # Define nodes
        workflow.add_node("supervisor", self.supervisor_logic)
        workflow.add_node("agent_executor", self.execute_agent)
        workflow.add_node("critic", self.execute_critic)

        # Define edges
        workflow.set_entry_point("supervisor")
        
        workflow.add_conditional_edges(
            "supervisor",
            self.route_next,
            {
                "execute": "agent_executor",
                "finish": END
            }
        )
        
        workflow.add_conditional_edges(
             "agent_executor",
             self.check_review,
             {
                 "review": "critic",
                 "next": "supervisor"
             }
        )
        
        # Critic always goes back to Supervisor to decide next step (Next or Retry)
        workflow.add_edge("critic", "supervisor")
        
        return workflow.compile()

    def check_review(self, state: AgentState):
        plan = state["plan"]
        idx = state["current_step"]
        
        # If we have completed all steps, we shouldn't be here, but just in case:
        if idx >= len(plan.steps):
            return "next" # This goes to supervisor, which sees idx >= len and finishes

        step = plan.steps[idx]
        
        # Check if step requires review
        # Default True if not present to be safe
        requires_review = getattr(step, 'requires_review', True)
        
        if requires_review:
            return "review"
        
        # If no review, we manually advance the step here or let supervisor do it?
        # Supervisor routes based on current_step.
        # If we go back to supervisor without incrementing, it will execute same step again!
        # Ideally, we should increment step here if skipping review.
        return "next"

    def supervisor_logic(self, state: AgentState):
        return {} 

    def route_next(self, state: AgentState):
        plan = state["plan"]
        idx = state["current_step"]
        
        if idx >= len(plan.steps):
            return "finish"
        
        return "execute"

    async def execute_agent(self, state: AgentState):
        plan = state["plan"]
        idx = state["current_step"]
        step = plan.steps[idx]
    async def execute_agent(self, state: AgentState):
        plan = state["plan"]
        idx = state["current_step"]
        step = plan.steps[idx]
    async def execute_agent(self, state: AgentState):
        plan = state["plan"]
        idx = state["current_step"]
        step = plan.steps[idx]
        retry_idx = state.get('retry_count', 0)
        feedback = state.get("critic_feedback")
        
        # User Feedback: Visibility
        # print(f"🔄 Executing Step {idx+1}/{len(plan.steps)}: {step.agent} (Attempt {retry_idx + 1})")

        agent = agents_map[step.agent]
        
        payload = {"instruction": step.instruction}
        if feedback:
            payload["feedback"] = feedback
            payload["instruction"] += f"\n\n[CRITICAL FEEDBACK FROM PREVIOUS ATTEMPT]: {feedback}"

        msg = A2AMessage(
            correlation_id=state["correlation_id"],
            from_agent="supervisor",
            to_agent=step.agent,
            intent=step.intent,
            payload=payload
        )
        
        response = await agent.run(msg)
        
        # Check if we are skipping review
        requires_review = getattr(step, 'requires_review', True)
        
        if not requires_review:
             step_id = step.step_id if hasattr(step, 'step_id') else f"step_{idx}"
             return {
                "step_results": {step_id: response},
                "current_step": idx + 1, # Move to next step immediately
                "retry_count": 0,
                "critic_feedback": None,
                "last_agent_output": response 
             }
        
        return {
            "last_agent_output": response,
        }

    async def execute_critic(self, state: AgentState):
        last_response = state["last_agent_output"]
        plan = state["plan"]
        idx = state["current_step"]
        step = plan.steps[idx]
        
        # print(f"⚖️  Critic Reviewing Step {idx+1}...")
        critic = agents_map["critic"]
        
        msg = A2AMessage(
            correlation_id=state["correlation_id"],
            from_agent="supervisor",
            to_agent="critic",
            intent="review",
            payload={
                "target_output": str(last_response.output),
                "instruction_was": step.instruction
            },
            constraints={"criteria": "Check if output matches instruction and is high quality."}
        )
        
        critic_response = await critic.run(msg)
        
        # If approved, save result
        if critic_response.status == "success": # Approved
             step_id = step.step_id if hasattr(step, 'step_id') else f"step_{idx}"
             # print(f"✅ Step {idx+1} Approved.")
             return {
                 "step_results": {step_id: last_response},
                 "current_step": idx + 1, # Move to next step
                 "retry_count": 0, # Reset retries for next step
                 "critic_feedback": None # Reset feedback
             }
        else:
             # If needs rework, we check retry count
             current_retries = state.get("retry_count", 0)
             feedback = critic_response.output.get("feedback", "No specific feedback provided.")
             
             if current_retries >= 3: # MAX_RETRIES = 3
                # print(f"⚠️  Max retries ({current_retries}) reached for Step {idx+1}. Forcing approval.")
                # Force move forward to avoid infinite loop
                step_id = step.step_id if hasattr(step, 'step_id') else f"step_{idx}"
                 
                # Augment output with warning
                last_response.output["warning"] = "Critic validation failed after max retries. Moving forward."
                last_response.notes = f"Critic Feedback: {feedback}"
                 
                return {
                    "step_results": {step_id: last_response},
                    "current_step": idx + 1,
                    "retry_count": 0,
                    "critic_feedback": None
                }
             
             # Otherwise, loop back for retry
             # print(f"❌ Step {idx+1} Rejected. Retrying...")
             return {
                "retry_count": current_retries + 1,
                "critic_feedback": feedback
            }

    async def ainvoke(self, user_input: str):
        from uuid import uuid4
        plan = await self.planner.plan(user_input)
        
        initial_state: AgentState = {
            "plan": plan,
            "step_results": {},
            "current_step": 0,
            "correlation_id": uuid4(),
            "last_agent_output": None,
            "retry_count": 0
        }
        
        final_state = await self.workflow.ainvoke(initial_state)
        return final_state
