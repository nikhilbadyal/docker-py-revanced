# Docker-Py-ReVanced

A little python script that will help you in building Revanced and Revanced-Extended [apps](#note)

Note - I prefer [Revanced Extended](https://github.com/inotia00/revanced-patches/tree/revanced-extended) more
(for YouTube & YouTube Music) hence the YouTube and YouTube Music builds in this repo are from
Revanced Extended.

## Pre-Built APKs
You can get pre-built apks [here](https://t.me/revanced_apkss)

## Build Yourself

You can use any of the following methods to build.

- 🚀In GitHub (**_`Recommended`_**)
   1. Fork the project.
   ![fork]
   2. Add `ENVS` (**optional**) secret to the repo. Required only if you want to cook specific apps/versions.
       <details>
         <summary>🚶Detailed step by step guide</summary>

         - Go to the repo settings and then to actions->secret
           ![step_1]
         - Add Repository secret
           ![step_2]

      </details>

   3. Go to actions tab. Select `Build & Release`.Click on `Run Workflow`.

       <details>
         <summary>🚶Detailed step by step guide</summary>

         - Go to actions tab
           ![action_0]
         - Check the status of build, It should look green.
           ![build_wait]

       </details>

   4. If the building process is successful, you’ll get your APKs in the ![apks]


<details>
<summary>🐳With Docker Compose</summary>

1. Install Docker(Skip if already installed)
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   ```
2. Grant Permissions with(Skip if already there)
   ```bash
    sudo usermod -a -G docker ec2-user
    sudo usermod -a -G docker $USER
    sudo chmod 777 /var/run/docker.sock
    ````
3. Install Docker compose(Skip if already installed or using **_`Docker Desktop`_**)
    ```bash
    curl -L "https://github.com/docker/compose/releases/download/v2.10.2/docker-compose-$(uname -s)-$(uname -m)" \
    -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    ```
4. Clone the repo
   ```bash
   git clone https://github.com/nikhilbadyal/docker-py-revanced
   ```
5. cd to the cloned repo
   ```bash
   cd docker-py-revanced
   ```
6. Run script with
    ```shell
    docker-compose up
    ```

</details>

<details>
<summary>🐳With Docker</summary>

1. Install Docker(Skip if already installed)
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sh get-docker.sh
   ```
2.  Run script with
    ```shell
    docker run -v "$(pwd)"/apks:/app/apks/  nikhilbadyal/docker-py-revanced
    ```
    You can pass below envs with `-e` flag.

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
(Pay attention to 3,4)<br>
By default, script build the version as recommended by Revanced team.

1. Supported values for **_<REVANCED_APPS_NAME>_** are :
   1. youtube
   2. youtube_music
   3. twitter
   4. reddit
   5. tiktok
   6. warnwetter
   7. spotify

2. Remember to download the **_Microg_**. Otherwise, you will not be able to open YouTube.
3. By default, it will build [all](#note) build app supported by Revanced team. If you
   don't
   want to waste time and build only few apps. Add the apps you want to build in `.env` file or in `ENVS` in
   `GitHub secrets` in the format
   ```ini
   PATCH_APPS=<REVANCED_APPS_NAME>
   ```
   Example:
   ```ini
   PATCH_APPS=youtube,twitter,reddit
   ```
4. If you want to exclude any patch. Set comma separated patch in `.env` file or in `ENVS` in `GitHub secrets`
   (Recommended) in
   the format
   ```ini
   EXCLUDE_PATCH_<REVANCED_APPS_NAME>=<PATCH_TO_EXCLUDE-1,PATCH_TO_EXCLUDE-2>
   ```
   Example:
   ```dotenv
    EXCLUDE_PATCH_YOUTUBE=custom-branding,hide-get-premium
    EXCLUDE_PATCH_YOUTUBE_MUSIC=yt-music-is-shit
   ```
   If you are using `Revanced Extended.` Add `_EXTENDED` in exclude options.
   Example:
   ```dotenv
    EXCLUDE_PATCH_YOUTUBE_EXTENDED=custom-branding-red,custom-branding-blue,materialyou
    EXCLUDE_PATCH_YOUTUBE_MUSIC_EXTENDED=custom-branding-music
   ```
5. If you want to build a specific version . Add `version` in `.env` file or in `ENVS` in `GitHub secrets` (Recommended)
   in the format
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
   SPOTIFY_VERSION=X.X.X
   ```
6. If you want to build `latest` version, whatever latest is available(including
   beta) .
   Add `latest` in `.env` file or in `ENVS` in `GitHub secrets` (Recommended) in the format
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
   SPOTIFY_VERSION=latest
   ```

7. If you don't want to use default keystore. You can provide your own by placing it
   inside `apks` folder. And adding the name of `keystore-file` in `.env` file or in `ENVS` in `GitHub secrets`
   (Recommended) in the format
   ```dotenv
    KEYSTORE_FILE_NAME=revanced.keystore
   ```
8. If you want to use Revanced-Extended for YouTube and YouTube Music. Add the following adding
   in `.env` file or in `ENVS` in `GitHub secrets` (Recommended) in the format
   ```dotenv
    BUILD_EXTENDED=True
   ```
   or disable it with (default)
   ```dotenv
    BUILD_EXTENDED=False
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
10. Configuration defined in `ENVS` in `GitHub secrets` will override the configuration in `.env` file. You can use this
    fact to define your normal configurations in `.env` file and sometimes if you want to build something different just
    once. Add it in `GitHub secrets` or you can ignore `.env` file and always use `GitHub secrets` because to modify
    `.env` you need to modify the repo. Edit it and make a commit.
11. If you want to build YouTube with `original icon` and `custom branding icon` both. Add `BUILD_OG_BRANDING_YOUTUBE`
    in `.env` file or in `ENVS` in `GitHub secrets` (Recommended) in the format
    ```dotenv
     BUILD_OG_BRANDING_YOUTUBE=True
    ```

    You can also specify the branding patch to use for custom icon build. This can be done with by adding
    `BRANDING_PATCH` in `ENVS` in `GitHub secrets` (Recommended) in the format
    ```dotenv
     BRANDING_PATCH=custom-branding-icon-blue
    ```
12. You can build only for a particular arch in order to get smaller apk files.This can be done with by adding comma
    separated `ARCHS_TO_BUILD` in `ENVS` in `GitHub secrets` (Recommended) in the format.
    ```dotenv
     ARCHS_TO_BUILD=arm64-v8a,armeabi-v7a
    ```
    Possible values for `ARCHS_TO_BUILD` are: `armeabi-v7a`,`x86`,`x86_64`,`arm64-v8a`
    Make sure you are using `revanced-extended` as `revanced` doesn't support this.
13. You can scan your build apks files with VirusTotal. For that, Add `VT_API_KEY` in `GitHub secrets`.
14. Sample Envs ![envs]

[fork]: https://i.imgur.com/R5HdByI.png
[secrets]: https://i.imgur.com/083Bjpg.png
[step_1]: https://i.imgur.com/Inj82KK.png
[step_2]: https://i.imgur.com/V2Wfx3J.png
[action_0]: https://i.imgur.com/XSCvzav.png
[build_wait]: https://i.imgur.com/CsJt9W1.png
[apks]: https://i.imgur.com/S5d7qAO.png
[chat id]: https://i.imgur.com/22UiaWs.png
[bot api]: https://i.imgur.com/A6JCyK2.png
[tg api]: https://i.imgur.com/eha3nnb.png
[tg api hash]: https://i.imgur.com/7n5k1mp.png
[envs]: https://i.imgur.com/ajSE5nA.png

Thanks to [@aliharslan0](https://github.com/aliharslan0/pyrevanced) for his work.
