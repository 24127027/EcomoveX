from backend.schemas.plan_schema import PlanDestinationResponse, PlanResponse
from services.plan_service import PlanService
from typing import List
import hdbscan

class GroupDestinationAgent:
    def __init__(self):
        self.plan_service = PlanService()
    
    def get_group_destinations(self, destinations: List[PlanDestinationResponse]) -> PlanResponse:
        group = []
        # group destination, calculate distance between 2 points, plus Kmeans return a list of grouped destinations
         
            
        