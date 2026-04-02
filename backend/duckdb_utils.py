import json
import re
from pathlib import Path
from typing import Dict, Any, Optional
import config
from duckdb_binary import execute_sql as _execute_sql, get_db_path as _get_db_path

def _safe_name(name: str) -> str:
    base = re.sub(r"[^0-9a-zA-Z_]+", "_", Path(name).stem)
    if re.match(r"^\d", base):
        base = "_" + base
    return base.lower()

def register_file(path: Path) -> str:
    view_name = _safe_name(path.name)
    p = str(path.resolve().as_posix())
    p_escaped = p.replace("'", "''")
    
    if path.suffix.lower() == ".csv":
        sql = f"""
        CREATE OR REPLACE VIEW {view_name} AS
        SELECT * FROM read_csv_auto('{p_escaped}', header=True);
        """
    elif path.suffix.lower() in (".parquet", ".pq"):
        sql = f"CREATE OR REPLACE VIEW {view_name} AS SELECT * FROM read_parquet('{p_escaped}');"
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")
    
    result = _execute_sql(sql)
    
    if "error" in result:
        raise RuntimeError(result["error"])
    
    return view_name

def execute_sql(query: str) -> Dict[str, Any]:
    return _execute_sql(query)

def explain_query(query: str) -> Dict[str, Any]:
    from db_session import explain_query as _explain_query
    return _explain_query(query)

def shell_explain_text(db_path: Path, sql: str) -> str:
    from duckdb_binary import explain_query as _explain_query
    result = _explain_query(sql, str(db_path))
    if result.get("format") == "text":
        return result.get("text", "")
    else:
        import json
        return json.dumps(result.get("raw", {}), indent=2)

def run_from_json(input_path: Path, output_path: Path) -> None:
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        query = (payload.get("query") or "").strip()
        if not query:
            raise ValueError("Empty query")
        res = execute_sql(query)
        out = {"ok": True, **res}
    except Exception as e:
        out = {"ok": False, "error": str(e)}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)

def explain_from_json(input_path: Path, output_path: Path) -> None:
    try:
        with open(input_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        query = (payload.get("query") or "").strip()
        if not query:
            raise ValueError("Empty query")
        res = explain_query(query)
        out = {"ok": True, **res}
    except Exception as e:
        out = {"ok": False, "error": str(e)}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
