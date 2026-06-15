from dataclasses import dataclass, field
from typing import Dict, Any
from ui.themes.theme_manager import ThemeManager

@dataclass
class QualityResult:
    source_id: str
    score: int           # 0–100
    label: str           # "Excellent" | "Great" | "Poor"
    is_estimate: bool    # True = fase 1, False = fase 2

    breakdown: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def label_from_score(score: int) -> str:
        if score >= 95:  return "Excellent"
        if score >= 80:  return "Great"
        return "Poor"

    @property
    def badge_color(self) -> str:
        colors = {
            "Excellent": ThemeManager.get_color("success"),
            "Great":     ThemeManager.get_color("warning"),
            "Poor":      ThemeManager.get_color("danger"),
        }
        return colors.get(self.label, ThemeManager.get_color("text_muted"))
