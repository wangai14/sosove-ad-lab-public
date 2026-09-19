from __future__ import annotations

import unittest
from pathlib import Path


class MaterialReversePromptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.static_dir = Path(__file__).resolve().parents[1] / "static"
        cls.materials_html = (cls.static_dir / "materials.html").read_text(encoding="utf-8")
        cls.materials_script = (cls.static_dir / "materials.js").read_text(encoding="utf-8")
        cls.creator_script = (cls.static_dir / "app.js").read_text(encoding="utf-8")
        cls.styles = (cls.static_dir / "styles.css").read_text(encoding="utf-8")

    def test_each_smart_segment_exposes_reverse_prompt_action(self) -> None:
        self.assertIn('data-action="reverse-prompt"', self.materials_script)
        self.assertIn("openReversePromptDialog(item, segment)", self.materials_script)
        self.assertIn("反推 Prompt", self.materials_script)

    def test_dialog_supports_local_and_reference_modes(self) -> None:
        self.assertIn('id="material-reverse-prompt-dialog"', self.materials_html)
        self.assertIn('value="rebuild"', self.materials_html)
        self.assertIn('value="reference"', self.materials_html)
        self.assertIn("T2V。", self.materials_script)
        self.assertIn("R2V。@Video1", self.materials_script)
        self.assertIn("不转移原人物身份、面部、服装、房间、Logo、字幕或音频", self.materials_script)

    def test_seedance_skill_can_refine_reverse_prompt(self) -> None:
        self.assertIn('requestJson("/api/skill/optimize-prompt"', self.materials_script)
        self.assertIn("review.improvedPrompt", self.materials_script)
        self.assertIn("reversePromptEvidenceParts(item, segment)", self.materials_script)

    def test_prompt_handoff_preserves_creation_context(self) -> None:
        key = "seedanceMaterialReversePromptDraftV1"
        self.assertIn(key, self.materials_script)
        self.assertIn(key, self.creator_script)
        self.assertIn("function applyMaterialReversePromptDraft", self.creator_script)
        self.assertIn("draft.refVideo", self.creator_script)
        self.assertIn("draft.targetMarket", self.creator_script)
        self.assertIn("draft.contentLanguage", self.creator_script)

    def test_reverse_prompt_dialog_has_responsive_layout(self) -> None:
        self.assertIn(".material-reverse-prompt-panel", self.styles)
        self.assertIn(".material-reverse-prompt-mode", self.styles)
        self.assertIn(".material-reverse-prompt-footer", self.styles)


if __name__ == "__main__":
    unittest.main()
