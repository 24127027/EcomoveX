from pydantic import BaseModel
from schemas.route_schema import TransportMode

class EmissionRequest(BaseModel):
    transport_mode: TransportMode
    distance_km: float
    passengers: int = 1
