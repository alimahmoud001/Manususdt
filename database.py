import os
import logging
from supabase import create_client
from dotenv import load_dotenv
import uuid

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

logger = logging.getLogger(__name__)

# Initialize Supabase client
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {e}")
    supabase = None


def create_user(user_id: int, username: str, first_name: str):
    """Create a new user with initial 30 USDT balance."""
    try:
        referral_code = str(uuid.uuid4())[:8]
        
        data = {
            "user_id": user_id,
            "username": username or "unknown",
            "first_name": first_name,
            "referral_code": referral_code,
            "balance": 30.0,
            "referral_count": 0,
        }
        
        response = supabase.table("users").insert(data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return None


def get_user(user_id: int):
    """Get user by user_id."""
    try:
        response = supabase.table("users").select("*").eq("user_id", user_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        return None


def get_user_by_referral_code(referral_code: str):
    """Get user by referral code."""
    try:
        response = supabase.table("users").select("*").eq("referral_code", referral_code).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Error getting user by referral code: {e}")
        return None


def add_referral(referrer_id: int, referred_user_id: int):
    """Add a referral record and update referral count."""
    try:
        data = {
            "referrer_id": referrer_id,
            "referred_user_id": referred_user_id,
        }
        
        supabase.table("referrals").insert(data).execute()
        
        # Update referral count
        user = get_user(referrer_id)
        if user:
            new_count = user["referral_count"] + 1
            supabase.table("users").update({"referral_count": new_count}).eq("user_id", referrer_id).execute()
    except Exception as e:
        logger.error(f"Error adding referral: {e}")


def get_referral_count(user_id: int) -> int:
    """Get the number of referrals for a user."""
    try:
        user = get_user(user_id)
        return user["referral_count"] if user else 0
    except Exception as e:
        logger.error(f"Error getting referral count: {e}")
        return 0


def get_balance(user_id: int) -> float:
    """Get user balance."""
    try:
        user = get_user(user_id)
        return float(user["balance"]) if user else 0.0
    except Exception as e:
        logger.error(f"Error getting balance: {e}")
        return 0.0


def update_balance(user_id: int, amount: float):
    """Update user balance."""
    try:
        user = get_user(user_id)
        if user:
            new_balance = float(user["balance"]) + amount
            supabase.table("users").update({"balance": new_balance}).eq("user_id", user_id).execute()
    except Exception as e:
        logger.error(f"Error updating balance: {e}")


def create_withdrawal_request(user_id: int, wallet_address: str, amount: float):
    """Create a withdrawal request."""
    try:
        data = {
            "user_id": user_id,
            "wallet_address": wallet_address,
            "amount": amount,
            "status": "pending",
        }
        
        response = supabase.table("withdrawals").insert(data).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Error creating withdrawal request: {e}")
        return None


def get_pending_withdrawal(user_id: int):
    """Get pending withdrawal for a user."""
    try:
        response = supabase.table("withdrawals").select("*").eq("user_id", user_id).eq("status", "pending").execute()
        return response.data[0] if response.data else None
    except Exception as e:
        logger.error(f"Error getting pending withdrawal: {e}")
        return None


def update_withdrawal_status(withdrawal_id: int, status: str):
    """Update withdrawal status."""
    try:
        supabase.table("withdrawals").update({"status": status}).eq("id", withdrawal_id).execute()
    except Exception as e:
        logger.error(f"Error updating withdrawal status: {e}")


def mark_withdrawal_processing(user_id: int):
    """Mark user's withdrawal as processing."""
    try:
        withdrawal = get_pending_withdrawal(user_id)
        if withdrawal:
            update_withdrawal_status(withdrawal["id"], "processing")
    except Exception as e:
        logger.error(f"Error marking withdrawal as processing: {e}")
