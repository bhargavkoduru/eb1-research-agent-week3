# Deploy the Week 3 app

This is a standalone public app. No examiner password or API key is required. Its hosted URL is not created yet.

1. Sign in as the owner to [Streamlit Community Cloud](https://share.streamlit.io/).
2. Choose **Create app**: repository `bhargavkoduru/eb1-research-agent-week3`, branch `main`, entrypoint `app.py`, Python **3.12** in Advanced settings.
3. Configure the owner's Nebius key. With a local `.env` set up, run `python -m scripts.prepare_cloud_secrets` and paste the resulting `runtime/deployment/streamlit.secrets.toml` into Advanced settings > Secrets. This private file must never go into GitHub or the Google Doc.
4. Click **Deploy** and make the app **public** in Sharing settings.
5. Open the assigned URL in a private/incognito window. Enter a research goal, inspect the source evidence, edit or cancel if needed, then approve and download the checklist. No login screen should appear.
6. Add this URL to the README and Week 3 Google Doc. Use the separate repository's deployment for the other week if two hosted links are wanted. The local `127.0.0.1` URL is not accessible to an examiner on another computer.

The owner must finish the Streamlit browser sign-in. GitHub publication alone does not deploy the app.

## Limits and state

The public corpus and checked index are bundled; startup makes no parsing or embedding calls. Questions and retrieved excerpts go to Nebius. Hosted browser sessions get separate random identities; a URL parameter cannot select another visitor's workspace.

Default UTC-day allowances per deployment: 30 actions/120 reserved provider attempts per browser session, 100 actions/400 attempts globally. A new browser session does not reset the global counter. Each deployment has its own counter, so these limits are not shared between the two apps. They are request limits, not a guaranteed monetary cap; server storage resets can clear them. Set `EB1_ENABLE_LIVE_CALLS = false` in server secrets to pause calls.

Hosted visitors can resume research during their current browser session. Refreshing or closing the page loses the anonymous workspace identity; download approved checklists first. Server files are not immediately deleted, but may be lost on platform rebuild. The owner can access them. Local mode retains SQLite state across restarts and supports the checkpoint demonstration.

Sources: [deployment](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy), [sharing](https://docs.streamlit.io/deploy/streamlit-community-cloud/share-your-app), [secrets](https://docs.streamlit.io/deploy/concepts/secrets), [session lifetime](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state).
