# Reddit Video Maker

This project is focused on automating the creations of Reddit storytime videos for platforms such as Youtube and TikTok. 

Example video:

[![Watch the video](https://img.youtube.com/vi/wsF16p9QL4Y/hqdefault.jpg)](https://youtube.com/shorts/wsF16p9QL4Y)

## Setup
- To Create your own branch run.
```bash
git clone https://github.com/kshinde6804/RedditToTiktokPublic.git
cd RedditToTiktokPublic

```
- Setup Virtual Environment
```bash
python3 -m venv env
```
#On Windows
```bash
.\env\Scripts\activate
```
#On macOS/Linux
```bash
source env/bin/activate
```

#You will need to run the activation command each time you start a new terminal session
```bash
.\env\Scripts\activate 
```

- Install packages
```bash
pip install -r requirements.txt
```

Change line 37 of env > Lib > moviepy > fx > resize.py to 
```bash
resized_pil = pilim.resize(newsize[::-1], Image.LANCZOS)
```

- Run the script:
```bash
python videomaker.py
```

- Use tags for customization:
```bash
python videomaker.py --videos 1 --num_comments 1 --subreddit AskReddit --text comment --voice_type standard
```
--videos: Number of videos to make. (default=1)
--num_comments: Number of comments to use (default=1).
--subreddit: Subreddit to get videos from. (default=AskReddit)
--text: Type of content, either "comment" or "body". (default=comment)
--voice_type: Type of voice to use, either "standard" or "neural". (default=standard)
#Note- neural has better quality, but less characters allowed per month so use sparingly

## Setup for Youtube Uploader:

- Install packages
```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client oauth2client httplib2
```

- Run script
```bash
python upload_video.py --file="C:\Users\kshin\OneDrive\Documents\GitHub\RedditScraper\final_video_1.mp4" --title="Best of AskReddit pt1" --description="Funny and entertaining AskReddit posts!" --keywords="Reddit,interesting,AskReddit" --category="22" --privacyStatus="public"
```
Change --file input to match the desired video file path, and update other parameters accordingly


<!-- NEED TO ADD OTHER USERS TO GOOGLE CLOUD > APIs & SERVICES > OAUTH CONSENT SCREEN > TEST USERS -->
