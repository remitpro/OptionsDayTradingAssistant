# Production Deployment (Fly.io)

This guide details how to deploy your Options Day-Trading Assistant to Fly.io for 24/7 scanning.

## 1. Prerequisites

- [flyctl](https://fly.io/docs/hands-on/install-flyctl/) installed
- A valid `token.json` generated locally via `tda-api` authentication flow

## 2. Initial Setup

Initialize the app with Fly.io:

```bash
# Initialize the app (steps will prompt for a name)
fly launch --no-deploy
```

This generates a `fly.toml` file tailored to your application.

## 3. Configure Persistence (CRITICAL)

The application requires persistent storage for:
-   **TDA Token**: The API token must be refreshed periodically. Ephemeral containers lose this file on restarts.
-   **Trade Database**: Your trade history (`trades.db`) should persist across deployments.
-   **Logs**: System logs for troubleshooting.

Create a volume in your preferred region (e.g., `iad`):

```bash
fly volumes create options_data --region iad --size 1
```

Confirm the volume is created:

```bash
fly volumes list
```

## 4. Set Environment Secrets

Configure your sensitive environment variables using Fly's secrets management:

```bash
fly secrets set \
    TDA_API_KEY=your_api_key_here \
    DATABASE_URL="sqlite:////data/trades.db"
```

## 5. Deploy

Deploy the application:

```bash
fly deploy
```

Wait for the deployment to complete.

## 6. Upload Token (CRITICAL)

The TDA API requires a valid token file to refresh sessions. Since this file is not checked into version control, you **MUST** upload your local `token.json` to the persistent volume on the running machine.

1.  Open an SFTP shell to the running VM:
    ```bash
    fly sftp shell
    ```

2.  Upload the token file:
    ```bash
    put config/token.json /data/token.json
    ```

3.  Exit the shell (`exit`).

Once uploaded, the app will automatically pick up the token from `/data/token.json` (configured via `fly.toml` environment variables).

## 7. Configuration Details (`fly.toml`)

Ensure your `fly.toml` is configured correctly:

```toml
[env]
  TDA_TOKEN_PATH = "/data/token.json"
  LOG_PATH = "/data/logs"
  OUTPUT_DIR = "/data/outputs"

[mounts]
  source = "options_data"
  destination = "/data"
```

This maps the persistent volume to `/data` inside the container and points the application to use paths within that volume.

## 8. Accessing the Dashboard

Once deployed, your application will be available at:

```
https://your-app-name.fly.dev
```

The Streamlit dashboard runs on port 8080.

## Troubleshooting

-   **Logs**: Check application logs using `fly logs`.
-   **Status**: Check machine status with `fly status`.
-   **Restart**: If the token expires or issues occur, restart the app with `fly apps restart options-day-trading-assistant`.

## Updates

To deploy code changes:

```bash
fly deploy
```
