# Indentation and Model Fixes

## Issues Fixed ✅

### 1. **Gemini Model Name** ✅
- **Old**: `"gemini-flash-latest"`
- **New**: `"models/gemini-2.0-flash-exp"`
- **Why**: Proper Gemini API model format

### 2. **Indentation Problems** ✅
Multiple improvements to code generation and insertion:

#### A. Cow Class Modifications
**Problem**: AI-generated code had inconsistent indentation when adding to `__init__` and methods

**Fix**:
```python
import textwrap

# Clean up indentation
raw_init = init_match.group(1).strip()
init_lines = raw_init.split('\n')
fixed_init_lines = []
for line in init_lines:
    if line.strip():
        # Remove existing indentation, add correct indentation (8 spaces)
        fixed_init_lines.append("        " + line.strip())
```

**Result**: Proper 8-space indentation for `__init__` content

#### B. Method Indentation
**Problem**: Methods added to classes had wrong indentation

**Fix**:
```python
# Use textwrap to dedent first
methods_dedented = textwrap.dedent(raw_methods)

# Then apply correct indentation:
# - def statements: 4 spaces (class method level)
# - docstrings: 8 spaces
# - method body: 8 spaces
```

**Result**: Proper Python class method formatting

#### C. Effect Application Code
**Problem**: Generated effect application had indentation issues

**Fix**:
```python
# Properly indented with 12 spaces (inside if statement)
effect_application_code += f"            if hasattr(target, 'apply_{effect}'):\n"
effect_application_code += f"                target.apply_{effect}({duration})\n"
```

**Result**: Correct nested indentation

#### D. Arena Loot Pool Code
**Problem**: Multi-line weapon pool code had mixed indentation

**Fix**:
```python
# Use explicit string with proper spacing (36 spaces for golden field section)
new_code = '''# Weapon pool for random drops
                                    weapons_pool = [
                                        Weapon(...),
                                        create_weapon(),
                                    ]'''
```

**Result**: Maintains Arena's existing indentation style

## Technical Details

### Indentation Strategy

1. **Strip all existing indentation**: `line.strip()`
2. **Add correct indentation for context**:
   - `__init__` content: 8 spaces
   - Method definitions: 4 spaces
   - Method body: 8 spaces
   - Nested code: 12+ spaces
3. **Use `textwrap.dedent()`** for AI responses to normalize first

### Model Configuration

**File**: `Agent/gemini_client.py`

```python
self.model = "models/gemini-2.0-flash-exp"
```

This uses:
- Latest Gemini 2.0 Flash (experimental)
- Proper model namespace format
- Best performance for code generation

## Testing

### Before Fixes
```python
# BAD - Mixed indentation
def apply_freeze(self, duration_ms: int):
self.is_frozen = True  # Wrong indent!
    self.freeze_end_time = now + duration_ms  # Also wrong!
```

### After Fixes
```python
# GOOD - Consistent indentation
    def apply_freeze(self, duration_ms: int):
        """Apply freeze effect to this character."""
        if self.is_dead():
            return
        now = pygame.time.get_ticks()
        self.is_frozen = True
        self.freeze_end_time = now + duration_ms
```

## Files Modified

1. ✅ `Agent/gemini_client.py` - Model name updated
2. ✅ `Agent/agent_main.py` - Indentation fixes in:
   - `_add_effects_to_cow()` - Init and method formatting
   - `_create_effect_projectile()` - Effect application code
   - `_add_weapon_to_loot_pool()` - Arena code formatting

## Verification

```bash
# Test model
python -c "from Agent.gemini_client import GeminiClient; \
           client = GeminiClient(); \
           print(f'Model: {client.model}')"

# Expected output:
# Model: models/gemini-2.0-flash-exp
```

## Impact

**Before**: Generated code would cause Python syntax errors due to indentation

**After**: 
- ✅ Generated code follows PEP 8
- ✅ Proper class method indentation
- ✅ Correct nesting levels
- ✅ Consistent spacing throughout

## Additional Improvements

### Safety Checks
Added `hasattr()` checks before calling effect methods:
```python
if hasattr(target, 'apply_freeze'):
    target.apply_freeze(duration, slow_percent)
```

This prevents errors if effect methods aren't defined.

### Docstrings
Added docstrings to generated methods:
```python
def apply_freeze(self, duration_ms: int):
    """Apply freeze effect to this character."""
    ...
```

## Summary

✅ **Model**: Now uses `models/gemini-2.0-flash-exp`
✅ **Indentation**: Consistent, PEP 8 compliant code generation
✅ **Safety**: Added hasattr checks
✅ **Documentation**: Generated code includes docstrings

**Ready to use!** The agent will now generate properly formatted code.
