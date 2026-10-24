#!/bin/bash
# CHIH MING 網站行業新聞自動更新：抓新聞 → 產生 news.json → commit/push → 同步桌面
cd /home/mrnie/chihming-website || exit 1
"/home/mrnie/.hermes/tools/python-3.14.7+20260901-linux-x64/bin/python3" .github/fetch_news.py || exit 1
git add news.json
if ! git diff --cached --quiet; then
  git -c user.name="CHIH MING" -c user.email="admin@chihming.com" commit -q -m "Auto-update industry news $(date -u +%F)"
  git push -q origin main
fi
cp news.json "/mnt/c/Users/mrnir/Desktop/news.json" 2>/dev/null
echo "$(date -u +%F_%T) news updated OK" >> /home/mrnie/chihming-website/.news_cron.log
