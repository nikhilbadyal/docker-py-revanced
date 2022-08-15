# Docker Py ReVanced
This little utility will help you in building all revanced apps.

## Build
You can use any of the following methods to build
- With Docker
   1. Install Docker
   2. Run script with
   ```shell
   docker-compose up
  ```
- Without Docker
   1. Install Java17 (zulu preferred)
   2. Install Python
   3. Install Dependencies with
   ```python
   pip install -r requirements.txt
  ```
   4. Run the script with
   ```python
   python main.py
  ```
## Note
By default script build the version as recommended by revanced team. If you want to
build and unsupported version and do experiments. Add the version in .env file like
```dotenv
YOUTUBE_VERSION=17.31.36
YOUTUBE-MUSIC_VERSION=X.X.X
TWITTER_VERSION==X.X.X
REDDIT_VERSION==X.X.X
```
### Note
Thanks to [@aliharslan0](https://github.com/aliharslan0/pyrevanced) for his work.
