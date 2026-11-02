"""Management commands.

Usage: python -m app.cli make-admin <username>
"""

import asyncio
import sys

from sqlalchemy import func, select

from app.db.session import SessionLocal, engine
from app.models import User, UserRole


async def make_admin(username: str) -> int:
    async with SessionLocal() as db:
        user = await db.scalar(select(User).where(func.lower(User.username) == username.lower()))
        if user is None:
            print(f"User '{username}' not found", file=sys.stderr)
            return 1
        user.role = UserRole.ADMIN
        await db.commit()
    await engine.dispose()
    print(f"'{username}' is now an admin")
    return 0


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] != "make-admin":
        print(__doc__, file=sys.stderr)
        return 2
    return asyncio.run(make_admin(sys.argv[2]))


if __name__ == "__main__":
    sys.exit(main())
