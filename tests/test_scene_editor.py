"""
Unit and integration tests for scene_editor module and create-scene / add-node / edit-node / remove-node CLI commands
"""

from typer.testing import CliRunner

from godot_cli_connect.cli import app
from godot_cli_connect.operations.scene_editor import (
    add_node_to_scene,
    create_scene,
    edit_node_in_scene,
    remove_node_from_scene,
)

runner = CliRunner()


def test_create_scene_offline(tmp_path):
    scene_file = tmp_path / "player.tscn"
    res = create_scene(
        str(tmp_path), str(scene_file), root_type="CharacterBody2D", root_name="Player"
    )

    assert res["status"] == "success"
    assert res["root_name"] == "Player"
    assert res["root_type"] == "CharacterBody2D"
    assert scene_file.exists()

    content = scene_file.read_text()
    assert 'name="Player"' in content
    assert 'type="CharacterBody2D"' in content


def test_add_node_to_scene_offline(tmp_path):
    scene_file = tmp_path / "player.tscn"
    create_scene(
        str(tmp_path), str(scene_file), root_type="CharacterBody2D", root_name="Player"
    )

    res = add_node_to_scene(
        str(tmp_path),
        str(scene_file),
        node_name="Sprite2D",
        node_type="Sprite2D",
        parent_path=".",
    )
    assert res["status"] == "success"
    assert res["node_name"] == "Sprite2D"

    content = scene_file.read_text()
    assert 'name="Sprite2D"' in content


def test_edit_and_remove_node_in_scene(tmp_path):
    scene_file = tmp_path / "player.tscn"
    create_scene(
        str(tmp_path), str(scene_file), root_type="CharacterBody2D", root_name="Player"
    )
    add_node_to_scene(
        str(tmp_path),
        str(scene_file),
        node_name="Sprite2D",
        node_type="Sprite2D",
        parent_path=".",
    )

    # Edit node
    edit_res = edit_node_in_scene(
        str(tmp_path),
        str(scene_file),
        node_path="Sprite2D",
        properties_json='{"visible": false}',
    )
    assert edit_res["status"] == "success"

    # Remove node
    rm_res = remove_node_from_scene(
        str(tmp_path), str(scene_file), node_path="Sprite2D"
    )
    assert rm_res["status"] == "success"


def test_cli_create_scene(tmp_path):
    res = runner.invoke(
        app,
        [
            "create-scene",
            "res://enemy.tscn",
            "-r",
            "Node2D",
            "-p",
            str(tmp_path),
            "--json",
        ],
    )
    assert res.exit_code == 0
    assert '"status": "success"' in res.stdout


def test_cli_add_node(tmp_path):
    scene_file = tmp_path / "enemy.tscn"
    create_scene(str(tmp_path), str(scene_file), root_type="Node2D")

    res = runner.invoke(
        app,
        [
            "add-node",
            str(scene_file),
            "-n",
            "Gun",
            "-t",
            "Node2D",
            "-p",
            str(tmp_path),
            "--json",
        ],
    )
    assert res.exit_code == 0
    assert '"status": "success"' in res.stdout
    assert '"node_name": "Gun"' in res.stdout


def test_cli_edit_and_remove_node(tmp_path):
    scene_file = tmp_path / "enemy.tscn"
    create_scene(str(tmp_path), str(scene_file), root_type="Node2D")
    add_node_to_scene(
        str(tmp_path), str(scene_file), node_name="Gun", node_type="Node2D"
    )

    edit_res = runner.invoke(
        app,
        [
            "edit-node",
            str(scene_file),
            "-n",
            "Gun",
            "-props",
            '{"visible": false}',
            "-p",
            str(tmp_path),
            "--json",
        ],
    )
    assert edit_res.exit_code == 0
    assert '"status": "success"' in edit_res.stdout

    rm_res = runner.invoke(
        app,
        [
            "remove-node",
            str(scene_file),
            "-n",
            "Gun",
            "-p",
            str(tmp_path),
            "--json",
        ],
    )
    assert rm_res.exit_code == 0
    assert '"status": "success"' in rm_res.stdout


