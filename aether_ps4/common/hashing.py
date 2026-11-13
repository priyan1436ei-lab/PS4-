"""
Sony Name Identifier (NID) hashing algorithms.
On PS4, symbol names in dynamic modules are hashed into 64-bit integers
and encoded into 11-character base64 strings or hex digests.
"""

import hashlib
import base64

def compute_sha1_nid(symbol_name: str) -> int:
    """
    Computes a 64-bit integer NID from a symbol name using SHA-1 prefix.
    Used by Sony Orbis OS symbol tables.
    """
    digest = hashlib.sha1(symbol_name.encode("utf-8")).digest()
    # Take first 8 bytes in little-endian as u64 NID
    return int.from_bytes(digest[:8], byteorder="little")

def compute_nid_string(symbol_name: str) -> str:
    """
    Computes the 11-character base64-encoded NID representation (e.g., #D2YQ7G8zFk).
    """
    digest = hashlib.sha1(symbol_name.encode("utf-8")).digest()
    b64 = base64.b64encode(digest[:8]).decode("ascii").rstrip("=")
    # Replace standard URL chars with Sony NID format: + -> -, / -> _
    b64 = b64.replace("+", "-").replace("/", "_")
    return f"#{b64}"

