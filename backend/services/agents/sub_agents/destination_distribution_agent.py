from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, datetime, timedelta
from models.plan import DestinationType, TimeSlot


class DestinationDistributionAgent:
    """
    Agent that intelligently distributes destinations across the date range
    and assigns appropriate time slots within each day.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db

    def _parse_date(self, val: Any) -> Optional[date]:
        """Parse various date formats into date object."""
        if val is None:
            return None
        if isinstance(val, date) and not isinstance(val, datetime):
            return val
        if isinstance(val, datetime):
            return val.date()
        if isinstance(val, str):
            try:
                return datetime.strptime(val.split("T")[0], "%Y-%m-%d").date()
            except:
                pass
        return None

    def _get_destination_type(self, dest: Any) -> Optional[DestinationType]:
        """Extract destination type from destination object or dict.
        Also attempts to detect restaurants from name if type is generic."""
        if isinstance(dest, dict):
            dest_type = dest.get("type") or dest.get("destination_type")
            dest_name = dest.get("note") or dest.get("name") or ""
        else:
            dest_type = getattr(dest, "type", None) or getattr(dest, "destination_type", None)
            dest_name = getattr(dest, "note", "") or getattr(dest, "name", "")
        
        # Parse string type to enum
        if isinstance(dest_type, str):
            try:
                dest_type = DestinationType(dest_type)
            except:
                dest_type = None
        
        # Smart detection: If type is generic "attraction" but name suggests restaurant
        if dest_type == DestinationType.attraction or dest_type is None:
            # Check if name contains restaurant keywords (Vietnamese and English)
            restaurant_keywords = [
                "phở", "cơm", "bún", "bánh", "quán", "nhà hàng", "restaurant", 
                "cafe", "coffee", "food", "kitchen", "ăn", "dining", "grill",
                "bistro", "buffet", "canteen"
            ]
            name_lower = dest_name.lower()
            for keyword in restaurant_keywords:
                if keyword in name_lower:
                    return DestinationType.restaurant
        
        return dest_type

    def _clone_destination(self, dest: Any, repeat_index: int) -> Dict[str, Any]:
        """Clone a destination and mark it as repeated.
        
        Args:
            dest: Original destination (dict or Pydantic model)
            repeat_index: Index of this repetition (1-based)
            
        Returns:
            Cloned destination dict with repeat markers
        """
        if isinstance(dest, dict):
            dest_copy = dest.copy()
        elif hasattr(dest, "model_dump"):
            dest_copy = dest.model_dump()
        else:
            dest_copy = {
                "destination_id": getattr(dest, "destination_id", None),
                "destination_type": getattr(dest, "destination_type", None) or getattr(dest, "type", None),
                "type": getattr(dest, "type", None) or getattr(dest, "destination_type", None),
                "note": getattr(dest, "note", None),
                "estimated_cost": getattr(dest, "estimated_cost", None),
                "url": getattr(dest, "url", None),
            }
        
        # Mark as repeated (don't set visit_date, time_slot, order_in_day yet)
        dest_copy["is_repeated"] = True
        dest_copy["repeat_index"] = repeat_index
        
        # Clear scheduling fields - will be set during distribution
        dest_copy.pop("visit_date", None)
        dest_copy.pop("time_slot", None)
        dest_copy.pop("order_in_day", None)
        
        return dest_copy

    def expand_destinations_by_demand(
        self, 
        destinations: List[Any], 
        start_date: date, 
        end_date: date
    ) -> List[Any]:
        """Expand destinations list based on implicit daily needs.
        
        This function implements demand-based expansion:
        - Restaurants: 2 per day (lunch + dinner) - allows repeats
        - Accommodation: 1 per day - allows repeats
        - Attractions: 1 per day - NO repeats (user must provide variety)
        
        STRICT RULES:
        - Does NOT mutate existing destinations
        - Only CLONES existing destinations to meet demand
        - Does NOT create fake/new destination data
        - Does NOT assign visit_date, time_slot, or order_in_day
        - Marks cloned destinations with is_repeated=true
        
        Args:
            destinations: List of original user-provided destinations
            start_date: Trip start date
            end_date: Trip end date
            
        Returns:
            Expanded list of destinations (originals + clones)
        """
        if not destinations or not start_date or not end_date:
            return destinations
        
        # Calculate trip duration
        trip_days = (end_date - start_date).days + 1
        
        # Group destinations by type
        by_type: Dict[DestinationType, List[Any]] = {
            DestinationType.restaurant: [],
            DestinationType.accommodation: [],
            DestinationType.attraction: [],
        }
        
        other_destinations = []  # Transport or unknown types
        
        for dest in destinations:
            dest_type = self._get_destination_type(dest)
            if dest_type in by_type:
                by_type[dest_type].append(dest)
            else:
                other_destinations.append(dest)
        
        # Calculate required counts based on implicit needs
        required_counts = {
            DestinationType.restaurant: trip_days * 2,  # Lunch + dinner
            DestinationType.accommodation: trip_days,   # 1 per night
            DestinationType.attraction: trip_days,       # 1 per day (but no repeats)
        }
        
        # Build expanded list
        expanded_destinations = []
        
        # Process each destination type
        for dest_type, required_count in required_counts.items():
            current_destinations = by_type[dest_type]
            current_count = len(current_destinations)
            
            # Add all original destinations first (preserve order)
            expanded_destinations.extend(current_destinations)
            
            # Check if expansion is needed
            if current_count >= required_count:
                # Already have enough, no expansion needed
                continue
            
            # Determine if this type allows repeats
            allow_repeats = dest_type in [
                DestinationType.restaurant,
                DestinationType.accommodation
            ]
            
            if not allow_repeats:
                # Attractions don't repeat - user must provide variety
                # Just keep what they gave us
                continue
            
            if current_count == 0:
                # No destinations of this type provided
                # Cannot create fake data - skip
                continue
            
            # Calculate how many clones needed
            needed = required_count - current_count
            
            # Clone existing destinations cyclically
            for i in range(needed):
                # Round-robin through existing destinations
                source_dest = current_destinations[i % current_count]
                
                # Clone with repeat marker
                cloned_dest = self._clone_destination(source_dest, repeat_index=i + 1)
                
                expanded_destinations.append(cloned_dest)
        
        # Add other destinations (transport, etc.)
        expanded_destinations.extend(other_destinations)
        
        return expanded_destinations

    def _suggest_time_slot_for_type(self, dest_type: Optional[DestinationType]) -> TimeSlot:
        """Suggest appropriate time slot based on destination type."""
        if not dest_type:
            return TimeSlot.morning
        
        # Restaurants: prefer afternoon (lunch) or evening (dinner)
        if dest_type == DestinationType.restaurant:
            return TimeSlot.afternoon
        
        # Accommodations: evening (check-in)
        if dest_type == DestinationType.accommodation:
            return TimeSlot.evening
        
        # Attractions, museums, parks: morning or afternoon
        if dest_type == DestinationType.attraction:
            return TimeSlot.morning
        
        # Default
        return TimeSlot.morning

    def _distribute_time_slots(self, count: int, dest_types: List[Optional[DestinationType]]) -> List[TimeSlot]:
        """
        Distribute time slots for a given number of destinations in a day.
        
        Args:
            count: Number of destinations in the day
            dest_types: List of destination types to consider preferences
            
        Returns:
            List of TimeSlot assignments
        """
        if count == 0:
            return []
        
        if count == 1:
            return [self._suggest_time_slot_for_type(dest_types[0])]
        
        if count == 2:
            # First destination in morning, second in afternoon or evening
            return [TimeSlot.morning, TimeSlot.afternoon]
        
        if count == 3:
            # Balanced: morning, afternoon, evening
            slots = [TimeSlot.morning, TimeSlot.afternoon, TimeSlot.evening]
            
            # Adjust based on types
            for i, dest_type in enumerate(dest_types):
                if dest_type == DestinationType.restaurant:
                    slots[i] = TimeSlot.afternoon if i < 2 else TimeSlot.evening
                elif dest_type == DestinationType.accommodation:
                    slots[i] = TimeSlot.evening
            
            return slots
        
        # 4+ destinations: distribute evenly
        slots = []
        time_slot_order = [TimeSlot.morning, TimeSlot.morning, TimeSlot.afternoon, TimeSlot.afternoon, TimeSlot.evening, TimeSlot.evening]
        
        for i in range(count):
            if i < len(time_slot_order):
                suggested = time_slot_order[i]
            else:
                # Cycle through if more than 6 destinations
                suggested = time_slot_order[i % len(time_slot_order)]
            
            # Override based on destination type
            dest_type = dest_types[i] if i < len(dest_types) else None
            if dest_type == DestinationType.restaurant and suggested == TimeSlot.morning:
                suggested = TimeSlot.afternoon
            elif dest_type == DestinationType.accommodation:
                suggested = TimeSlot.evening
            
            slots.append(suggested)
        
        return slots

    async def process(self, plan: Any, action: str = "distribute") -> Dict[str, Any]:
        """
        Main processing method: distribute destinations across date range and time slots.
        
        Args:
            plan: Plan object or dict containing destinations and date range
            action: Action type (default: "distribute")
            
        Returns:
            Dict with success status, message, and distributed destinations
        """
        modifications: List[Dict] = []
        warnings: List[str] = []

        # Extract plan data
        if isinstance(plan, dict):
            destinations = plan.get("destinations", [])
            start_date = self._parse_date(plan.get("start_date"))
            end_date = self._parse_date(plan.get("end_date"))
            place_name = plan.get("place_name", "")
        else:
            destinations = getattr(plan, "destinations", []) or []
            start_date = self._parse_date(getattr(plan, "start_date", None))
            end_date = self._parse_date(getattr(plan, "end_date", None))
            place_name = getattr(plan, "place_name", "")

        # Validation
        if not destinations:
            return {
                "success": False,
                "message": "Không có điểm đến nào để phân bổ",
                "modifications": [],
                "distributed_destinations": []
            }

        if not start_date or not end_date:
            return {
                "success": False,
                "message": "Thiếu ngày bắt đầu hoặc kết thúc",
                "modifications": [],
                "distributed_destinations": destinations
            }

        if start_date > end_date:
            return {
                "success": False,
                "message": "Ngày bắt đầu phải trước ngày kết thúc",
                "modifications": [],
                "distributed_destinations": destinations
            }

        # Calculate number of days in trip
        total_days = (end_date - start_date).days + 1
        
        # STEP 1: Expand destinations based on implicit daily needs
        # This creates realistic plans by repeating restaurants/accommodations
        expanded_destinations = self.expand_destinations_by_demand(
            destinations, start_date, end_date
        )
        
        # Use expanded list for distribution
        total_destinations = len(expanded_destinations)

        # Check if destinations already have proper distribution
        has_distribution = True
        unique_dates = set()
        time_slot_issues = 0
        
        for dest in expanded_destinations:
            visit_date = dest.get("visit_date") if isinstance(dest, dict) else getattr(dest, "visit_date", None)
            time_slot = dest.get("time_slot") if isinstance(dest, dict) else getattr(dest, "time_slot", None)
            
            if not visit_date:
                has_distribution = False
                break
            
            parsed_date = self._parse_date(visit_date)
            if parsed_date:
                unique_dates.add(parsed_date)
            
            if not time_slot:
                time_slot_issues += 1

        # If all destinations are on the same day or have time slot issues, redistribute
        needs_redistribution = (
            not has_distribution or 
            len(unique_dates) == 1 and total_destinations > 3 or
            time_slot_issues > total_destinations // 2
        )

        if not needs_redistribution:
            # Already distributed, just validate time slots within each day
            return await self._validate_existing_distribution(expanded_destinations, start_date, end_date)

        # STEP 2: Perform SEMANTIC-AWARE distribution across days
        # Group expanded destinations by type for semantic distribution
        by_type: Dict[DestinationType, List[Any]] = {
            DestinationType.restaurant: [],
            DestinationType.accommodation: [],
            DestinationType.attraction: [],
        }
        other_destinations = []
        
        for dest in expanded_destinations:
            dest_type = self._get_destination_type(dest)
            if dest_type in by_type:
                by_type[dest_type].append(dest)
            else:
                other_destinations.append(dest)
        
        # Build day-by-day schedule with semantic rules
        distributed_destinations = []
        
        for day_num in range(total_days):
            day_date = start_date + timedelta(days=day_num)
            day_schedule = []
            order = 1
            
            # RULE 1: Attractions in morning (1-2 per day)
            attractions = by_type[DestinationType.attraction]
            attractions_for_day = min(2, len(attractions))  # Max 2 attractions per day
            for _ in range(attractions_for_day):
                if attractions:
                    dest = attractions.pop(0)
                    dest_copy = dest.copy() if isinstance(dest, dict) else dest.model_dump()
                    dest_copy["visit_date"] = day_date
                    dest_copy["time_slot"] = TimeSlot.morning
                    dest_copy["order_in_day"] = order
                    day_schedule.append(dest_copy)
                    order += 1
                    
                    modifications.append({
                        "destination_id": dest.get("destination_id") if isinstance(dest, dict) else getattr(dest, "destination_id", None),
                        "field": "distribution",
                        "old_date": dest.get("visit_date") if isinstance(dest, dict) else getattr(dest, "visit_date", None),
                        "new_date": str(day_date),
                        "old_time_slot": dest.get("time_slot") if isinstance(dest, dict) else getattr(dest, "time_slot", None),
                        "new_time_slot": "morning",
                        "order_in_day": order - 1
                    })
            
            # RULE 2: EXACTLY 2 restaurants per day (lunch at afternoon, dinner at evening)
            restaurants = by_type[DestinationType.restaurant]
            
            # Lunch (afternoon)
            if restaurants:
                dest = restaurants.pop(0)
                dest_copy = dest.copy() if isinstance(dest, dict) else dest.model_dump()
                dest_copy["visit_date"] = day_date
                dest_copy["time_slot"] = TimeSlot.afternoon
                dest_copy["order_in_day"] = order
                day_schedule.append(dest_copy)
                order += 1
                
                modifications.append({
                    "destination_id": dest.get("destination_id") if isinstance(dest, dict) else getattr(dest, "destination_id", None),
                    "field": "distribution",
                    "old_date": dest.get("visit_date") if isinstance(dest, dict) else getattr(dest, "visit_date", None),
                    "new_date": str(day_date),
                    "old_time_slot": dest.get("time_slot") if isinstance(dest, dict) else getattr(dest, "time_slot", None),
                    "new_time_slot": "afternoon",
                    "order_in_day": order - 1
                })
            
            # Dinner (evening)
            if restaurants:
                dest = restaurants.pop(0)
                dest_copy = dest.copy() if isinstance(dest, dict) else dest.model_dump()
                dest_copy["visit_date"] = day_date
                dest_copy["time_slot"] = TimeSlot.evening
                dest_copy["order_in_day"] = order
                day_schedule.append(dest_copy)
                order += 1
                
                modifications.append({
                    "destination_id": dest.get("destination_id") if isinstance(dest, dict) else getattr(dest, "destination_id", None),
                    "field": "distribution",
                    "old_date": dest.get("visit_date") if isinstance(dest, dict) else getattr(dest, "visit_date", None),
                    "new_date": str(day_date),
                    "old_time_slot": dest.get("time_slot") if isinstance(dest, dict) else getattr(dest, "time_slot", None),
                    "new_time_slot": "evening",
                    "order_in_day": order - 1
                })
            
            # RULE 3: EXACTLY 1 accommodation per day (always evening)
            accommodations = by_type[DestinationType.accommodation]
            if accommodations:
                dest = accommodations.pop(0)
                dest_copy = dest.copy() if isinstance(dest, dict) else dest.model_dump()
                dest_copy["visit_date"] = day_date
                dest_copy["time_slot"] = TimeSlot.evening
                dest_copy["order_in_day"] = order
                day_schedule.append(dest_copy)
                order += 1
                
                modifications.append({
                    "destination_id": dest.get("destination_id") if isinstance(dest, dict) else getattr(dest, "destination_id", None),
                    "field": "distribution",
                    "old_date": dest.get("visit_date") if isinstance(dest, dict) else getattr(dest, "visit_date", None),
                    "new_date": str(day_date),
                    "old_time_slot": dest.get("time_slot") if isinstance(dest, dict) else getattr(dest, "time_slot", None),
                    "new_time_slot": "evening",
                    "order_in_day": order - 1
                })
            
            # Add other destinations if any
            if other_destinations:
                dest = other_destinations.pop(0)
                dest_copy = dest.copy() if isinstance(dest, dict) else dest.model_dump()
                dest_copy["visit_date"] = day_date
                dest_copy["time_slot"] = TimeSlot.afternoon
                dest_copy["order_in_day"] = order
                day_schedule.append(dest_copy)
                order += 1
            
            distributed_destinations.extend(day_schedule)

        # Calculate unique days with destinations
        unique_days = set()
        for dest in distributed_destinations:
            visit_date = dest.get("visit_date")
            if visit_date:
                unique_days.add(visit_date)
        
        summary = f"Đã phân bổ {len(distributed_destinations)} điểm đến vào {len(unique_days)} ngày"
        
        return {
            "success": True,
            "message": summary,
            "modifications": modifications,
            "distributed_destinations": distributed_destinations,
            "distribution_summary": {
                "total_destinations": len(distributed_destinations),
                "total_days": total_days,
                "days_with_destinations": len(unique_days),
                "avg_per_day": len(distributed_destinations) / total_days
            }
        }

    async def _validate_existing_distribution(self, destinations: List[Any], start_date: date, end_date: date) -> Dict[str, Any]:
        """Validate and potentially adjust time slots in existing distribution."""
        modifications: List[Dict] = []
        warnings: List[str] = []
        
        # Group by date
        date_groups: Dict[date, List[Any]] = {}
        for dest in destinations:
            visit_date = dest.get("visit_date") if isinstance(dest, dict) else getattr(dest, "visit_date", None)
            parsed_date = self._parse_date(visit_date)
            
            if parsed_date and start_date <= parsed_date <= end_date:
                if parsed_date not in date_groups:
                    date_groups[parsed_date] = []
                date_groups[parsed_date].append(dest)
        
        # Check time slot distribution within each day
        adjusted_destinations = []
        for day_date, day_dests in sorted(date_groups.items()):
            time_slot_counts = {"morning": 0, "afternoon": 0, "evening": 0}
            
            for dest in day_dests:
                time_slot = dest.get("time_slot") if isinstance(dest, dict) else getattr(dest, "time_slot", None)
                if time_slot:
                    slot_value = time_slot.value if hasattr(time_slot, "value") else str(time_slot)
                    if slot_value in time_slot_counts:
                        time_slot_counts[slot_value] += 1
            
            # Check if all destinations are in morning (the main issue)
            if len(day_dests) >= 3 and time_slot_counts["morning"] == len(day_dests):
                warnings.append(f"Ngày {day_date}: Tất cả {len(day_dests)} điểm đến đều trong buổi sáng - nên phân bổ lại")
                
                # Redistribute time slots for this day
                dest_types = [self._get_destination_type(d) for d in day_dests]
                new_time_slots = self._distribute_time_slots(len(day_dests), dest_types)
                
                for order, (dest, new_slot) in enumerate(zip(day_dests, new_time_slots), start=1):
                    dest_copy = dest.copy() if isinstance(dest, dict) else dest.model_dump()
                    dest_copy["time_slot"] = new_slot
                    dest_copy["order_in_day"] = order
                    adjusted_destinations.append(dest_copy)
                    
                    modifications.append({
                        "destination_id": dest.get("destination_id") if isinstance(dest, dict) else getattr(dest, "destination_id", None),
                        "date": str(day_date),
                        "field": "time_slot",
                        "old_value": "morning",
                        "new_value": new_slot.value if hasattr(new_slot, "value") else str(new_slot),
                        "suggestion": "Phân bổ lại thời gian trong ngày"
                    })
            else:
                # Keep as is
                adjusted_destinations.extend(day_dests)
        
        if warnings:
            return {
                "success": False,
                "message": "\n".join(warnings),
                "modifications": modifications,
                "distributed_destinations": adjusted_destinations
            }
        
        return {
            "success": True,
            "message": "Phân bổ hiện tại hợp lý",
            "modifications": [],
            "distributed_destinations": destinations
        }
