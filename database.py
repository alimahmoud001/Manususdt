import os
from supabase import create_client, Client
from dotenv import load_dotenv
import uuid

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def init_tables():
    """Initialize database tables if they don't exist."""
    try:
        # Check if users table exists by trying to query it
        supabase.table("users").select("id").limit(1).execute()
    except Exception as e:
        print(f"Creating users table...")
        # Create users table
        supabase.rpc("create_users_table").execute()

    try:
        supabase.table("referrals").select("id").limit(1).execute()
    except Exception as e:
        print(f"Creating referrals table...")
        supabase.rpc("create_referrals_table").execute()

    try:
        supabase.table("withdrawals").select("id").limit(1).execute()
    except Exception as e:
        print(f"Creating withdrawals table...")
        supabase.rpc("create_withdrawals_table").execute()


def create_user(user_id: int, username: str, first_name: str):
    """Create a new user with initial 30 USDT balance."""
    referral_code = str(uuid.uuid4())[:8]
    
    data = {
        "user_id": user_id,
        "username": username,
        "first_name": first_name,
        "referral_code": referral_code,
        "balance": 30.0,
        "referral_count": 0,
        "created_at": "now()",
    }
    
    response = supabase.table("users").insert(data).execute()
    return response.data[0] if response.data else None


def get_user(user_id: int):
    """Get user by user_id."""
    response = supabase.table("users").select("*").eq("user_id", user_id).execute()
    return response.data[0] if response.data else None


def get_user_by_referral_code(referral_code: str):
    """Get user by referral code."""
    response = supabase.table("users").select("*").eq("referral_code", referral_code).execute()
    return response.data[0] if response.data else None


def add_referral(referrer_id: int, referred_user_id: int):
    """Add a referral record and update referral count."""
    data = {
        "referrer_id": referrer_id,
        "referred_user_id": referred_user_id,
        "created_at": "now()",
    }
    
    supabase.table("referrals").insert(data).execute()
    
    # Update referral count
    user = get_user(referrer_id)
    if user:
        new_count = user["referral_count"] + 1
        supabase.table("users").update({"referral_count": new_count}).eq("user_id", referrer_id).execute()


def get_referral_count(user_id: int) -> int:
    """Get the number of referrals for a user."""
    user = get_user(user_id)
    return user["referral_count"] if user else 0


def get_balance(user_id: int) -> float:
    """Get user balance."""
    user = get_user(user_id)
    return user["balance"] if user else 0.0


def update_balance(user_id: int, amount: float):
    """Update user balance."""
    user = get_user(user_id)
    if user:
        new_balance = user["balance"] + amount
        supabase.table("users").update({"balance": new_balance}).eq("user_id", user_id).execute()


def create_withdrawal_request(user_id: int, wallet_address: str, amount: float):
    """Create a withdrawal request."""
    data = {
        "user_id": user_id,
        "wallet_address": wallet_address,
        "amount": amount,
        "status": "pending",
        "created_at": "now()",
    }
    
    response = supabase.table("withdrawals").insert(data).execute()
    return response.data[0] if response.data else None


def get_pending_withdrawal(user_id: int):
    """Get pending withdrawal for a user."""
    response = supabase.table("withdrawals").select("*").eq("user_id", user_id).eq("status", "pending").execute()
    return response.data[0] if response.data else None


def update_withdrawal_status(withdrawal_id: int, status: str):
    """Update withdrawal status."""
    supabase.table("withdrawals").update({"status": status}).eq("id", withdrawal_id).execute()


def mark_withdrawal_processing(user_id: int):
    """Mark user's withdrawal as processing."""
    withdrawal = get_pending_withdrawal(user_id)
    if withdrawal:
        update_withdrawal_status(withdrawal["id"], "processing")


def get_user_by_id(user_id: int):
    """Get user info by user_id."""
    user = get_user(user_id)
    return user
