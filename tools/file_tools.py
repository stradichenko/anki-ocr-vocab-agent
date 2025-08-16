"""File operation tools for reading and writing files."""

import os
import base64
from smolagents import tool

@tool
def file_reader(path: str) -> str:
    """
    Read the contents of a local file. Returns text or BINARY_BASE64::<b64> for binary files.
    
    Args:
        path: Path to the file to read
        
    Returns:
        File content as string or base64-encoded binary with prefix
    """
    if not isinstance(path, str):
        raise RuntimeError("path must be a string.")
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")

    # Try to read as UTF-8 text first
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        # Binary file: return base64 encoded content with a prefix so callers know
        with open(path, "rb") as bf:
            b = bf.read()
        b64 = base64.b64encode(b).decode("ascii")
        return f"BINARY_BASE64::{b64}"
    except Exception as e:
        raise RuntimeError(f"Error reading file {path}: {e}")

@tool
def file_writer(path: str, content: str) -> str:
    """
    Write content to a local file. Accepts plain text or BINARY_BASE64::<b64> to write binary.
    
    Args:
        path: Path where the content should be written
        content: Content to write into the file. If writing binary, prefix with 'BINARY_BASE64::'
        
    Returns:
        Absolute path of the written file
    """
    if not isinstance(path, str) or not isinstance(content, str):
        raise RuntimeError("path and content must be strings.")
    # create directories if needed
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    if content.startswith("BINARY_BASE64::"):
        b64 = content.split("BINARY_BASE64::", 1)[1]
        try:
            data = base64.b64decode(b64)
        except Exception as e:
            raise RuntimeError(f"Invalid base64 content: {e}")
        with open(path, "wb") as bf:
            bf.write(data)
    else:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
    return os.path.abspath(path)
