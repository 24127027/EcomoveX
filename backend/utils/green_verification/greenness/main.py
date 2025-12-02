import argparse
import asyncio
import numpy as np
from pathlib import Path
import cv2
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Tuple
from orchestrator import GreenVerificationOrchestrator
from segmentation import TreeSegmenter
from database import get_db


def save_visualization(image: np.ndarray, filepath: str):
    """Save numpy array as image file."""
    if image.dtype != np.uint8:
        if image.max() <= 1.0:
            image = (image * 255).astype(np.uint8)
        else:
            image = image.astype(np.uint8)
    
    cv2.imwrite(filepath, image)
    print(f"Saved: {filepath}")


async def verify_by_place_id(
    place_id: str,
    output_dir: Path,
    threshold: Tuple[float, float],
    db: AsyncSession
):
    """Verify a destination by place_id."""
    print(f"Initializing TreeSegmenter...")
    segmentation = TreeSegmenter(model_name="best.pt")
    
    print(f"Creating orchestrator...")
    orchestrator = GreenVerificationOrchestrator(
        segmentation=segmentation,
        green_threshold=threshold,
        use_depth_weighting=True
    )
    
    print(f"Processing place: {place_id}")
    result = await orchestrator.verify_destination_by_place_id(
        db=db,
        place_id=place_id,
        save_to_db=True
    )
    
    # Print results
    print("\n" + "="*50)
    print("VERIFICATION RESULTS")
    print("="*50)
    if "error" in result:
        print(f"Error: {result['error']}")
        return
    
    metadata = result.get("metadata", {})
    print(f"Place: {metadata.get('place_name', 'Unknown')}")
    print(f"Address: {metadata.get('address', 'Unknown')}")
    print(f"Green Proportion: {result['green_proportion']:.2%}")
    print(f"Green Score: {result['green_score']:.4f}")
    print(f"Threshold: {result['threshold_used']:.2f}")
    print(f"Status: {'✓ VERIFIED' if result['verified'] else '✗ NOT VERIFIED'}")
    print("="*50 + "\n")
    
    # Save debug outputs
    print("Saving debug outputs...")
    
    save_visualization(result['image'], str(output_dir / "original.png"))
    save_visualization(result['mask'] * 255, str(output_dir / "mask.png"))
    
    if result.get('depth') is not None:
        save_visualization(result['depth'] * 255, str(output_dir / "depth.png"))
    
    # Save overlay
    overlay = result['image'].copy()
    if len(overlay.shape) == 2:
        overlay = cv2.cvtColor(overlay, cv2.COLOR_GRAY2BGR)
    green_overlay = np.zeros_like(overlay)
    green_overlay[:, :, 1] = result['mask'] * 255
    overlay = cv2.addWeighted(overlay, 0.7, green_overlay, 0.3, 0)
    save_visualization(overlay, str(output_dir / "overlay.png"))
    
    print(f"\nAll outputs saved to: {output_dir}")


async def verify_by_coordinates(
    latitude: float,
    longitude: float,
    output_dir: Path,
    threshold: Tuple[float, float],
    db: AsyncSession
):
    """Verify a location by coordinates."""
    print(f"Initializing TreeSegmenter...")
    segmentation = TreeSegmenter(model_name="best.pt")
    
    print(f"Creating orchestrator...")
    orchestrator = GreenVerificationOrchestrator(
        segmentation=segmentation,
        green_threshold=threshold,
        use_depth_weighting=True
    )
    
    print(f"Processing coordinates: ({latitude}, {longitude})")
    result = await orchestrator.verify_destination_by_coordinates(
        db=db,
        latitude=latitude,
        longitude=longitude,
        save_to_db=False
    )
    
    # Print results
    print("\n" + "="*50)
    print("VERIFICATION RESULTS")
    print("="*50)
    if "error" in result:
        print(f"Error: {result['error']}")
        return
    
    print(f"Location: ({latitude}, {longitude})")
    print(f"Green Proportion: {result['green_proportion']:.2%}")
    print(f"Green Score: {result['green_score']:.4f}")
    print(f"Status: {'✓ VERIFIED' if result['verified'] else '✗ NOT VERIFIED'}")
    print("="*50 + "\n")
    
    # Save debug outputs
    print("Saving debug outputs...")
    save_visualization(result['image'], str(output_dir / "original.png"))
    save_visualization(result['mask'] * 255, str(output_dir / "mask.png"))
    
    if result.get('depth') is not None:
        save_visualization(result['depth'] * 255, str(output_dir / "depth.png"))
    
    print(f"\nAll outputs saved to: {output_dir}")


async def main():
    parser = argparse.ArgumentParser(
        description="Green Verification for Destinations"
    )
    parser.add_argument(
        "--place-id",
        type=str,
        help="Google Place ID to verify"
    )
    parser.add_argument(
        "--latitude",
        type=float,
        help="Latitude coordinate"
    )
    parser.add_argument(
        "--longitude",
        type=float,
        help="Longitude coordinate"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./output",
        help="Directory to save debug outputs"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        nargs=2,
        default=[0.3, 0.6],
        help="Green threshold range (default: 0.3 0.6)"
    )
    
    args = parser.parse_args()
    
    # Validate input
    if not args.place_id and not (args.latitude and args.longitude):
        parser.error("Either --place-id or both --latitude and --longitude must be provided")
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get database session
    async for db in get_db():
        try:
            if args.place_id:
                await verify_by_place_id(
                    place_id=args.place_id,
                    output_dir=output_dir,
                    threshold=tuple(args.threshold),
                    db=db
                )
            else:
                await verify_by_coordinates(
                    latitude=args.latitude,
                    longitude=args.longitude,
                    output_dir=output_dir,
                    threshold=tuple(args.threshold),
                    db=db
                )
        finally:
            await db.close()
        break


if __name__ == "__main__":
    asyncio.run(main())