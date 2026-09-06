"""
Script utilitaire pour réinitialiser ou modifier le mot de passe d'un utilisateur en ligne de commande.

Usage:
    python scripts/reset_password.py <username> <nouveau_mot_de_passe>

Exemple:
    python scripts/reset_password.py admin mon_super_mot_de_passe
"""
import sys
import os

# Ensure root workspace is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import hash_password

def reset_password(username: str, new_password: str):
    username = username.strip()
    if not username:
        print("[-] Erreur : Le nom d'utilisateur ne peut pas être vide.")
        sys.exit(1)
        
    if len(new_password) < 6:
        print("[-] Erreur : Le mot de passe doit comporter au moins 6 caractères.")
        sys.exit(1)

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            print(f"[-] Erreur : L'utilisateur « {username} » n'existe pas dans la base de données.")
            sys.exit(1)

        user.hashed_password = hash_password(new_password)
        db.commit()
        print(f"[+] Succès : Le mot de passe de l'utilisateur « {username} » (rôle: {user.role}) a été mis à jour avec succès !")
    except Exception as e:
        db.rollback()
        print(f"[-] Erreur lors de la mise à jour : {e}")
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    user_arg = sys.argv[1]
    pass_arg = sys.argv[2]
    reset_password(user_arg, pass_arg)
