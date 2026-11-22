import asyncio
import getpass
import sys

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.database import AsyncSessionLocal
from app.core.security import hash_password
from app.models.enums import Peran
from app.models.pengguna import Pengguna
from app.schemas.auth import POLA_EMAIL


async def buat_admin_interaktif() -> None:
    nama = input("Nama Admin: ").strip()
    if not nama:
        print("Error: nama tidak boleh kosong", file=sys.stderr)
        sys.exit(1)
    if len(nama) > 100:
        print("Error: nama maksimal 100 karakter", file=sys.stderr)
        sys.exit(1)

    email = input("Email Admin: ").strip().lower()
    if not email:
        print("Error: email tidak boleh kosong", file=sys.stderr)
        sys.exit(1)
    if not POLA_EMAIL.match(email):
        print("Error: format email tidak valid", file=sys.stderr)
        sys.exit(1)

    password = getpass.getpass("Password Admin (min 12 karakter): ")
    if not password:
        print("Error: password tidak boleh kosong", file=sys.stderr)
        sys.exit(1)

    panjang_password = len(password.encode("utf-8"))
    if panjang_password < 12:
        print("Error: password minimal 12 karakter", file=sys.stderr)
        sys.exit(1)
    if panjang_password > 72:
        print("Error: password maksimal 72 karakter", file=sys.stderr)
        sys.exit(1)

    password_ulang = getpass.getpass("Ulangi password: ")
    if password != password_ulang:
        print("Error: password tidak cocok", file=sys.stderr)
        sys.exit(1)

    async with AsyncSessionLocal() as db:
        # Cek email sudah ada
        existing = await db.scalar(select(Pengguna).where(Pengguna.email == email))
        if existing is not None:
            print("Error: Email sudah terdaftar", file=sys.stderr)
            sys.exit(1)

        # Buat akun Admin
        password_hash = await hash_password(password)
        pengguna = Pengguna(nama=nama, email=email, password_hash=password_hash, peran=Peran.ADMIN)
        db.add(pengguna)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            print("Error: Email sudah terdaftar", file=sys.stderr)
            sys.exit(1)

        print(f"Akun Admin dibuat untuk {email}.")


if __name__ == "__main__":
    asyncio.run(buat_admin_interaktif())
