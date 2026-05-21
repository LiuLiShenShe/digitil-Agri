import tempfile
import unittest
from pathlib import Path

import phase0_baseline_guard as guard


class Phase0BaselineGuardTest(unittest.TestCase):
    def test_count_assets_counts_backend_and_frontend_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            backend_models = root / "digital-twingo" / "scene-server-go" / "scene-assets" / "models"
            backend_thumbs = root / "digital-twingo" / "scene-server-go" / "scene-assets" / "thumbs"
            frontend_models = root / "digital-twingo" / "scene-design-v2" / "public" / "models"
            frontend_images = root / "digital-twingo" / "scene-design-v2" / "public" / "images"
            for directory in (backend_models, backend_thumbs, frontend_models, frontend_images):
                directory.mkdir(parents=True)

            (backend_models / "greenhouse.glb").write_text("", encoding="utf-8")
            (backend_models / "tomato.GLB").write_text("", encoding="utf-8")
            (backend_thumbs / "greenhouse.jpg").write_text("", encoding="utf-8")
            (frontend_models / "sensor.glb").write_text("", encoding="utf-8")
            (frontend_images / "sensor.png").write_text("", encoding="utf-8")

            counts = guard.count_assets(root)

        self.assertEqual(counts.backend_glb, 2)
        self.assertEqual(counts.backend_thumbnails, 1)
        self.assertEqual(counts.frontend_glb, 1)
        self.assertEqual(counts.frontend_images, 1)

    def test_evaluate_hard_gates_fails_on_failed_command(self):
        commands = [
            guard.CommandResult("openspec validate --all --strict", 0, "ok", "- Validating..."),
            guard.CommandResult("go test ./...", 1, "", "boom"),
            guard.CommandResult(
                "npm run build",
                0,
                "rendering chunks...\n(!) Some chunks are larger than 500 kB after minification.",
                "",
            ),
        ]

        result = guard.evaluate_hard_gates(commands)

        self.assertFalse(result.ok)
        self.assertEqual(result.failed_commands, ["go test ./..."])
        self.assertEqual(
            result.warnings,
            ["npm run build: (!) Some chunks are larger than 500 kB after minification."],
        )

    def test_parse_active_changes_keeps_unimplemented_changes_uncomplete(self):
        payload = {
            "changes": [
                {
                    "name": "add-agricultural-object-model",
                    "completedTasks": 0,
                    "totalTasks": 10,
                    "status": "in-progress",
                },
                {
                    "name": "add-agent-operation-trace",
                    "completedTasks": 0,
                    "totalTasks": 10,
                    "status": "in-progress",
                },
            ]
        }

        changes = guard.parse_active_changes(payload)

        self.assertEqual([change.name for change in changes], ["add-agricultural-object-model", "add-agent-operation-trace"])
        self.assertFalse(any(change.is_implemented for change in changes))

    def test_render_report_redacts_secrets_and_records_mvp_boundary(self):
        report = guard.render_report(
            generated_on="2026-05-21",
            command_results=[
                guard.CommandResult(
                    "check config",
                    0,
                    "api-key: abc\npassword: root\nauthorization: bearer token\nsafe: value",
                    "",
                )
            ],
            active_changes=[
                guard.ActiveChange("add-farm-memory-layer", 0, 10, "in-progress"),
            ],
            asset_counts=guard.AssetCounts(341, 7, 27, 34),
            data_sources=guard.default_data_sources(),
            gate_result=guard.GateResult(ok=True, failed_commands=[], warnings=[]),
        )

        self.assertIn("1 个温室、20 株番茄、1 个气象站、1 个水泵/灌溉设备、1 个摄像头、1 个传感器组", report)
        self.assertIn("add-farm-memory-layer | 0/10 | in-progress | 未实现", report)
        self.assertIn("backend scene-assets GLB | 341", report)
        self.assertIn("api-key: [REDACTED]", report)
        self.assertIn("password: [REDACTED]", report)
        self.assertIn("authorization: [REDACTED]", report)
        self.assertNotIn("abc", report)
        self.assertNotIn("bearer token", report)


if __name__ == "__main__":
    unittest.main()
