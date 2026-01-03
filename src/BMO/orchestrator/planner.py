from ..agents.schemas import ExecutionPlan
from src.BMO.core.llm import get_llm_client
from src.BMO.config.settings import settings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

class Planner:
    def __init__(self):
        self.llm = get_llm_client(
            streaming=False 
        )
        self.parser = PydanticOutputParser(pydantic_object=ExecutionPlan)

    async def plan(self, user_prompt: str) -> ExecutionPlan:
        system_prompt = (
            "You are the Master Planner for BMO, an advanced orchestration system. "
            "Your objective is to decompose the User's Request into a logical, executable sequence of steps (a Plan) using specific specialized agents.\n\n"
            
            "### Available Agents & Capabilities\n"
            "1. **researcher**: Web search, data gathering, fact-checking, looking up documentation/APIs. (Output: Text/Data)\n"
            "2. **coder**: Writing executable code, refactoring, debugging, file operations, script generation. (Output: Code/Files)\n"
            "3. **writer**: Drafting content, summarizing data, translation, creative writing, formatting final answers, chitchat. (Output: Text)\n\n"
            
            "### Execution Rules\n"
            "1. **Output Format:** You must output **ONLY VALID JSON**. Do not use Markdown code blocks (```json). Do not add introductory text or explanations outside the JSON.\n"
            "2. **Dependency Management:** logical flow is critical. If Step 2 needs information from Step 1, list 'step_1' in Step 2's `depends_on` list.\n"
            "3. **Critic/Review:** Do NOT schedule a 'critic' agent. Verification is implicit. However, set `requires_review: true` for complex tasks (coding, research) and `false` for trivial tasks (greetings).\n"
            "4. **Agent Selection:**\n"
            "   - Use 'writer' for general conversation, greetings, or questions that don't need external tools.\n"
            "   - Use 'researcher' BEFORE 'coder' if the library/API is unknown.\n"
            "5. **Ambiguity:** If the user request is vague, schedule a 'writer' step to ask clarifying questions.\n\n"
            
            " Examples:\n"
            "User: \"hi\"\n"
            "Output: {{\"steps\": [{{\"step_id\": \"step_1\", \"agent\": \"writer\", \"intent\": \"reply\", \"instruction\": \"Reply to user greeting warmly.\", \"depends_on\": [], \"requires_review\": false}}], \"strategy_rationale\": \"Simple greeting handled by writer.\"}}\n\n"
            "User: \"Research python async\"\n"
            "Output: {{\"steps\": [{{\"step_id\": \"step_1\", \"agent\": \"researcher\", \"intent\": \"research\", \"instruction\": \"Research python async features.\", \"depends_on\": [], \"requires_review\": true}}], \"strategy_rationale\": \"Research task requiring verification.\"}}\n"
        )

        # Prepare prompt. Note: format_instructions are only needed for standard parser.
        # But we keep it in prompt to help LLM even with structured output.
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{input}"),
        ])

        if hasattr(self.llm, "with_structured_output"):
             chain = prompt | self.llm.with_structured_output(ExecutionPlan)
             
             try:
                 plan = await chain.ainvoke({"input": user_prompt})
             except Exception as e:
                 print(f"❌ Structured Output Error: {e}")
                 # Fallback to standard parsing
                 fallback_prompt = ChatPromptTemplate.from_messages([
                    ("system", system_prompt),
                    ("human", "{input}"),
                    ("human", "Format instructions:\n{format_instructions}")
                 ])
                 chain = fallback_prompt | self.llm
                 
                 print(f"⚠️  Falling back to manual parsing due to: {e}")
                 raw = await chain.ainvoke({
                     "input": user_prompt,
                     "format_instructions": self.parser.get_format_instructions()
                 })
                 plan = self.parser.parse(raw.content)
        else:
             fallback_prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", "{input}"),
                ("human", "Format instructions:\n{format_instructions}")
             ])
             chain = fallback_prompt | self.llm | self.parser
             plan = await chain.ainvoke({
                 "input": user_prompt,
                 "format_instructions": self.parser.get_format_instructions()
             })
             
        # Normalize plan if needed (structured output returns object, parser returns object)

        if not plan.steps:
             return ExecutionPlan(steps=[], strategy_rationale="No actionable steps found.")
        
        return plan
