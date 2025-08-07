# Remnawave Telegram Management Bot

A `Telegram` bot that provides administrative capabilities for managing users and system resources. With this bot, administrators can:

- Create new `user` accounts.
- Assign `users` to available `squads`.
- Generate and distribute `subscription` links.
- Reboot `nodes`.

This bot is meant to be used when you're not a large scale seller, but rather a self-host proxy enthusiast and you want to manage some of the stuff through Telegram.

> [!IMPORTANT]
> This is a simple pet project, not a large-scale bot that gives you a complete control over the panel.
> It's quite obvious most of the actions (such as squads/nodes/metrics control) can be done much more comfortably through the panel itself.

## Installation

Copy `.env` and `docker-compose.yml` on your system:

```bash
wget https://raw.githubusercontent.com/hzhexee/remnawave-telegram-management-bot/refs/heads/main/docker-compose.yml -O docker-compose.yml
wget https://raw.githubusercontent.com/hzhexee/remnawave-telegram-management-bot/refs/heads/main/.env -O .env
```

Then, edit the `.env` file to set your environment variables.

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
