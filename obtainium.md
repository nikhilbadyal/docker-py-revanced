# Obtainium

[Obtainium](https://github.com/ImranR98/Obtainium) is an Android app that installs and updates apps straight from
their source (GitHub releases, F-Droid, direct APK links, arbitrary HTML pages, etc.), skipping app stores
entirely. Since this project's own releases are just GitHub Releases, Obtainium can track them directly - this
integration exists to make setting that up (and keeping version numbers readable) less manual.

> **Warning**: Enabling any of this generates a public APK discovery URL for your fork or self-hosted setup. Only
> enable it if you're comfortable with that.

## How it works

Two things get generated, and the second builds on the first:

1. **Per-app HTML source pages** (`OBTAINIUM_EXPORT`) - one static HTML file per patched app, containing a link to
   its latest release asset. Obtainium's "HTML" source type can point at a page like this and periodically re-check
   it for updates, the same way it'd scrape any other HTML page.
2. **One-click install site** (`OBTAINIUM_SITE_EXPORT`) - an `index.html` at the repo root of the `changelogs`
   branch, listing every app as an
   [`obtainium://app/...`](https://github.com/ImranR98/Obtainium/blob/main/README.md) deep link. These links carry
   a URL-encoded JSON blob of an app's full Obtainium configuration (source URL, author, name, version regex,
   etc.). Tapping one on a device with Obtainium installed opens the app with that config pre-filled - equivalent
   to manually adding the HTML source from step 1 and typing in all the same settings by hand, minus the typing.
   It's written at the branch root rather than alongside the per-app pages in `obtainium_sources/` because GitHub
   Pages' branch-deploy mode can only serve from a branch's root or its `/docs` folder, never an arbitrary
   subfolder.

Version detection deserves a specific callout, since it's the part most likely to need tuning: the per-app HTML
page's only meaningful content is a link to the release asset, and that asset's filename already encodes the app
version and patch bundle version (see `APP.get_output_file_name` in `src/app.py`), e.g.:

```text
ReYouTube-Version20.47.62-PatchVersionv1.37.0-PatchSetabc123def456-2026AUG01.0131AM-output.apk
```

Obtainium can apply a regex against that link text to pull out a human-readable version instead of falling back to
hashing the link (which still works, just shows a hash instead of a version). `OBTAINIUM_VERSION_EXTRACTION_REGEX`
and `OBTAINIUM_VERSION_MATCH_GROUP` (see below) control that regex, and the deep links from `OBTAINIUM_SITE_EXPORT`
pre-fill it automatically. If you add a source manually via its HTML URL instead of via a deep link, you'd otherwise
have to configure this same regex by hand in Obtainium's UI.

## Setup

1. Enable `OBTAINIUM_EXPORT=true` (see [Configuration](#configuration) below). This is the minimum needed - it
   generates `obtainium_sources/*.html` in the `changelogs` branch, one file per patched app.
2. Add sources to Obtainium one of two ways:
   - **Manually**: in Obtainium, add each app via its raw HTML URL as an "HTML" source, e.g.
     `https://raw.githubusercontent.com/<user>/<repo>/changelogs/obtainium_sources/youtube.html`. You'll need to
     configure the version regex yourself if you want readable versions (see above).
   - **One-click site**: also enable `OBTAINIUM_SITE_EXPORT=true`. This additionally generates `index.html` at
     the `changelogs` branch root with a ready-to-tap link per app, version regex included.
3. *(Optional, for the one-click site)* Publish it with GitHub Pages: repo Settings -> Pages -> set the source
   branch to `changelogs` and the folder to `/ (root)` - GitHub Pages' branch-deploy mode only offers root or
   `/docs`, so this only works because `index.html` is generated at the branch root. Visit the published Pages
   URL on an Android device with Obtainium installed and tap the links you want.

## Configuration

Add these to your `.env` file, or (recommended) to the `ENVS` GitHub secret.

<a id="obtainium_export"></a>
### `OBTAINIUM_EXPORT`

- **Default**: `false`
- Generates `obtainium_sources/*.html` (one file per patched app) in the `changelogs` branch. Required for
  everything else in this document; the rest of these variables have no effect unless this is enabled.

```ini
OBTAINIUM_EXPORT=true
```

<a id="obtainium_github_tag"></a>
### `OBTAINIUM_GITHUB_TAG`

- **Default**: `latest`
- The release tag the generated HTML links point to. By default, links point at `latest` so they survive the
  default CI's dynamic timestamp-based release tags.

```ini
OBTAINIUM_GITHUB_TAG=latest
```

> **Warning**: If you set this to a fixed tag, make sure your CI workflow actually releases under that exact tag -
> otherwise the generated links will point at a release that doesn't exist (or doesn't contain that app's APK).

<a id="obtainium_site_export"></a>
### `OBTAINIUM_SITE_EXPORT`

- **Default**: `false`
- Generates `index.html` at the `changelogs` branch root, listing a one-click `obtainium://app/...` install link
  for every app covered by `OBTAINIUM_EXPORT`. See [How it works](#how-it-works) above for what these links
  contain and why it's at the branch root rather than inside `obtainium_sources/`.

```ini
OBTAINIUM_SITE_EXPORT=true
```

<a id="obtainium_version_extraction_regex"></a>
### `OBTAINIUM_VERSION_EXTRACTION_REGEX`

- **Default**: `Version([\w.]+)-PatchVersion[v]?([\w.]+)-PatchSet`
- The regex Obtainium applies to the release asset link text to extract version info, embedded into each
  `OBTAINIUM_SITE_EXPORT` deep link's `additionalSettings.versionExtractionRegEx`. The default matches this
  project's own output filename convention (app version, then patch bundle version - with or without a leading
  `v`, since that varies by patch source) and needs no configuration out of the box. Only override this if you've
  customized the build's output filename format elsewhere.

```ini
OBTAINIUM_VERSION_EXTRACTION_REGEX=Version([\w.]+)-PatchVersion[v]?([\w.]+)-PatchSet
```

<a id="obtainium_version_match_group"></a>
### `OBTAINIUM_VERSION_MATCH_GROUP`

- **Default**: `$1+$2`
- The match-group template Obtainium uses to assemble the extracted version, embedded into each deep link's
  `additionalSettings.matchGroupToUse`. The default combines the app version and patch version (regex groups 1 and
  2 above) into a single `<app_version>+<patch_version>` string. Only override this if you've also changed
  `OBTAINIUM_VERSION_EXTRACTION_REGEX` and need a different group arrangement.

```ini
OBTAINIUM_VERSION_MATCH_GROUP=$1+$2
```
