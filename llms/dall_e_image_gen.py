import requests
import json
import time
import base64
from typing import Optional, Dict, Any
import os
from datetime import datetime

class DallEImageGenerator:
    def __init__(self, api_key: str, base_url: str = "https://api.a4f.co/v1"):
        """
        Initialize the Dall-E Image Generator
        
        Args:
            api_key: Your a4f.co API key
            base_url: Base URL for the API (default: https://api.a4f.co/v1)
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def generate_image(self, 
                      prompt: str,
                      model: str = "provider-3/dall-e-3",
                      width: int = 1024,
                      height: int = 1024,
                      steps: int = 25,
                      guidance_scale: float = 7.0,
                      seed: Optional[int] = None,
                      negative_prompt: Optional[str] = None,
                      output_format: str = "png") -> Dict[str, Any]:
        """
        Generate an image using Dall-E models
        
        Args:
            prompt: Text description of the image to generate
            model: Model to use (provider-3/dall-e-3, provider-3/dall-e-3-v2)
            width: Image width in pixels
            height: Image height in pixels
            steps: Number of inference steps
            guidance_scale: How closely to follow the prompt
            seed: Random seed for reproducibility
            negative_prompt: What to avoid in the image
            output_format: Output format (png, jpg, webp)
            
        Returns:
            Dictionary containing the response data
        """
        payload = {
            "prompt": prompt,
            "model": model,
            "width": width,
            "height": height,
            "steps": steps,
            "guidance_scale": guidance_scale,
            "output_format": output_format
        }
        
        if seed is not None:
            payload["seed"] = seed
            
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        
        try:
            response = requests.post(
                f"{self.base_url}/images/generations",
                headers=self.headers,
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}
    
    def save_image_from_response(self, response_data: Dict[str, Any], 
                                filename: Optional[str] = None,
                                output_dir: str = "images/generated_images") -> str:
        """
        Save image from API response to file
        
        Args:
            response_data: Response from generate_image()
            filename: Custom filename (optional)
            output_dir: Directory to save images
            
        Returns:
            Path to saved image file
        """
        if "error" in response_data:
            raise ValueError(f"Cannot save image due to error: {response_data['error']}")
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dall_e_image_{timestamp}.png"
        
        filepath = os.path.join(output_dir, filename)
        
        # Handle different response formats
        if "data" in response_data and len(response_data["data"]) > 0:
            image_data = response_data["data"][0]
            
            if "b64_json" in image_data:
                # Base64 encoded image
                print("Base64 encoded image")
                image_bytes = base64.b64decode(image_data["b64_json"])
                with open(filepath, "wb") as f:
                    f.write(image_bytes)
            elif "url" in image_data:
                # Image URL - download it
                print("URL based Image")
                img_response = requests.get(image_data["url"])
                img_response.raise_for_status()
                with open(filepath, "wb") as f:
                    f.write(img_response.content)
            else:
                raise ValueError("No valid image data found in response")
        else:
            raise ValueError("No image data found in response")
        
        return filepath
    
    def generate_and_save(self, 
                         prompt: str,
                         filename: Optional[str] = None,
                         **kwargs) -> tuple[str, str]:
        """
        Generate an image and save it in one step
        
        Args:
            prompt: Text description of the image
            filename: Custom filename (optional)
            **kwargs: Additional arguments for generate_image()
            
        Returns:
            Path to saved image file
        """
        print(f"Generating image with prompt: '{prompt}'")
        
        response = self.generate_image(prompt, **kwargs)
        
        if "error" in response:
            raise ValueError(f"Image generation failed: {response['error']}")
        
        filepath = self.save_image_from_response(response, filename)

        print(f"API response: {response}")
        ai_response = response.get("data", [{}])[0].get("revised_prompt")
        if ai_response is None:
            ai_response = f"Generated image successfully for prompt: {prompt}\n"
        
        return filepath, ai_response

# Example usage
def dall_e_image_generator(prompt: str):
    # Initialize the generator with your API key
    api_key = str(os.getenv("OPENAI_API_KEY"))  # Replace with your actual API key
    generator = DallEImageGenerator(api_key)
    
    # Example 1: Simple image generation
    try:        
        filepath, response = generator.generate_and_save(
            prompt=prompt,
            model="provider-3/dall-e-3",
            width=1024,
            height=1024,
            steps=30,
            guidance_scale=7.5,
            seed=42  # For reproducible results
        )
        
        print(f"\nSuccess! Image saved to: {filepath} \nRevised prompt: {response}")
        return response, filepath
        
    except Exception as e:
        print(f"Error: {e}")
        return None, None


if __name__ == "__main__":
    dall_e_image_generator("A majestic dragon soaring through cloudy skies at sunset, photorealistic, highly detailed")