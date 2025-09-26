import os
import nest_asyncio
import uvicorn
from pyngrok import ngrok
from config.settings import settings

# Apply nest_asyncio for environments like Colab
nest_asyncio.apply()

def run_with_ngrok():
    """Run the application with ngrok tunnel."""
    
    # Set ngrok auth token if provided
    if settings.ngrok_auth_token:
        ngrok.set_auth_token(settings.ngrok_auth_token)
        print("Ngrok auth token set")
    else:
        print("Warning: NGROK_AUTH_TOKEN not set!")
    
    # Kill any existing tunnels
    ngrok.kill()
    
    port = 8000
    
    try:
        # Start ngrok tunnel
        public_url = ngrok.connect(port)
        print(f"Public URL: {public_url}")
        print(f"Access the API docs at: {public_url}/docs")
        print(f"Test authentication at: {public_url}/auth/token")
        print(f"Ask questions at: {public_url}/chat/ask")
        
        # Start FastAPI server
        print(f"Starting FastAPI server on port {port}")
        uvicorn.run("main:app", host="0.0.0.0", port=port)
        
    except Exception as e:
        print(f"Error starting application with ngrok: {e}")
    finally:
        ngrok.kill()

if __name__ == "__main__":
    run_with_ngrok()