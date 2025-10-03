#!/usr/bin/env python3
"""
Script to generate a secure Django SECRET_KEY

Usage:
    python scripts/generate_secret_key.py

This script generates a cryptographically secure random SECRET_KEY
suitable for Django production environments.
"""

def generate_secret_key():
    """Generate a secure Django SECRET_KEY"""
    try:
        # Try using Django's built-in generator (recommended)
        from django.core.management.utils import get_random_secret_key
        return get_random_secret_key()
    except ImportError:
        # Fallback to Python's secrets module
        import secrets
        import string
        
        # Use a mix of letters, digits, and special characters
        chars = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
        return ''.join(secrets.choice(chars) for _ in range(50))


def main():
    """Main function to generate and display a new SECRET_KEY"""
    print("=" * 70)
    print("Django SECRET_KEY Generator")
    print("=" * 70)
    print()
    
    secret_key = generate_secret_key()
    
    print("Generated SECRET_KEY:")
    print("-" * 70)
    print(secret_key)
    print("-" * 70)
    print()
    print("IMPORTANT SECURITY NOTES:")
    print("  ✅ Copy this key and set it as an environment variable")
    print("  ✅ Keep this key secret - never commit it to version control")
    print("  ✅ Use different keys for development, staging, and production")
    print("  ✅ Rotate keys periodically for enhanced security")
    print()
    print("To use this key:")
    print(f'  export SECRET_KEY="{secret_key}"')
    print("  # or add it to your .env file:")
    print(f'  SECRET_KEY={secret_key}')
    print()


if __name__ == "__main__":
    main()
