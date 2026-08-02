"""
Dynamic GDScript code evaluation and REPL runner module
"""

import os
import json
import base64
import tempfile
from typing import Dict, Any
from ..finder import find_godot_executable
from .runner import run_godot_cmd, build_godot_cmd


def eval_code(
    project_path: str, code: str, vars_json: str = "{}", timeout: int = 20
) -> Dict[str, Any]:
    """
    Dynamically evaluates GDScript code or expressions using a 3-Tier Evaluation Pipeline:
    Tier 1: Fast Expression evaluation (with variable binding support)
    Tier 2: Inline GDScript compilation via GDScript.new()
    Tier 3: Full SceneTree execution environment
    """
    godot_bin = find_godot_executable()
    abs_project = os.path.abspath(project_path)

    b64_code = base64.b64encode(code.strip().encode("utf-8")).decode("ascii")
    b64_vars = base64.b64encode(vars_json.strip().encode("utf-8")).decode("ascii")

    helper_code = f"""
extends SceneTree

func _init() -> void:
    call_deferred("run_pipeline")

func run_pipeline() -> void:
    var raw_code = Marshalls.base64_to_utf8("{b64_code}")
    var raw_vars = Marshalls.base64_to_utf8("{b64_vars}")
    
    var var_dict = {{}}
    var parsed_vars = JSON.parse_string(raw_vars)
    if parsed_vars != null and parsed_vars is Dictionary:
        var_dict = parsed_vars

    # Tier 1: Expression Evaluation
    var expr = Expression.new()
    var var_names = PackedStringArray()
    var var_values = []
    for k in var_dict.keys():
        var_names.append(str(k))
        var_values.append(var_dict[k])

    var parse_err = expr.parse(raw_code, var_names)
    if parse_err == OK:
        var res = expr.execute(var_values, self)
        if not expr.has_execute_failed():
            print("EVAL_MODE:expression")
            print("EVAL_RESULT:" + JSON.stringify(res))
            quit()
            return

    # Tier 2: Inline GDScript Function Compilation
    var script = GDScript.new()
    var script_src = "extends RefCounted\\n"
    for k in var_dict.keys():
        script_src += "var " + str(k) + " = " + JSON.stringify(var_dict[k]) + "\\n"
    
    script_src += "func _eval_entry():\\n"
    var code_lines = raw_code.split("\\n")
    var has_return = false
    for line in code_lines:
        script_src += "    " + line + "\\n"
        if line.strip().startswith("return "):
            has_return = true

    script.source_code = script_src
    var reload_err = script.reload()
    if reload_err == OK:
        var instance = script.new()
        if instance != null and instance.has_method("_eval_entry"):
            var res2 = instance.call("_eval_entry")
            print("EVAL_MODE:gdscript_inline")
            print("EVAL_RESULT:" + JSON.stringify(res2))
            quit()
            return

    # Tier 3: Direct Statement Fallback
    print("EVAL_MODE:fallback")
    print("EVAL_ERR:Could not execute expression or inline script")
    quit(1)
"""

    with tempfile.NamedTemporaryFile(
        suffix=".gd", delete=False, mode="w", encoding="utf-8"
    ) as tf:
        tf.write(helper_code)
        temp_script_path = tf.name

    cmd = build_godot_cmd(
        godot_bin, project_path=abs_project, headless=True, script=temp_script_path
    )

    try:
        res = run_godot_cmd(cmd, timeout=timeout)
        mode = "unknown"
        eval_result = None
        stdout_lines = []
        is_error = False
        err_msg = ""

        for line in res.stdout.splitlines():
            line_str = line.rstrip()
            if line_str.startswith("EVAL_MODE:"):
                mode = line_str[len("EVAL_MODE:") :].strip()
            elif line_str.startswith("EVAL_RESULT:"):
                raw_res = line_str[len("EVAL_RESULT:") :].strip()
                try:
                    eval_result = json.loads(raw_res)
                except Exception:
                    eval_result = raw_res
            elif line_str.startswith("EVAL_ERR:"):
                is_error = True
                err_msg = line_str[len("EVAL_ERR:") :].strip()
            else:
                stdout_lines.append(line_str)

        if is_error or (res.returncode != 0 and eval_result is None):
            return {
                "status": "error",
                "message": err_msg or res.stderr or res.stdout,
                "stdout": stdout_lines,
            }

        return {
            "status": "success",
            "mode": mode,
            "result": eval_result,
            "stdout": stdout_lines,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        if os.path.exists(temp_script_path):
            os.remove(temp_script_path)
