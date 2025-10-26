"""
Generate VAPID keys for Web Push notifications
Run once: python generate_vapid_keys.py
"""
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import base64

# Generate private key
private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())

# Get public key
public_key = private_key.public_key()

# Serialize private key
private_key_bytes = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
)

# Serialize public key (uncompressed format for VAPID)
public_key_bytes = public_key.public_bytes(
    encoding=serialization.Encoding.X962,
    format=serialization.PublicFormat.UncompressedPoint
)

# Convert to base64 URL-safe encoding
private_key_b64 = base64.urlsafe_b64encode(private_key_bytes).decode().rstrip('=')
public_key_b64 = base64.urlsafe_b64encode(public_key_bytes).decode().rstrip('=')

print("\n" + "="*70)
print("VAPID KEYS GENERATED")
print("="*70)
print("\nAdd these to your settings.py or .env file:\n")
print(f"VAPID_PUBLIC_KEY = '{public_key_b64}'")
print(f"VAPID_PRIVATE_KEY = '{private_key_b64}'")
print(f"VAPID_ADMIN_EMAIL = 'mailto:your-email@example.com'")
print("\n" + "="*70)
print("\nKeep the private key SECRET and never commit it to version control!")
print("="*70 + "\n")
