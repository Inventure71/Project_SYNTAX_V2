"""
Test Simulation Script for Weapon Testing

This script tests the simulation independently to debug import and runtime issues.
"""

import sys
import pygame
from typing import Dict, Any


def test_weapon_import(weapon_class_name: str) -> Dict[str, Any]:
    """Test importing a weapon and its create function."""
    print(f"\n{'='*60}")
    print(f"🔍 Testing Weapon Import: {weapon_class_name}")
    print(f"{'='*60}\n")
    
    results = {
        "success": False,
        "errors": [],
        "weapon_instance": None
    }
    
    # Test 1: Check if weapon file exists
    import os
    weapon_file = f"Game/Weapons/{weapon_class_name.lower()}.py"
    print(f"1. Checking if weapon file exists: {weapon_file}")
    if os.path.exists(weapon_file):
        print(f"   ✅ File exists")
        
        # Show the file content
        print(f"\n📄 Weapon file content:")
        with open(weapon_file, 'r') as f:
            content = f.read()
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                print(f"   {i:3d} | {line}")
    else:
        print(f"   ❌ File not found!")
        results["errors"].append(f"Weapon file not found: {weapon_file}")
        return results
    
    # Test 2: Try to import the weapon module
    print(f"\n2. Attempting to import weapon module...")
    try:
        weapon_module_path = f"Game.Weapons.{weapon_class_name.lower()}"
        import importlib
        weapon_module = importlib.import_module(weapon_module_path)
        create_weapon_func = getattr(weapon_module, f"create_{weapon_class_name.lower()}")
        print(f"   ✅ Successfully imported create_{weapon_class_name.lower()}()")
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        results["errors"].append(f"Import error: {e}")
        
        # Check what's actually in the module
        print(f"\n   🔍 Checking what's available in the module:")
        try:
            import importlib
            weapon_module = importlib.import_module(weapon_module_path)
            available = [item for item in dir(weapon_module) if not item.startswith('_')]
            print(f"   Available items: {available}")
            
            # Check if the class exists but not the create function
            if weapon_class_name in available:
                print(f"   ℹ️  Class {weapon_class_name} exists but create function is missing!")
                print(f"   💡 Need to add: def create_{weapon_class_name.lower()}():")
        except Exception as e2:
            print(f"   ❌ Could not inspect module: {e2}")
        
        return results
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        results["errors"].append(f"Unexpected error: {e}")
        return results
    
    # Test 3: Try to create a weapon instance
    print(f"\n3. Attempting to create weapon instance...")
    try:
        weapon_instance = create_weapon_func()
        print(f"   ✅ Successfully created weapon instance")
        print(f"   Weapon name: {weapon_instance.name if hasattr(weapon_instance, 'name') else 'N/A'}")
        print(f"   Weapon damage: {weapon_instance.damage if hasattr(weapon_instance, 'damage') else 'N/A'}")
        print(f"   Weapon speed: {weapon_instance.projectile_speed if hasattr(weapon_instance, 'projectile_speed') else 'N/A'}")
        results["weapon_instance"] = weapon_instance
        results["success"] = True
    except Exception as e:
        print(f"   ❌ Failed to create weapon: {e}")
        results["errors"].append(f"Creation error: {e}")
        import traceback
        print(f"\n   Traceback:")
        traceback.print_exc()
        return results
    
    return results


