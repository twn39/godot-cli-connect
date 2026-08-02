"""
Dynamic GDScript code evaluation and REPL runner module
"""

import base64
import json
import os
import tempfile
from typing import Any

from ..finder import find_godot_executable
from ..models import err, ok
from .runner import build_godot_cmd, run_godot_cmd


def eval_code(
    project_path: str, code: str, vars_json: str = "{}", timeout: int = 20
) -> dict[str, Any]:
    """
    Dynamically evaluates GDScript code or expressions using a 2-Tier Evaluation Pipeline:
    Tier 1: Fast Expression evaluation (with variable binding support)
    Tier 2: Direct disk-compiled GDScript function execution
    """
    godot_bin = find_godot_executable()
    abs_project = os.path.abspath(project_path)

    b64_code = base64.b64encode(code.strip().encode("utf-8")).decode("ascii")
    b64_vars = base64.b64encode(vars_json.strip().encode("utf-8")).decode("ascii")

    # Prepare indented user function body for Tier 2 fallback
    body_lines = []
    try:
        parsed_vars_dict = json.loads(vars_json or "{}")
        if isinstance(parsed_vars_dict, dict):
            for v_key in parsed_vars_dict.keys():
                body_lines.append(f"var {v_key} = _vars.get('{v_key}')")
    except Exception:
        pass

    code_clean = code.strip().replace(";", "\n")
    has_return = False
    for line in code_clean.splitlines():
        line_s = line.strip()
        if line_s:
            body_lines.append(line_s)
            if line_s.startswith("return "):
                has_return = True
    if not has_return:
        body_lines.append("return null")

    indented_body = "\n    ".join(body_lines) if body_lines else "return null"

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

    # Tier 2: Custom Function Execution
    var res2 = _user_eval_entry(var_dict)
    print("EVAL_MODE:gdscript_inline")
    print("EVAL_RESULT:" + JSON.stringify(res2))
    quit()

func _user_eval_entry(_vars: Dictionary) -> Variant:
    {indented_body}
"""

    with tempfile.NamedTemporaryFile(suffix=".gd", delete=False, mode="w", encoding="utf-8") as tf:
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
            return err(
                err_msg or res.stderr or res.stdout or "Evaluation failed",
                stdout=stdout_lines,
            )

        return ok(mode=mode, result=eval_result, stdout=stdout_lines)
    except Exception as e:
        return err(str(e))
    finally:
        if os.path.exists(temp_script_path):
            os.remove(temp_script_path)
