import os
import sys
import pkgutil

# 1. Allow Python to discover subpackages in both this directory (user, merchant)
#    and the official PyPI 'mcp' library in site-packages.
__path__ = pkgutil.extend_path(__path__, __name__)

_sp_mcp_dir = None
for _p in sys.path:
    if "site-packages" in _p:
        _cand = os.path.join(_p, "mcp")
        if os.path.isdir(_cand):
            _sp_mcp_dir = _cand
            if _cand not in __path__:
                __path__.append(_cand)
            break

# 2. Re-export official PyPI 'mcp' attributes into this module namespace
if _sp_mcp_dir:
    _init_file = os.path.join(_sp_mcp_dir, "__init__.py")
    if os.path.isfile(_init_file):
        with open(_init_file, "r", encoding="utf-8") as _f:
            _code = _f.read()
        exec(compile(_code, _init_file, "exec"), globals())
