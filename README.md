# Docker-Py-ReVanced

A little python script that will help you in building Revanced and Revanced-Extended [apps](#note)

Note - I prefer [Revanced Extended](https://github.com/inotia00/revanced-patches/tree/revanced-extended) more
(for YouTube & YouTube Music) hence the YouTube and YouTube Music builds in this repo are from
Revanced Extended.

## Pre-Build APKs
You can get pre-build apks [here](https://t.me/revanced_apkss)

## Build Yourself

You can use any of the following methods to build.

<details>
<summary>🚀In GitHub(Recommended)</summary>

1. Fork the project.
![image](https://user-images.githubusercontent.com/22337329/186554644-7d4c2172-c0dd-4ea6-9ec1-08e9b567a5e3.png)
2. Add following secrets to the repo.
    1. _GH_TOKEN_ (**required**) - GitHub token so that it can upload to GitHub
       after building. Click [here](#generate-token) to learn how to get that.
    2. _VT_API_KEY_ (optional) - required only if you want Virus total scan.
    3. _ENVS_ (optional) - required only if you want to cook specific apps/versions.
    <details>
      <summary>🚶Detailed step by step guide</summary>

      - Go to the repo settings and then to actions->secret
        ![step_1]
      - Add Repository secret
        ![step_2]
      - **`GitHub Secrets`** might look like this(With VT_SCAN)
       ![secrets]

      - After adding secrets, **`ENVS`** secret might look like this
        ```ini
        PATCH_APPS=youtube_music,twitter
        EXCLUDE_PATCH_YOUTUBE=custom-branding
        EXCLUDE_PATCH_YOUTUBE_MUSIC=yt-music-is-shit
        YOUTUBE_VERSION=67.68.69
        YOUTUBE_MUSIC_VERSION=latest
        TWITTER_VERSION=0.2.2
        REDDIT_VERSION=latest
        TIKTOK_VERSION=latest
        WARNWETTER_VERSION=latest
        ```

   </details>

3. Go to actions tab. Select `Build Revanced APK`.Click on `Run Workflow`.
   1. It can take a few minute to start. Just be patient.

    <details>
      <summary>🚶Detailed step by step guide</summary>

      - Go to actions tab
        ![action_0]
      - Check the status of build, It should look green.
        ![action_1]
      - Check logs if something fails.
        ![action_2]
        ![action_3]

    </details>

4. If the building process is successful, you’ll get your APKs in the releases
    - ![apks]
5. Click on **`Build-<SomeRandomDate>`** and download the apk file.
</details>

<details>
<summary>🐳With Docker</summary>

1.  Install Docker
2.  Run script with
    ```shell
    docker-compose up
    ```

</details>

<details>
<summary>🫠Without Docker</summary>

1.  Install Java17 (zulu preferred)
2.  Install Python
3.  Create virtual environment
    ```
    python3 -m venv venv
    ```
4.  Activate virtual environment
    ```
    source venv/bin/activate
    ```
5.  Install Dependencies with
    ```
    pip install -r requirements.txt
    ```
6.  Run the script with
    ```
    python python main.py
    ```
</details>


### Note

By default, script build the version as recommended by Revanced team.

1. Supported values for **_<REVANCED_APPS_NAME>_** are :
   1. youtube
   2. youtube_music
   3. twitter
   4. reddit
   5. tiktok
   6. warnwetter
   7. Spotify
2. If you want to build a specific version . Add `version` in `environment` in the
   format
   ```ini
   <APPNAME>_VERSION=<VERSION>
   ```
   Example:
   ```ini
   YOUTUBE_VERSION=17.31.36
   YOUTUBE_MUSIC_VERSION=X.X.X
   TWITTER_VERSION=X.X.X
   REDDIT_VERSION=X.X.X
   TIKTOK_VERSION=X.X.X
   WARNWETTER_VERSION=X.X.X
   ```
3. If you want to build `latest` version, whatever latest is available(including
   beta) .
   Add `latest` in `environment` in the format
   ```ini
   <APPNAME>_VERSION=latest
   ```
   Example:
   ```ini
   YOUTUBE_VERSION=latest
   YOUTUBE_MUSIC_VERSION=latest
   TWITTER_VERSION=latest
   REDDIT_VERSION=latest
   TIKTOK_VERSION=latest
   WARNWETTER_VERSION=latest
   ```
4. By default, it will build [all](#note) build app supported by Revanced team. If you
   don't
   want to waste time and build only few apps. Add the apps you want to build in
   `environment` in the format
   ```ini
   PATCH_APPS=<REVANCED_APPS_NAME>
   ```
   Example:
   ```ini
   PATCH_APPS=youtube,twitter,reddit
   ```
5. If you don't want to use default keystore. You can provide your own by placing it
   inside `apks` folder. And adding the name of `keystore-file` in `environment` like
   ```dotenv
    KEYSTORE_FILE_NAME=revanced.keystore
   ```
6. If you want to exclude any patch. Set comma separated patch in `environment` in
   the format
   ```ini
   EXCLUDE_PATCH_<REVANCED_APPS_NAME>=<PATCH_TO_EXCLUDE-1,PATCH_TO_EXCLUDE-2>
   ```
   Example:
   ```dotenv
    EXCLUDE_PATCH_YOUTUBE=custom-branding,hide-get-premium
    EXCLUDE_PATCH_YOUTUBE_MUSIC=yt-music-is-shit
   ```
7. Remember to download the **_Microg_**. Otherwise, you will not be able to open YouTube.
8. If you want to disable use Revanced-Extended for YouTube and YouTube Music. Add the following adding
   in `environment` like
   ```dotenv
    BUILD_EXTENDED=False
   ```
   or enable it with
   ```dotenv
    BUILD_EXTENDED=True
   ```
9. For Telegram Upload.
   1. Set up a telegram channel, send a message to it and forward the message to
      this telegram [bot](https://t.me/username_to_id_bot)
   2. Copy `id` and save it to `TELEGRAM_CHAT_ID`<br>
      ![chat id]
   3. `TELEGRAM_BOT_TOKEN` - Telegram provides BOT_TOKEN. It works as sender. Open [bot](https://t.me/BotFather) and
       create one copy api key<br>
      ![bot api]
   4. `TELEGRAM_API_ID`  - Telegram API_ID is provided by telegram [here](https://my.telegram.org/apps)<br>
     ![tg api]
   5. `TELEGRAM_API_HASH` - Telegram API_HASH is provided by telegram [here](https://my.telegram.org/apps)<br>
     ![tg api hash]
   6. After Everything done successfully the actions secrets of the repository will look something like<br>
      <img src="https://i.imgur.com/dzC1KFa.png" width="400">

### Generate Token
1. Go to your account developer [settings](https://github.com/settings/tokens). Click on generate new token.<br>
   <img src="https://i.imgur.com/grofl9E.png" height="150">
2. Give a nice name. and grant following permissions<br>
   <img src="https://user-images.githubusercontent.com/22337329/186550702-69c5fb77-32c3-4689-bb5c-3a213daa5e19.png" width="400" height="450">

[secrets]: https://i.imgur.com/083Bjpg.png
[step_1]: https://i.imgur.com/Inj82KK.png
[step_2]: https://user-images.githubusercontent.com/22337329/186521861-42786e8d-5db4-43ef-9676-2f7e7c0eddc4.png
[action_0]: https://i.imgur.com/M1XdjZC.png
[action_1]: https://user-images.githubusercontent.com/22337329/186533319-0aebf294-9bac-4859-b4e1-1b4c87d39f48.png
[action_2]: https://user-images.githubusercontent.com/22337329/186533358-e27e30bc-0d16-4f56-a335-0387c481dbf8.png
[action_3]: https://user-images.githubusercontent.com/22337329/186533417-15477a2c-28c3-4e39-9f3d-c4e18202d000.png
[apks]: https://i.imgur.com/S5d7qAO.png
[chat id]: https://i.imgur.com/22UiaWs.png
[bot api]: https://i.imgur.com/A6JCyK2.png
[tg api]: https://i.imgur.com/eha3nnb.png
[tg api hash]: https://i.imgur.com/7n5k1mp.png

Thanks to [@aliharslan0](https://github.com/aliharslan0/pyrevanced) for his work.
