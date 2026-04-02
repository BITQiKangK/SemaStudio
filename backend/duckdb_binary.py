#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import subprocess
import time
import re
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
import tempfile
import os
import logging
import threading

import config

logger = logging.getLogger(__name__)

_DUCKDB_MUTEX = threading.Lock()


DUCKDB_BINARY = Path(__file__).resolve().parent / "db" / "duckdb"
DUCKDB_BIN_DIR = Path(__file__).resolve().parent / "db"

LOCAL_GLIBC_DIR = Path(__file__).resolve().parent / "db" / "glibc"
LOCAL_GLIBC_LIB = LOCAL_GLIBC_DIR / "lib"
LOCAL_LD = LOCAL_GLIBC_LIB / "ld-linux-x86-64.so.2"

_db_path: Optional[Path] = None
if config.DB_PATH is not None:
    try:
        _db_path = Path(config.DB_PATH).resolve()
        _db_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        _db_path = None


def _get_duckdb_cmd() -> List[str]:
    return [str(DUCKDB_BINARY)]


def _get_semantic_config_sql_without_extension() -> str:
    configs = []
    
    configs.append(f"SET llm_model = '{config.LLM_MODEL}';")
    configs.append(f"SET llm_url = '{config.LLM_URL}';")
    configs.append(f"SET llm_api_key = '{config.LLM_API_KEY}';")

    # configs.append(f"SET optimizer_url = '{config.OPTIMIZER_URL}';")
    # configs.append(f"SET optimizer_model = '{config.OPTIMIZER_MODEL}';")
    
    configs.append(f"SET enable_logging = {str(config.ENABLE_LOGGING).lower()};")
    configs.append(f"SET logging_level = '{config.LOGGING_LEVEL}';")
    
    configs.append(f"SET semantic_batch_size = {config.SEMANTIC_BATCH_SIZE};")
    
    configs.append(f"SET enable_semantic_filter_multiplexer = {str(config.ENABLE_SEMANTIC_FILTER_MULTIPLEXER).lower()};")
    configs.append(f"SET semantic_filter_accuracy_threshold = {config.SEMANTIC_FILTER_ACCURACY_THRESHOLD};")
    configs.append(f"SET semantic_filter_latency_first = {str(config.SEMANTIC_FILTER_LATENCY_FIRST).lower()};")
    configs.append(f"SET semantic_filter_batch_size = {config.SEMANTIC_FILTER_BATCH_SIZE};")
    configs.append(f"SET enable_partial_deduction = {str(config.ENABLE_PARTIAL_DEDUCTION).lower()};")
    configs.append(f"SET enable_nl_expression_compression = {str(config.ENABLE_NL_EXPRESSION_COMPRESSION).lower()};")
    
    return "\n".join(configs)


def set_db_path(path: str) -> str:
    global _db_path
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    _db_path = p.resolve()
    
    if not p.exists():
        try:
            _run_duckdb_command("SELECT 1;", str(_db_path), output_format="json", apply_semantic_config=False)
        except Exception as e:
            import logging
            logging.warning(f"Database initialization warning for {str(_db_path)}: {str(e)}")
    
    return str(_db_path)


def get_db_path() -> str:
    if _db_path is None:
        return ""
    return str(_db_path)


def _run_duckdb_command(sql: str, db_path: Optional[str] = None, output_format: str = "json", apply_semantic_config: bool = True) -> str:

    if db_path is None:
        db_path_str = get_db_path()
        db_path = db_path_str if db_path_str else ":memory:"
    
    if apply_semantic_config:
        config_sql = _get_semantic_config_sql_without_extension()
        full_sql = config_sql + "\n" + sql
        logger.debug(f"应用语义 SQL 配置，配置行数: {len(config_sql.split(chr(10)))}")
        logger.debug(f"用户 SQL: {sql[:100]}..." if len(sql) > 100 else f"用户 SQL: {sql}")
    else:
        full_sql = sql
        logger.debug(f"跳过语义配置，直接执行 SQL: {sql[:100]}..." if len(sql) > 100 else f"SQL: {sql}")

    _LLM_TRANSIENT_ERRORS = (
        "json.exception.type_error.302",
        "json.exception.out_of_range",
    )
    _MAX_RETRIES = 5

    last_exc: Optional[RuntimeError] = None
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            return _run_duckdb_command_internal(full_sql, db_path, output_format)
        except RuntimeError as e:
            err_str = str(e)
            is_transient = any(sig in err_str for sig in _LLM_TRANSIENT_ERRORS)
            if is_transient and attempt < _MAX_RETRIES:
                wait = attempt * 2
                logger.warning(
                    f"[LLM 偶发错误] 第 {attempt} 次尝试失败（{err_str[:120]}），"
                    f"{wait}s 后重试…"
                )
                time.sleep(wait)
                last_exc = e
                continue
            raise
    if last_exc is not None:
        raise last_exc
    raise RuntimeError("DuckDB command failed after retries")

def _sql_fingerprint(sql: str) -> str:
    return hashlib.md5(sql.encode()).hexdigest()[:8]


