# services/rule_engine.py
import re
from typing import Dict, Any, Optional
from datetime import datetime

class Intent:
    ADD = "add_activity"
    REMOVE = "remove_activity"
    MODIFY_TIME = "modify_time"
    MODIFY_DAY = "modify_day"
    CHANGE_BUDGET = "change_budget"
    VIEW_PLAN = "view_plan"
    SUGGEST = "suggest_alternative"
    UNKNOWN = "unknown"

class ParseResult:
    def __init__(self, intent: str = Intent.UNKNOWN, entities: Dict[str,Any]=None):
        self.intent = intent
        self.entities = entities or {}

class RuleEngine:
    day_patterns = [
        r"ngày\s*(\d+)",
        r"day\s*(\d+)"
    ]
    time_patterns = [
        r"(\d{1,2}[:h]\d{0,2})",   # "08:30" or "8h30" or "8:30"
        r"(\d{1,2})\s*h\b"         # "8h"
    ]
    
    def __init__(self):
        # synonyms
        self.add_syn = ["thêm", "add", "insert", "put"]
        self.remove_syn = ["xoá", "xóa", "remove", "delete"]
        self.time_syn = ["giờ", "h", ":"]
        self.suggest_syn = ["gợi ý", "recommend", "suggest", "thay thế", "alternative"]
        self.modify_syn = ["đổi", "change", "sửa", "update", "thay"]
        self.budget_syn = ["budget", "ngân sách", "chi phí", "tiền"]

    def _find_day(self, text: str) -> Optional[int]:
        for p in self.day_patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                try:
                    return int(m.group(1))
                except:
                    pass
        return None

    def _find_time(self, text: str) -> Optional[str]:
        for p in self.time_patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                return m.group(1).replace("h", ":").strip()
        return None

    def classify(self, text: str) -> ParseResult:
        lower = text.lower()
        # add
        if any(w in lower for w in self.add_syn):
            day = self._find_day(text)
            time = self._find_time(text)
            # try extract title after verbs: "thêm nhà hàng chay ngày 2 lúc 19:00"
            title = self._extract_title_for_add(text)
            return ParseResult(Intent.ADD, {"day": day, "time": time, "title": title})
        if any(w in lower for w in self.remove_syn):
            # try get item id (if user says id=123) or title
            m = re.search(r"id\s*(?:=|:)?\s*(\d+)", text)
            item_id = int(m.group(1)) if m else None
            title = self._extract_title_for_remove(text)
            day = self._find_day(text)
            return ParseResult(Intent.REMOVE, {"item_id": item_id, "title": title, "day": day})
        if any(w in lower for w in self.modify_syn) and "giờ" in lower or re.search(r"\d{1,2}[:h]\d{0,2}", text):
            item_id = None
            m = re.search(r"id\s*(?:=|:)?\s*(\d+)", text)
            if m:
                item_id = int(m.group(1))
            time = self._find_time(text)
            day = self._find_day(text)
            return ParseResult(Intent.MODIFY_TIME, {"item_id": item_id, "time": time, "day": day})
        if any(w in lower for w in self.budget_syn):
            m = re.search(r"(\d+[.,]?\d*)\s*(k|vnđ|vnd|usd)?", text)
            budget = m.group(1) if m else None
            return ParseResult(Intent.CHANGE_BUDGET, {"budget": budget})
        if any(w in lower for w in self.suggest_syn):
            day = self._find_day(text)
            return ParseResult(Intent.SUGGEST, {"day": day})
        # view plan
        if "xem" in lower or "show" in lower or "hiện tại" in lower:
            return ParseResult(Intent.VIEW_PLAN, {})
        return ParseResult(Intent.UNKNOWN, {})

    def _extract_title_for_add(self, text: str) -> Optional[str]:
        # heuristic: after 'thêm' or 'add' take following 1-6 words until 'ngày' or 'lúc' or 'vào'
        m = re.search(r"(?:thêm|add)\s+(.+?)(?:\bngày\b|\blúc\b|\bvào\b|$)", text, re.IGNORECASE)
        if m:
            t = m.group(1).strip()
            # truncate long
            return t[:200]
        return None

    def _extract_title_for_remove(self, text: str) -> Optional[str]:
        m = re.search(r"(?:xoá|xóa|remove|delete)\s+(.+?)(?:\bngày\b|\blúc\b|\bvào\b|$)", text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
        return None
