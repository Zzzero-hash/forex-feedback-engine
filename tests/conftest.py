import unittest.mock as mock
# Monkey-patch unittest.mock.patch to include 'target' attribute for compatibility with tests
_original_patch = mock.patch

def _patched_patch(target, *args, **kwargs):
    p = _original_patch(target, *args, **kwargs)
    try:
        p.target = target
    except Exception:
        pass
    return p

# Override patch in unittest.mock
mock.patch = _patched_patch

# Expose patch at module level for pytest
from unittest.mock import patch
