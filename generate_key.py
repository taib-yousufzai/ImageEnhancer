import hashlib
import secrets

def generate_api_key(prefix="pe_live_"):
    # Generate 32 bytes of secure random hex
    random_part = secrets.token_hex(32)
    # Combine prefix and random hex to form the key
    api_key = f"{prefix}{random_part}"
    
    # Hash the key using SHA-256
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    return api_key, key_hash

if __name__ == "__main__":
    print("-" * 60)
    print("🔐 PhotoEnhancer API Key Generator 🔐")
    print("-" * 60)
    
    key, hashed = generate_api_key()
    
    print("\n1. GIVE THIS KEY TO YOUR FRONTEND (Next.js config):")
    print(f"--> {key} <--")
    print("\n   *(Keep this strictly secret!)*")
    
    print("\n2. SET THIS IN YOUR PYTHON BACKEND (.env):")
    print(f"ALLOWED_API_KEY_HASHES={hashed}")
    print("\n   *(You can comma-separate multiple hashes if you want multiple keys)*")
    print("-" * 60)
