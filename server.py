# server.py - NEW ENTRY POINT
import sys
import os

# Fix for Python 3.13 + Pydantic v1
if sys.version_info >= (3, 13):
    # Set environment variable before importing anything
    os.environ["PYDANTIC_SKIP_VERSION_CHECK"] = "1"
    
    # Apply deep monkey patch
    import pydantic.typing
    
    # Store original
    _original_update_field_forward_refs = pydantic.typing.update_field_forward_refs
    
    def _patched_update_field_forward_refs(f, globalns=None, localns=None):
        # Extract recursive_guard from localns if present
        recursive_guard = localns.pop("recursive_guard", set()) if isinstance(localns, dict) else set()
        return _original_update_field_forward_refs(f, globalns, localns)
    
    pydantic.typing.update_field_forward_refs = _patched_update_field_forward_refs

# Now import and run your app
from app.main import app
import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)