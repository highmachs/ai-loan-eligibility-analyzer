import sys
import argparse
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.database import SessionLocal
from app.models.user import User, UserRole
from app.services.auth_service import hash_password

def create_or_append_user(username, password, role_str):
    username = username.strip()
    password = password.strip()
    role_str = role_str.strip().upper()

    # Normalize role
    role_map = {
        "1": UserRole.LOAN_OFFICER,
        "LOAN_OFFICER": UserRole.LOAN_OFFICER,
        "OFFICER": UserRole.LOAN_OFFICER,
        "2": UserRole.SENIOR_CREDIT_MANAGER,
        "SENIOR_CREDIT_MANAGER": UserRole.SENIOR_CREDIT_MANAGER,
        "SCM": UserRole.SENIOR_CREDIT_MANAGER,
        "3": UserRole.ADMIN,
        "ADMIN": UserRole.ADMIN,
        "ADMINISTRATOR": UserRole.ADMIN,
    }

    if role_str not in role_map:
        print(f"\n[ERROR] Invalid role '{role_str}'. Allowed roles: LOAN_OFFICER, SENIOR_CREDIT_MANAGER, ADMIN")
        return False

    selected_role = role_map[role_str]

    if len(username) < 3:
        print("\n[ERROR] Username must be at least 3 characters long.")
        return False
    if len(password) < 4:
        print("\n[ERROR] Password must be at least 4 characters long.")
        return False

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            print(f"\n[NOTICE] User '{username}' already exists (Current Role: {existing.role.value}).")
            choice = input("Do you want to update their password and role? (y/N): ").strip().lower()
            if choice == 'y':
                existing.hashed_password = hash_password(password)
                existing.role = selected_role
                db.commit()
                print(f"[SUCCESS] User '{username}' updated successfully with Role: {selected_role.value}!")
                return True
            else:
                print("[CANCELLED] No changes made.")
                return False

        # Create new user and append to existing database
        new_user = User(
            username=username,
            hashed_password=hash_password(password),
            role=selected_role
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        print("\n========================================================")
        print("  ACCOUNT CREATED SUCCESSFULLY!")
        print("========================================================")
        print(f"  User ID  : {new_user.id}")
        print(f"  Username : {new_user.username}")
        print(f"  Role     : {new_user.role.value}")
        print("========================================================\n")
        return True
    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Failed to save user to database: {e}")
        return False
    finally:
        db.close()

def main():
    parser = argparse.ArgumentParser(description="Create or Append User Account in Loan Eligibility Analyzer Database")
    parser.add_argument("-u", "--username", help="Account Username", type=str)
    parser.add_argument("-p", "--password", help="Account Password", type=str)
    parser.add_argument("-r", "--role", help="Account Role (LOAN_OFFICER / SENIOR_CREDIT_MANAGER / ADMIN)", type=str)
    args = parser.parse_args()

    print("\n--------------------------------------------------------")
    print("  Loan Eligibility Analyzer - Account Provisioning Tool")
    print("--------------------------------------------------------")

    if args.username and args.password and args.role:
        create_or_append_user(args.username, args.password, args.role)
    else:
        # Interactive prompt
        username = input("\nEnter Username: ").strip()
        password = input("Enter Password: ").strip()
        print("\nSelect Role:")
        print("  1. LOAN_OFFICER         (Limit <= INR 5,00,000)")
        print("  2. SENIOR_CREDIT_MANAGER(Limit <= INR 25,00,000)")
        print("  3. ADMIN                (Unlimited / Governance)")
        role_choice = input("Enter Choice (1/2/3 or Role Name): ").strip()
        
        create_or_append_user(username, password, role_choice)

if __name__ == "__main__":
    main()
