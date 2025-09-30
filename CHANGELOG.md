# Changelog

## [Latest] - Current Version

### Fixed
- **Import Error**: Fixed `ImportError` for `read_lines` function
  - Changed from `read_lines` to `read_file` (correct function name)
  - Updated file reading logic in `agent_main.py`
  - Properly handles list output from `read_file`

### Added
- **Request Limiting System**: Safety feature to prevent excessive API calls
  - Default limit: 10 API requests before asking for authorization
  - Configurable via `max_requests_before_auth` parameter
  - User-friendly prompt to continue or stop
  - Counter resets after user approval
  - Prevents runaway API costs
  
  ```python
  # Usage
  agent = AgentMain(use_gemini=True, max_requests_before_auth=10)
  ```

### How Request Limiting Works

1. **Counter Tracking**: Each API call increments a counter
2. **Threshold Check**: When counter reaches limit, workflow pauses
3. **User Authorization**: Displays warning and asks "Continue? (yes/no)"
4. **Decision Handling**:
   - `yes` → Resets counter, continues workflow
   - `no` → Stops workflow gracefully, raises exception
5. **Protection**: Prevents infinite loops and unexpected costs

### Warning Display

When limit is reached:
```
⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️
⚠️  Request limit reached (10 requests)
⚠️  The agent has made multiple API calls.
⚠️  This may incur costs depending on your API plan.
⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️ ⚠️

👉 Continue with more requests? (yes/no):
```

### Updated Documentation
- Updated `ABILITY_CREATION_GUIDE.md` with request limiting section
- Updated `README.md` to mention safety feature
- Updated `test_ability_creation.py` to show configuration

### Technical Details

**Files Modified:**
- `Agent/agent_main.py`:
  - Added `max_requests_before_auth` parameter to `__init__`
  - Added `request_count` and `user_approved_continuation` tracking
  - Added `_check_request_limit()` method
  - Integrated limit checks before all API calls (plan, implement, verify)
  - Fixed import from `read_lines` to `read_file`
  - Added list-to-string conversion for file contents

**Integration Points:**
- `_plan_ability()`: Checks before planning API call
- `_implement_task()`: Checks before each task implementation
- `_verify_implementation()`: Checks before verification

**Error Handling:**
- Raises `Exception("User stopped workflow - request limit reached")` if user denies
- Gracefully caught by `create_ability_workflow()` and added to results["errors"]

## Benefits

1. **Cost Control**: Prevents unexpected API bills
2. **User Control**: Gives manual oversight of long operations
3. **Debugging**: Helps identify infinite loops or excessive iterations
4. **Transparency**: User always knows how many requests have been made
5. **Flexibility**: Configurable limit per workflow needs

## Usage Examples

```python
# Very cautious (testing)
agent = AgentMain(use_gemini=True, max_requests_before_auth=3)

# Default (balanced)
agent = AgentMain(use_gemini=True, max_requests_before_auth=10)

# Permissive (complex abilities)
agent = AgentMain(use_gemini=True, max_requests_before_auth=20)

# Almost unlimited (be careful!)
agent = AgentMain(use_gemini=True, max_requests_before_auth=100)
```

## Migration Guide

**Old Code:**
```python
agent = AgentMain(use_gemini=True)
```

**New Code (same behavior):**
```python
agent = AgentMain(use_gemini=True, max_requests_before_auth=10)
```

The default is 10 requests, so existing code works without changes.
