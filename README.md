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
