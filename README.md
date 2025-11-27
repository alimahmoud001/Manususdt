# Telegram Referral Bot

A simple and profitable Telegram bot with a referral system. Users can earn money by inviting friends.

## Features

- **Sign-up Bonus**: New users receive $30 USDT upon registration
- **Referral System**: Users earn $30 USDT for each friend who joins via their referral link
- **Withdrawal**: Users can withdraw their balance after reaching 30 referrals
- **Transaction Fee**: A $30 USDT fee is required to process withdrawals
- **Admin Notifications**: Admin receives notifications for new users and withdrawal requests

## Prerequisites

- Python 3.8+
- Telegram Bot Token (from BotFather)
- Supabase account with API credentials

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/telegram-referral-bot.git
cd telegram-referral-bot
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_CHAT_ID=your_admin_chat_id_here
SUPABASE_URL=your_supabase_project_url_here
SUPABASE_KEY=your_supabase_api_key_here
```

### 5. Set up Supabase Database

Create the following tables in your Supabase project:

#### Users Table
```sql
CREATE TABLE users (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT UNIQUE NOT NULL,
  username TEXT,
  first_name TEXT,
  referral_code TEXT UNIQUE NOT NULL,
  balance DECIMAL(10, 2) DEFAULT 30.0,
  referral_count INT DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW()
);
```

#### Referrals Table
```sql
CREATE TABLE referrals (
  id BIGSERIAL PRIMARY KEY,
  referrer_id BIGINT NOT NULL REFERENCES users(user_id),
  referred_user_id BIGINT NOT NULL REFERENCES users(user_id),
  created_at TIMESTAMP DEFAULT NOW()
);
```

#### Withdrawals Table
```sql
CREATE TABLE withdrawals (
  id BIGSERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL REFERENCES users(user_id),
  wallet_address TEXT NOT NULL,
  amount DECIMAL(10, 2) NOT NULL,
  status TEXT DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT NOW()
);
```

## Running Locally

```bash
python bot.py
```

## Deployment on Render

### 1. Push to GitHub

```bash
git add .
git commit -m "Initial commit"
git push origin main
```

### 2. Create a new service on Render

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" and select "Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: `telegram-referral-bot`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`

### 3. Add environment variables

In the Render dashboard, add the following environment variables:

- `BOT_TOKEN`: Your Telegram bot token
- `ADMIN_CHAT_ID`: Your admin chat ID
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase API key

### 4. Deploy

Click "Deploy" to start the bot.

## Bot Commands

- `/start` - Register or start the bot
- `/menu` - Show main menu
- `/balance` - Check your balance
- `/referral` - Get your referral link

## How It Works

1. **User Registration**: When a user starts the bot, they receive $30 USDT
2. **Referrals**: Users can share their referral link to invite friends
3. **Earning**: For each friend who joins via their link, they earn $30 USDT
4. **Withdrawal**: After 30 referrals, users can request a withdrawal
5. **Fee**: A $30 USDT transaction fee is required to process the withdrawal
6. **Processing**: After payment, the withdrawal is marked as "Processing"

## Important Notes

- The bot uses Supabase for data storage
- Admin receives notifications for all new users and withdrawals
- Users must have at least 30 referrals to withdraw
- Transaction fees are mandatory for withdrawals

## Support

For issues or questions, please open an issue on GitHub.

## License

MIT License
