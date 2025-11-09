from __future__ import annotations

from typing import Any, Dict, Optional

from neo4j import GraphDatabase, Driver

from app.core.config import settings

_driver: Optional[Driver] = None


def get_neo4j_driver() -> Driver:
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
        )
    return _driver


async def close_neo4j_driver() -> None:
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None


def _merge_node(tx, label: str, identity: Dict[str, Any], props: Dict[str, Any]):
    if props:
        keys = ", ".join([f"n.{k} = $props.{k}" for k in props.keys()])
        set_clause = f" SET {keys}"
    else:
        set_clause = ""
    match_keys = ", ".join([f"{k}: $id.{k}" for k in identity.keys()])
    cypher = f"MERGE (n:{label} {{{match_keys}}}){set_clause} RETURN n"
    return tx.run(cypher, id=identity, props=props).single()


def _merge_rel(
    tx,
    from_label: str,
    from_ident: Dict[str, Any],
    rel: str,
    to_label: str,
    to_ident: Dict[str, Any],
    rel_props: Optional[Dict[str, Any]] = None,
):
    rel_props = rel_props or {}
    rel_set = "" if not rel_props else " SET " + ", ".join([f"r.{k} = $rprops.{k}" for k in rel_props.keys()])
    from_match = ", ".join([f"{k}: $from.{k}" for k in from_ident.keys()])
    to_match = ", ".join([f"{k}: $to.{k}" for k in to_ident.keys()])
    cypher = (
        f"MERGE (a:{from_label} {{{from_match}}}) "
        f"MERGE (b:{to_label} {{{to_match}}}) "
        f"MERGE (a)-[r:{rel}]->(b)"  # idempotent
        f"{rel_set} RETURN r"
    )
    return tx.run(cypher, **{"from": from_ident, "to": to_ident, "rprops": rel_props}).single()


# Node helpers
def upsert_file(
    id: str,
    path: str,
    name: str,
    language: Optional[str] = None,
    lines_of_code: Optional[int] = None,
    complexity_score: Optional[float] = None,
) -> None:
    driver = get_neo4j_driver()
    props = {
        "id": id,
        "path": path,
        "name": name,
        "language": language,
        "lines_of_code": lines_of_code,
        "complexity_score": complexity_score,
    }
    with driver.session() as sess:
        sess.execute_write(
            _merge_node,
            "File",
            {"id": id},
            {k: v for k, v in props.items() if v is not None},
        )


def upsert_function(
    id: str,
    name: str,
    file_path: str,
    start_line: int,
    end_line: int,
    complexity: Optional[float] = None,
    parameters: Optional[list[str]] = None,
) -> None:
    driver = get_neo4j_driver()
    props = {
        "id": id,
        "name": name,
        "file_path": file_path,
        "start_line": start_line,
        "end_line": end_line,
        "complexity": complexity,
        "parameters": parameters or [],
    }
    with driver.session() as sess:
        sess.execute_write(_merge_node, "Function", {"id": id}, props)


def upsert_class(
    id: str,
    name: str,
    file_path: str,
    start_line: int,
    end_line: int,
    methods: Optional[list[str]] = None,
) -> None:
    driver = get_neo4j_driver()
    props = {
        "id": id,
        "name": name,
        "file_path": file_path,
        "start_line": start_line,
        "end_line": end_line,
        "methods": methods or [],
    }
    with driver.session() as sess:
        sess.execute_write(_merge_node, "Class", {"id": id}, props)


def upsert_module(id: str, name: str, file_path: str) -> None:
    driver = get_neo4j_driver()
    props = {"id": id, "name": name, "file_path": file_path}
    with driver.session() as sess:
        sess.execute_write(_merge_node, "Module", {"id": id}, props)


# Relationship helpers
def link_imports(file_from_id: str, file_to_id: str) -> None:
    driver = get_neo4j_driver()
    with driver.session() as sess:
        sess.execute_write(
            _merge_rel,
            "File",
            {"id": file_from_id},
            "IMPORTS",
            "File",
            {"id": file_to_id},
        )


def link_calls(function_from_id: str, function_to_id: str) -> None:
    driver = get_neo4j_driver()
    with driver.session() as sess:
        sess.execute_write(
            _merge_rel,
            "Function",
            {"id": function_from_id},
            "CALLS",
            "Function",
            {"id": function_to_id},
        )


def link_contains_file_function(file_id: str, function_id: str) -> None:
    driver = get_neo4j_driver()
    with driver.session() as sess:
        sess.execute_write(
            _merge_rel,
            "File",
            {"id": file_id},
            "CONTAINS",
            "Function",
            {"id": function_id},
        )


def link_contains_file_class(file_id: str, class_id: str) -> None:
    driver = get_neo4j_driver()
    with driver.session() as sess:
        sess.execute_write(
            _merge_rel,
            "File",
            {"id": file_id},
            "CONTAINS",
            "Class",
            {"id": class_id},
        )


def link_inherits(class_child_id: str, class_parent_id: str) -> None:
    driver = get_neo4j_driver()
    with driver.session() as sess:
        sess.execute_write(
            _merge_rel,
            "Class",
            {"id": class_child_id},
            "INHERITS",
            "Class",
            {"id": class_parent_id},
        )