def test_connect_and_disconnect_signal(tmp_path):
    scene_file = tmp_path / "ui.tscn"
    create_scene(str(tmp_path), str(scene_file), root_type="Control", root_name="UI")
    add_node_to_scene(
        str(tmp_path), str(scene_file), node_name="Button", node_type="Button"
    )

    from godot_cli_connect.operations.scene_editor import (
        connect_signal,
        disconnect_signal,
        inspect_signals,
    )

    # Connect signal
    conn_res = connect_signal(
        str(tmp_path),
        str(scene_file),
        from_node="Button",
        signal_name="pressed",
        to_node=".",
        method_name="_on_button_pressed",
        one_shot=True,
    )
    assert conn_res["status"] == "success"

    # Inspect signals
    insp_res = inspect_signals(str(tmp_path), str(scene_file))
    assert insp_res["status"] == "success"
    assert insp_res["connections_count"] == 1
    assert insp_res["connections"][0]["signal"] == "pressed"

    # Disconnect signal
    disc_res = disconnect_signal(
        str(tmp_path),
        str(scene_file),
        from_node="Button",
        signal_name="pressed",
        to_node=".",
        method_name="_on_button_pressed",
    )
    assert disc_res["status"] == "success"

    # Verify disconnected
    insp_res2 = inspect_signals(str(tmp_path), str(scene_file))
    assert insp_res2["connections_count"] == 0


def test_rename_and_reparent_node(tmp_path):
    scene_file = tmp_path / "game.tscn"
    create_scene(str(tmp_path), str(scene_file), root_type="Node2D", root_name="Game")
    add_node_to_scene(
        str(tmp_path), str(scene_file), node_name="Box", node_type="Node2D"
    )
    add_node_to_scene(
        str(tmp_path), str(scene_file), node_name="Container", node_type="Node2D"
    )

    from godot_cli_connect.operations.scene_editor import (
        rename_node,
        reparent_node,
    )

    # Rename
    ren_res = rename_node(
        str(tmp_path), str(scene_file), node_path="Box", new_name="MagicBox"
    )
    assert ren_res["status"] == "success"

    # Reparent
    rep_res = reparent_node(
        str(tmp_path),
        str(scene_file),
        node_path="MagicBox",
        new_parent_path="Container",
    )
    assert rep_res["status"] == "success"

    content = scene_file.read_text()
    assert 'name="MagicBox"' in content
    assert 'parent="Container"' in content


def test_cli_bind_signal_and_rename_node(tmp_path):
    scene_file = tmp_path / "menu.tscn"
    create_scene(str(tmp_path), str(scene_file), root_type="Control", root_name="Menu")
    add_node_to_scene(
        str(tmp_path), str(scene_file), node_name="StartBtn", node_type="Button"
    )

    # Bind signal CLI
    res = runner.invoke(
        app,
        [
            "bind-signal",
            str(scene_file),
            "-f",
            "StartBtn",
            "-s",
            "pressed",
            "-t",
            ".",
            "-m",
            "_on_start_pressed",
            "-p",
            str(tmp_path),
            "--json",
        ],
    )
    assert res.exit_code == 0
    assert '"status": "success"' in res.stdout

    # Inspect signals CLI
    insp_res = runner.invoke(
        app,
        [
            "inspect-signals",
            str(scene_file),
            "-p",
            str(tmp_path),
            "--json",
        ],
    )
    assert insp_res.exit_code == 0
    assert '"connections_count": 1' in insp_res.stdout

    # Rename node CLI
    ren_res = runner.invoke(
        app,
        [
            "rename-node",
            str(scene_file),
            "-n",
            "StartBtn",
            "-new",
            "PlayButton",
            "-p",
            str(tmp_path),
            "--json",
        ],
    )
    assert ren_res.exit_code == 0
    assert '"status": "success"' in ren_res.stdout

