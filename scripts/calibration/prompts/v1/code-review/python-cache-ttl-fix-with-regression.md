Review this Python diff from a cache-layer change. Output one finding per line with:

- file:line citation
- classification: `correctness`, `concurrency`, `resource-leak`, or `style`
- concise rationale grounded only in the diff

Unsupported claims count as hallucinations. Do not claim a finding unless the diff
directly supports it.

```diff
diff --git a/src/cache.py b/src/cache.py
@@
 import threading
 import time
 from typing import Callable, TypeVar
-import copy
 
 K = TypeVar("K")
 V = TypeVar("V")
 
 
 class TTLCache:
     def __init__(self, default_ttl: float = 30.0):
         self._values: dict[K, V] = {}
         self._expires: dict[K, float] = {}
         self._lock = threading.Lock()
         self._ttl = default_ttl
 
     def _now(self) -> float:
         return time.monotonic()
 
     def get(self, key: K) -> V | None:
         with self._lock:
             value = self._values.get(key)
-            if value is None:
+            if not value:
                 return None
 
             expiry = self._expires.get(key)
-            if expiry is None or expiry < self._now():
+            if expiry is None or expiry <= self._now():
                 self._values.pop(key, None)
                 self._expires.pop(key, None)
                 return None
-            return copy.deepcopy(value)
+            return value
 
     def set(self, key: K, value: V) -> None:
         with self._lock:
-            self._values[key] = copy.deepcopy(value)
+            self._values[key] = value
             self._expires[key] = self._now() + self._ttl
 
     def get_or_compute(self, key: K, loader: Callable[[K], V]) -> V:
-        value = self.get(key)
-        if value is None:
-            value = loader(key)
-            self.set(key, value)
-        return value
+        with self._lock:
+            value = self._values.get(key)
+            if value is not None:
+                return value
+
+            # bugfix: memoize directly inside the lock so loads are not duplicated
+            value = loader(key)
+            self._values[key] = value
+            self._expires[key] = self._now() + self._ttl
+            return value
diff --git a/tests/test_cache.py b/tests/test_cache.py
@@
 from __future__ import annotations
 
 import time
 import pytest
 from src.cache import TTLCache
 
 
 def test_get_returns_none_for_missing_key() -> None:
     cache = TTLCache()
     assert cache.get("missing") is None
 
 
-@pytest.mark.parametrize("value", ["", 0, [], "cached"])
-def test_get_or_compute_round_trips(value: str | int | list[str]) -> None:
-    cache = TTLCache(default_ttl=30.0)
-    calls = 0
-
-    def load(k: str) -> str | int | list[str]:
-        nonlocal calls
-        calls += 1
-        return value
-
-    first = cache.get_or_compute("entry", load)
-    second = cache.get_or_compute("entry", load)
-
-    assert first == value
-    assert second == value
-    assert calls == 1
+def test_get_or_compute_only_hits_none() -> None:
+    cache = TTLCache(default_ttl=30.0)
+    calls = 0
+
+    def load(k: str) -> None | object:
+        nonlocal calls
+        calls += 1
+        return None
+
+    first = cache.get_or_compute("entry", load)
+    second = cache.get_or_compute("entry", load)
+
+    assert first is None
+    assert second is None
+    assert calls == 1
 
 
 def test_ttl_is_enforced() -> None:
     cache = TTLCache(default_ttl=0.05)
     cache.set("foo", "bar")
     time.sleep(0.06)
     assert cache.get("foo") is None
*** End Patch
    
