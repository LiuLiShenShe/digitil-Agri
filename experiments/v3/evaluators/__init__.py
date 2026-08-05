"""v3 semantic evaluator package.

Importing this package registers the task_type adapters (memory_query ->
Query-CVSR, graph types -> object-graph CVSR).
"""

from register_adapters import register_adapters  # noqa: E402,F401

register_adapters()
