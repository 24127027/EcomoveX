import re
from typing import Any, Dict, List, Optional


class Intent:
    ADD = "add_activity"
    REMOVE = "remove_activity"
    MODIFY_TIME = "modify_time"
    MODIFY_DAY = "modify_day"
    MODIFY_LOCATION = "modify_location"
    CHANGE_BUDGET = "change_budget"
    VIEW_PLAN = "view_plan"
    SUGGEST = "suggest_alternative"
    SEARCH_DESTINATION = "search_destination"
    GET_WEATHER = "get_weather"
    GET_ROUTE = "get_route"
    UNKNOWN = "unknown"


class ParseResult:
    def __init__(
        self,
        intent: str = Intent.UNKNOWN,
        entities: Dict[str, Any] = None,
        confidence: float = 0.0,
    ):
        self.intent = intent
        self.entities = entities or {}
        self.confidence = confidence

    def __repr__(self):
        return (
            f"ParseResult(intent={self.intent}, "
            f"entities={self.entities}, confidence={self.confidence})"
        )


class RuleEngine:
    day_patterns = [r"ngày\s*(\d+)", r"day\s*(\d+)", r"thứ\s*(\d+)", r"hôm\s*(\d+)"]

    time_patterns = [
        r"(\d{1,2}[:h]\d{2})",  # "08:30" or "8h30"
        r"(\d{1,2})\s*giờ\s*(\d{2})?",  # "8 giờ 30"
        r"(\d{1,2})\s*h\s*(\d{2})?",  # "8h" or "8h30"
        r"lúc\s*(\d{1,2}[:h]\d{0,2})",  # "lúc 8h30"
        r"at\s*(\d{1,2}[:]\d{2})",  # "at 8:30"
    ]

    budget_patterns = [
        r"(\d+(?:[.,]\d+)?)\s*(?:triệu|tr|million|m)",
        r"(\d+(?:[.,]\d+)?)\s*(?:nghìn|k|thousand)",
        r"(\d+(?:[.,]\d+)?)\s*(?:vnđ|vnd|đồng|dong)",
        r"(\d+(?:[.,]\d+)?)\s*(?:usd|\$)",
        r"(\d+(?:[.,]\d+)?)",
    ]

    location_patterns = [
        r"(?:ở|tại|at|in)\s+([A-Za-zÀ-ỹ\s]+?)(?:\s+ngày|\s+lúc|\s+vào|$)",
        r"đến\s+([A-Za-zÀ-ỹ\s]+?)(?:\s+ngày|\s+lúc|\s+vào|$)",
    ]

    def __init__(self):
        self.add_syn_vi = [
            "thêm",
            "thêm vào",
            "cho thêm",
            "bổ sung",
            "đưa thêm",
            "thêm nữa",
        ]
        self.add_syn_en = ["add", "insert", "put", "include", "append", "create"]

        self.remove_syn_vi = [
            "xoá",
            "xóa",
            "bỏ",
            "loại bỏ",
            "gỡ bỏ",
            "xoá đi",
            "bỏ đi",
            "hủy",
        ]
        self.remove_syn_en = ["remove", "delete", "cancel", "drop", "eliminate"]

        self.modify_syn_vi = [
            "đổi",
            "thay",
            "sửa",
            "chỉnh",
            "cập nhật",
            "thay đổi",
            "điều chỉnh",
        ]
        self.modify_syn_en = ["change", "modify", "update", "edit", "adjust", "alter"]

        self.suggest_syn_vi = [
            "gợi ý",
            "đề xuất",
            "giới thiệu",
            "tư vấn",
            "recommend",
            "thay thế",
        ]
        self.suggest_syn_en = [
            "suggest",
            "recommend",
            "advise",
            "propose",
            "alternative",
        ]

        self.budget_syn_vi = ["ngân sách", "chi phí", "tiền", "giá", "budget", "cost"]
        self.budget_syn_en = ["budget", "cost", "price", "expense", "money"]

        self.view_syn_vi = ["xem", "hiển thị", "cho xem", "cho biết", "show", "view"]
        self.view_syn_en = ["view", "show", "display", "see", "list"]

        self.search_syn_vi = ["tìm", "tìm kiếm", "search", "tra", "tra cứu"]
        self.search_syn_en = ["search", "find", "look for", "locate"]

        self.weather_syn_vi = ["thời tiết", "weather", "nhiệt độ", "trời"]
        self.weather_syn_en = ["weather", "temperature", "climate", "forecast"]

        self.route_syn_vi = ["đường", "lộ trình", "chỉ đường", "route", "direction"]
        self.route_syn_en = ["route", "direction", "path", "way", "navigate"]

        self.activity_keywords_vi = [
            "nhà hàng",
            "khách sạn",
            "bảo tàng",
            "công viên",
            "biển",
            "núi",
            "chùa",
            "đền",
            "phố cổ",
            "cafe",
            "quán",
        ]
        self.activity_keywords_en = [
            "restaurant",
            "hotel",
            "museum",
            "park",
            "beach",
            "mountain",
            "temple",
            "cafe",
            "shop",
        ]

    def _find_day(self, text: str) -> Optional[int]:
        for pattern in self.day_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    day = int(match.group(1))
                    return day if 1 <= day <= 31 else None
                except:
                    pass
        return None

    def _find_time(self, text: str) -> Optional[str]:
        for pattern in self.time_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    time_str = match.group(1)
                    time_str = time_str.replace("h", ":").replace("giờ", ":").strip()

                    if ":" in time_str:
                        parts = time_str.split(":")
                        hour = int(parts[0])
                        minute = int(parts[1]) if len(parts) > 1 and parts[1] else 0
                    else:
                        hour = int(time_str)
                        minute = 0

                    if 0 <= hour <= 23 and 0 <= minute <= 59:
                        return f"{hour:02d}:{minute:02d}"
                except:
                    pass
        return None

    def _find_budget(self, text: str) -> Optional[Dict[str, Any]]:
        for pattern in self.budget_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    amount_str = match.group(1).replace(",", ".")
                    amount = float(amount_str)

                    text_lower = text.lower()
                    currency = "VND"
                    multiplier = 1

                    if "triệu" in text_lower or "tr" in text_lower or "million" in text_lower:
                        multiplier = 1000000
                    elif "nghìn" in text_lower or "k" in text_lower or "thousand" in text_lower:
                        multiplier = 1000
                    elif "usd" in text_lower or "$" in text_lower:
                        currency = "USD"

                    return {
                        "amount": amount * multiplier,
                        "currency": currency,
                        "original": match.group(0),
                    }
                except:
                    pass
        return None

    def _find_location(self, text: str) -> Optional[str]:
        for pattern in self.location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                if len(location) > 2:
                    return location
        return None

    def _extract_title(self, text: str, keywords: List[str]) -> Optional[str]:
        pattern = rf"(?:{'|'.join(keywords)})\s+(.+?)(?:\s+(?:ngày|lúc|vào|at|on|day)\b|$)"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            title = match.group(1).strip()
            title = re.sub(r"\s+(id|number|số)\s*[:=]?\s*\d+$", "", title, flags=re.IGNORECASE)
            return title[:200] if len(title) > 0 else None
        return None

    def _extract_item_id(self, text: str) -> Optional[int]:
        patterns = [
            r"id\s*[:=]?\s*(\d+)",
            r"số\s*[:=]?\s*(\d+)",
            r"number\s*[:=]?\s*(\d+)",
            r"#(\d+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except:
                    pass
        return None

    def _check_keywords(self, text: str, keywords: List[str]) -> bool:
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in keywords)

    def classify(self, text: str) -> ParseResult:
        if not text or len(text.strip()) == 0:
            return ParseResult(Intent.UNKNOWN, {}, 0.0)

        text = text.strip()
        text_lower = text.lower()

        if self._check_keywords(text_lower, self.add_syn_vi + self.add_syn_en):
            day = self._find_day(text)
            time = self._find_time(text)
            title = self._extract_title(text, self.add_syn_vi + self.add_syn_en)
            location = self._find_location(text)

            entities = {}
            if day:
                entities["day"] = day
            if time:
                entities["time"] = time
            if title:
                entities["title"] = title
            if location:
                entities["location"] = location

            confidence = 0.9 if title else 0.7
            return ParseResult(Intent.ADD, entities, confidence)

        if self._check_keywords(text_lower, self.remove_syn_vi + self.remove_syn_en):
            item_id = self._extract_item_id(text)
            title = self._extract_title(text, self.remove_syn_vi + self.remove_syn_en)
            day = self._find_day(text)

            entities = {}
            if item_id:
                entities["item_id"] = item_id
                confidence = 0.95
            elif title:
                entities["title"] = title
                confidence = 0.8
            else:
                confidence = 0.6

            if day:
                entities["day"] = day

            return ParseResult(Intent.REMOVE, entities, confidence)

        if self._check_keywords(text_lower, self.modify_syn_vi + self.modify_syn_en):
            time = self._find_time(text)
            if time or "giờ" in text_lower or "time" in text_lower:
                item_id = self._extract_item_id(text)
                day = self._find_day(text)

                entities = {}
                if item_id:
                    entities["item_id"] = item_id
                if time:
                    entities["time"] = time
                if day:
                    entities["day"] = day

                confidence = 0.85 if time else 0.6
                return ParseResult(Intent.MODIFY_TIME, entities, confidence)

            location = self._find_location(text)
            if location or self._check_keywords(text_lower, ["địa điểm", "location", "nơi"]):
                item_id = self._extract_item_id(text)
                day = self._find_day(text)

                entities = {}
                if item_id:
                    entities["item_id"] = item_id
                if location:
                    entities["location"] = location
                if day:
                    entities["day"] = day

                confidence = 0.85 if location else 0.6
                return ParseResult(Intent.MODIFY_LOCATION, entities, confidence)

        if self._check_keywords(text_lower, self.budget_syn_vi + self.budget_syn_en):
            budget = self._find_budget(text)
            if budget:
                return ParseResult(Intent.CHANGE_BUDGET, {"budget": budget}, 0.9)

        if self._check_keywords(text_lower, self.weather_syn_vi + self.weather_syn_en):
            location = self._find_location(text)
            day = self._find_day(text)
            entities = {}
            if location:
                entities["location"] = location
            if day:
                entities["day"] = day
            return ParseResult(Intent.GET_WEATHER, entities, 0.85)

        if self._check_keywords(text_lower, self.route_syn_vi + self.route_syn_en):
            match = re.search(
                r"(?:từ|from)\s+(.+?)\s+(?:đến|tới|to)\s+(.+?)(?:\s|$)",
                text,
                re.IGNORECASE,
            )
            if match:
                return ParseResult(
                    Intent.GET_ROUTE,
                    {"from": match.group(1).strip(), "to": match.group(2).strip()},
                    0.9,
                )

        if self._check_keywords(text_lower, self.search_syn_vi + self.search_syn_en):
            title = self._extract_title(text, self.search_syn_vi + self.search_syn_en)
            location = self._find_location(text)
            entities = {}
            if title:
                entities["query"] = title
            if location:
                entities["location"] = location
            return ParseResult(Intent.SEARCH_DESTINATION, entities, 0.8)

        if self._check_keywords(text_lower, self.suggest_syn_vi + self.suggest_syn_en):
            day = self._find_day(text)
            location = self._find_location(text)
            entities = {}
            if day:
                entities["day"] = day
            if location:
                entities["location"] = location
            return ParseResult(Intent.SUGGEST, entities, 0.85)

        if self._check_keywords(text_lower, self.view_syn_vi + self.view_syn_en):
            if any(
                word in text_lower
                for word in [
                    "kế hoạch",
                    "plan",
                    "lịch trình",
                    "itinerary",
                    "hiện tại",
                ]
            ):
                return ParseResult(Intent.VIEW_PLAN, {}, 0.9)

        return ParseResult(Intent.UNKNOWN, {}, 0.0)
