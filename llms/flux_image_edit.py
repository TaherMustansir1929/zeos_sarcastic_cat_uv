import requests
import os
import base64
from PIL import Image
import io
from pathlib import Path
import time
from dotenv import load_dotenv

load_dotenv()


def edit_image_with_bfl(image_filepath, prompt, api_key, output_filename=None):
    """
    Edit an image using Black Forest Labs API based on a text prompt.
    
    Args:
        image_filepath (str): Full path to the image file (e.g., "images/edit_images/saved_images/photo.jpg")
        prompt (str): Text prompt describing the desired edits
        api_key (str): Your Black Forest Labs API key
        output_filename (str, optional): Custom output filename. If None, auto-generates based on input
    
    Returns:
        str: Relative path from base directory (e.g., "images/edit_images/results/image.png"), or None if failed
    """
    
    # Set up paths
    output_dir = Path("images/edit_images/results")
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Full path to input image
    input_path = Path(image_filepath)
    
    # Check if input image exists
    if not input_path.exists():
        print(f"Error: Image {input_path} not found")
        return None
    
    try:
        # Load and encode the image
        with open(input_path, "rb") as img_file:
            img_data = img_file.read()
            img_base64 = base64.b64encode(img_data).decode('utf-8')
        
        # Prepare the API request
        url = "https://api.bfl.ai/v1/flux-kontext-pro"
        
        headers = {
            "accept": "application/json",
            "x-key": api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "prompt": prompt,
            "input_image": img_base64,
            "width": 1024,  # Adjust as needed
            "height": 1024,  # Adjust as needed
            "steps": 50,     # Number of inference steps
            "guidance_scale": 7.5,  # How closely to follow the prompt
            "seed": None     # Random seed, set to specific number for reproducible results
        }
        
        print(f"Sending image editing request for: {input_path.name}")
        print(f"Prompt: {prompt}")
        
        # Make the API request
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            
            # Check if the response contains the edited image
            if 'images' in result and len(result['images']) > 0:
                # Decode the base64 image
                edited_image_data = base64.b64decode(result['images'][0])
                
                # Generate output filename if not provided
                if output_filename is None:
                    name_part = input_path.stem
                    extension = input_path.suffix
                    timestamp = int(time.time())
                    output_filename = f"flux_edit_{name_part}_{timestamp}{extension}"
                
                # Save the edited image
                output_path = output_dir / output_filename
                
                with open(output_path, "wb") as f:
                    f.write(edited_image_data)
                
                print(f"Successfully saved edited image to: {output_path}")
                return f"images/edit_images/results/{output_filename}"
            
            elif 'id' in result:
                # If the API returns a job ID (async processing)
                job_id = result['id']
                print(f"Image editing job submitted with ID: {job_id}")
                
                # Poll for results
                return poll_for_result(job_id, api_key, output_dir, output_filename or f"flux_edit_{input_path.name}")
            
            else:
                print(f"Unexpected response format: {result}")
                return None
                
        else:
            print(f"API request failed with status {response.status_code}")
            print(f"Error: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        return None

def poll_for_result(job_id, api_key, output_dir, output_filename, max_wait=300):
    """
    Poll the BFL API for job completion and download the result.
    
    Args:
        job_id (str): The job ID returned by the API
        api_key (str): Your Black Forest Labs API key
        output_dir (Path): Directory to save the result
        output_filename (str): Filename for the output
        max_wait (int): Maximum time to wait in seconds
    
    Returns:
        str: Relative path from base directory, or None if failed
    """
    
    url = f"https://api.bfl.ai/v1/get_result"
    headers = {
        "accept": "application/json",
        "x-key": api_key,
    }
    
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(f"{url}?id={job_id}", headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('status') == 'Ready':
                    # Download the image
                    if 'result' in result and 'sample' in result['result']:
                        image_url = result['result']['sample']
                        
                        # Download the image
                        img_response = requests.get(image_url)
                        if img_response.status_code == 200:
                            output_path = output_dir / output_filename
                            
                            with open(output_path, "wb") as f:
                                f.write(img_response.content)
                            
                            print(f"Successfully downloaded edited image to: {output_path}")
                            return f"images/edit_images/results/{output_filename}"
                    
                elif result.get('status') == 'Pending':
                    print("Job still processing, waiting...")
                    time.sleep(10)
                    continue
                    
                else:
                    print(f"Job failed with status: {result.get('status')}")
                    return None
            
            else:
                print(f"Failed to check job status: {response.status_code}")
                time.sleep(10)
                
        except Exception as e:
            print(f"Error checking job status: {str(e)}")
            time.sleep(10)
    
    print("Timeout waiting for job completion")
    return None


def flux_image_edit(prompt: str, image_path: str) -> tuple[str, str]:
    # Set your API key
    API_KEY = str(os.getenv("BFL_API_KEY"))
    
    # Example: Edit a single image
    result = edit_image_with_bfl(
        image_filepath=image_path,
        prompt=prompt,
        api_key=API_KEY
    )
    
    if result:
        print(f"Edited image saved at: {result}")
        return "", result
    else:
        print("Image editing failed")
        return "", ""


# Example usage
if __name__ == "__main__":
    # Set your API key
    API_KEY = str(os.getenv("BFL_API_KEY"))
    
    # Example: Edit a single image
    result = edit_image_with_bfl(
        image_filepath="images/edit_images/saved_images/dall_e_image_20250610_130858.png",
        prompt="Make the cat blue",
        api_key=API_KEY
    )
    
    if result:
        print(f"Edited image saved at: {result}")
    else:
        print("Image editing failed")