#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

export PATCH_APPS=youtube,twitter,reddit
export YOUTUBE_VERSION=latest
export YOUTUBE_MUSIC_VERSION=latest
export TWITTER_VERSION=latest
export REDDIT_VERSION=latest
export TIKTOK_VERSION=latest
export WARNWETTER_VERSION=latest
