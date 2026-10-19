# TheMaineSpark Trend Engine — Nigeria-first MVP (v1.1)

A **free, static GitHub Pages dashboard** with Nigeria-prioritised news RSS, curated video search links, an evidence-first numerical comparison lab, editable social captions, local saved drafts, and manual publishing shortcuts for existing personal Facebook, Instagram and X accounts. No platform logins or paid APIs.

## Deploy

1. Create a **public** GitHub repository named `themainespark-trend-engine`.
2. Upload the **contents** of the extracted ZIP into the repository root, including `.github/workflows/trends.yml` (show hidden files when uploading).
3. Go to **Settings → Actions → General → Workflow permissions**: enable **Read and write permissions** so the workflow can commit updated headlines.
4. Go to **Settings → Pages → Build and deployment → Source** and choose **GitHub Actions** (not Deploy from a branch).
5. Go to **Actions → Refresh trends and publish website → Run workflow** to retrieve current headlines and deploy the dashboard.
6. Open `https://YOUR_GITHUB_USERNAME.github.io/themainespark-trend-engine/`.

## Local preview

```bash
python scripts/fetch_trends.py
python -m http.server 8000 --directory docs
```
Visit http://localhost:8000. RSS requires an internet connection; if sources fail the script preserves existing category data when available.

## How it works

- **Headlines:** Google News RSS search with Nigeria region and categories Economy, Politics, Public Services, Diaspora, Entertainment, International. Headlines are *candidates*, not verified trending rankings. Automatic collection scheduled around 08:17, 13:17 and 19:17 **Europe/London**; actual workflow runs can be delayed.
- **Videos:** human-facing searches of YouTube, TikTok, Instagram plus a video-link field. The app does **not** claim these are measured viral videos. Paste links and prepare original commentary outlines; it does **not** download or repost other creators' clips.
- **Data lab:** enter independently verified comparable figures, periods and an evidence URL; calculate absolute and relative changes. Note that percentage-point differences (for percentages) are not the same as percentage relative change. Figures are not fetched or validated automatically.
- **Composer:** rule-based draft templates, not generative AI. Automatically generated text is based on the headline only, **not full articles**. Always read sources and check claims.
- **Publishing:** copy text and use official Facebook, Instagram and X sites. No app social login, OAuth, API integration or automated posting. Reels/images must be uploaded on the destination platform.

## Privacy and limitations

This is a **public GitHub Pages website**. Never put passwords, tokens, private datasets or account credentials in your repository or `docs/`. Drafts and video notes are processed in the browser; saved drafts use localStorage, so they are private to that browser profile, not synced or secured like a private cloud database. Sources can go offline, and GitHub scheduled Actions may be delayed. Content and publication remain under your review. Only reuse video materials you have rights to use, or a valid legal basis for use.

## Later improvements

A real scored video-trend feed (where permitted), local data CSV import and chart visuals, verified automated dataset refreshes, AI-assisted drafting with explicit costs, and optional private server for account sync.
