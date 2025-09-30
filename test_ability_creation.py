"""
Test script to demonstrate the ability creation workflow.

This shows how users can create new abilities using natural language.
"""

from Agent.agent_main import AgentMain


def test_ability_creation():
    """Test the ability creation workflow."""
    
    # Initialize the agent (using Gemini by default)
    print("Initializing agent...")
    agent = AgentMain(use_gemini=True)
    
    # Example ability descriptions
    example_abilities = [
        "Create a freeze ability that slows down enemies when they are hit. The freeze effect should last 3 seconds and reduce movement speed by 50%. It should work on any character.",
        
        "Create a shield ability that gives the character temporary invincibility for 2 seconds. While the shield is active, the character should have a visual indicator and take no damage.",
        
        "Create a speed boost ability that increases movement speed by 100% for 5 seconds. Any character should be able to use this.",
    ]
    
    # Let user choose or provide custom description
    print("\n" + "="*60)
    print("ABILITY CREATION TEST")
    print("="*60)
    print("\nExample abilities you can create:")
    for i, desc in enumerate(example_abilities, 1):
        print(f"{i}. {desc}")
    print(f"{len(example_abilities) + 1}. Custom ability (type your own)")
    
    choice = input("\nChoose an option (1-4) or press Enter to skip: ").strip()
    
    if not choice:
        print("Skipping ability creation test.")
        return
    
    try:
        choice_num = int(choice)
        if 1 <= choice_num <= len(example_abilities):
            ability_description = example_abilities[choice_num - 1]
        elif choice_num == len(example_abilities) + 1:
            ability_description = input("Describe your ability: ").strip()
            if not ability_description:
                print("No description provided. Exiting.")
                return
        else:
            print("Invalid choice.")
            return
    except ValueError:
        print("Invalid input.")
        return
    
    # Run the workflow
    print(f"\n🎯 Creating ability: {ability_description}\n")
    results = agent.create_ability_workflow(ability_description)
    
    # Display results
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    
    if results["success"]:
        print("✅ Ability created successfully!")
        print(f"\nPlan: {results['plan'].get('ability_name', 'Unknown')}")
        print(f"Tasks completed: {len(results['tasks'])}")
        
        # Show files created/modified
        all_files = []
        for task_result in results["tasks"]:
            all_files.extend(task_result.get("files_written", []))
        
        if all_files:
            print(f"\nFiles created/modified:")
            for file_path in all_files:
                print(f"  - {file_path}")
    else:
        print("❌ Ability creation failed")
        if results["errors"]:
            print("\nErrors:")
            for error in results["errors"]:
                print(f"  - {error}")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    test_ability_creation()
