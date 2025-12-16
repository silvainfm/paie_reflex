# Module Import Fix

## Issue
```
ModuleNotFoundError: Module paie_reflex.paie_reflex not found.
Ensure app_name='paie_reflex' in rxconfig.py matches your folder structure.
```

## Root Cause
Files within the `paie_reflex/` package were using **absolute imports** like:
```python
from paie_reflex.services.data_mgt import DataManager
```

When Reflex loaded the app, it tried to import `paie_reflex.paie_reflex.services.data_mgt` (double nesting), causing the error.

## Solution
Changed all absolute imports to **relative imports**:

### For files in package root (state.py)
```python
# Before
from paie_reflex.services.auth import AuthManager

# After
from .services.auth import AuthManager
```

### For files in subdirectories (pages/, components/)
```python
# Before
from paie_reflex.services.data_mgt import DataManager

# After
from ..services.data_mgt import DataManager
```

## Files Modified

1. **paie_reflex/__init__.py**
   - Changed `from paie_reflex.services.data_mgt` → `from .services.data_mgt`

2. **paie_reflex/state.py**
   - Removed sys.path hack
   - Changed `from paie_reflex.services.auth` → `from .services.auth`
   - Changed `from paie_reflex.services.data_mgt` → `from ..services.data_mgt` (in methods)

3. **paie_reflex/pages/** (all files)
   - Changed `from paie_reflex.services.*` → `from ..services.*`
   - Files: validation.py, import_page.py, config.py

4. **paie_reflex/services/** (internal imports)
   - Changed `from paie_reflex.services.*` → `from ..services.*`
   - Files: scheduler.py, import_export.py, edge_case_agent.py

## Verification

```bash
# Test imports
uv run python -c "from paie_reflex import app; print('✓ App imports successful')"
# Result: ✓ App imports successful

# Initialize app
reflex init
# Result: Success: Initialized paie_reflex

# Run app
reflex run
```

## Key Takeaway

**Rule**: Files inside a Python package should use **relative imports** (`.` or `..`), not absolute imports with the package name.

- **Absolute imports** (`from package.module`) are for importing FROM OUTSIDE the package
- **Relative imports** (`from .module` or `from ..module`) are for importing WITHIN the package
