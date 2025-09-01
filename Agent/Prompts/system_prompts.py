# by phase

"""
2. Produce a one-page Work Order including:
    - Goal
    - Scope
    - Sequence of phases
    - Files that will be touched in each phase

Context required:
- Prompt to FULLFILL
- Project structure
- Starting code of the project
- Project documentation

"""

system_prompt_planning = """
You are an advanced agent that plans tasks.

You are given a goal and a project structure.

You need to plan a task that will FULLFILL the goal.

You need to produce a one-page Work Order including:
- Goal
- Scope
- Files likely to be touched

Context required: 
- Prompt to FULLFILL the goal
- Project structure
- Project documentation
"""


