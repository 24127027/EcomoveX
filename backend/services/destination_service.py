from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from models.destination import GreenVerifiedStatus
from repository.destination_repository import DestinationRepository
from schemas.destination_schema import (
    DestinationCreate,
    DestinationEmbeddingCreate,
    DestinationResponse,
    DestinationUpdate,
    UserSavedDestinationResponse,
)
from utils.embedded.embedding_utils import encode_text


class DestinationService:
    @staticmethod
    async def get_destination_by_id(db: AsyncSession, destination_id: str):
        try:
            destination = await DestinationRepository.get_destination_by_id(
                db, destination_id
            )
            if not destination:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Destination with ID {destination_id} not found",
                )
            return destination
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving destination ID {destination_id}: {e}",
            )

    @staticmethod
    async def create_destination(db: AsyncSession, destination_data: DestinationCreate):
        try:
            new_destination = await DestinationRepository.create_destination(
                db, destination_data
            )
            if not new_destination:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create destination",
                )
            return new_destination
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error creating destination: {e}",
            )

    @staticmethod
    async def update_destination(
        db: AsyncSession, destination_id: str, updated_data: DestinationUpdate
    ):
        try:
            updated_destination = await DestinationRepository.update_destination(
                db, destination_id, updated_data
            )
            if not updated_destination:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Destination with ID {destination_id} not found",
                )
            return updated_destination
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error updating destination ID {destination_id}: {e}",
            )

    @staticmethod
    async def delete_destination(db: AsyncSession, destination_id: str):
        try:
            success = await DestinationRepository.delete_destination(db, destination_id)
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Destination with ID {destination_id} not found",
                )
            return {"detail": "Destination deleted successfully"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error deleting destination ID {destination_id}: {e}",
            )

    @staticmethod
    async def save_destination_for_user(
        db: AsyncSession, user_id: int, destination_id: str
    ) -> UserSavedDestinationResponse:
        try:
            destination = await DestinationRepository.get_destination_by_id(
                db, destination_id
            )
            if not destination:
                new_dest_data = DestinationCreate(place_id=destination_id)
                await DestinationRepository.create_destination(db, new_dest_data)
            is_saved = await DestinationRepository.is_saved_destination(
                db, user_id, destination_id
            )
            if is_saved:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Destination already saved for this user",
                )
            saved = await DestinationRepository.save_destination_for_user(
                db, user_id, destination_id
            )
            if not saved:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to save destination for user",
                )
            return UserSavedDestinationResponse(
                user_id=saved.user_id,
                destination_id=saved.destination_id,
                saved_at=saved.saved_at,
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error saving destination for user ID {user_id}: {e}",
            )

    @staticmethod
    async def get_saved_destinations_for_user(
        db: AsyncSession, user_id: int
    ) -> list[UserSavedDestinationResponse]:
        try:
            saved_destinations = (
                await DestinationRepository.get_saved_destinations_for_user(db, user_id)
            )
            saved_list = []
            for saved in saved_destinations:
                saved_list.append(
                    UserSavedDestinationResponse(
                        user_id=saved.user_id,
                        destination_id=saved.destination_id,
                        saved_at=saved.saved_at,
                    )
                )
            return saved_list
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error retrieving saved destinations for user ID {user_id}: {e}",
            )

    @staticmethod
    async def delete_saved_destination(
        db: AsyncSession, user_id: int, destination_id: str
    ):
        try:
            success = await DestinationRepository.delete_saved_destination(
                db, user_id, destination_id
            )
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Saved destination not found for user",
                )
            return {"message": "Saved destination deleted successfully"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    f"Unexpected error deleting saved destination for user ID "
                    f"{user_id} and destination ID {destination_id}: {e}"
                ),
            )

    @staticmethod
    async def is_saved_destination(db: AsyncSession, user_id: int, destination_id: str):
        try:
            saved_destinations = (
                await DestinationRepository.get_saved_destinations_for_user(db, user_id)
            )
            for saved in saved_destinations:
                if saved.destination_id == destination_id:
                    return True
            return False
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    f"Unexpected error checking saved destination for user ID "
                    f"{user_id} and destination ID {destination_id}: {e}"
                ),
            )

    @staticmethod
    async def embed_destination(
        db: AsyncSession, destination_data: Dict[str, Any]
    ) -> List[float]:
        try:
            text_parts = []

            if "name" in destination_data:
                text_parts.append(destination_data["name"])
            if "tags" in destination_data:
                if isinstance(destination_data["tags"], list):
                    text_parts.extend(destination_data["tags"])
                else:
                    text_parts.append(str(destination_data["tags"]))
            if "description" in destination_data:
                text_parts.append(destination_data["description"])
            if "category" in destination_data:
                text_parts.append(destination_data["category"])

            text = " ".join(text_parts) if text_parts else "destination"
            embedding = encode_text(text)
            return embedding

        except Exception:
            return encode_text("destination")

    @staticmethod
    async def embed_destination_by_id(
        db: AsyncSession, destination_id: str, destination_data: Dict[str, Any]
    ) -> Optional[List[float]]:
        try:
            destination = await DestinationRepository.get_destination_by_id(
                db, destination_id
            )
            if not destination:
                return None

            embedding = await DestinationService.embed_destination(db, destination_data)

            embedding_data = DestinationEmbeddingCreate(
                destination_id=destination_id,
                embedding_vector=embedding,
                model_version="v1",
            )
            await DestinationRepository.save_embedding(db, embedding_data)

            return embedding

        except Exception:
            return None

    @staticmethod
    async def get_destination_embedding(db: AsyncSession, destination_id: str):
        try:
            return await DestinationRepository.get_embedding(db, destination_id)
        except Exception:
            return None

    @staticmethod
    async def get_embeddings_by_model(
        db: AsyncSession, model_version: str, skip: int = 0, limit: int = 1000
    ):
        try:
            return await DestinationRepository.get_embeddings_by_model(
                db, model_version, skip, limit
            )
        except Exception:
            return []

    @staticmethod
    async def delete_destination_embedding(db: AsyncSession, destination_id: str):
        try:
            return await DestinationRepository.delete_embedding(db, destination_id)
        except Exception:
            return False

    @staticmethod
    async def bulk_unsave_destinations_for_user(
        db: AsyncSession, user_id: int, destination_ids: List[str]
    ):
        try:
            for destination_id in destination_ids:
                try:
                    success = await DestinationRepository.delete_saved_destination(
                        db, user_id, destination_id
                    )
                    if not success:
                        raise HTTPException(
                            status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Saved destination {destination_id} not found for user",
                        )
                except Exception:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to unsave destination {destination_id} for user",
                    )

            return {"detail": "All specified destinations unsaved successfully"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error bulk unsaving destinations: {e}",
            )

    @staticmethod
    async def get_all_destinations(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        verified_status: Optional[GreenVerifiedStatus] = None,
    ) -> List[DestinationResponse]:
        """Get all destinations with optional filtering by verification status (Admin only)"""
        try:
            if verified_status:
                destinations = await DestinationRepository.get_destinations_by_green_status(
                    db, verified_status, skip, limit
                )
            else:
                destinations = await DestinationRepository.get_all_destinations(
                    db, skip, limit
                )

            return [
                DestinationResponse(
                    place_id=dest.place_id,
                    green_verified=dest.green_verified,
                )
                for dest in destinations
            ]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve destinations: {e}",
            )
