from backend.models.destination import Destination
from backend.services.map_service import MapService

class DestinationEmbeddingService:
    def __init__(self, encoder, google_client, model_version: str):
        self.encoder = encoder
        self.google_client = google_client
        self.model_version = model_version

    async def build_embedding_record(self, destination: Destination):
        # 1) Lấy dữ liệu thật từ Google API
        place = await MapService.get_location_details(destination.google_place_id)

        # 2) Build text
        text = self._build_text(place)

        # 3) Encode
        vector = await self._encode(text)

        # 4) Return DB record
        return {
            "google_place_id": destination.google_place_id,
            "embedding": vector,
            "model_version": self.model_version,
        }
        
    def _build_text(self, place):
        """Chuyển dữ liệu Google Place → đoạn mô tả cho embedding."""

        name = place.name or ""
        types = ", ".join(place.types or [])
        address = place.formatted_address or ""
        rating = place.rating or "N/A"
        description = (
            getattr(place, "editorial_summary", None) or
            getattr(place, "editorial_summary_description", None) or
            ""
        )

        return (
            f"Name: {name}\n"
            f"Category: {types}\n"
            f"Address: {address}\n"
            f"Rating: {rating}\n"
            f"Description: {description}\n"
        ).strip()
        

    async def _encode(self, text: str):
        """Encode thành vector embedding."""
        return await self.encoder.encode(text)
