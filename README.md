###### 15/JULY/2023:
### Merged upstream changes.
* Now with support for **RVX mMicroG** and **RVX Reddit**.

Also supports the other Reddit clients, such as **RV Sync**.
* Read the [README-ORIGINAL.md](https://github.com/Spacellary/ReVanced-Extended-Automated-Builds/blob/main/readme-history/README-ORIGINAL.md) for more information about those.

###### 23/MAR/2023:
### Builds are now automated!
Added simple scheduled action that checks for patch updates, and if an update is found, records the new version of patches for future reference and automatically triggers the workflow to build and release the new applications.


<hr>

### Feel free to fork this fork.
Let the 'forkception' begin!

### How to use this fork:

**Before running the workflows for the first time, you need to go the Settings page of the repository and under Actions, then General, change the "Workflow permissions" to "read and write".**

1. Go to the Actions page at the top.
2. Select the "Build & Release" action.
3. Click the "Run Workflow" drop-down button and run it.
4. Optionally select the "Update Checker" action, and **enable** it. It will periodically check for new patch releases and trigger a new Build & Release when necessary.

* This requires you to set your PERSONAL_ACCESS_TOKEN secret to trigger builds. Read about how to get a token [here](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens).

*It will take around 5 minutes to complete the workflow.*

5. Go to "Releases" at the bottom (on mobile) or at the right (on Desktop).
6. Download your patched applications.

#### Set up to build:
* ReVanced Extended **YouTube** (latest supported).
* ReVanced Extended **YouTube Music** (latest) in the **arm64-v8a** architecture.
* ReVanced Extended **mMicroG** (latest supported).
* ReVanced **Sync for Reddit** (version most compatible with patches).
* ReVanced Extended **Reddit** (latest supported).


###### Check [.env](https://github.com/Spacellary/docker-py-revanced/blob/main/.env) for a list of excluded patches and [options.json](https://github.com/Spacellary/docker-py-revanced/blob/main/apks/options.json) for patch options.
###### Complete and original README can be found [here](https://github.com/Spacellary/ReVanced-Extended-Automated-Builds/blob/main/readme-history/README-ORIGINAL.md).
