# Remnawave Telegram Management Bot

A `Telegram` bot that provides administrative capabilities for managing users and system resources through Telegram interface. With this bot, administrators can:

- **User Management**: Create, delete, enable/disable user accounts with custom or quick setup
- **Squad Assignment**: Assign users to available squads for organized management  
- **Subscription Links**: Generate and distribute subscription links instantly
- **Node Control**: Monitor, enable, disable, and reboot nodes remotely
- **System Monitoring**: View comprehensive system statistics, bandwidth usage, and health metrics
- **Traffic Management**: Reset user traffic and monitor usage patterns

This bot is designed for self-hosted proxy enthusiasts who want convenient Telegram-based management without constantly accessing the web panel.

> [!IMPORTANT]
> This is a simple pet project, not a large-scale bot that gives you complete control over the panel.
> It's quite obvious most of the actions (such as squads/nodes/metrics control) can be comfortably done through the panel itself. This bot is just a convenience tool for quick actions.

## Features

### User Management
- **Quick User Creation**: Generate users with random usernames and default settings
- **Custom User Creation**: Full control over username, expiration, traffic limits, and metadata
- **User Status Control**: Enable/disable users instantly
- **Traffic Reset**: Reset user traffic consumption
- **Subscription Links**: Generate and share subscription URLs

### Node Management  
- **Node Monitoring**: View detailed node status, traffic, and health
- **Remote Control**: Enable, disable, and restart nodes
- **Bulk Operations**: Restart all nodes with confirmation
- **Real-time Updates**: Auto-refresh node information after actions

### System Statistics
- **System Overview**: Memory usage, CPU stats, and general health
- **Bandwidth Analytics**: Traffic consumption and usage patterns  
- **Node Metrics**: Detailed per-node statistics and performance
- **Real-time Data**: Live system monitoring and health checks
- **User Analytics**: Active/inactive user counts and traffic distribution

## Requirements

- Docker and Docker Compose
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Remnawave API token from your panel
- Admin Telegram User ID(s)

## Quick Start

Copy `.env` and `docker-compose.yml` on your system (for example, in `/opt/management`):

```bash
wget https://raw.githubusercontent.com/hzhexee/remnawave-telegram-management-bot/refs/heads/main/docker-compose.yml -O docker-compose.yml
wget https://raw.githubusercontent.com/hzhexee/remnawave-telegram-management-bot/refs/heads/main/.env -O .env
```

Then, edit the `.env` file to set your environment variables.

After that, run the bot using Docker Compose:

```bash
docker-compose up -d && docker compose logs -f
```

### Important Configuration Notes

**Local Network Setup**
If your bot runs on the same network as the panel (e.g., using Docker Compose), set:
```bash
IS_LOCAL_NETWORK=true
```
This enables proper forwarding headers (`X-Forwarded-Proto` and `X-Forwarded-For`) which help prevent connection issues like "Server disconnected without sending a response."

**Remote Setup**
If your bot runs on a different server than the panel, set:
```bash
IS_LOCAL_NETWORK=false
```

### Setting up Admin Access

Configure the `ADMIN_USER_ID` environment variable in your `.env` file:

**Option 1: JSON Array Format (recommended)**
```bash
ADMIN_USER_ID=["123456789", "987654321"]
```

**Option 2: Comma-separated Format**
```bash
ADMIN_USER_ID=123456789,987654321
```

**Single Admin**
```bash
ADMIN_USER_ID=["123456789"]
# or
ADMIN_USER_ID=123456789
```

> [!WARNING]
> Make sure to set the `ADMIN_USER_ID` environment variable before running the bot, otherwise it will not start.

### How to Find Your Telegram User ID

1. **Using @userinfobot**: Send `/start` to [@userinfobot](https://t.me/userinfobot)
2. **Using @myidbot**: Send `/getid` to [@myidbot](https://t.me/myidbot)  
3. **Manual method**: Forward any message to [@userinfobot](https://t.me/userinfobot)

## Bot Commands & Usage

### Basic Commands
- `/start` - Initialize bot and show main menu

## Environment Variables

Complete list of required environment variables:

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `API_TOKEN` | Panel API token from settings | `your_panel_api_token` | ✅ |
| `REMNAWAVE_BASE_URL` | Panel base URL | `http://remnawave:3000` | ✅ |
| `IS_LOCAL_NETWORK` | Enable X-Forwarded headers for local network | `true` | ✅ |
| `COOKIES` | Required for eGames script when not on same server | `{"key":"value"}` | ⚠️ |
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather | `123456:ABC-DEF...` | ✅ |
| `ADMIN_USER_ID` | Admin Telegram user ID(s) | `["123456789"]` | ✅ |

## Docker Information

The bot runs in a Docker container with the following features:

- **Image**: `hzhexee/remnawave-telegram-management-bot:latest`
- **Health Check**: Automatic bot status monitoring
- **Network**: Connects to `remnawave-network` by default
- **Restart Policy**: `unless-stopped` for reliability

### Container Health Check
The container includes a health check that verifies bot connectivity every 30 seconds:
```bash
python -c "import requests; requests.get('https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe')"
```

### Logs and Debugging

View bot logs:
```bash
docker compose logs -f remnawave-telegram-management-bot
```

## Updates

To update the bot to the latest version:

```bash
docker compose pull && docker compose down && docker compose up -d && docker compose logs -f
```

## 🤝 Contributing

PR/Issue welcome