def _run_duckdb_command_internal(sql: str, db_path: str, output_format: str, ignore_errors: bool = False) -> str:
    
    with _DUCKDB_MUTEX:
        cmd = _get_duckdb_cmd()
        
        if output_format == "json":
            cmd.extend([db_path, "-json", "-c", sql])
        else:
            cmd.extend([db_path, "-csv", "-c", sql])
        
        env = os.environ.copy()
        
        lib_paths = []
        if LOCAL_GLIBC_LIB.exists():
            lib_paths.append(str(LOCAL_GLIBC_LIB))
        
        if lib_paths:
            existing_path = env.get("LD_LIBRARY_PATH", "")
            env["LD_LIBRARY_PATH"] = ":".join(lib_paths + ([existing_path] if existing_path else []))
        
        use_local_ld = LOCAL_LD.exists() and LOCAL_GLIBC_LIB.exists()
        command_timeout = 600

        fp = _sql_fingerprint(sql)
        sql_preview = sql.strip()[:500] + ("..." if len(sql.strip()) > 500 else "")
        logger.info(f"[SQL START] fp={fp}  time={time.strftime('%H:%M:%S')}  db={Path(db_path).name}")
        logger.info(f"[SQL body/fp={fp}]\n{sql_preview}")
        t0 = time.time()

        try:
            final_cmd = ([str(LOCAL_LD), "--library-path", ":".join(lib_paths)] + cmd
                         if use_local_ld else cmd)
            if not use_local_ld:
                logger.warning("LOCAL_LD 不存在，直接运行 DuckDB 可能会失败")

            proc = subprocess.Popen(
                final_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                cwd=str(DUCKDB_BIN_DIR)
            )

            try:
                stdout, stderr = proc.communicate(timeout=command_timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.communicate()
                logger.error(f"[SQL TIMEOUT] fp={fp}  elapsed={time.time()-t0:.1f}s")
                raise RuntimeError("DuckDB query timed out")

            elapsed = time.time() - t0
            logger.info(f"[SQL END]   fp={fp}  elapsed={elapsed:.3f}s  return={proc.returncode}")

            if stderr.strip():
                logger.info(f"[SQL stderr/fp={fp}]\n{stderr}")

            if proc.returncode != 0:
                logger.error(f"[SQL FAILED] fp={fp}  return={proc.returncode}")
                logger.error(f"[SQL FAILED] cmd: {' '.join(cmd)}")
                logger.error(f"[SQL FAILED] stderr: {stderr}")
                logger.error(f"[SQL FAILED] stdout: {stdout}")

                if ignore_errors:
                    return ""

                error_msg = stderr.strip() if stderr else "Unknown error"
                error_lines = [l for l in error_msg.split('\n')
                               if 'libcurl' not in l.lower() and l.strip()]
                if error_lines:
                    raise RuntimeError('\n'.join(error_lines))
                raise RuntimeError(f"DuckDB command failed with return code {proc.returncode}")

            logger.debug(f"[SQL OK/fp={fp}] stdout={len(stdout)}B  stderr={len(stderr)}B")

            if not stdout.strip() and stderr:
                error_indicators = ["extension", "not found", "error", "failed"]
                if any(ind in stderr.lower() for ind in error_indicators):
                    logger.warning(f"[SQL WARN/fp={fp}] stdout为空但stderr有内容: {stderr[:200]}")
                    if not ignore_errors:
                        raise RuntimeError(f"Command failed: {stderr.strip()}")

            if output_format == "json":
                return stdout.strip()

            output_lines = []
            for line in stdout.split('\n'):
                line = line.strip()
                if not line:
                    continue
                if any(skip in line.lower() for skip in ['使用本地', 'libcurl', 'duckdb:']):
                    continue
                output_lines.append(line)
            return '\n'.join(output_lines)

        except RuntimeError:
            raise
        except Exception as e:
            logger.error(f"[SQL ERROR] fp={fp}  err={e}")
            raise RuntimeError(f"Failed to execute DuckDB command: {str(e)}")


def _extract_json_blob(s: str) -> str:
   
    s = s.strip()
    
    try:
        json.loads(s)
        return s
    except Exception:
        pass
    
    last_arr_l = s.rfind('[')
    last_arr_r = s.rfind(']')
    if last_arr_l != -1 and last_arr_r != -1 and last_arr_r > last_arr_l:
        return s[last_arr_l:last_arr_r + 1]
    
    last_obj_l = s.rfind('{')
    last_obj_r = s.rfind('}')
    if last_obj_l != -1 and last_obj_r != -1 and last_obj_r > last_obj_l:
        return s[last_obj_l:last_obj_r + 1]
    
    raise RuntimeError(f"No JSON blob found in output, preview: {s[:300]}")


def _jsonify_value(x: Any) -> Any:
    if x is None or isinstance(x, (str, int, float, bool)):
        return x
    if isinstance(x, (list, tuple)):
        return [_jsonify_value(v) for v in x]
    if isinstance(x, dict):
        return {k: _jsonify_value(v) for k, v in x.items()}
    return str(x)



def _node(
    id_str: str,
    label: str,
    detail: str = "",
    children: Optional[List[Dict[str, Any]]] = None,
    extra_info: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "id": id_str,
        "label": label,
        "detail": detail,
        "extra_info": extra_info or {},
        "children": children or []
    }


def _resolve_plan_section(payload: Dict[str, Any], key: str) -> Any:

    if key in payload:
        return payload[key]
    
    plural_key = key + "s"
    if plural_key in payload:
        return payload[plural_key]
    
    if "raw" in payload and isinstance(payload["raw"], dict):
        raw = payload["raw"]
        if key in raw:
            return raw[key]
        if plural_key in raw:
            return raw[plural_key]
    
    return None


def _extract_label(node: Dict[str, Any]) -> str:
    for key in ["name", "type", "operator", "operator_type", "node_type", "plan_type"]:
        if key in node:
            value = node[key]
            if isinstance(value, str):
                return value
    return "Unknown"



_PLAN_CHILD_KEYS = ["children", "inputs", "subplans", "plans", "child", "input"]

_DETAIL_KEYS = [
    "filters", "condition", "conditions", "expressions", "expression",
    "extra_info", "extraInfo", "info", "details", "detail",
    "join_type", "joinType", "table", "tables", "index", "indexes"
]


def _extract_detail(node: Dict[str, Any]) -> str:
    details = []
    
    for key in _DETAIL_KEYS:
        if key in node:
            value = node[key]
            if value:
                if isinstance(value, (list, tuple)):
                    details.append(f"{key}: {', '.join(str(v) for v in value)}")
                elif isinstance(value, dict):
                    detail_str = ", ".join(f"{k}: {v}" for k, v in value.items() if v)
                    if detail_str:
                        details.append(detail_str)
                else:
                    details.append(f"{key}: {value}")
    
    return " | ".join(details) if details else ""


def _plan_node(node_data: Any, node_id: str = "root", depth: int = 0) -> Dict[str, Any]:

    if isinstance(node_data, str):
        try:
            node_data = json.loads(node_data)
        except:
            return _node(node_id, "Invalid JSON", node_data[:100], [])
    
    if isinstance(node_data, list):
        if len(node_data) > 0:
            return _plan_node(node_data[0], node_id, depth)
        return _node(node_id, "Empty", "", [])
    
    if not isinstance(node_data, dict):
        return _node(node_id, str(node_data), "", [])
    
    if "name" not in node_data:

        if "children" in node_data and isinstance(node_data["children"], list) and len(node_data["children"]) > 0:
                return _plan_node(node_data["children"][0], node_id, depth)
        return _node(node_id, "Unknown", "", [])
    
    label = _extract_label(node_data)
    detail = _extract_detail(node_data)
    
    children = []
    for child_key in _PLAN_CHILD_KEYS:
        if child_key in node_data:
            child_data = node_data[child_key]
            if isinstance(child_data, list):
                for idx, child in enumerate(child_data):
                    if child:
                        child_node = _plan_node(child, f"{node_id}.{child_key}[{idx}]", depth + 1)
                        children.append(child_node)
            elif isinstance(child_data, dict):
                child_node = _plan_node(child_data, f"{node_id}.{child_key}", depth + 1)
                children.append(child_node)
            break
    
    return _node(node_id, label, detail, children)


def _maybe_json(s: Any) -> Any:

    if isinstance(s, str):
        try:
            return json.loads(s)
        except:
            return s
    return s


def _build_plan_tree(plan_data: Any, plan_id: str = "plan") -> Dict[str, Any]:

    if plan_data is None:
        return _node(plan_id, "Empty Plan", "", [])
    
    parsed = _maybe_json(plan_data)
    
    if isinstance(parsed, (dict, list)):
        return _plan_node(parsed, plan_id, 0)
    
    return _node(plan_id, "Invalid Plan Data", str(plan_data)[:200], [])


def _strip_plan_artifacts(text: str) -> str:

    import re
    text = re.sub(r'[┌┐└┘├┤│─━═║╔╗╚╝╠╣╦╩╬]', ' ', text)
    text = re.sub(r'[→←↑↓]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def _estimate_indent(line: str) -> int:

    indent = 0
    for char in line:
        if char == ' ':
            indent += 1
        elif char == '\t':
            indent += 4
        else:
            break
    return indent


def _split_plan_sections(text: str) -> Dict[str, str]:

    sections = {
        "unoptimized": "",
        "optimized": "",
        "physical": ""
    }
    
    markers = {
        "unoptimized": "Unoptimized Logical Plan",
        "optimized": "Optimized Logical Plan",
        "physical": "Physical Plan"
    }
    
    positions = {}
    for key, marker in markers.items():
        pos = text.find(marker)
        if pos != -1:
            positions[key] = pos
    
    if not positions:
        return sections
    
    sorted_keys = sorted(positions.keys(), key=lambda k: positions[k])
    
    for i, key in enumerate(sorted_keys):
        start_pos = positions[key]
        if i + 1 < len(sorted_keys):
            next_key = sorted_keys[i + 1]
            end_pos = positions[next_key]
            sections[key] = text[start_pos:end_pos]
        else:
            sections[key] = text[start_pos:]
    
    return sections


def _extract_json_from_section(section_text: str) -> Optional[Union[Dict[str, Any], List[Any]]]:
    if not section_text:
        return None
    
    start_idx = section_text.find('[')
    if start_idx == -1:
        return None
    
    depth = 0
    for i in range(start_idx, len(section_text)):
        char = section_text[i]
        if char == '[':
            depth += 1
        elif char == ']':
            depth -= 1
            if depth == 0:
                json_str = section_text[start_idx:i + 1]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON from section: {e}")
                    return None
    
    return None


def _normalize_plan_node(node: Dict[str, Any], node_id: str = "root", node_counter: Optional[List[int]] = None) -> Dict[str, Any]:

    if node_counter is None:
        node_counter = [0]
    
    node_counter[0] += 1
    current_id = f"{node_id}.{node_counter[0]}"
    
    label = (node.get("name") or 
             node.get("operator_type") or 
             node.get("type") or 
             node.get("operator") or 
             "UNKNOWN")
    
    raw_children = node.get("children") or []
    children = []
    if raw_children:
        logger.debug(f"Node {label} has {len(raw_children)} children")
    for child in raw_children:
        if isinstance(child, dict):
            normalized_child = _normalize_plan_node(child, current_id, node_counter)
            children.append(normalized_child)
        elif child:
            logger.warning(f"Child node is not a dict: {type(child)}, value: {str(child)[:100]}")
    
    detail_parts = []
    extra_info = node.get("extra_info")
    cleaned_extra_info = {}

    if isinstance(extra_info, dict):
        key_fields = ["Table", "Tables", "Filters", "Filter", "Conditions", "Condition",
                     "Join Type", "Expressions", "Expression", "Type",
                     "Estimated Cardinality", "Projections"]

        for field in key_fields:
            if field in extra_info:
                value = extra_info[field]
                if value:
                    if isinstance(value, list):
                        detail_parts.append(f"{field}={', '.join(str(v) for v in value)}")
                    else:
                        detail_parts.append(f"{field}={value}")

        if not detail_parts:
            for k, v in extra_info.items():
                if v and k not in ["name", "children"]:
                    if isinstance(v, list):
                        detail_parts.append(f"{k}={', '.join(str(x) for x in v)}")
                    else:
                        detail_parts.append(f"{k}={v}")

        import re as _re
        for k, v in extra_info.items():
            if k in ["name", "children"]:
                continue
            if isinstance(v, str) and _re.search(r'={8,}', v):
                continue
            cleaned_extra_info[k] = v

    detail = "; ".join(detail_parts)

    return _node(current_id, label, detail, children, cleaned_extra_info)


def _parse_plan_text(text: str, plan_id: str = "plan") -> Dict[str, Any]:

    if not text or not isinstance(text, str):
        return _node(plan_id, "Empty Plan", "", [])
    
    sections = _split_plan_sections(text)
    
    result = {}
    for section_key, section_text in sections.items():
        if not section_text:
            continue

        json_data = _extract_json_from_section(section_text)
        if json_data is None:
            logger.warning(f"Failed to extract JSON from {section_key} section")
            continue
        
        if isinstance(json_data, list) and len(json_data) > 0:
            root_node = json_data[0]
            if isinstance(root_node, dict):
                normalized = _normalize_plan_node(root_node, f"{plan_id}.{section_key}")
                result[section_key] = normalized
        elif isinstance(json_data, dict):
            normalized = _normalize_plan_node(json_data, f"{plan_id}.{section_key}")
            result[section_key] = normalized
    if result:
        return list(result.values())[0]
    
    return _node(plan_id, "Failed to parse plan", "", [])


def build_plan_flow(query: str, explain_payload: Dict[str, Any]) -> Dict[str, Any]:

    result: Dict[str, Optional[Dict[str, Any]]] = {
        "parser_planner": None,
        "optimizer": None,
        "executor": None
    }
    
    plan_data = (
        _resolve_plan_section(explain_payload, "unoptimized") or
        _resolve_plan_section(explain_payload, "unoptimized_logical_plan") or
        _resolve_plan_section(explain_payload, "logical_plan") or
        explain_payload.get("logical_plan")
    )
    
    if plan_data:
        if isinstance(plan_data, (dict, list)) or (isinstance(plan_data, str) and plan_data.strip().startswith(('{', '['))):
            result["parser_planner"] = _build_plan_tree(plan_data, "parser_planner")
        else:
            result["parser_planner"] = _parse_plan_text(plan_data, "parser_planner")
    
    plan_data = (
        _resolve_plan_section(explain_payload, "optimized") or
        _resolve_plan_section(explain_payload, "optimized_logical_plan") or
        explain_payload.get("optimized_logical_plan")
    )
    
    if plan_data:
        if isinstance(plan_data, (dict, list)) or (isinstance(plan_data, str) and plan_data.strip().startswith(('{', '['))):
            result["optimizer"] = _build_plan_tree(plan_data, "optimizer")
        else:
            result["optimizer"] = _parse_plan_text(plan_data, "optimizer")
    
    plan_data = (
        _resolve_plan_section(explain_payload, "physical") or
        _resolve_plan_section(explain_payload, "physical_plan") or
        _resolve_plan_section(explain_payload, "pipelines") or
        explain_payload.get("physical_plan") or
        explain_payload.get("pipelines")
    )
    
    if plan_data:
        if isinstance(plan_data, (dict, list)) or (isinstance(plan_data, str) and plan_data.strip().startswith(('{', '['))):
            result["executor"] = _build_plan_tree(plan_data, "executor")
        else:
            result["executor"] = _parse_plan_text(plan_data, "executor")
    
    return result


def execute_sql(query: str, db_path: Optional[str] = None) -> Dict[str, Any]:
    
    if db_path is None:
        db_path_str = get_db_path()
        db_path = db_path_str if db_path_str else None
    
    t0 = time.time()
    
    query_upper = query.strip().upper()
    apply_semantic_config = not any(query_upper.startswith(cmd) for cmd in [
        'CREATE', 'DROP', 'ALTER', 'INSERT', 'UPDATE', 'DELETE', 'TRUNCATE'
    ])
    
    try:
        output = _run_duckdb_command(query, db_path, output_format="json", apply_semantic_config=apply_semantic_config)
        logger.debug(f"execute_sql: DuckDB output (semantic_config={apply_semantic_config}): {output[:200] if output else '(empty)'}...")
        
        if not output.strip():
            elapsed_ms = int((time.time() - t0) * 1000)
            logger.warning(f"execute_sql: Empty output from DuckDB for query: {query[:100]}...")
            return {
                "columns": [],
                "rows": [],
                "row_count": None,
                "elapsed_ms": elapsed_ms
            }
        
        try:
            rows_data = json.loads(output)
            if not isinstance(rows_data, list):
                rows_data = [rows_data]
        except json.JSONDecodeError:
            raise RuntimeError(f"Failed to parse DuckDB output: {output[:200]}")
        
        if not rows_data:
            elapsed_ms = int((time.time() - t0) * 1000)
            return {
                "columns": [],
                "rows": [],
                "row_count": 0,
                "elapsed_ms": elapsed_ms
            }
        
        columns = list(rows_data[0].keys()) if rows_data else []
        

        max_rows = config.MAX_ROWS_RETURN
        rows_data = rows_data[:max_rows]

        rows = []
        for row_dict in rows_data:
            row = [row_dict.get(col) for col in columns]
            rows.append([_jsonify_value(v) for v in row])
        
        elapsed_ms = int((time.time() - t0) * 1000)
        
        return {
            "columns": columns,
            "rows": rows,
            "row_count": len(rows),
            "elapsed_ms": elapsed_ms
        }
    
    except Exception as e:
        elapsed_ms = int((time.time() - t0) * 1000)
        query_upper = query.strip().upper()
        logger.error(f"execute_sql: Exception occurred for query: {query[:100]}...")
        logger.error(f"execute_sql: Exception: {e}", exc_info=True)
        if any(query_upper.startswith(cmd) for cmd in ['CREATE', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER']):
            logger.warning(f"execute_sql: Returning empty result for DDL/DML statement")
            return {
                "columns": [],
                "rows": [],
                "row_count": None,
                "elapsed_ms": elapsed_ms
            }
        raise


def _get_profiling_info(query: str, db_path: Optional[str] = None) -> Dict[str, Any]:
    logger.info(f"[PROFILING] 开始执行 profiling，查询: {query[:100]}...")
    try:
        import tempfile
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        temp_file_path = temp_file.name
        temp_file.close()
        logger.info(f"[PROFILING] 临时文件路径: {temp_file_path}")
        
        try:
            profiling_query_sql = f"""
PRAGMA enable_profiling = 'json';
PRAGMA profiling_mode = 'detailed';
PRAGMA profiling_output = '{temp_file_path}';
{query}
"""
            
            logger.info(f"[PROFILING] 执行 profiling 查询...")
            _run_duckdb_command(profiling_query_sql, db_path, output_format="json", apply_semantic_config=False)
            logger.info(f"[PROFILING] Profiling 查询执行完成，检查文件: {temp_file_path}")
            
            if Path(temp_file_path).exists():
                logger.info(f"[PROFILING] 文件存在，开始读取...")
                with open(temp_file_path, 'r', encoding='utf-8') as f:
                    profiling_content = f.read()
                
                if profiling_content and profiling_content.strip():
                    try:
                        profiling_data = json.loads(profiling_content)
                        logger.info(f"成功解析 profiling JSON，类型: {type(profiling_data)}, 长度: {len(profiling_data) if isinstance(profiling_data, (list, dict)) else 'N/A'}")
                        
                        if isinstance(profiling_data, list) and len(profiling_data) > 0:
                            profiling_data = profiling_data[0]
                            logger.info(f"从数组中提取第一个元素，类型: {type(profiling_data)}")
                        
                        if isinstance(profiling_data, dict):
                            logger.info(f"Profiling 数据键: {list(profiling_data.keys())[:20]}")
                            return profiling_data
                        else:
                            logger.warning(f"Profiling 数据不是字典格式: {type(profiling_data)}")
                            return {}
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse profiling JSON: {e}, content preview: {profiling_content[:500]}")
                        return {}
                else:
                    logger.warning("Profiling file is empty")
                    return {}
            else:
                logger.warning(f"Profiling file not found: {temp_file_path}")
                return {}
        finally:
            try:
                if Path(temp_file_path).exists():
                    Path(temp_file_path).unlink()
            except Exception as e:
                logger.warning(f"Failed to delete temp profiling file: {e}")
    except Exception as e:
        logger.warning(f"Failed to get profiling info: {e}")
        return {}


def _merge_profiling_to_plan(plan_node: Dict[str, Any], profiling_data: Dict[str, Any]) -> float:
    if not profiling_data or not plan_node:
        return 0.0
    
    global_time_ms = 0.0
    
    def extract_time_from_dict(data: Dict[str, Any]) -> float:
        if "timing" in data:
            timing = data["timing"]
            if isinstance(timing, dict):
                time_val = timing.get("total") or timing.get("time") or timing.get("elapsed") or timing.get("wall_time") or timing.get("duration")
                if time_val is not None:
                    time_val = float(time_val)
                    if time_val < 1000:
                        time_val = time_val * 1000
                    return time_val
            elif isinstance(timing, (int, float)):
                time_val = float(timing)
                if time_val < 1000:
                    time_val = time_val * 1000
                return time_val
        
        for key in ["time", "elapsed", "total_time", "wall_time", "duration", "execution_time"]:
            if key in data:
                time_val = float(data[key])
                if time_val < 1000:
                    time_val = time_val * 1000
                return time_val
        
        return 0.0
    
    global_time_ms = extract_time_from_dict(profiling_data)
    if global_time_ms == 0.0:
        def find_root_operator(data: Any) -> Optional[Dict[str, Any]]:
            if isinstance(data, dict):
                if "name" in data:
                    return data
                for key in ["children", "operators", "inputs", "subplans"]:
                    if key in data:
                        child = data[key]
                        if isinstance(child, list) and len(child) > 0:
                            result = find_root_operator(child[0])
                            if result:
                                return result
                        elif isinstance(child, dict):
                            result = find_root_operator(child)
                            if result:
                                return result
            elif isinstance(data, list) and len(data) > 0:
                return find_root_operator(data[0])
            return None
        
        root_op = find_root_operator(profiling_data)
        if root_op:
            root_time = extract_time_from_dict(root_op)
            if root_time > 0:
                global_time_ms = root_time
                logger.info(f"从根算子节点提取全局时间: {global_time_ms} ms")
    
    if global_time_ms == 0.0:
        total_op_time = 0.0
        def sum_operator_times(data: Any):
            nonlocal total_op_time
            if isinstance(data, dict):
                if "name" in data:
                    op_timing = data.get("timing", {})
                    if isinstance(op_timing, dict):
                        op_time = op_timing.get("total") or op_timing.get("time") or op_timing.get("elapsed", 0.0)
                        if op_time > 0:
                            op_time = float(op_time)
                            if op_time < 1000:
                                op_time = op_time * 1000
                            total_op_time = max(total_op_time, op_time)
                
                for key, value in data.items():
                    if key in ["children", "operators", "inputs", "subplans"]:
                        if isinstance(value, list):
                            for item in value:
                                sum_operator_times(item)
                        elif isinstance(value, dict):
                            sum_operator_times(value)
            elif isinstance(data, list):
                for item in data:
                    sum_operator_times(item)
        
        sum_operator_times(profiling_data)
        if total_op_time > 0:
            global_time_ms = total_op_time
            logger.info(f"从算子时间累加得到全局时间: {global_time_ms} ms")
    
    if global_time_ms == 0.0:
        logger.warning(f"未能从 profiling 数据中提取全局时间，profiling_data keys: {list(profiling_data.keys())[:20]}")
    
    operator_map = {}
    
    def collect_operators(data: Any, path: str = ""):
        if isinstance(data, dict):
            if "name" in data:
                op_name = data.get("name", "")
                operator_map[op_name] = data
            
            for key, value in data.items():
                if key in ["children", "operators", "inputs", "subplans"]:
                    if isinstance(value, list):
                        for idx, item in enumerate(value):
                            collect_operators(item, f"{path}.{key}[{idx}]")
                    elif isinstance(value, dict):
                        collect_operators(value, f"{path}.{key}")
        elif isinstance(data, list):
            for idx, item in enumerate(data):
                collect_operators(item, f"{path}[{idx}]")
    
    collect_operators(profiling_data)
    
    def merge_node(node: Dict[str, Any]):
        node_name = node.get("name", "")
        
        if not node_name:
            return
        
        matched_op = None
        for op_name, op_data in operator_map.items():
            if node_name.upper() in op_name.upper() or op_name.upper() in node_name.upper():
                matched_op = op_data
                break
        
        if matched_op:
            if "profiling" not in node:
                node["profiling"] = {}
            
            op_timing = matched_op.get("timing", {})
            exec_time = 0.0
            if isinstance(op_timing, dict):
                exec_time = op_timing.get("total", op_timing.get("time", op_timing.get("elapsed", 0.0)))
            elif isinstance(op_timing, (int, float)):
                exec_time = float(op_timing)
            
            if exec_time > 0:
                if exec_time < 1000:
                    exec_time = exec_time * 1000
                node["profiling"]["execution_time_ms"] = exec_time
                logger.debug(f"为算子 {node_name} 添加执行时间: {exec_time} ms")
            
            if "SEM_FILTER" in node_name.upper() or "SEMANTIC" in node_name.upper():
                if "input_tokens" in matched_op:
                    node["profiling"]["input_tokens"] = matched_op["input_tokens"]
                if "output_tokens" in matched_op:
                    node["profiling"]["output_tokens"] = matched_op["output_tokens"]
                if "parse_success_rate" in matched_op:
                    node["profiling"]["parse_success_rate"] = matched_op["parse_success_rate"]
        
        for child_key in ["children", "inputs", "subplans"]:
            if child_key in node and isinstance(node[child_key], list):
                for child in node[child_key]:
                    if isinstance(child, dict):
                        merge_node(child)
                break
    
    merge_node(plan_node)
    
    return global_time_ms


def explain_query(query: str, db_path: Optional[str] = None, config_overrides: Optional[Dict[str, Any]] = None, set_commands: Optional[str] = None) -> Dict[str, Any]:
    if db_path is None:
        db_path_str = get_db_path()
        db_path = db_path_str if db_path_str else None
    
    original_config = {}
    if config_overrides:
        import config as cfg
        for key, value in config_overrides.items():
            if hasattr(cfg, key.upper()):
                original_config[key.upper()] = getattr(cfg, key.upper())
                setattr(cfg, key.upper(), value)
                logger.info(f"临时覆盖配置: {key.upper()} = {value}")
    
    t0 = time.time()
    
    try:
        query_stripped = query.strip()
        query_upper = query_stripped.upper()
        
        actual_query = query_stripped
        if query_upper.startswith('EXPLAIN'):
            match = re.match(r'EXPLAIN\s*(?:\([^)]+\))?\s*(.+)', query_stripped, re.IGNORECASE | re.DOTALL)
            if match:
                actual_query = match.group(1).strip()

        if set_commands and set_commands.strip():
            logger.info("=" * 60)
            logger.info("【用户提供的 SET 命令】")
            logger.info(set_commands)
            logger.info("=" * 60)
            explain_sql = f"{set_commands}\nPRAGMA explain_output='all';\nEXPLAIN (FORMAT JSON) {actual_query}"
        else:
            explain_sql = f"PRAGMA explain_output='all';\nEXPLAIN (FORMAT JSON) {actual_query}"
        
        logger.info("=" * 60)
        logger.info("【最终执行的 SQL（包含所有 SET 命令）】")
        logger.info(explain_sql[:500] + ("..." if len(explain_sql) > 500 else ""))
        logger.info("=" * 60)
        
        output = _run_duckdb_command(explain_sql, db_path, output_format="json")
        
        logger.debug(f"EXPLAIN raw output length: {len(output)}, first 500 chars: {output[:500]}")
        
        if not output or not output.strip():
            logger.warning("EXPLAIN output is empty")
            elapsed_ms = int((time.time() - t0) * 1000)
            return {
                "format": "text",
                "text": "No output received from EXPLAIN",
                "elapsed_ms": elapsed_ms
            }
        

        try:
            json_blob = _extract_json_blob(output)
            rows_data = json.loads(json_blob)
            logger.debug(f"Parsed JSON, type: {type(rows_data)}")
            
            if isinstance(rows_data, dict):
                rows_data = [rows_data]
            
            if not isinstance(rows_data, list):
                raise RuntimeError(f"Unexpected EXPLAIN json type: {type(rows_data)}")
            
            plan_dict = {}
            
            for row in rows_data:
                if not isinstance(row, dict):
                    if isinstance(row, list) and len(row) >= 2:
                        plan_name = row[0]
                        plan_val = row[1]
                    else:
                        continue
                else:
                    plan_name = (row.get("explain_key") or row.get("explain_name") or 
                                row.get("key") or row.get("name") or row.get("plan_name"))
                    plan_val = (row.get("explain_value") or row.get("explain") or 
                               row.get("value") or row.get("json") or row.get("plan_json"))
                
                if not plan_name or plan_val is None:
                    logger.debug(f"Skipping row without plan_name/plan_val: {list(row.keys())[:5] if isinstance(row, dict) else 'not a dict'}")
                    continue
                if isinstance(plan_val, str):
                    plan_val = plan_val.strip()
                    try:
                        plan_json = json.loads(plan_val)
                        logger.debug(f"Parsed plan_val as JSON string, type: {type(plan_json)}")
                    except json.JSONDecodeError as e:
                        logger.warning(f"Failed to parse plan_val as JSON: {e}, storing as string")
                        plan_json = plan_val
                    except Exception as e:
                        logger.warning(f"Unexpected error parsing plan_val: {e}, storing as string")
                        plan_json = plan_val
                else:
                    plan_json = plan_val
                    logger.debug(f"plan_val is already an object, type: {type(plan_json)}")
                
                if isinstance(plan_json, list):
                    if len(plan_json) > 0:
                        for item in plan_json:
                            if isinstance(item, dict) and "name" in item:
                                plan_json = item
                                break
                        else:
                            plan_json = plan_json[0]
                    else:
                        logger.warning(f"Empty plan array for {plan_name}")
                        continue
                
                if not isinstance(plan_json, dict):
                    logger.warning(f"Plan {plan_name} is not a dict, type: {type(plan_json)}")
                    continue
                
                if "name" not in plan_json:
                    logger.warning(f"Plan {plan_name} does not have 'name' field, keys: {list(plan_json.keys())[:10]}")
                    if "children" in plan_json and isinstance(plan_json["children"], list) and len(plan_json["children"]) > 0:
                        plan_json = plan_json["children"][0]
                    else:
                        continue
                
                plan_dict[plan_name] = plan_json
                logger.debug(f"Parsed plan: {plan_name}, root node: {plan_json.get('name', 'Unknown')}")
            
            if original_config:
                import config as cfg
                for key, value in original_config.items():
                    setattr(cfg, key, value)
                    logger.debug(f"恢复配置: {key} = {value}")
            
            elapsed_ms = int((time.time() - t0) * 1000)
            result = {
                "format": "json",
                "unoptimized": plan_dict.get("Unoptimized Logical Plan"),
                "optimized": plan_dict.get("Optimized Logical Plan"),
                "physical": plan_dict.get("Physical Plan"),
                "raw": plan_dict,
                "elapsed_ms": elapsed_ms
            }
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}, output preview: {output[:500]}")
        except Exception as e:
            logger.error(f"Failed to parse plans: {e}")
        logger.warning(f"JSON parsing failed, trying CSV format")
        try:
            output_text = _run_duckdb_command(explain_sql, db_path, output_format="csv")
            
            sections = _split_plan_sections(output_text)
            
            result_plans = {}
            for section_key, section_text in sections.items():
                if not section_text:
                    continue
                
                json_data = _extract_json_from_section(section_text)
                if json_data is None:
                    logger.warning(f"Failed to extract JSON from {section_key} section")
                    continue
                        
                if isinstance(json_data, list) and len(json_data) > 0:
                    root_node = json_data[0]
                    if isinstance(root_node, dict):
                        normalized = _normalize_plan_node(root_node, f"plan.{section_key}")
                        result_plans[section_key] = normalized
                elif isinstance(json_data, dict):
                    normalized = _normalize_plan_node(json_data, f"plan.{section_key}")
                    result_plans[section_key] = normalized
            
            if original_config:
                import config as cfg
                for key, value in original_config.items():
                    setattr(cfg, key, value)
                    logger.debug(f"恢复配置: {key} = {value}")
            
            elapsed_ms = int((time.time() - t0) * 1000)
            if result_plans:
                result = {
                    "format": "json",
                    "unoptimized": result_plans.get("unoptimized"),
                    "optimized": result_plans.get("optimized"),
                    "physical": result_plans.get("physical"),
                    "raw": {"text": output_text, "original_output": output},
                    "elapsed_ms": elapsed_ms
                }
                return result
            else:
                return {
                    "format": "text",
                    "text": output_text,
                    "raw": output,
                    "elapsed_ms": elapsed_ms
                }
                
        except Exception as csv_e:
            logger.error(f"Both JSON and CSV formats failed. CSV error: {csv_e}")
            elapsed_ms = int((time.time() - t0) * 1000)
            return {
                "format": "text",
                "text": output if output else "No output received",
                "raw": output,
                "elapsed_ms": elapsed_ms,
                "error": str(csv_e)
        }
    
    except Exception as e:
        elapsed_ms = int((time.time() - t0) * 1000)
        raise RuntimeError(f"Failed to explain query: {str(e)}")


def list_catalog() -> Dict[str, Any]:
    
    query = """
    SELECT table_schema, table_name, table_type
    FROM information_schema.tables
    WHERE table_type IN ('BASE TABLE', 'VIEW')
    ORDER BY table_schema, table_name
    """
    
    try:
        db_path = get_db_path()
        output = _run_duckdb_command(query, db_path, output_format="json", apply_semantic_config=False)
        logger.info(f"list_catalog: DuckDB output: {output[:200] if output else '(empty)'}...")
        
        if not output.strip():
            logger.warning("list_catalog: Empty output from DuckDB")
            return {"schemas": []}
        
        rows_data = json.loads(output)
        if not isinstance(rows_data, list):
            rows_data = [rows_data]
        
        result = {"rows": [[r.get("table_schema"), r.get("table_name"), r.get("table_type")] for r in rows_data]}
        logger.info(f"list_catalog: Parsed {len(result['rows'])} rows")
        
        hidden = {"information_schema", "pg_catalog", "duckdb_catalog"}
        schemas: Dict[str, list] = {}
        
        if result.get("rows"):
            logger.info(f"list_catalog: found {len(result['rows'])} rows")
            for row in result["rows"]:
                sch, name, typ = row[0], row[1], row[2]
                logger.debug(f"list_catalog: processing {sch}.{name} ({typ})")
                if sch in hidden:
                    continue
                schemas.setdefault(sch, []).append({"name": str(name), "type": str(typ)})
        else:
            logger.info("list_catalog: no rows returned")
        
        result_schemas = {"schemas": [{"name": s, "tables": t} for s, t in schemas.items()]}
        logger.info(f"list_catalog: returning {len(result_schemas['schemas'])} schemas")
        return result_schemas
    
    except Exception as e:
        logger.error(f"list_catalog: exception occurred: {e}", exc_info=True)
        return {"schemas": []}


def get_table_columns(schema_name: str, table_name: str) -> Dict[str, Any]:
    schema_escaped = schema_name.replace("'", "''")
    table_escaped = table_name.replace("'", "''")
    
    query = f"""
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_schema = '{schema_escaped}' AND table_name = '{table_escaped}'
    ORDER BY ordinal_position
    """
    
    try:
        result = execute_sql(query)
        columns = []
        
        if result.get("rows"):
            for row in result["rows"]:
                columns.append({
                    "name": str(row[0]),
                    "type": str(row[1])
                })
        
        return {"ok": True, "columns": columns}
    
    except Exception as e:
        return {"ok": False, "error": str(e), "columns": []}


def execute_multiple_queries(queries: List[str], db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    
    if db_path is None:
        db_path = get_db_path() if _db_path else ":memory:"
    
    results = []
    for query in queries:
        try:
            result = execute_sql(query)
            results.append(result)
        except Exception as e:
            results.append({"error": str(e)})
    
    return results


def profile_query(query: str, db_path: Optional[str] = None, config_overrides: Optional[Dict[str, Any]] = None, set_commands: Optional[str] = None) -> Dict[str, Any]:
    if db_path is None:
        db_path_str = get_db_path()
        db_path = db_path_str if db_path_str else None
    
    original_config = {}
    if config_overrides:
        import config as cfg
        for key, value in config_overrides.items():
            if hasattr(cfg, key.upper()):
                original_config[key.upper()] = getattr(cfg, key.upper())
                setattr(cfg, key.upper(), value)
                logger.info(f"[Profiling] 临时覆盖配置: {key.upper()} = {value}")
    
    t0 = time.time()
    
    try:
        import config as cfg
        output = ""

        def _read_json_file(file_path: Union[str, Path]) -> Dict[str, Any]:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(f"File not found: {path}")
            with open(path, 'r', encoding='utf-8') as f:
                data = json.loads(f.read())
            if isinstance(data, list) and data:
                data = data[0]
            if not isinstance(data, dict):
                raise ValueError(f"Invalid JSON structure in {path}: expected object")
            return data

        use_split = getattr(cfg, 'USE_SPLIT_PROFILING_FILES', False)
        profiling_data: Optional[Dict[str, Any]] = None
        if use_split:
            prompt_path    = getattr(cfg, 'SPLIT_PROMPT_FILE_PATH',
                                     Path(__file__).resolve().parent / "results" / "deduction.json")
            profiling_path = getattr(cfg, 'SPLIT_PROFILING_FILE_PATH',
                                     Path(__file__).resolve().parent / "results" / "profiling.json")
            logger.info(f"[分离模式] Prompt 文件: {prompt_path} | Profiling 文件: {profiling_path}")
            try:
                profiling_data = _read_json_file(profiling_path)
                prompt_data    = _read_json_file(prompt_path)
                if isinstance(prompt_data.get('extra_info'), dict) and prompt_data['extra_info']:
                    profiling_data['extra_info'] = prompt_data['extra_info']
            except Exception as e:
                elapsed_ms = int((time.time() - t0) * 1000)
                return {"ok": False, "error": f"分离模式文件读取失败: {e}", "elapsed_ms": elapsed_ms}
            skip_to_aqe_extraction = True

        if not use_split:
            skip_to_aqe_extraction = False
            
            query_stripped = query.strip()
            query_upper = query_stripped.upper()
            
            actual_query = query_stripped
            if query_upper.startswith('EXPLAIN'):
                match = re.match(r'EXPLAIN\s+ANALYZE\s+(.+)', query_stripped, re.IGNORECASE | re.DOTALL)
                if match:
                    actual_query = match.group(1).strip()
                else:
                    match = re.match(r'EXPLAIN\s*(?:\([^)]+\))?\s*(.+)', query_stripped, re.IGNORECASE | re.DOTALL)
                    if match:
                        actual_query = match.group(1).strip()
            
        
            import uuid, tempfile
            profile_file_name = f"profile_{uuid.uuid4().hex}.json"
            profile_file_path = Path(tempfile.gettempdir()) / profile_file_name
            profile_file_abs_path = str(profile_file_path.resolve())
            
            profile_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            if profile_file_path.exists():
                try:
                    profile_file_path.unlink()
                except Exception as e:
                    logger.debug(f"删除已存在的 profiling 文件失败: {e}")
            
            profiling_pragmas = [
                "PRAGMA enable_profiling='json';",
                "PRAGMA profiling_mode='detailed';",
                f"PRAGMA profiling_output='{profile_file_abs_path}';"
            ]
            
            if set_commands and set_commands.strip():
                profiling_sql = f"{set_commands}\n" + "\n".join(profiling_pragmas) + f"\n{actual_query}"
            else:
                profiling_sql = "\n".join(profiling_pragmas) + f"\n{actual_query}"
            output = ""
            try:
                output = _run_duckdb_command(profiling_sql, db_path, output_format="json")
            except RuntimeError as run_err:
                err_str = str(run_err)
                if "json.exception.type_error" in err_str or "type must be string, but is null" in err_str:
                    logger.warning(
                        f"[PROFILING] DuckDB 查询结果 JSON 输出失败（含 NULL 值），"
                        f"但 profiling 文件可能已写入，继续尝试读取: {err_str[:200]}"
                    )
                else:
                    raise

            profile_data_from_file = None
            if profile_file_path.exists():
                try:

                    max_retries = 10
                    retry_delay = 0.1
                    for retry in range(max_retries):
                        if profile_file_path.stat().st_size > 0:
                            break
                        time.sleep(retry_delay)
                    
                    with open(profile_file_path, 'r', encoding='utf-8') as f:
                        profile_content = f.read()
                        if profile_content and profile_content.strip():
                            profile_data_from_file = json.loads(profile_content)
                            logger.info("=" * 60)
                            logger.info("【Profiling Output 文件内容】")
                            logger.info(json.dumps(profile_data_from_file, indent=2, ensure_ascii=False))
                            logger.info("=" * 60)
                
                    try:
                        profile_file_path.unlink()
                    except Exception as e:
                        logger.debug(f"删除 profiling 文件失败: {e}")
                except Exception as e:
                    logger.warning(f"读取 profiling 文件失败: {e}")
                    try:
                        if profile_file_path.exists():
                            profile_file_path.unlink()
                    except:
                        pass
            
            if not profile_data_from_file:
                elapsed_ms = int((time.time() - t0) * 1000)
                return {
                    "ok": False,
                    "error": "Failed to read profiling data from file",
                    "elapsed_ms": elapsed_ms
                }
            
            raw_profiling_data = profile_data_from_file
            if isinstance(raw_profiling_data, list):
                if not raw_profiling_data:
                    elapsed_ms = int((time.time() - t0) * 1000)
                    return {
                        "ok": False,
                        "error": "Invalid profiling data format from file",
                        "elapsed_ms": elapsed_ms
                    }
                raw_profiling_data = raw_profiling_data[0]

            if not isinstance(raw_profiling_data, dict):
                logger.warning(f"Profiling data is not a dict, type: {type(raw_profiling_data)}")
                elapsed_ms = int((time.time() - t0) * 1000)
                return {
                    "ok": False,
                    "error": "Invalid profiling data format from file",
                    "elapsed_ms": elapsed_ms
                }
            profiling_data = raw_profiling_data
        
        if profiling_data is None:
            elapsed_ms = int((time.time() - t0) * 1000)
            return {
                "ok": False,
                "error": "Profiling data is unavailable",
                "elapsed_ms": elapsed_ms
            }

        expected_fields = ["latency", "cpu_time", "children"]
        has_expected_fields = any(field in profiling_data for field in expected_fields)
        
        if not has_expected_fields:
            logger.warning(f"Profiling data missing expected fields. Keys: {list(profiling_data.keys())[:10]}")
        
        def extract_aqe_info(node: Dict[str, Any], aqe_info_list: List[Dict[str, Any]]):
            if not isinstance(node, dict):
                return
            
            operator_type = node.get("operator_type", "")
            operator_name = node.get("operator_name", "")
            
            if "SEM_FILTER_MULTIPLEXER" in operator_type.upper() or "MULTIPLEXER" in operator_name.upper():
                extra_info = node.get("extra_info", {})
                if extra_info and isinstance(extra_info, dict):
                    aqe_data = {
                        "operator_type": operator_type,
                        "operator_name": operator_name,
                        "operator_timing": node.get("operator_timing", 0),
                        "operator_rows_scanned": node.get("operator_rows_scanned", 0),
                        "operator_cardinality": node.get("operator_cardinality", 0),
                        "cumulative_rows_scanned": node.get("cumulative_rows_scanned", 0),
                        "cumulative_cardinality": node.get("cumulative_cardinality", 0),
                    }
                    
                    expression_exploration = {}
                    expr_selectivities = {}
                    expr_samples = {}
                    expr_names = {}
                    similarities = {}
                    
                    for key, value in extra_info.items():
                        if key.startswith("expr_") and "_selectivity" in key:
                            expr_idx = key.replace("expr_", "").replace("_selectivity", "")
                            expr_selectivities[expr_idx] = value
                        elif key.startswith("expr_") and "_samples" in key:
                            expr_idx = key.replace("expr_", "").replace("_samples", "")
                            expr_samples[expr_idx] = value
                        elif key.startswith("expr_") and "_name" in key:
                            expr_idx = key.replace("expr_", "").replace("_name", "")
                            expr_names[expr_idx] = value
                        elif key.startswith("similarity_"):
                            similarities[key] = value
                        elif key in ["expression_count", "multiplexer_type", "total_paths"]:
                            expression_exploration[key] = value
                        elif key.startswith("expression_exploration_"):
                            expression_exploration[key.replace("expression_exploration_", "")] = value
                    
                    if expr_selectivities or expr_names:
                        expression_exploration["expressions"] = []
                        for expr_idx in sorted(expr_selectivities.keys(), key=lambda x: int(x) if x.isdigit() else 0):
                            expr_data = {
                                "index": expr_idx,
                                "name": expr_names.get(expr_idx, ""),
                                "selectivity": expr_selectivities.get(expr_idx, ""),
                                "samples": expr_samples.get(expr_idx, "")
                            }
                            expression_exploration["expressions"].append(expr_data)
                    
                    if similarities:
                        expression_exploration["similarities"] = similarities
                    
                    if expression_exploration:
                        aqe_data["expression_exploration"] = expression_exploration
                    
                    path_exploration = {}
                    paths = []
                    path_keys = set()
                    
                    for key, value in extra_info.items():
                        if key.startswith("path_") and "_" in key:
                            parts = key.split("_")
                            if len(parts) >= 3:
                                path_idx = parts[1]
                                path_attr = "_".join(parts[2:])
                                path_keys.add(path_idx)
                    
                    for path_idx in sorted(path_keys, key=lambda x: int(x) if x.isdigit() else 0):
                        path_data = {
                            "index": path_idx,
                            "accuracy": extra_info.get(f"path_{path_idx}_accuracy", ""),
                            "latency": extra_info.get(f"path_{path_idx}_latency", ""),
                            "cost": extra_info.get(f"path_{path_idx}_cost", ""),
                            "input_tokens": extra_info.get(f"path_{path_idx}_input_tokens", ""),
                            "output_tokens": extra_info.get(f"path_{path_idx}_output_tokens", ""),
                            "samples": extra_info.get(f"path_{path_idx}_samples", ""),
                            "skipped": extra_info.get(f"path_{path_idx}_skipped", ""),
                            "expression": extra_info.get(f"path_{path_idx}_expression", ""),
                            "exploration_time_ms": extra_info.get(f"path_{path_idx}_exploration_time_ms", "")
                        }
                        paths.append(path_data)
                    
                    if paths:
                        path_exploration["paths"] = paths
                    
                    if "best_path_index" in extra_info:
                        path_exploration["best_path"] = {
                            "index": extra_info.get("best_path_index", ""),
                            "accuracy": extra_info.get("best_path_accuracy", ""),
                            "latency": extra_info.get("best_path_latency", ""),
                            "cost": extra_info.get("best_path_cost", ""),
                            "expression": extra_info.get("best_path_expression", "")
                        }
                    
                    for key, value in extra_info.items():
                        if key.startswith("path_exploration_"):
                            path_exploration[key.replace("path_exploration_", "")] = value
                    
                    if path_exploration:
                        aqe_data["path_exploration"] = path_exploration
                    
                    exploitation = {}
                    for key, value in extra_info.items():
                        if key.startswith("exploitation_"):
                            exploitation[key.replace("exploitation_", "")] = value
                    
                    if exploitation:
                        aqe_data["exploitation"] = exploitation
                    
                    overall_stats = {}
                    for key in ["total_tuples_processed", "total_input_tokens", "total_output_tokens", 
                               "total_cost", "total_execution_time_ms", "total_exploration_time_ms",
                               "best_path_selection_time_ms", "individual_path_count"]:
                        if key in extra_info:
                            overall_stats[key] = extra_info[key]
                    
                    if overall_stats:
                        aqe_data["overall_stats"] = overall_stats
                    
                    other_info = {}
                    for key, value in extra_info.items():
                        if not any(key.startswith(prefix) for prefix in [
                            "expr_", "similarity_", "path_", "expression_exploration_",
                            "path_exploration_", "exploitation_", "best_path_", "total_"
                        ]):
                            other_info[key] = value
                    
                    if other_info:
                        aqe_data["other_info"] = other_info
                    
                    aqe_info_list.append(aqe_data)
            
            children = node.get("children", [])
            if isinstance(children, list):
                for child in children:
                    if isinstance(child, dict):
                        extract_aqe_info(child, aqe_info_list)
            elif isinstance(children, dict):
                extract_aqe_info(children, aqe_info_list)
        
        aqe_info_list = []
        extract_aqe_info(profiling_data, aqe_info_list)
        
        def add_path_children_to_multiplexer(node: Dict[str, Any]):
            if not isinstance(node, dict):
                return
            
            operator_type = node.get("operator_type", "")
            operator_name = node.get("operator_name", "")
            
            if "SEM_FILTER_MULTIPLEXER" in operator_type.upper() or "MULTIPLEXER" in operator_name.upper():
                extra_info = node.get("extra_info", {})
                if extra_info and isinstance(extra_info, dict):

                    total_paths = int(extra_info.get("total_paths", 0))
                    best_path_index = extra_info.get("best_path_index", "")
                    
                    if total_paths > 0:
                        path_children = []
                        original_children = node.get("children", [])
                        
                        for path_idx in range(total_paths):
                            path_idx_str = str(path_idx)
                            path_expression = extra_info.get(f"path_{path_idx_str}_expression", "")
                            path_accuracy = extra_info.get(f"path_{path_idx_str}_accuracy", "")
                            path_latency = extra_info.get(f"path_{path_idx_str}_latency", "")
                            path_cost = extra_info.get(f"path_{path_idx_str}_cost", "")
                            path_input_tokens = extra_info.get(f"path_{path_idx_str}_input_tokens", "")
                            path_output_tokens = extra_info.get(f"path_{path_idx_str}_output_tokens", "")
                            
                            is_fusion = "Predicates A" in path_expression or "Predicates B" in path_expression
                            path_type = "Operator Fusion" if is_fusion else "Adaptative Execution"
     
                            path_node = {
                                "operator_name": "SemFilter",
                                "operator_type": "SEM_FILTER",
                                "operator_timing": float(path_latency) / 1000.0 if path_latency else 0.0,  
                                "operator_rows_scanned": 0,
                                "operator_cardinality": 0,
                                "cumulative_rows_scanned": 0,
                                "cumulative_cardinality": 0,
                                "result_set_size": 0,
                                "cpu_time": 0.0,
                                "extra_info": {
                                    "path_index": path_idx_str,
                                    "path_type": path_type,
                                    "accuracy": path_accuracy,
                                    "latency_ms": path_latency,
                                    "cost": path_cost,
                                    "input_tokens": path_input_tokens,
                                    "output_tokens": path_output_tokens,
                                    "expression": path_expression,
                                    "is_best": path_idx_str == best_path_index,
                                    "is_path_node": True 
                                },
                                "children": [] 
                            }
                            path_children.append(path_node)
                        

                        if path_children:
                            node["children"] = path_children + (original_children if original_children else [])
                            
                            cleaned_extra_info = {}
                            path_related_prefixes = [
                                "path_", "expr_", "similarity_", "expression_exploration_",
                                "path_exploration_", "exploitation_", "best_path_", "total_",
                                "expression_count", "multiplexer_type", "total_paths",
                                "input_tokens", "output_tokens", "parse_success", "parse_failure",
                                "parse_success_rate"
                            ]
                            
                            for key, value in extra_info.items():
                                if not any(key.startswith(prefix) for prefix in path_related_prefixes):
                                    cleaned_extra_info[key] = value
                            
                            node["extra_info"] = cleaned_extra_info
                            
                            logger.info(f"为 SEM_FILTER_MULTIPLEXER 添加了 {len(path_children)} 个路径子节点，并清理了路径相关信息")
            
            children = node.get("children", [])
            if isinstance(children, list):
                for child in children:
                    if isinstance(child, dict):
                        add_path_children_to_multiplexer(child)
            elif isinstance(children, dict):
                add_path_children_to_multiplexer(children)
        
        add_path_children_to_multiplexer(profiling_data)
        
        if aqe_info_list:
            logger.info("=" * 60)
            logger.info("【AQE (Adaptive Query Execution) 信息】")
            logger.info(f"找到 {len(aqe_info_list)} 个 SEM_FILTER_MULTIPLEXER 操作符")
            for idx, aqe_info in enumerate(aqe_info_list):
                logger.info(f"\n--- AQE 操作符 #{idx + 1} ---")
                if "expression_exploration" in aqe_info:
                    logger.info("Expression Exploration Phase:")
                    expr_expl = aqe_info["expression_exploration"]
                    if "expressions" in expr_expl:
                        for expr in expr_expl["expressions"]:
                            logger.info(f"  表达式 {expr['index']}: selectivity={expr.get('selectivity', 'N/A')}, samples={expr.get('samples', 'N/A')}")
                            logger.info(f"    名称: {expr.get('name', 'N/A')[:80]}...")
                    if "total_paths" in expr_expl:
                        logger.info(f"  生成路径总数: {expr_expl['total_paths']}")
                
                if "path_exploration" in aqe_info:
                    logger.info("Path Exploration Phase:")
                    path_expl = aqe_info["path_exploration"]
                    if "paths" in path_expl:
                        logger.info(f"  评估路径数: {len(path_expl['paths'])}")
                        for path in path_expl["paths"]:
                            logger.info(f"    路径 {path['index']}: accuracy={path.get('accuracy', 'N/A')}, "
                                      f"latency={path.get('latency', 'N/A')}ms, cost={path.get('cost', 'N/A')}")
                    if "best_path" in path_expl:
                        best = path_expl["best_path"]
                        logger.info(f"  最优路径: 索引={best.get('index', 'N/A')}, "
                                  f"accuracy={best.get('accuracy', 'N/A')}, "
                                  f"latency={best.get('latency', 'N/A')}ms")
                
                if "exploitation" in aqe_info:
                    logger.info("Path Exploitation Phase:")
                    expl = aqe_info["exploitation"]
                    logger.info(f"  处理元组数: {expl.get('tuples', 'N/A')}")
                    logger.info(f"  执行时间: {expl.get('time_ms', 'N/A')}ms")
                    logger.info(f"  输入 tokens: {expl.get('input_tokens', 'N/A')}")
                    logger.info(f"  输出 tokens: {expl.get('output_tokens', 'N/A')}")
                
                if "overall_stats" in aqe_info:
                    logger.info("总体统计:")
                    stats = aqe_info["overall_stats"]
                    logger.info(f"  总执行时间: {stats.get('total_execution_time_ms', 'N/A')}ms")
                    logger.info(f"  总探索时间: {stats.get('total_exploration_time_ms', 'N/A')}ms")
                    logger.info(f"  总成本: {stats.get('total_cost', 'N/A')}")
            logger.info("=" * 60)
        
        try:
            if profiling_data.get('latency', 0) == 0.0 or profiling_data.get('cpu_time', 0) == 0.0:
                def aggregate_from_children(node: Dict[str, Any]) -> Dict[str, Any]:
                    result = {
                        'latency': node.get('latency', 0.0),
                        'cpu_time': node.get('cpu_time', 0.0),
                        'rows_returned': node.get('rows_returned', 0),
                        'cumulative_rows_scanned': node.get('cumulative_rows_scanned', 0),
                        'result_set_size': node.get('result_set_size', 0)
                    }
                    
                    children = node.get('children', [])
                    if children:
                        for child in children:
                            child_stats = aggregate_from_children(child)
                            result['latency'] = max(result['latency'], child_stats['latency'])
                            result['cpu_time'] = max(result['cpu_time'], child_stats['cpu_time'])
                            result['rows_returned'] = max(result['rows_returned'], child_stats['rows_returned'])
                            result['cumulative_rows_scanned'] = max(result['cumulative_rows_scanned'], child_stats['cumulative_rows_scanned'])
                            result['result_set_size'] = max(result['result_set_size'], child_stats['result_set_size'])
                    
                    return result
                
                aggregated = aggregate_from_children(profiling_data)
                if profiling_data.get('latency', 0) == 0.0 and aggregated['latency'] > 0:
                    profiling_data['latency'] = aggregated['latency']
                if profiling_data.get('cpu_time', 0) == 0.0 and aggregated['cpu_time'] > 0:
                    profiling_data['cpu_time'] = aggregated['cpu_time']
                if profiling_data.get('rows_returned', 0) == 0 and aggregated['rows_returned'] > 0:
                    profiling_data['rows_returned'] = aggregated['rows_returned']
                if profiling_data.get('cumulative_rows_scanned', 0) == 0 and aggregated['cumulative_rows_scanned'] > 0:
                    profiling_data['cumulative_rows_scanned'] = aggregated['cumulative_rows_scanned']
                if profiling_data.get('result_set_size', 0) == 0 and aggregated['result_set_size'] > 0:
                    profiling_data['result_set_size'] = aggregated['result_set_size']
            
            elapsed_ms = int((time.time() - t0) * 1000)
            
            if original_config:
                import config as cfg
                for key, value in original_config.items():
                    setattr(cfg, key, value)
                    logger.debug(f"恢复配置: {key} = {value}")
            
            logger.info("=" * 60)
            logger.info("【Profiling 统计信息】")
            logger.info(f"  总延迟: {profiling_data.get('latency', 0):.6f} 秒")
            logger.info(f"  CPU 时间: {profiling_data.get('cpu_time', 0):.6f} 秒")
            logger.info(f"  返回行数: {profiling_data.get('rows_returned', 0)}")
            logger.info(f"  扫描行数: {profiling_data.get('cumulative_rows_scanned', 0)}")
            logger.info(f"  结果集大小: {profiling_data.get('result_set_size', 0)} bytes")
            logger.info("=" * 60)
            
            result = {
                "ok": True,
                "profiling": profiling_data,
                "elapsed_ms": elapsed_ms
            }
            
            if aqe_info_list:
                result["aqe_info"] = aqe_info_list
                result["has_aqe"] = True
            else:
                result["has_aqe"] = False
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse profiling JSON: {e}, output preview: {output[:500]}")
            return {
                "ok": False,
                "error": f"Failed to parse profiling output: {str(e)}",
                "raw_output": output[:1000]
            }
        except Exception as e:
            logger.error(f"Failed to process profiling data: {e}")
            return {
                "ok": False,
                "error": str(e),
                "raw_output": output[:1000] if output else None
            }
    
    except Exception as e:
        logger.error(f"Profiling failed: {str(e)}", exc_info=True)

        if original_config:
            import config as cfg
            for key, value in original_config.items():
                setattr(cfg, key, value)
        
        elapsed_ms = int((time.time() - t0) * 1000)
        return {
            "ok": False,
            "error": str(e),
            "elapsed_ms": elapsed_ms
        }

