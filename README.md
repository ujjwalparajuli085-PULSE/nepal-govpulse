# Nepal GovPulse — Automated Publishing Setup

This package runs **Nepal GovPulse** as a self-updating website on **GitHub Pages** with **GitHub Actions** refreshing `data.json` every hour—no manual copy-pasting needed.

## 1. Upload to GitHub
1. Create a new public repository on [GitHub](https://github.com/new) (for example, `nepal-govpulse`).
2. Upload all files from this folder (`index.html`, `data.json`, `scripts/update_feed.py`, `.github/workflows/update.yml`, and `README.md`) to the root of the `main` branch.

## 2. Enable GitHub Pages
1. Open **Settings → Pages** in your repository.
2. Under **Build and deployment**, set **Source** to **Deploy from a branch**.
3. Select branch **`main`** and folder **`/ (root)`**, then click **Save**.
4. Within a minute, your live public URL will appear (e.g., `https://<your-username>.github.io/nepal-govpulse/`).

## 3. Enable Hourly Automated Updates
1. Open **Settings → Actions → General**.
2. Scroll to **Workflow permissions**, select **Read and write permissions**, and click **Save**.
3. Go to the **Actions** tab, select **Hourly Nepal GovPulse Update**, and click **Run workflow** to test immediately. From then on, it runs automatically at the top of every 15 minutes (`*/15 * * * *`).

## 4. Optional: Connect to Google Sites Once
1. Open your site in [Google Sites](https://sites.google.com/).
2. Click **Insert → Embed → By URL** and paste your GitHub Pages URL.
3. Expand the embed frame to fill the page and click **Publish**. Every hourly GitHub Pages update will now appear on your Google Site automatically.
