from flask import Flask, request, jsonify  # pyright: ignore[reportMissingImports]
from flask_cors import CORS  # pyright: ignore[reportMissingModuleSource]
from pathlib import Path
from werkzeug.utils import secure_filename  # pyright: ignore[reportMissingImports]
import logging
import traceback
from dotenv import load_dotenv  # pyright: ignore[reportMissingImports]

load_dotenv()

import config
from duckdb_utils import register_file
from db_session import set_db_path, get_db_path, execute_sql, explain_query, profile_query, list_catalog, get_table_columns

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

ALLOWED_EXT = {".csv", ".parquet", ".pq"}

app = Flask(__name__)
CORS(app)


def _allowed(filename: str) -> bool:
    return Path(filename).suffix.lower() in ALLOWED_EXT


@app.route("/", methods=["GET"])
def root():
    
    return jsonify({
        "message": "DuckDB API Server",
        "version": "1.0",
        "endpoints": {
            "health": "/api/health",
            "connection": "/api/connection",
            "connect": "/api/connect",
            "catalog": "/api/catalog",
            "upload": "/api/upload",
            "run": "/api/run",
            "explain": "/api/explain",
            "debug": "/api/debug/test-response"
        },
        "note": "This is an API server. For the web interface, please use the frontend application."
    })


@app.route("/api/debug/test-response", methods=["GET", "POST"])
def debug_test_response():
    
    try:
        method = request.method
        body = None
        if method == "POST":
            try:
                body = request.get_json(force=True, silent=True)
            except:
                body = "Failed to parse JSON"
        
        response_data = {
            "ok": True,
            "message": "Debug test endpoint",
            "method": method,
            "headers": dict(request.headers),
            "body": body,
            "server_status": "running"
        }
        
        logger.info(f"Debug test response: {response_data}")
        return jsonify(response_data)
    except Exception as e:
        logger.error(f"Debug endpoint error: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            "ok": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"ok": True})


@app.route("/api/connection", methods=["GET"])
def connection_info():
    try:
        logger.info("Getting connection info")
        db_path = get_db_path() or ""
        logger.info(f"Current db_path: {db_path}")
        return jsonify({"ok": True, "db_path": db_path})
    except Exception as e:
        logger.error(f"Failed to get connection info: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            "ok": False,
            "error": f"Failed to get connection info: {str(e)}",
            "db_path": ""
        }), 500


@app.route("/api/connect", methods=["POST"])
def api_connect():
    try:
        data = request.get_json(force=True, silent=True) or {}
        db_path = (data.get("db_path") or "").strip()
        logger.info(f"Connection request received: db_path={db_path}")
        
        if not db_path:
            logger.warning("Empty db_path provided")
            return jsonify({"ok": False, "error": "Empty db_path"}), 400
        
        path_obj = Path(db_path)
        
        if not path_obj.is_absolute():
            path_obj = Path(__file__).parent / "db" / db_path
        
        logger.info(f"Resolved database path: {path_obj}")
        
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            logger.info(f"Setting database path: {path_obj}")
            path = set_db_path(str(path_obj))
            logger.info(f"Database path set successfully: {path}")
            
            try:
                logger.info("Testing database connection with SELECT 1")
                test_result = execute_sql("SELECT 1 as test;")
                logger.info(f"Test query result: {test_result}")
                
                if "error" in test_result:
                    error_msg = f"Database connection test failed: {test_result.get('error', 'Unknown error')}"
                    logger.error(error_msg)
                    return jsonify({
                        "ok": False, 
                        "error": error_msg,
                        "debug": {
                            "db_path": str(path),
                            "test_result": test_result
                        }
                    }), 500
            except Exception as test_e:
                error_msg = f"Database connection test failed: {str(test_e)}"
                logger.error(f"{error_msg}\n{traceback.format_exc()}")
                return jsonify({
                    "ok": False,
                    "error": error_msg,
                    "debug": {
                        "db_path": str(path),
                        "exception_type": type(test_e).__name__,
                        "traceback": traceback.format_exc()
                    }
                }), 500
            
            logger.info(f"Connection successful: {path}")
            return jsonify({"ok": True, "db_path": path})
        except Exception as db_e:
            error_msg = f"Failed to connect to database: {str(db_e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            return jsonify({
                "ok": False,
                "error": error_msg,
                "debug": {
                    "db_path": str(path_obj),
                    "exception_type": type(db_e).__name__,
                    "traceback": traceback.format_exc()
                }
            }), 500
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(f"{error_msg}\n{traceback.format_exc()}")
        return jsonify({
            "ok": False,
            "error": error_msg,
            "debug": {
                "exception_type": type(e).__name__,
                "traceback": traceback.format_exc()
            }
        }), 500


