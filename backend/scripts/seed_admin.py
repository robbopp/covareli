"""Create or update the admin user. Usage:
    python scripts/seed_admin.py admin@covareli.ro 'strong-password-here'
"""
import asyncio
import sys

sys.path.insert(0, ".")

from app.auth.security import hash_password  # noqa: E402
from app.db import init_db  # noqa: E402
from app.models import AdminUser  # noqa: E402


async def main(email: str, password: str) -> None:
    await init_db()
    existing = await AdminUser.find_one(AdminUser.email == email)
    if existing:
        existing.password_hash = hash_password(password)
        await existing.save()
        print(f"Updated password for {email}")
    else:
        await AdminUser(email=email, password_hash=hash_password(password)).insert()
        print(f"Created admin {email}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    asyncio.run(main(sys.argv[1], sys.argv[2]))
