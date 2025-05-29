from dotenv import load_dotenv
import os
import time

from langchain_core.tools import tool

from instagrapi import Client
from instagrapi.exceptions import LoginRequired, UserNotFound, DirectError, TwoFactorRequired, ChallengeRequired

load_dotenv()

@tool
def send_instagram_dm(username: str, message: str) -> str:
    """
    Send a direct message to a user on Instagram.
    
    Args:
        username (str): The Instagram username of the recipient.
        message (str): The text message to be sent to the user.
    """
    
    # Input validation
    if not username or not isinstance(username, str):
        raise ValueError("Username must be a non-empty string")
    
    if not message or not isinstance(message, str):
        raise ValueError("Message must be a non-empty string")
    
    # Remove @ symbol if present
    username = username.lstrip('@').strip()
    
    # Check message length
    if len(message) > 1000:
        raise ValueError("Message exceeds maximum length limit (1000 characters)")
    
    # Get credentials from environment variables
    login_username = os.getenv('IG_USERNAME')
    login_password = os.getenv('IG_PASSWORD')
    session_file = os.getenv('IG_SESSION_FILE')
    
    if not login_username or not login_password:
        raise ValueError("Instagram credentials not provided. Set IG_USERNAME and IG_PASSWORD environment variables")
    
    # Set default session file if not provided
    if not session_file:
        session_file = f"ig_session_{login_username}.json"
    
    # Configure client with better settings
    client = Client()
    client.delay_range = [1, 3]  # Add delay between requests
    
    try:
        # Try to load existing session first
        session_loaded = False
        if os.path.exists(session_file):
            try:
                print("Loading existing session...")
                client.load_settings(session_file) # type: ignore
                # Test if session is still valid
                client.get_timeline_feed()
                print("✓ Session is valid and loaded")
                session_loaded = True
            except Exception as e:
                print(f"Session invalid or expired: {e}")
                session_loaded = False
        
        # If session loading failed, do fresh login
        if not session_loaded:
            print("Performing fresh login...")
            login_success = False
            
            for attempt in range(3):  # Try up to 3 times
                try:
                    if attempt > 0:
                        print(f"Login attempt {attempt + 1}/3...")
                        time.sleep(5)  # Wait between attempts
                    
                    client.login(login_username, login_password)
                    print("✓ Logged in successfully")
                    login_success = True
                    break
                    
                except TwoFactorRequired:
                    print("Two-factor authentication required!")
                    
                    # Prompt user for 2FA code
                    verification_code = input("Enter your 2FA verification code: ").strip()
                    
                    if not verification_code:
                        print("Error: 2FA verification code is required")
                        return "Error: 2FA verification code is required"
                    
                    try:
                        client.login(login_username, login_password, verification_code=verification_code)
                        print("✓ Logged in with 2FA")
                        login_success = True
                        break
                    except ChallengeRequired:
                        print("Challenge required after 2FA. Attempting to resolve...")
                        if _handle_challenge(client):
                            try:
                                client.login(login_username, login_password, verification_code=verification_code)
                                print("✓ Successfully logged in after challenge resolution")
                                login_success = True
                                break
                            except Exception as retry_error:
                                print(f"Login failed after challenge resolution: {retry_error}")
                        
                except ChallengeRequired:
                    print("Challenge required. Attempting to resolve...")
                    if _handle_challenge(client):
                        try:
                            client.login(login_username, login_password)
                            print("✓ Successfully logged in after challenge resolution")
                            login_success = True
                            break
                        except Exception as retry_error:
                            print(f"Login failed after challenge resolution: {retry_error}")
                    
                except Exception as login_error:
                    print(f"Login attempt {attempt + 1} failed: {login_error}")
                    if attempt == 2:  # Last attempt
                        print("All login attempts failed")
                        return "All login attempts failed"
            
            if not login_success:
                print("Could not complete login after multiple attempts")
                return "Could not complete login after multiple attempts"
            
            # Save session for future use
            try:
                client.dump_settings(session_file) # type: ignore
                print("✓ Session saved for future logins")
            except Exception as e:
                print(f"Warning: Could not save session: {e}")
        
        # Get user ID from username
        print(f"Finding user: {username}...")
        try:
            user_id = client.user_id_from_username(username)
        except UserNotFound:
            print(f"Error: User '{username}' not found")
            return f"Error: User '{username}' not found"
        
        # Send direct message
        print(f"Sending message to @{username}...")
        result = client.direct_send(message, [user_id]) # type: ignore
        
        if result:
            print(f"✓ Message sent successfully to @{username}")
            return f"✓ Message sent successfully to @{username}"
        else:
            print(f"✗ Failed to send message to @{username}")
            return f"✗ Failed to send message to @{username}"
            
    except ChallengeRequired:
        print("Error: Instagram challenge required but could not be resolved automatically")
        print("Please log into Instagram manually to complete security verification")
        return (
            "Error: Instagram challenge required but could not be resolved automatically"
            "Please log into Instagram manually to complete security verification"
        )
    
    except TwoFactorRequired:
        print("Error: Two-factor authentication required but verification failed")
        return "Error: Two-factor authentication required but verification failed"
    
    except LoginRequired:
        print("Error: Instagram login failed. Check your credentials.")
        return "Error: Instagram login failed. Check your credentials."
    
    except DirectError as e:
        print(f"Error sending direct message: {e}")
        return f"Error sending direct message: {e}"
    
    except Exception as e:
        print(f"Unexpected error: {e}")
        return f"Unexpected error: {e}"
    
    finally:
        # Don't logout if we want to keep session
        pass


def _handle_challenge(client):
    """
    Helper function to handle Instagram challenges.
    
    Args:
        client: Instagram client instance
        
    Returns:
        bool: True if challenge was resolved, False otherwise
    """
    try:
        print("Attempting to resolve Instagram challenge...")
        
        # Get challenge info
        challenge = client.last_challenge
        
        if challenge:
            print(f"Challenge type: {challenge.get('challenge', {}).get('challenge_context', 'Unknown')}")
            
            # Try automatic resolution
            challenge_resolved = client.challenge_resolve(challenge)
            
            if challenge_resolved:
                print("✓ Challenge resolved automatically")
                return "✓ Challenge resolved automatically"
            else:
                print("Could not resolve challenge automatically")
                
        print("\nManual steps required:")
        print("1. Open Instagram on your phone or browser")
        print("2. Complete any security verification (CAPTCHA, email/SMS verification)")
        print("3. Try running this script again in a few minutes")
        print("4. Consider using the same device/IP you normally use for Instagram")
        
        return "Could not resolve challenge automatically"
        
    except Exception as e:
        print(f"Error handling challenge: {e}")
        return f"Error handling challenge: {str(e)}"


# Example usage
if __name__ == "__main__":
    # Set environment variables first:
    # export IG_USERNAME="your_instagram_username"
    # export IG_PASSWORD="your_instagram_password"
    # export IG_SESSION_FILE="my_custom_session.json"  # Optional
    
    # Then call the function:
    success = send_instagram_dm.invoke(input={
        "username": "taher_m.16",
        "message": "Get a job lmao",
    })
    
    if success:
        print("Message sent successfully!")
    else:
        print("Failed to send message.")
    
    pass