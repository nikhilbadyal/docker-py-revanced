# 🤓Docker-Py-ReVanced

A little python script that will help you in building Revanced [apps](#patch-apps).

**`Note`** - If you are a root user and want magisk module (Extended). Get them [here](https://github.com/nikhilbadyal/revanced-magisk-module)

This is just a builder for revanced and not a revanced support. Please be understanding and refrain from asking
about revanced features/bugs. Discuss those on proper relevant forums.

## Pre-Built APKs

You can get pre-built apks [here](https://revanced_apkss.t.me/)

## Build Yourself

You can use any of the following methods to build.

- 🚀 **_GitHub**_ (**_`Recommended`_**)

     1. Click Star to support the project.<br>
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

     5. If the building process is successful, you’ll get your APKs in the<br>
        <img src="https://i.imgur.com/S5d7qAO.png" width="700" style="left">

- 🐳 **_Docker Compose_**<br>
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
       docker-compose up --build
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
       You can pass the below environment variables (See notes) with the `-e` flag or use the `--env-file`
       [flag](https://docs.docker.com/engine/reference/commandline/run/#options).

- 🫠Without Docker

    1. Install Java >= 17
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
       python main.py
       ```

## Configurations

### Global Config

| **Env Name**                                             |                  **Description**                  | **Default**                                                                                              |
|:---------------------------------------------------------|:-------------------------------------------------:|:---------------------------------------------------------------------------------------------------------|
| [PATCH_APPS](#patch-apps)                                |                Apps to patch/build                | youtube                                                                                                  |
| [EXISTING_DOWNLOADED_APKS ](#existing-downloaded-apks)   |           Already downloaded clean apks           | []                                                                                                       |
| [PERSONAL_ACCESS_TOKEN](#personal-access-token)          |              Github Token to be used              | None                                                                                                     |
| DRY_RUN                                                  |                   Do a dry run                    | False                                                                                                    |
| [GLOBAL_CLI_DL*](#global-resources)                      |     DL for CLI to be used for patching apps.      | [Revanced CLI](https://github.com/revanced/revanced-cli)                                                 |
| [GLOBAL_PATCHES_DL*](#global-resources)                  |   DL for Patches to be used for patching apps.    | [Revanced Patches](https://github.com/revanced/revanced-patches)                                         |
| [GLOBAL_PATCHES_JSON_DL*](#global-resources)             | DL for Patches Json to be used for patching apps. | [Revanced Patches](https://github.com/revanced/revanced-patches)                                         |
| [GLOBAL_INTEGRATIONS_DL*](#global-resources)             | DL for Integrations to be used for patching apps. | [Revanced CLI](https://github.com/revanced/revanced-integrations)                                        |
| [GLOBAL_KEYSTORE_FILE_NAME*](#global-keystore-file-name) |       Key file to be used for signing apps        | [Builder's own key](https://github.com/nikhilbadyal/docker-py-revanced/blob/main/apks/revanced.keystore) |
| [GLOBAL_ARCHS_TO_BUILD*](#global-archs-to-build)         |         Arch to keep in the patched apk.          | All                                                                                                      |
| REDDIT_CLIENT_ID                                         |       Reddit Client ID to patch reddit apps       | None                                                                                                     |
| VT_API_KEY                                               |           Virus Total Key to scan APKs            | None                                                                                                     |
| [TELEGRAM_CHAT_ID](#telegram-support)                    |            Receiver in Telegram upload            | None                                                                                                     |
| [TELEGRAM_BOT_TOKEN](#telegram-support)                  |          APKs Sender for Telegram upload          | None                                                                                                     |
| [TELEGRAM_API_ID](#telegram-support)                     |         Used for telegram Authentication          | None                                                                                                     |
| [TELEGRAM_API_HASH](#telegram-support)                   |         Used for telegram Authentication          | None                                                                                                     |

`*` - Can be overridden for individual app.
### App Level Config

| Env Name                                                    |                        Description                        | Default                        |
|:------------------------------------------------------------|:---------------------------------------------------------:|:-------------------------------|
| [*APP_NAME*_CLI_DL](#global-resources)                      |     DL for CLI to be used for patching **APP_NAME**.      | GLOBAL_CLI_DL                  |
| [*APP_NAME*_PATCHES_DL](#global-resources)                  |   DL for Patches to be used for patching **APP_NAME**.    | GLOBAL_PATCHES_DL              |
| [*APP_NAME*_PATCHES_JSON_DL](#global-resources)             | DL for Patches Json to be used for patching **APP_NAME**. | GLOBAL_PATCHES_JSON_DL         |
| [*APP_NAME*_INTEGRATIONS_DL](#global-resources)             | DL for Integrations to be used for patching **APP_NAME**. | GLOBAL_INTEGRATIONS_DL         |
| [*APP_NAME*_KEYSTORE_FILE_NAME](#global-keystore-file-name) |       Key file to be used for signing **APP_NAME**.       | GLOBAL_KEYSTORE_FILE_NAME      |
| [*APP_NAME*_ARCHS_TO_BUILD](#global-archs-to-build)         |         Arch to keep in the patched **APP_NAME**.         | GLOBAL_ARCHS_TO_BUILD          |
| [*APP_NAME*_EXCLUDE_PATCH**](#custom-exclude-patching)      |     Patches to exclude while patching  **APP_NAME**.      | []                             |
| [*APP_NAME*_INCLUDE_PATCH**](#custom-include-patching)      |     Patches to include while patching  **APP_NAME**.      | []                             |
| [*APP_NAME*_VERSION**](#app-version)                        |         Version to use for download for patching.         | Recommended by patch resources |

`**` - By default all patches for a given app are included.<br>
`**` - Can be used to included universal patch.

## Note

1. Supported values for **APP_NAME** are :

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
    13. [windy](https://www.apkmirror.com/apk/windy-weather-world-inc/windy-wind-weather-forecast/)
    14. [my-expenses](https://my-expenses.en.uptodown.com/android)
    15. [backdrops](https://backdrops.en.uptodown.com/android)
    16. [expensemanager](https://apksos.com/app/com.ithebk.expensemanager)
    17. [tasker](https://www.apkmirror.com/apk/joaomgcd/tasker-crafty-apps-eu/)
    18. [irplus](https://irplus.en.uptodown.com/android)
    19. [vsco](https://www.apkmirror.com/apk/vsco/vsco-cam/)
    20. [meme-generator-free](https://meme-generator-free.en.uptodown.com/android)
    21. [nova_launcher](https://www.apkmirror.com/apk/teslacoil-software/nova-launcher/)
    22. [netguard](https://www.apkmirror.com/apk/marcel-bokhorst/netguard-no-root-firewall/)
    23. [instagram](https://www.apkmirror.com/apk/instagram/instagram-instagram/)
    24. [inshorts](https://www.apkmirror.com/apk/inshorts-formerly-news-in-shorts/)
    25. [facebook](https://www.apkmirror.com/apk/facebook-2/facebook/)
    26. [grecorder](https://www.apkmirror.com/apk/google-inc/google-recorder/)
    27. [trakt](https://www.apkmirror.com/apk/trakt/trakt/)
    28. [candyvpn](https://www.apkmirror.com/apk/liondev-io/candylink-vpn/)
    29. [sonyheadphone](https://www.apkmirror.com/apk/sony-corporation/sony-headphones-connect/)
    30. [androidtwelvewidgets](https://m.apkpure.com/android-12-widgets-twelve/com.dci.dev.androidtwelvewidgets)
    31. [yuka](https://yuka.en.uptodown.com/android)
    32. [relay](https://www.apkmirror.com/apk/dbrady/relay-for-reddit-2/)
    33. [boost](https://www.apkmirror.com/apk/ruben-mayayo/boost-for-reddit/)
    34. [rif](https://www.apkmirror.com/apk/talklittle/reddit-is-fun/)
    35. [sync](https://www.apkmirror.com/apk/red-apps-ltd/sync-for-reddit/)
    36. [infinity](https://www.apkmirror.com/apk/red-apps-ltd/sync-for-reddit/)
    37. [slide](https://www.apkmirror.com/apk/haptic-apps/slide-for-reddit/)
    38. [bacon](https://www.apkmirror.com/apk/onelouder-apps/baconreader-for-reddit/)
    39. [microg](https://github.com/inotia00/mMicroG/releases)
    40. [pixiv](https://www.apkmirror.com/apk/pixiv-inc/pixiv/)

    <br>Please verify the source of original APKs yourself with links provided. I'm not responsible for any damage
    caused.If you know any better/safe source to download clean. Open a discussion.
2. By default, script build the latest version as recommended by `patches.json` team.
3. Remember to download the **_Microg_**. Otherwise, you may not be able to open YouTube/YouTube Music.
4. <a id="patch-apps"></a>By default, tool will build only `youtube`. To build other apps supported by patching
   resources.Add the apps you want to build in `.env` file or in `ENVS` in `GitHub secrets` in the format
   ```ini
   PATCH_APPS=<APP_NAME>
   ```
   Example:
   ```ini
   PATCH_APPS=youtube,twitter,reddit
   ```
5. <a id="existing-downloaded-apks"></a>If APKMirror or other apk sources are blocked in your region or script
   somehow is unable to download from apkmirror. You can download apk manually from any source. Place them in
   `/apks` directory and provide environment variable in `.env` file or in `ENVS` in `GitHub secrets`(Recommended)
   in the format.
   ```dotenv
    EXISTING_DOWNLOADED_APKS=<Comma,Seperate,App,Name>
   ```
   Example:
   ```dotenv
    EXISTING_DOWNLOADED_APKS=youtube,youtube_music
   ```
   If you add above. Script will not download the `youtube` & `youtube_music`apk from internet and expects an apk in
   `/apks` folder with **same** name.
6. <a id="personal-access-token"></a>If you run script again & again. You might hit GitHub API limit. In that case
   you can provide your Personal GitHub Access Token in `.env` file or in `ENVS` in `GitHub secrets` (Recommended)
   in the format -
   ```dotenv
    PERSONAL_ACCESS_TOKEN=<PAT>
   ```
7. <a id="global-resources"></a>You can provide Direct download to the resource to used for patching apps `.env` file
   or in `ENVS` in `GitHub secrets` (Recommended) in the format -
   ```dotenv
    GLOBAL_CLI_DL=https://github.com/revanced/revanced-cli
    GLOBAL_PATCHES_DL=https://github.com/revanced/revanced-patches
    GLOBAL_PATCHES_JSON_DL=https://github.com/revanced/revanced-patches
    GLOBAL_INTEGRATIONS_DL=https://github.com/revanced/revanced-integrations
   ```
   Resources downloaded from envs and will be used for patching for any **APP_NAME**.
   Unless provided different resource for the individual app.<br><br>
   Tool also support resource config at app level. You can patch A app with X resources while patching B with Y
   resources.
   This can be done by providing Direct download link for resources for app.<br>
   Example:
   ```dotenv
    YOUTUBE_CLI_DL=https://github.com/inotia00/revanced-cli
    YOUTUBE_PATCHES_DL=https://github.com/inotia00/revanced-patches
    YOUTUBE_PATCHES_JSON_DL=https://github.com/inotia00/revanced-patches
    YOUTUBE_INTEGRATIONS_DL=https://github.com/inotia00/revanced-integrations
   ```
   With the config tool will try to patch youtube with resources from inotia00 while other global resource will used
   for patching other apps.
   *Note* - The link provided must be DLs. Unless they are from GitHub.
8. <a id="global-keystore-file-name"></a>If you don't want to use default keystore. You can provide your own by
   placing it inside `apks` folder. And adding the name of `keystore-file` in `.env` file or in `ENVS` in `GitHub
   secrets` (Recommended) in the format
   ```dotenv
    GLOBAL_KEYSTORE_FILE_NAME=revanced.keystore
   ```
   Tool also support providing secret key at app level. You can sign A app with X key while signing B with Y
   key.<br>
    Example:
   ```dotenv
    YOUTUBE_KEYSTORE_FILE_NAME=youtube.keystore
   ```
9. <a id="global-archs-to-build"></a>You can build only for a particular arch in order to get smaller apk files.This
   can be done with by adding comma separated `ARCHS_TO_BUILD` in `ENVS` in `GitHub secrets` (Recommended) in the
   format.
   ```dotenv
    GLOABAL_ARCHS_TO_BUILD=arm64-v8a,armeabi-v7a
   ```
   Tool also support configuring at app level.<br>

   Example:
   ```dotenv
    YOUTUBE_ARCHS_TO_BUILD=arm64-v8a,armeabi-v7a
   ```
   *Note* -
   1. Possible values are: `armeabi-v7a`,`x86`,`x86_64`,`arm64-v8a`
   2. Make sure the patching resource(CLI) support this feature.
10. <a id="custom-exclude-patching"></a>If you want to exclude any patch. Set comma separated patch in `.env` file
    or in `ENVS` in `GitHub secrets` (Recommended) in the format
    ```ini
    <APP_NAME>_EXCLUDE_PATCH=<PATCH_TO_EXCLUDE-1,PATCH_TO_EXCLUDE-2>
    ```
    Example:
    ```dotenv
     YOUTUBE_EXCLUDE_PATCH=custom-branding,hide-get-premium
     YOUTUBE_MUSIC_EXCLUDE_PATCH=yt-music-is-shit
    ```
    Note -
    1. **All** the patches for an app are **included** by default.<br>
    2. Revanced patches are provided as space separated, make sure you type those **-** separated here.
    It means a patch named _**Hey There**_ must be entered as **_hey-there_** in the above example.
11. <a id="custom-include-patching"></a>If you want to include any universal patch. Set comma separated patch in `.env`
    file or in `ENVS` in `GitHub secrets` (Recommended) in the format
    ```ini
    <APP_NAME>_INCLUDE_PATCH=<PATCH_TO_EXCLUDE-1,PATCH_TO_EXCLUDE-2>
    ```
    Example:
    ```dotenv
     YOUTUBE_INCLUDE_PATCH=remove-screenshot-restriction
    ```
    Note -
    1. Revanced patches are provided as space separated, make sure you type those **-** separated here.
       It means a patch named _**Hey There**_ must be entered as **_hey-there_** in the above example.
12. <a id="app-version"></a>If you want to build a specific version or latest version. Add `version` in `.env` file
    or in `ENVS` in `GitHub secrets` (Recommended) in the format
    ```ini
    <APP_NAME>_VERSION=<VERSION>
    ```
    Example:
    ```ini
    YOUTUBE_VERSION=17.31.36
    YOUTUBE_MUSIC_VERSION=X.X.X
    TWITTER_VERSION=latest
    ```
13. <a id="telegram-support"></a>For Telegram Upload.
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
     6. After Everything done successfully a part of the actions secrets of the repository may look like<br>
        <img src="https://i.imgur.com/Cjifz1M.png" width="400">
14. Configuration defined in `ENVS` in `GitHub secrets` will override the configuration in `.env` file. You can use this
    fact to define your normal configurations in `.env` file and sometimes if you want to build something different just
    once. Add it in `GitHub secrets`.<br>
15. Sample Envs<br>
    <img src="https://i.imgur.com/FxOtiGs.png" width="600" style="left">
16. Make sure your Action has write access. If not click
    [here](https://github.com/nikhilbadyal/docker-py-revanced/settings/actions).
    In the bottom give read and write access to Actions.
    <img src="https://i.imgur.com/STSv2D3.png" width="400">