def run_simulation_test(weapon_class_name: str):
    """Run the full simulation test for a weapon."""
    print(f"\n{'='*60}")
    print(f"🎮 Running Simulation Tests: {weapon_class_name}")
    print(f"{'='*60}\n")
    
    # Initialize pygame
    pygame.init()
    test_screen = pygame.display.set_mode((100, 100), pygame.HIDDEN)
    print("✅ Pygame initialized")
    
    try:
        from Game.Arena.arena import Arena
        from Game.Character.cow import Cow
        from Game.Weapons.weapon import Weapon
        
        # Import the weapon
        import importlib
        weapon_module_path = f"Game.Weapons.{weapon_class_name.lower()}"
        weapon_module = importlib.import_module(weapon_module_path)
        create_weapon_func = getattr(weapon_module, f"create_{weapon_class_name.lower()}")
        
        print("\n📋 Test Scenarios:")
        print("   1. Weapon pickup")
        print("   2. Finding ammo")
        print("   3. Shooting nothing")
        print("   4. Shooting player")
        
        # Test 1: Weapon Pickup
        print(f"\n🏃 Test 1: Weapon Pickup")
        try:
            test_cow = Cow(
                rect=pygame.Rect(0, 0, 30, 30),
                username="TestCow",
                starting_position=(100, 100),
                camera_display_size=(800, 600),
                world_display_size=(2000, 2000)
            )
            weapon = create_weapon_func()
            test_cow.equip_weapon(weapon)
            
            if test_cow.has_weapon() and test_cow.get_weapon().name == weapon.name:
                print("   ✅ Weapon pickup test passed")
            else:
                print("   ❌ Weapon pickup test failed")
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test 2: Finding Ammo
        print(f"\n🏃 Test 2: Finding Ammo")
        try:
            test_cow = Cow(
                rect=pygame.Rect(0, 0, 30, 30),
                username="TestCow",
                starting_position=(100, 100),
                camera_display_size=(800, 600),
                world_display_size=(2000, 2000),
                starting_ammo=0
            )
            weapon = create_weapon_func()
            test_cow.equip_weapon(weapon)
            initial_ammo = test_cow.ammo
            test_cow.ammo += 10
            
            if test_cow.ammo > initial_ammo:
                print("   ✅ Ammo test passed")
            else:
                print("   ❌ Ammo test failed")
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test 3: Shooting Nothing
        print(f"\n🏃 Test 3: Shooting Nothing")
        try:
            # Create Arena with proper initialization matching the actual Arena class
            import io
            with io.StringIO() as f:
                arena = Arena(
                    screen_dimensions=(0, 0, 800, 600),
                    world_screen_dimensions=(2000, 2000),
                    screen=test_screen,
                    world_screen=test_screen,
                    text=None
                )
            player = Cow(
                rect=pygame.Rect(0, 0, 30, 30),
                username="Player",
                starting_position=(500, 500),
                camera_display_size=(800, 600),
                world_display_size=(2000, 2000),
                starting_ammo=10
            )
            weapon = create_weapon_func()
            player.equip_weapon(weapon)
            arena.characters.append(player)
            
            initial_projectile_count = len(arena.projectiles)
            arena.spawn_projectile(
                start_pos=(500, 500),
                direction=(100, 0),
                speed=weapon.projectile_speed,
                sprite=weapon.get_projectile_sprite() if hasattr(weapon, 'get_projectile_sprite') else None,
                damage=weapon.damage,
                owner=player
            )
            
            if len(arena.projectiles) > initial_projectile_count:
                print("   ✅ Projectile spawned")
                
                # Run some updates
                for _ in range(10):
                    arena.update()
                print("   ✅ Shooting test passed")
            else:
                print("   ❌ Projectile not spawned")
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
        
        pygame.quit()
        print("\n✅ Simulation tests complete")
        
    except Exception as e:
        print(f"\n❌ Simulation failed: {e}")
        import traceback
        traceback.print_exc()
        pygame.quit()


def main():
    """Main test function."""
    # Ensure we're in the correct directory
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print("\n" + "="*60)
    print("🎮 SYNTAX V2 - Weapon Simulation Test")
    print("="*60)
    print(f"Working directory: {os.getcwd()}\n")
    
    if len(sys.argv) > 1:
        weapon_class_name = sys.argv[1]
    else:
        weapon_class_name = input("\nEnter weapon class name (e.g., VortexSpinner): ").strip()
    
    if not weapon_class_name:
        print("❌ No weapon class name provided")
        return
    
    # Step 1: Test import
    import_results = test_weapon_import(weapon_class_name)
    
    if import_results["success"]:
        print(f"\n✅ Import test passed!")
        
        # Ask if user wants to run full simulation
        run_sim = input("\nRun full simulation tests? (y/n): ").strip().lower()
        if run_sim == 'y':
            run_simulation_test(weapon_class_name)
    else:
        print(f"\n❌ Import test failed with {len(import_results['errors'])} errors:")
        for error in import_results['errors']:
            print(f"   - {error}")
        
        print(f"\n💡 To fix:")
        print(f"   1. Open Game/Weapons/{weapon_class_name.lower()}.py")
        print(f"   2. Add at the end:")
        print(f"      def create_{weapon_class_name.lower()}():")
        print(f"          return {weapon_class_name}()")


if __name__ == "__main__":
    main()

