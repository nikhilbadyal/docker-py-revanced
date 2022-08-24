# Docker-Py-ReVanced

A little python script that will help you in building [Revanced apps](#note) directly from GitHub. This fork support Youtube, Youtube Music, twitter, reddit, tiktok and WARNWETTER. The [original script] documentation is not as detailed as this one for newbies. So read the following.

## Build

### 🚀 In GitHub (Recommended)

1. Fork the project.
2. Add following **_repository secrets_** 
    - _GH_TOKEN_ (**required**) - GitHub token so that it can upload to GitHub
       after building.
    - _VT_API_KEY_ (optional) - required only if you want Virus total scan.
    - _ENVS_ (optional) - required only if you want to cook specific apps/versions.

    <details>
      <summary>🛈 How to</summary>

      - Go to the repo settings to create the secret variables
        ![step_1]
        ![step_2]

      - **`ENVS`** secret might look like this
        (You should copy your **`ENVS`** content somewhere before saving because secret var can not be edited or copied after. You’ll have to delete and recreate if you want change your **`ENVS`** settings.)

        ```ini
        PATCH_APPS=youtube,twitter
        EXCLUDE_PATCH_YOUTUBE=custom-branding,hide-cast-button,hide-autoplay-button,premium-heading,disable-fullscreen-panels,old-quality-layout,tablet-mini-player,always-autorepeat,enable-debugging,hide-infocard-suggestions
        EXCLUDE_PATCH_YOUTUBE_MUSIC=yt-music-is-shit
        YOUTUBE_VERSION=17.32.39
        YOUTUBE_MUSIC_VERSION=latest
        TWITTER_VERSION=latest    
        ```
    </details>    
3. Go to actions tab. Select `Build Revanced APK`. Click on `Run Workflow`.
    - It can take a few minute to start. Just be patient.

    <details>
      <summary>📖 See report</summary>

      - access logs
        ![action_1]
        ![action_2]
        ![action_3]

    </details>  
4. If the building process is successful, you’ll get your APKs in the releases
    - ![image](https://user-images.githubusercontent.com/22337329/186534074-4a2837b9-bca3-4ef9-abec-1e7d568a4c59.png)


### Note

By default, script builds the version as recommended by Revanced team.

1. Supported values for **_<REVANCED_APPS_NAME>_** are :
   - youtube
   - youtube_music
   - twitter
   - reddit
   - tiktok
   - warnwetter
2. If you want to build a specific version . Add `version` in `environment` in the
   format
   ```
   <APPNAME>_VERSION=<VERSION>
   ```
   Example:
   ```
   YOUTUBE_VERSION=17.31.36
   YOUTUBE_MUSIC_VERSION=X.X.X
   TWITTER_VERSION=X.X.X
   REDDIT_VERSION=X.X.X
   TIKTOK_VERSION=X.X.X
   WARNWETTER_VERSION=X.X.X
   ```
   Check available versions on **APKMirror**.
   - [youtube]
   - [youtube music]
   - [twitter]
3. If you want to a `latest` version, whatever latest is available(including beta) .
   Add `latest` in `environment` in the format
   ```
   <APPNAME>_VERSION=latest
   ```
   Example:
   ```
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
   ```
   PATCH_APPS=<REVANCED_APPS_NAME>
   ```
   Example:
   ```
   PATCH_APPS=youtube,twitter
   ```
5. If you don't want to use default keystore. You can provide your own by placing it
   inside `apks` folder. And adding the name of `keystore-file` in `environment` like
   ```
    KEYSTORE_FILE_NAME=revanced.keystore
   ```
6. If you want to exclude any patch. Set comma separated patch in `environment` in
   the format
   ```
   EXCLUDE_PATCH_<REVANCED_APPS_NAME>=<PATCH_TO_EXCLUDE-1,PATCH_TO_EXCLUDE-2>
   ```
   Example:
   ```
    EXCLUDE_PATCH_YOUTUBE=custom-branding,hide-get-premium
    EXCLUDE_PATCH_YOUTUBE_MUSIC=yt-music-is-shit
   ```
7. By default, the `--experimental` flag is used to allow patching new but untested apps releases.
    There is two ways to force the script only patches the apps releases supported and tested by ReVanced.
    1. Create a new **`ENVS`** and use `<APPNAME>_VERSION=<VERSION>`
    2. Edit the `main.py` file line 376 to change `is_experimental = True` to `is_experimental = False`
    

Thanks to [@aliharslan0](https://github.com/aliharslan0/pyrevanced) for his work.

[step_1]: https://user-images.githubusercontent.com/22337329/186522183-1fe9088c-2d63-45fe-ba6f-baa49cdfd989.png
[step_2]: https://user-images.githubusercontent.com/22337329/186521861-42786e8d-5db4-43ef-9676-2f7e7c0eddc4.png
[action_1]: https://user-images.githubusercontent.com/22337329/186533319-0aebf294-9bac-4859-b4e1-1b4c87d39f48.png
[action_2]: https://user-images.githubusercontent.com/22337329/186533358-e27e30bc-0d16-4f56-a335-0387c481dbf8.png
[action_3]: https://user-images.githubusercontent.com/22337329/186533417-15477a2c-28c3-4e39-9f3d-c4e18202d000.png
[original script]: https://github.com/nikhilbadyal/docker-py-revanced
[youtube]: https://www.apkmirror.com/apk/google-inc/youtube/
[youtube music]: https://www.apkmirror.com/apk/google-inc/youtube-music/
[twitter]: https://www.apkmirror.com/apk/twitter-inc/twitter/
