"""
Quick test script to verify all weapons work
"""

import sys
import os
import importlib

# Ensure we're in the correct directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

# Test all weapons quickly
weapons = ["VortexSpinner", "RotorShot", "AetherRotator"]

print("=" * 60)
print("🔫 Testing All Weapons")
print("=" * 60)

all_passed = True

for weapon in weapons:
    print(f"\n🔍 Testing {weapon}...")
    try:
        # Try to import the weapon using proper importlib
        weapon_module_path = f"Game.Weapons.{weapon.lower()}"
        weapon_module = importlib.import_module(weapon_module_path)
        create_func = getattr(weapon_module, f"create_{weapon.lower()}")
        weapon_class = getattr(weapon_module, weapon)
        
        # Create instance
        instance = create_func()
        
        # Verify
        if isinstance(instance, weapon_class):
            print(f"   ✅ {weapon} - Import & Creation: PASSED")
            print(f"      Name: {instance.name}")
            print(f"      Damage: {instance.damage}")
        else:
            print(f"   ❌ {weapon} - Wrong instance type")
            all_passed = False
            
    except Exception as e:
        print(f"   ❌ {weapon} - FAILED: {e}")
        all_passed = False

print("\n" + "=" * 60)
if all_passed:
    print("✅ All weapons passed!")
    sys.exit(0)
else:
    print("❌ Some weapons failed")
    sys.exit(1)