@app.route("/api/catalog", methods=["GET"])
def api_catalog():
    try:
        data = list_catalog()
        return jsonify({"ok": True, **data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/table/columns", methods=["GET"])
def api_table_columns():
    try:
        schema_name = request.args.get("schema", "").strip()
        table_name = request.args.get("table", "").strip()
        
        if not schema_name or not table_name:
            return jsonify({"ok": False, "error": "Missing schema or table parameter"}), 400
        
        result = get_table_columns(schema_name, table_name)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Failed to get table columns: {str(e)}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/upload", methods=["POST"])
def api_upload():
    if "files" not in request.files:
        return jsonify({"ok": False, "error": "No files field"}), 400

    files = request.files.getlist("files")
    saved, views = [], []
    for f in files:
        filename = f.filename
        if not filename:
            continue
        if not _allowed(filename):
            return jsonify({"ok": False, "error": f"Unsupported file: {filename}"}), 400

        fname = secure_filename(filename)
        dest = config.DATA_DIR / fname
        f.save(dest)
        view = register_file(dest)
        saved.append(str(dest.name))
        views.append(view)

    return jsonify({"ok": True, "files": saved, "views": views})


@app.route("/api/upload_db", methods=["POST"])
def api_upload_db():
    if "file" not in request.files:
        return jsonify({"ok": False, "error": "No file field"}), 400
    f = request.files["file"]
    filename = f.filename
    if not filename:
        return jsonify({"ok": False, "error": "Empty filename"}), 400
    if not filename.endswith(".duckdb"):
        return jsonify({"ok": False, "error": "Only .duckdb files are supported"}), 400
    fname = secure_filename(filename)
    dest = Path(__file__).parent / "db" / fname
    dest.parent.mkdir(parents=True, exist_ok=True)
    f.save(dest)
    try:
        path = set_db_path(str(dest))
        execute_sql("SELECT 1 as test;")
        return jsonify({"ok": True, "db_path": str(path)})
    except Exception as e:
        logger.error(f"Failed to connect after upload: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/run", methods=["POST"])
def api_run():
    data = request.get_json(force=True, silent=True) or {}
    query = (data.get("query") or "").strip()
    if not query:
        return jsonify({"ok": False, "error": "Empty query"}), 400
    
    logger.info(f"收到 SQL 查询请求: {query[:100]}..." if len(query) > 100 else f"收到 SQL 查询请求: {query}")
    
    try:
        result = execute_sql(query)
        logger.info(f"SQL 查询执行成功，返回 {result.get('row_count', 0)} 行，耗时 {result.get('elapsed_ms', 0)}ms")
        return jsonify({"ok": True, **result})
    except Exception as e:
        logger.error(f"SQL 查询执行失败: {str(e)}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/explain", methods=["POST"])
def api_explain():
    data = request.get_json(force=True, silent=True) or {}
    query = (data.get("query") or "").strip()
    custom_config = data.get("config", "").strip()  
    
    if not query:
        return jsonify({"ok": False, "error": "Empty query"}), 400
    
    logger.info(f"收到 EXPLAIN 查询请求: {query[:100]}..." if len(query) > 100 else f"收到 EXPLAIN 查询请求: {query}")
    
    try:
        config_overrides = {}
        if custom_config:
            logger.info(f"解析自定义配置: {custom_config[:100]}...")
            config_overrides = parse_set_commands(custom_config)
            if config_overrides:
                logger.info(f"配置覆盖: {config_overrides}")
        
        result = explain_query(query, config_overrides=config_overrides, set_commands=custom_config)
        logger.info(f"EXPLAIN 查询执行成功，耗时 {result.get('elapsed_ms', 0)}ms")
        return jsonify({"ok": True, **result})
    except Exception as e:
        logger.error(f"EXPLAIN 查询执行失败: {str(e)}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/profile", methods=["POST"])
def api_profile():
    data = request.get_json(force=True, silent=True) or {}
    query = (data.get("query") or "").strip()
    custom_config = data.get("config", "").strip()
    
    if not query:
        return jsonify({"ok": False, "error": "Empty query"}), 400
    
    logger.info(f"收到 PROFILING 查询请求: {query[:100]}..." if len(query) > 100 else f"收到 PROFILING 查询请求: {query}")
    
    try:
        config_overrides = {}
        if custom_config:
            logger.info(f"解析自定义配置: {custom_config[:100]}...")
            config_overrides = parse_set_commands(custom_config)
            if config_overrides:
                logger.info(f"配置覆盖: {config_overrides}")
        
        result = profile_query(query, config_overrides=config_overrides, set_commands=custom_config)
        
        if result.get("ok"):
            logger.info(f"PROFILING 查询执行成功，耗时 {result.get('elapsed_ms', 0)}ms")
            return jsonify(result)
        else:
            logger.error(f"PROFILING 查询执行失败: {result.get('error', 'Unknown error')}")
            return jsonify(result), 500
    except Exception as e:
        logger.error(f"PROFILING 查询执行失败: {str(e)}")
        return jsonify({"ok": False, "error": str(e)}), 500


def parse_set_commands(config_text):
    import re
    config_overrides = {}
    
    if not config_text or not config_text.strip():
        return config_overrides
    
    lines = config_text.split('\n')
    set_regex = re.compile(r'SET\s+(\w+)\s*=\s*(.+?);?\s*$', re.IGNORECASE)
    
    for line in lines:
        match = set_regex.match(line.strip())
        if match:
            key = match.group(1)
            value = match.group(2).strip()
            
            if value.endswith(';'):
                value = value[:-1].strip()
            
            if (value.startswith("'") and value.endswith("'")) or \
               (value.startswith('"') and value.endswith('"')):
                value = value[1:-1]
            
            if value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            elif value.replace('.', '', 1).replace('-', '', 1).isdigit():
                value = float(value) if '.' in value else int(value)
            
            config_overrides[key] = value
    
    return config_overrides


@app.route("/api/config", methods=["GET"])
def api_get_config():
    try:
        current_config = {
            "llm_model": config.LLM_MODEL,
            "optimizer_model": config.OPTIMIZER_MODEL,
            "llm_url": config.LLM_URL,
            "llm_api_key": config.LLM_API_KEY[:20] + "..." if len(config.LLM_API_KEY) > 20 else config.LLM_API_KEY,
            "semantic_batch_size": config.SEMANTIC_BATCH_SIZE,
            "enable_semantic_filter_multiplexer": config.ENABLE_SEMANTIC_FILTER_MULTIPLEXER,
            "semantic_filter_accuracy_threshold": config.SEMANTIC_FILTER_ACCURACY_THRESHOLD,
            "semantic_filter_latency_first": config.SEMANTIC_FILTER_LATENCY_FIRST,
            "semantic_filter_batch_size": config.SEMANTIC_FILTER_BATCH_SIZE,
            "enable_logging": config.ENABLE_LOGGING,
            "logging_level": config.LOGGING_LEVEL,
            "enable_partial_deduction": config.ENABLE_PARTIAL_DEDUCTION,
            "enable_nl_expression_compression": config.ENABLE_NL_EXPRESSION_COMPRESSION,
        }
        return jsonify({"ok": True, "config": current_config})
    except Exception as e:
        logger.error(f"获取配置失败: {str(e)}")
        return jsonify({"ok": False, "error": str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({"ok": False, "error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"ok": False, "error": "Internal server error"}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify({
        "ok": False,
        "error": f"Unexpected error: {str(e)}"
    }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=True)
