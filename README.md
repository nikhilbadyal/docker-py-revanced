###### 29/JANUARY/2024:
### As of the 26th of this month, RVX has been discontinued...
* Repo can still be used as a base to patch the original ReVanced applications, existing versions of Extended or any other fork by editing the [.env](https://github.com/Spacellary/docker-py-revanced/blob/main/.env) file for example.

###### 07/AUGUST/2023:
### Merged new upstream features...
* [Custom patch resources](https://github.com/nikhilbadyal/docker-py-revanced/issues/230) are now supported, with per-app configuration options available! For more information about this, [check here](https://github.com/Spacellary/ReVanced-Extended-Automated-Builder/blob/main/readme-history/README-ORIGINAL.md#global-config).

###### 15/JULY/2023:
### Merged upstream changes...
* Now with support for **RVX Reddit**.

Also supports the other Reddit clients, such as **RV Sync**.
* Read the [README-ORIGINAL.md](https://github.com/Spacellary/ReVanced-Extended-Automated-Builds/blob/main/readme-history/README-ORIGINAL.md) for more information about those.

###### 23/MARCH/2023:
### Builds are now automated!
Added simple scheduled action that checks for patch updates, and if an update is found, records the new version of patches for future reference and automatically triggers the workflow to build and release the new applications.

<hr>

### Feel free to fork this fork.
Let the 'forkception' begin!

### How to use this fork:

**Before running the workflows for the first time, you need to go the Settings page of the repository and under Actions, then General, change the "Workflow permissions" to "read and write".**

1. Go to the Actions page at the top.
2. Select the "Build & Release" action.
3. Click the "Run Workflow" drop-down button and run it. <br> <br> Optionally, select the "Update Checker" action, and **enable** it. It will periodically check for new `inotia00/revanced-patches` releases and trigger a new Build & Release when a new version is found. <br> <br> *You may change the repository to watch for updates in the [update.yml [line 28]](.github/workflows/update.yml) workflow file.*

<br>

**It will take around 7 minutes to complete the Build & Release workflow.** Once that's completed:

1. Go to "Releases" at the bottom of your repository page (on mobile) or at the right (on Desktop).
2. Download your patched applications.

#### Set up to build:
* [ReVanced Extended](https://github.com/inotia00/revanced-patches/releases/latest) **YouTube** (latest supported).
* [ReVanced Extended](https://github.com/inotia00/revanced-patches/releases/latest) **YouTube Music** (latest supported) in the **arm64-v8a** architecture.
* [ReVanced Extended](https://github.com/inotia00/revanced-patches/releases/latest) **Reddit** (latest).
* [ReVanced](https://github.com/revanced/revanced-patches/releases/latest) **Sync for Reddit** (latest).

###### Check [.env](https://github.com/Spacellary/docker-py-revanced/blob/main/.env) for a list of excluded patches and [options.json](https://github.com/Spacellary/docker-py-revanced/blob/main/apks/options.json) for patch options.
###### Complete and original README can be found [here](https://github.com/Spacellary/ReVanced-Extended-Automated-Builds/blob/main/readme-history/README-ORIGINAL.md).
