from dataclasses import dataclass
from typing import List, Dict
from engines.search.models.search_entity import SearchEntity
from engines.search.models.quality_result import QualityResult

@dataclass
class RankedGroup:
    label: str                    # "Excellent", "Very Good", dst
    sources: List[SearchEntity]
    quality_results: Dict[str, QualityResult]  # source_id → result

class RankingEngine:
    def rank(
        self,
        sources: List[SearchEntity],
        quality_results: Dict[str, QualityResult],
    ) -> List[RankedGroup]:
        """Sort by score desc, group by label."""
        
        # Sort sources based on tiebreaker rules:
        # 1. Score (desc)
        # 2. Track count (desc)
        # 3. Upload date (desc)
        
        def sort_key(source: SearchEntity):
            q = quality_results.get(source.id)
            score = q.score if q else 0
            track_count = getattr(source, 'track_count', getattr(source, 'item_count', 0))
            return (score, track_count, source.upload_date)

        sorted_sources = sorted(sources, key=sort_key, reverse=True)
        
        # Group by label
        groups_dict: Dict[str, RankedGroup] = {}
        # Enforce order of groups
        label_order = ["Excellent", "Very Good", "Good", "Fair", "Poor"]
        for label in label_order:
            groups_dict[label] = RankedGroup(label=label, sources=[], quality_results={})
            
        for s in sorted_sources:
            q = quality_results.get(s.id)
            if q:
                label = q.label
                if label not in groups_dict:
                    groups_dict[label] = RankedGroup(label=label, sources=[], quality_results={})
                groups_dict[label].sources.append(s)
                groups_dict[label].quality_results[s.id] = q

        # Filter out empty groups and return
        return [groups_dict[label] for label in label_order if len(groups_dict[label].sources) > 0]
