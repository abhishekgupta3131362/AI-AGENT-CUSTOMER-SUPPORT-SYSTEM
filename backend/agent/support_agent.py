import re
import json
from typing import Generator, Dict, Any, List, Optional
from backend.agent.prompts import SYSTEM_PROMPT
from backend.agent.tools import SupportTools
from backend.agent.sentiment import SentimentAnalyzer
from backend.llm.factory import LLMFactory
from backend.database.db import execute_db, query_db

class SupportAgent:
    def __init__(self):
        self.tools = SupportTools()
        self.sentiment_analyzer = SentimentAnalyzer()

    def _execute_tool(self, action_name: str, action_input: Dict[str, Any]) -> str:
        name = action_name.strip().lower()
        try:
            if "search" in name or "knowledge" in name:
                query = action_input.get("query", str(action_input))
                return self.tools.search_knowledge_base(query)
            elif "order" in name or "check" in name or "status" in name:
                order_id = action_input.get("order_id", str(action_input))
                return self.tools.check_order_status(order_id)
            elif "refund" in name or "return" in name:
                order_id = action_input.get("order_id", "")
                reason = action_input.get("reason", "Customer requested return")
                return self.tools.process_refund_return(order_id, reason)
            elif "ticket" in name:
                subject = action_input.get("subject", "General Support Inquiry")
                desc = action_input.get("description", str(action_input))
                priority = action_input.get("priority", "MEDIUM")
                return self.tools.create_support_ticket(subject, desc, priority)
            elif "escalat" in name or "human" in name:
                reason = action_input.get("reason", "Escalation requested")
                priority = action_input.get("priority", "HIGH")
                return self.tools.escalate_to_human(reason, priority)
            else:
                return f"Unrecognized tool '{action_name}'. Available tools: search_knowledge_base, check_order_status, process_refund_return, create_support_ticket, escalate_to_human."
        except Exception as e:
            return f"Error executing tool {action_name}: {str(e)}"

    def _parse_react_response(self, text: str) -> Dict[str, Any]:
        """Parses LLM output for Thought, Action, Action Input, or Final Answer."""
        result = {
            "thought": None,
            "action": None,
            "action_input": {},
            "final_answer": None
        }

        # Check for Final Answer
        fa_match = re.search(r"Final Answer:\s*(.*?)(?:\Z)", text, re.DOTALL | re.IGNORECASE)
        if fa_match:
            result["final_answer"] = fa_match.group(1).strip()

        # Check for Thought
        th_match = re.search(r"Thought:\s*(.*?)(?=\nAction:|\nFinal Answer:|\Z)", text, re.DOTALL | re.IGNORECASE)
        if th_match:
            result["thought"] = th_match.group(1).strip()

        # Check for Action & Action Input
        act_match = re.search(r"Action:\s*([a-zA-Z0-9_]+)", text, re.IGNORECASE)
        if act_match and not result["final_answer"]:
            result["action"] = act_match.group(1).strip()

            inp_match = re.search(r"Action Input:\s*(\{.*?\})", text, re.DOTALL)
            if inp_match:
                try:
                    result["action_input"] = json.loads(inp_match.group(1).strip())
                except Exception:
                    result["action_input"] = {"raw": inp_match.group(1).strip()}
            else:
                # Fallback: simple text input
                raw_inp = re.search(r"Action Input:\s*(.*?)(?:\n|\Z)", text)
                if raw_inp:
                    result["action_input"] = {"query": raw_inp.group(1).strip().strip('"').strip("'")}

        return result

    def run_agent_stream(self, message: str, session_id: str = "default_session", chat_history: Optional[List[Dict[str, str]]] = None) -> Generator[Dict[str, Any], None, None]:
        """
        Executes the ReAct reasoning loop with real-time event streaming.
        Emits dict events: {type: 'thought'|'tool_call'|'observation'|'final_answer', ...}
        """
        # Ensure session exists in database
        execute_db(
            "INSERT OR IGNORE INTO chat_sessions (session_id, customer_id, customer_name) VALUES (?, 'guest', 'Valued Customer')",
            (session_id,)
        )

        # 1. Analyze Customer Sentiment & Frustration
        sentiment = self.sentiment_analyzer.analyze(message)
        yield {
            "type": "sentiment",
            "score": sentiment["score"],
            "label": sentiment["label"],
            "is_frustrated": sentiment["is_frustrated"],
            "is_urgent": sentiment["is_urgent"]
        }

        # Update session sentiment
        execute_db(
            "UPDATE chat_sessions SET sentiment_score = ?, sentiment_label = ?, updated_at = CURRENT_TIMESTAMP WHERE session_id = ?",
            (sentiment["score"], sentiment["label"], session_id)
        )

        # Save user message to database
        execute_db(
            "INSERT INTO chat_messages (session_id, role, content, sentiment_score) VALUES (?, 'user', ?, ?)",
            (session_id, message, sentiment["score"])
        )

        # Check for Human Takeover
        session_row = query_db("SELECT is_human_takeover, active_human_agent FROM chat_sessions WHERE session_id = ?", (session_id,), one=True)
        if session_row and session_row["is_human_takeover"]:
            agent_name = session_row["active_human_agent"] or "Human Support Specialist"
            yield {
                "type": "final_answer",
                "content": f"[{agent_name} is actively connected to this chat]. Your message has been routed to the representative."
            }
            return

        llm = LLMFactory.get_provider()
        
        # Build prompt with tool definitions and history
        prompt_context = f"{self.tools.get_tool_definitions()}\n\n"
        if sentiment["is_frustrated"] or sentiment["is_urgent"]:
            prompt_context += f"NOTE: High customer frustration or urgency detected ({sentiment['label']}, score: {sentiment['score']}). Prioritize empathy, apologize for the inconvenience, and invoke escalate_to_human if appropriate.\n\n"

        if chat_history:
            prompt_context += "Previous Conversation:\n"
            for turn in chat_history[-4:]:
                prompt_context += f"{turn.get('role', 'user')}: {turn.get('content', '')}\n"
            prompt_context += "\n"

        prompt_context += f"Customer: {message}\n"
        current_prompt = prompt_context
        
        max_iterations = 4
        iterations = 0
        final_answer = ""
        tool_activities = []

        while iterations < max_iterations:
            iterations += 1
            llm_output = llm.generate(current_prompt, system_prompt=SYSTEM_PROMPT)
            parsed = self._parse_react_response(llm_output)

            # 1. Thought Event
            if parsed.get("thought"):
                yield {"type": "thought", "content": parsed["thought"]}

            # 2. Final Answer Event
            if parsed.get("final_answer"):
                final_answer = parsed["final_answer"]
                yield {"type": "final_answer", "content": final_answer}
                break

            # 3. Tool Invocation Event
            action = parsed.get("action")
            action_input = parsed.get("action_input", {})
            if action:
                yield {
                    "type": "tool_call",
                    "tool": action,
                    "input": action_input
                }
                
                # Execute tool
                observation = self._execute_tool(action, action_input)
                tool_activities.append({"tool": action, "input": action_input, "observation": observation})

                yield {
                    "type": "observation",
                    "tool": action,
                    "content": observation
                }

                # Append to current prompt for next ReAct cycle
                current_prompt += f"\nThought: {parsed.get('thought', 'Executed tool.')}\nAction: {action}\nAction Input: {json.dumps(action_input)}\nObservation: {observation}\n"
            else:
                # If neither action nor final answer was parsed, output raw text
                final_answer = llm_output.strip()
                yield {"type": "final_answer", "content": final_answer}
                break

        if not final_answer:
            final_answer = "I have processed your request. Please let me know if you need any additional assistance!"
            yield {"type": "final_answer", "content": final_answer}

        # Save assistant message to database
        execute_db(
            "INSERT INTO chat_messages (session_id, role, content, tool_calls) VALUES (?, 'assistant', ?, ?)",
            (session_id, final_answer, json.dumps(tool_activities) if tool_activities else None)
        )

    def run_agent(self, message: str, session_id: str = "default_session", chat_history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """Synchronous wrapper for agent execution."""
        events = list(self.run_agent_stream(message, session_id, chat_history))
        thoughts = [e["content"] for e in events if e["type"] == "thought"]
        tool_calls = [e for e in events if e["type"] == "tool_call"]
        observations = [e["content"] for e in events if e["type"] == "observation"]
        final_answer = next((e["content"] for e in reversed(events) if e["type"] == "final_answer"), "")

        return {
            "session_id": session_id,
            "thoughts": thoughts,
            "tool_calls": tool_calls,
            "observations": observations,
            "response": final_answer,
            "all_events": events
        }
