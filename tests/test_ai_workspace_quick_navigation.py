from __future__ import annotations

import unittest
from pathlib import Path


class AiWorkspaceQuickNavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.static_dir = Path(__file__).resolve().parents[1] / "static"
        cls.html = (cls.static_dir / "index.html").read_text(encoding="utf-8")
        cls.script = (cls.static_dir / "app.js").read_text(encoding="utf-8")
        cls.styles = (cls.static_dir / "styles.css").read_text(encoding="utf-8")

    def test_quick_navigation_exposes_each_workspace_view(self) -> None:
        for view in ("create", "assets", "assistant", "library", "settings"):
            self.assertIn(f'data-workspace-view="{view}"', self.html)
            self.assertIn(f'data-workspace-pane="{view}"', self.html)

    def test_workspace_switch_hides_inactive_panes_and_persists_view(self) -> None:
        self.assertIn("function setWorkspaceView", self.script)
        self.assertIn("pane.hidden = pane.dataset.workspacePane !== nextView", self.script)
        self.assertIn("WORKSPACE_VIEW_KEY", self.script)
        self.assertIn('target.closest("[data-workspace-pane]")', self.script)

    def test_layout_has_sticky_quick_nav_and_compact_mobile_views(self) -> None:
        self.assertIn(".creator-quick-nav", self.styles)
        self.assertIn('data-workspace-view="create"', self.styles)
        self.assertIn("[data-workspace-pane][hidden]", self.styles)
        self.assertIn("position: static", self.styles)


if __name__ == "__main__":
    unittest.main()
