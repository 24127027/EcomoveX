from typing import Optional
from PIL import Image
from huggingface_hub import InferenceClient
from utils.config import settings

class ImageGenerator:
    def __init__(self):
        self.client = InferenceClient(
            provider="auto",
            api_key=settings.HUGGINGFACE_API_KEY,
        )
        self.image_model = "tencent/HunyuanImage-3.0"
    
    def generate_image(
        self,
        prompt: str,
        model: Optional[str] = None,
    ) -> Image.Image:
        try:
            used_model = model or self.image_model
            image = self.client.text_to_image(
                prompt,
                model=used_model,
            )
            return image
        except Exception as e:
            print(f"Error in image generation: {e}")
            raise
    
    def generate_and_save(
        self,
        prompt: str,
        output_path: str = "generated_image.png",
        model: Optional[str] = None,
    ) -> Image.Image:
        print(f"Generating image with prompt: '{prompt}'")
        image = self.generate_image(prompt, model)
        
        image.save(output_path)
        print(f"✅ Image saved to: {output_path}")
        
        return image

_image_generator_instance: Optional[ImageGenerator] = None

def get_image_generator() -> ImageGenerator:
    global _image_generator_instance
    if _image_generator_instance is None:
        _image_generator_instance = ImageGenerator()
    return _image_generator_instance