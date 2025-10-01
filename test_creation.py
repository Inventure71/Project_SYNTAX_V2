"""
Test script for creating abilities and weapons using the AI agent.

This script supports:
- Creating weapons (simpler, just stats and sprites)
- Creating abilities (complex, with character effects)
- Backup/restore functionality
- Listing backups
"""

from Agent.agent_main import AgentMain


def main_menu():
    """Show main menu and handle user choice."""
    
    print("\n" + "="*60)
    print("🎮 SYNTAX V2 - AI CONTENT CREATOR")
    print("="*60)
    print("\n1. Create Weapon 🔫")
    print("2. Create Ability ⚡")
    print("3. List Backups 📦")
    print("4. Restore Backup ♻️")
    print("5. Exit")
    
    choice = input("\nChoose an option (1-5): ").strip()
    return choice


def create_weapon():
    """Weapon creation workflow."""
    print("\n" + "="*60)
    print("🔫 WEAPON CREATION")
    print("="*60)
    
    print("\nExample weapons:")
    print("1. A rainbow gun that does high damage but uses 3 ammo per shot")
    print("2. A fast laser gun with low damage but very fast projectiles")
    print("3. A shotgun that shoots multiple pellets")
    print("4. Custom weapon (describe your own)")
    
    choice = input("\nChoose (1-4) or press Enter to skip: ").strip()
    
    examples = [
        "A rainbow gun that does 25 damage but uses 3 ammo per shot and has rainbow-colored projectiles",
        "A laser gun with fast projectiles (speed 30) but only 5 damage per shot, uses 1 ammo",
        "A powerful shotgun that does 15 damage with slow projectiles (speed 12) but uses 2 ammo per shot",
    ]
    
    if choice == "1":
        description = examples[0]
    elif choice == "2":
        description = examples[1]
    elif choice == "3":
        description = examples[2]
    elif choice == "4":
        description = input("Describe your weapon: ").strip()
        if not description:
            print("No description provided.")
            return
    else:
        print("Skipping weapon creation.")
        return
    
    # Initialize agent
    print("\nInitializing agent...")
    print("(Request limit: 10 API calls before requiring authorization)\n")
    agent = AgentMain(use_gemini=True, max_requests_before_auth=10)
    
    # Create weapon
    print(f"\n🎯 Creating weapon: {description}\n")
    result = agent.create_weapon_workflow(description)
    
    # Display results
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    
    if result.get("success"):
        print("✅ Weapon created successfully!")
        print(f"\nWeapon Name: {result.get('weapon_name', 'N/A')}")
        print(f"Backup ID: {result.get('backup_id', 'N/A')}")
        
        if result.get("files_created"):
            print(f"\nFiles created:")
            for file_path in result["files_created"]:
                print(f"  - {file_path}")
        
        if "integration_example" in result:
            print(f"\n📖 Integration guide: {result['integration_example']}")
            print("\n⚠️  To use this weapon in the game, follow the instructions in the integration guide!")
    else:
        print("❌ Weapon creation failed")
        if result["errors"]:
            print("\nErrors:")
            for error in result["errors"]:
                print(f"  - {error}")
        
        if result.get("backup_id"):
            print(f"\n💡 You can restore the backup: {result['backup_id']}")
    
    print("\n" + "="*60)


def create_ability():
    """Ability creation workflow."""
    print("\n" + "="*60)
    print("⚡ ABILITY CREATION")
    print("="*60)
    
    print("\nExample abilities:")
    print("1. A freeze ability that slows enemies by 50% for 3 seconds")
    print("2. A shield that gives invincibility for 2 seconds")
    print("3. A speed boost that doubles movement for 5 seconds")
    print("4. Custom ability (describe your own)")
    
    choice = input("\nChoose (1-4) or press Enter to skip: ").strip()
    
    examples = [
        "Create a freeze ability that slows down enemies when they are hit. The freeze effect should last 3 seconds and reduce movement speed by 50%. It should work on any character.",
        "Create a shield ability that gives the character temporary invincibility for 2 seconds. While the shield is active, the character should have a visual indicator and take no damage.",
        "Create a speed boost ability that increases movement speed by 100% for 5 seconds. Any character should be able to use this.",
    ]
    
    if choice == "1":
        description = examples[0]
    elif choice == "2":
        description = examples[1]
    elif choice == "3":
        description = examples[2]
    elif choice == "4":
        description = input("Describe your ability: ").strip()
        if not description:
            print("No description provided.")
            return
    else:
        print("Skipping ability creation.")
        return
    
    # Initialize agent
    print("\nInitializing agent...")
    print("(Request limit: 10 API calls before requiring authorization)\n")
    agent = AgentMain(use_gemini=True, max_requests_before_auth=10)
    
    # Create ability
    print(f"\n🎯 Creating ability: {description}\n")
    result = agent.create_ability_workflow(description)
    
    # Display results
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    
    if result["success"]:
        print("✅ Ability created successfully!")
        print(f"\nBackup ID: {result['backup_id']}")
        print(f"Tasks completed: {len(result['tasks'])}")
        
        all_files = []
        for task_result in result["tasks"]:
            all_files.extend(task_result.get("files_written", []))
        
        if all_files:
            print(f"\nFiles created/modified:")
            for file_path in all_files:
                print(f"  - {file_path}")
    else:
        print("❌ Ability creation failed")
        if result["errors"]:
            print("\nErrors:")
            for error in result["errors"]:
                print(f"  - {error}")
        
        if result.get("backup_id"):
            print(f"\n💡 You can restore the backup: {result['backup_id']}")
    
    print("\n" + "="*60)


def list_backups():
    """List all available backups."""
    agent = AgentMain(use_gemini=True)
    agent.list_backups()


def restore_backup():
    """Restore from a backup."""
    agent = AgentMain(use_gemini=True)
    backups = agent.list_backups()
    
    if not backups:
        return
    
    print("\nEnter backup ID to restore (or press Enter for most recent):")
    backup_id = input("> ").strip()
    
    if not backup_id:
        backup_id = None  # Will use most recent
    
    confirm = input(f"\n⚠️  This will overwrite current files. Continue? (yes/no): ").strip().lower()
    
    if confirm in ['yes', 'y']:
        agent.restore_backup(backup_id)
    else:
        print("❌ Restore cancelled")


def main():
    """Main entry point."""
    while True:
        choice = main_menu()
        
        if choice == "1":
            create_weapon()
        elif choice == "2":
            create_ability()
        elif choice == "3":
            list_backups()
        elif choice == "4":
            restore_backup()
        elif choice == "5":
            print("\n👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice")


if __name__ == "__main__":
    main()
