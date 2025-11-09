from __future__ import annotations

from typing import Optional

from neo4j import Driver

from app.database.neo4j import (
    get_neo4j_driver,
    upsert_file,
    upsert_function,
    upsert_class,
    upsert_module,
    link_imports,
    link_calls,
    link_contains_file_function,
    link_contains_file_class,
    link_inherits,
)


def test_connection() -> bool:
    """Verify Neo4j connectivity by executing a simple RETURN 1."""
    driver: Driver = get_neo4j_driver()
    with driver.session() as session:
        res = session.run("RETURN 1 AS ok").single()
        return bool(res and res.get("ok") == 1)


def ensure_constraints_and_indexes() -> None:
    """Create id uniqueness constraints (which also create backing indexes)."""
    driver: Driver = get_neo4j_driver()
    stmts = [
        # Node ID unique constraints (indexes are created implicitly)
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:File) REQUIRE n.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Function) REQUIRE n.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Class) REQUIRE n.id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (n:Module) REQUIRE n.id IS UNIQUE",
    ]
    with driver.session() as session:
        for cypher in stmts:
            session.run(cypher)


# Re-export helper functions so callers can import a single client module
upsert_file_node = upsert_file
upsert_function_node = upsert_function
upsert_class_node = upsert_class
upsert_module_node = upsert_module

link_file_imports = link_imports
link_function_calls = link_calls
link_file_contains_function = link_contains_file_function
link_file_contains_class = link_contains_file_class
link_class_inherits = link_inherits
