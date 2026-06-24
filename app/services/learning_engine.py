"""
Learning Engine for Daily Practice.
Generates personalized study plans based on user history.
"""

from __future__ import annotations
from typing import Any

def generate_daily_plan(stats: dict) -> dict[str, Any]:
    """
    Generate a 15-25 min daily plan based on user stats.
    Returns:
      {
        "main_task": {"type": "writing", "title": "Independent Essay"},
        "drill": {"title": "Grammar Drill: Articles", "description": "Fixing common mistakes"},
        "vocab": ["abundant", "coincide", "distinct", "elaborate", "fluctuate"]
      }
    """
    total = stats.get("total_sessions", 0)
    
    if total < 3:
        # Default TOEFL 100 plan
        return {
            "main_task": {"type": "writing", "title": "Academic Discussion"},
            "drill": {"title": "Basic Grammar Drill", "description": "Subject-verb agreement"},
            "vocab": ["abundant", "coincide", "distinct", "elaborate", "fluctuate"]
        }
        
    # MVP logic: pick the skill with the lowest average score
    by_skill = stats.get("by_skill", {})
    lowest_skill = "writing"
    lowest_score = 30.0
    for skill, data in by_skill.items():
        if data["avg_score"] < lowest_score and data["sessions"] > 0:
            lowest_score = data["avg_score"]
            lowest_skill = skill
            
    # Map lowest skill to a main task
    task_map = {
        "writing": "Academic Discussion",
        "speaking": "Independent Speaking Task",
        "reading": "Reading Comprehension Passage",
        "listening": "Listening Conversation"
    }
    
    return {
        "main_task": {"type": lowest_skill, "title": task_map.get(lowest_skill, "Academic Discussion")},
        "drill": {"title": f"Targeted {lowest_skill.capitalize()} Drill", "description": "Based on your recent mistakes"},
        "vocab": ["paradigm", "empirical", "subsequent", "derive", "advocate"]
    }


def get_next_activity(stats: dict, current_step: int = 0) -> str:
    """
    Returns the next activity type based on progress in the daily plan.
    0 -> main_task
    1 -> drill
    2 -> vocab
    """
    if current_step == 0:
        total = stats.get("total_sessions", 0)
        if total < 3:
            return "writing"
        
        by_skill = stats.get("by_skill", {})
        lowest_skill = "writing"
        lowest_score = 30.0
        for skill, data in by_skill.items():
            if data["avg_score"] < lowest_score and data["sessions"] > 0:
                lowest_score = data["avg_score"]
                lowest_skill = skill
        return lowest_skill
    elif current_step == 1:
        return "drill"
    else:
        return "vocab"
