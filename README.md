# 🤓Docker-Py-ReVanced

A little python script that will help you in building Revanced and Revanced-Extended [apps](#note).

**`Note`** - If you are a root user and want magisk module (Extended). Get them [here](https://github.com/nikhilbadyal/revanced-magisk-module)

This is just a builder for revanced and not a revanced support. Please be understanding and refraining from asking
about revanced features/bugs. Discuss those on proper relevant forums(on Revanced GitHub , Discord)

**`Note`** - I prefer [Revanced Extended](https://github.com/inotia00/revanced-patches/tree/revanced-extended) more
(for YouTube & YouTube Music) hence the YouTube and YouTube Music builds in this repo are from
Revanced Extended.

## Pre-Built APKs

You can get pre-built apks [here](https://revanced_apkss.t.me/)

## Build Yourself

You can use any of the following methods to build.

- 🚀In GitHub (**_`Recommended`_**)

     1. Clik Star to support the project.<br>
       <img src="https://i.imgur.com/FFyXaWY.png" width="400" style="left"><br>
     2. Fork the project.<br>
     <img src="https://i.imgur.com/R5HdByI.png" width="400" style="left"><br>
     3. Add `ENVS` (**optional**) secret to the repo. Required only if you want to cook specific apps/versions.
         <details>
           <summary>🚶Detailed step by step guide</summary>

         - Go to the repo settings and then to actions->secret<br>
           <img src="https://i.imgur.com/Inj82KK.png" width="600" style="left"><br>
         - Add Repository secret<br>
           <img src="https://i.imgur.com/V2Wfx3J.png" width="600" style="left">

        </details>

     4. Go to actions tab. Select `Build & Release`.Click on `Run Workflow`.

        <details>
          <summary>🚶Detailed step by step guide</summary>

         - Go to actions tab<br>
           <img src="https://i.imgur.com/XSCvzav.png" width="600" style="left"><br>
         - Check the status of build, It should look green.<br>
           <img src="https://i.imgur.com/CsJt9W1.png" width="600" style="left">

        </details>

     5. If the building process is successful, you’ll get your APKs in the <br>
        <img src="https://i.imgur.com/S5d7qAO.png" width="700" style="left">

- 🐳With Docker Compose
  Windows/Mac users simply install Docker Desktop. If using Linux see below

    1. Install Docker(Skip if already installed)
       ```bash
       curl -fsSL https://get.docker.com -o get-docker.sh
       sh get-docker.sh
       ```
    2. Grant Permissions with(Skip if already there)
       ```bash
        sudo chmod 777 /var/run/docker.sock
       ```
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
    6. Update `.env` file if you want some customization(See notes)
    7. Run script with
       ```shell
       docker-compose up
       ```

- 🐳With Docker

    1. Install Docker(Skip if already installed)
       ```bash
       curl -fsSL https://get.docker.com -o get-docker.sh
       sh get-docker.sh
       ```
    2. Run script with
       ```shell
       docker run -v "$(pwd)"/apks:/app/apks/  nikhilbadyal/docker-py-revanced
       ```
       You can pass below envs(See notes) with `-e` flag or use `--env-file`
       [flag](https://docs.docker.com/engine/reference/commandline/run/#options).

- 🫠Without Docker

    1. Install Java17 (zulu preferred)
    2. Install Python
    3. Create virtual environment
       ```
       python3 -m venv venv
       ```
    4. Activate virtual environment
       ```
       source venv/bin/activate
       ```
    5. Install Dependencies with
       ```
       pip install -r requirements.txt
       ```
    6. Run the script with
       ```
       python python main.py
       ```

## Note

(Pay attention to 3,4)<br>
By default, script build the version as recommended by Revanced team.

1. Supported values for **REVANCED_APPS_NAME** are :

    1. [youtube](https://www.apkmirror.com/apk/google-inc/youtube/)
    2. [youtube_music](https://www.apkmirror.com/apk/google-inc/youtube-music/)
    3. [twitter](https://www.apkmirror.com/apk/twitter-inc/twitter/)
    4. [reddit](https://www.apkmirror.com/apk/redditinc/reddit/)
    5. [tiktok](https://www.apkmirror.com/apk/tiktok-pte-ltd/tik-tok-including-musical-ly/)
    6. [warnwetter](https://www.apkmirror.com/apk/deutscher-wetterdienst/warnwetter/)
    7. [spotify](https://spotify.en.uptodown.com/android)
    8. [nyx-music-player](https://nyx-music-player.en.uptodown.com/android)
    9. [icon_pack_studio](https://www.apkmirror.com/apk/smart-launcher-team/icon-pack-studio/)
    10. [ticktick](https://www.apkmirror.com/apk/appest-inc/ticktick-to-do-list-with-reminder-day-planner/)
    11. [twitch](https://www.apkmirror.com/apk/twitch-interactive-inc/twitch/)
    12. [hex-editor](https://m.apkpure.com/hex-editor/com.myprog.hexedit)
    13. [citra](https://www.apkmirror.com/apk/citra-emulator/citra-emulator/)
    14. [windy](https://www.apkmirror.com/apk/windy-weather-world-inc/windy-wind-weather-forecast/)
    15. [my-expenses](https://my-expenses.en.uptodown.com/android)
    16. [backdrops](https://backdrops.en.uptodown.com/android)
    17. [expensemanager](https://apksos.com/app/com.ithebk.expensemanager)
    18. [tasker](https://www.apkmirror.com/apk/joaomgcd/tasker-crafty-apps-eu/)

    <br>Please verify the source of original APKs yourself with links provided. I'm not responsible for any damaged caused.
    If you know any better/safe source to download clean. Please raise a PR.

2. Remember to download the **_Microg_**. Otherwise, you will not be able to open YouTube.
3. By default, it will build only `youtube`. To build other apps supported by revanced team.
   Add the apps you want to build in `.env` file or in `ENVS` in
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
       <img src="https://i.imgur.com/22UiaWs.png" width="300" style="left"><br>
    3. `TELEGRAM_BOT_TOKEN` - Telegram provides BOT_TOKEN. It works as sender. Open [bot](https://t.me/BotFather) and
       create one copy api key<br>
       <img src="https://i.imgur.com/A6JCyK2.png" width="300" style="left"><br>
    4. `TELEGRAM_API_ID` - Telegram API_ID is provided by telegram [here](https://my.telegram.org/apps)<br>
       <img src="https://i.imgur.com/eha3nnb.png" width="300" style="left"><br>
    5. `TELEGRAM_API_HASH` - Telegram API_HASH is provided by telegram [here](https://my.telegram.org/apps)<br>
       <img src="https://i.imgur.com/7n5k1mp.png" width="300" style="left"><br>
    6. After Everything done successfully the actions secrets of the repository will look something like<br>
       <img src="https://i.imgur.com/dzC1KFa.png" width="400">
10. You can build only for a particular arch in order to get smaller apk files.This can be done with by adding comma
    separated `ARCHS_TO_BUILD` in `ENVS` in `GitHub secrets` (Recommended) in the format.
    ```dotenv
     ARCHS_TO_BUILD=arm64-v8a,armeabi-v7a
    ```
    Possible values for `ARCHS_TO_BUILD` are: `armeabi-v7a`,`x86`,`x86_64`,`arm64-v8a`
    Make sure you are using `revanced-extended` as `revanced` doesn't support this.
11. You can scan your build apks files with VirusTotal. For that, Add `VT_API_KEY` in `GitHub secrets`.
12. Configuration defined in `ENVS` in `GitHub secrets` will override the configuration in `.env` file. You can use this
    fact to define your normal configurations in `.env` file and sometimes if you want to build something different just
    once. Add it in `GitHub secrets`.<br>
    Or you can ignore what I said above and always use `GitHub secrets`.
13. If APKMirror or other apk source is blocked in your region or script somehow is unable to download from apkmirror.
    You can download apk manually from any source. Place them in `/apks` directory and provide environment variable
    in `.env` file or in `ENVS` in `GitHub secrets`(Recommended) in the format.
    ```dotenv
     EXISTING_DOWNLOADED_APKS=<Comma,Seperate,App,Name>
    ```
    Example:
    ```dotenv
     EXISTING_DOWNLOADED_APKS=youtube,youtube_music
    ```
    If you add above. Script will not download the `Youtube` & `youtube music`apk from internet and expects an apk in
    `/apks` folder.

    Name of the downloaded apk must match with the available app choices found [here.](#note)
14. If you run script again & again. You might hit GitHub API limit. In that case you can provide your Personal
    GitHub Access Token in `.env` file or in `ENVS` in `GitHub secrets` (Recommended) in the format -
    ```dotenv
     PERSONAL_ACCESS_TOKEN=<PAT>
    ```
15. Sample Envs<br>
    <img src="https://i.imgur.com/ajSE5nA.png" width="600" style="left">
16. Make your Action has write access. If not click [here](https://github.
    com/nikhilbadyal/docker-py-revanced/settings/actions). In the bottom give read and write access to Actions.
    <img src="https://i.imgur.com/STSv2D3.png" width="400">

Thanks to [@aliharslan0](https://github.com/aliharslan0/pyrevanced) for his work.
