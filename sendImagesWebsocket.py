import torch
import numpy as np
from PIL import Image
import requests
import io
import time

# Note: This node requires dependencies from the requirements.txt file.
# Please install them by running the following command in your ComfyUI environment:
# pip install -r requirements.txt
try:
    import websocket
except ImportError:
    print("Warning: 'websocket-client' not installed. WebSocket functionality will not be available.")
    websocket = None

class SendImagesWebsocket:
    # This is the only class we need. It contains all the logic.

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE", ),
                "url": ("STRING", {"default": "http://127.0.0.1:8000/upload"}),
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "send_request" # Renamed for clarity
    OUTPUT_NODE = True
    CATEGORY = "api/image"

    def send_request(self, images, url):
        # This is the function that will be executed.
        for image in images:
            # 1. Convert tensor to PIL Image
            i = 255. * image.cpu().numpy()
            img_pil = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))

            # 2. Create an in-memory binary stream (acts like a file)
            buffer = io.BytesIO()

            # 3. Save the PIL image to the buffer in PNG format
            img_pil.save(buffer, format="PNG")

            # 4. Rewind the buffer to the beginning so it can be read
            buffer.seek(0)
            
            # 5. Check if the URL is for HTTP/HTTPS or WebSocket
            if url.startswith(('ws://', 'wss://')):
                # Handle WebSocket connection
                if websocket is None:
                    print("Error: 'websocket-client' library is required for WebSocket URLs. Please install dependencies from requirements.txt.")
                    continue
                
                try:
                    ws = websocket.create_connection(url)
                    # Send the image data as a binary message
                    ws.send(buffer.getvalue(), opcode=websocket.ABNF.OPCODE_BINARY)
                    ws.close()
                    print(f"Successfully sent image to WebSocket: {url}")
                except Exception as e:
                    print(f"Error sending image to WebSocket {url}: {e}")

            else:
                # Handle HTTP/HTTPS connection using requests
                # Prepare the data for the POST request as a file upload
                files = {'file': ('image.png', buffer, 'image/png')}
                try:
                    # Send the request with the file data
                    response = requests.post(url, files=files)
                    response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
                    print(f"Successfully sent image to {url}. Status: {response.status_code}")
                except requests.exceptions.RequestException as e:
                    print(f"Error sending image to {url}: {e}")
            
        return {}

    # This function tells ComfyUI to re-run this node every time
    def IS_CHANGED(self, images, url):
        return time.time()

# This dictionary tells ComfyUI what nodes to register from this file.
NODE_CLASS_MAPPINGS = {
    "Send Images via WebSocket": SendImagesWebsocket,
}

# A dictionary that contains human-readable titles for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "Send Images via WebSocket": "Send Image via HTTP/WebSocket",
}
