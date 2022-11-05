#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

export PATCH_APPS=youtube,twitter,reddit,youtube_music
export BUILD_EXTENDED=True
export EXCLUDE_PATCH_YOUTUBE=custom-branding,enable-debugging
export EXCLUDE_PATCH_YOUTUBE_EXTENDED=custom-branding-icon-red,custom-branding-icon-blue,custom-branding-icon-revancify,custom-branding-name,custom-package-name,materialyou,overlay-buttons-alternative-icon
export EXCLUDE_PATCH_YOUTUBE_MUSIC_EXTENDED=custom-branding-music-red,custom-branding-music-revancify,custom-package-name-music,compact-header
export ARCHS_TO_BUILD=arm64-v8a
