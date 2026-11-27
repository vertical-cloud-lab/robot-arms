"""Upload-only YouTube client for the BYU Vertical Cloud Lab channel.

Ported from vertical-cloud-lab/byu-vcl's youtube/yt_service.py, minus the
full-control token: that one lives only in byu-vcl's `youtube-admin`
environment and never reaches this repo.

    YOUTUBE_UPLOAD_TOKEN_PICKLE_B64  base64 token.pickle, scopes youtube.upload
                                     + youtube.readonly. Every @claude run and
                                     .claude/settings.local.json.

Refreshing replaces the short-lived access token in memory; the refresh
token inside the pickle never changes, so nothing is written back.

    python youtube/yt_service.py                  # which channel, which scopes
    python youtube/yt_service.py upload clip.mp4 --title "PiPER pick-and-place"
"""

import argparse
import base64
import json
import os
import pickle

from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

ENV_VAR = "YOUTUBE_UPLOAD_TOKEN_PICKLE_B64"


def get_credentials():
    b64 = os.environ.get(ENV_VAR, "").strip()
    if not b64:
        raise SystemExit(f"{ENV_VAR} is not set. See youtube/README.md.")
    if b64.startswith(ENV_VAR + "="):
        # Pasting "NAME=value" into the secret box breaks unpickling with a
        # confusing "invalid load key" -- it happened in me-en-372.
        print(f"WARNING: {ENV_VAR} starts with its own name; stripping it. Fix the stored secret.")
        b64 = b64[len(ENV_VAR) + 1:]
    creds = pickle.loads(base64.b64decode(b64))
    if not creds.valid:
        creds.refresh(Request())
    return creds


def get_youtube_service():
    return build("youtube", "v3", credentials=get_credentials())


def triggering_link():
    """html_url of the comment, review or issue that started this Actions run.

    GitHub writes the triggering event to $GITHUB_EVENT_PATH. For an @claude
    reply that is the reply itself (an issue or PR comment, a review comment,
    or a review); for a new or assigned issue it is the issue. None outside
    GitHub Actions.
    """
    path = os.environ.get("GITHUB_EVENT_PATH")
    if not path:
        return None
    try:
        with open(path, encoding="utf-8") as f:
            event = json.load(f)
    except (OSError, ValueError):
        return None
    for key in ("comment", "review", "issue", "pull_request"):
        url = (event.get(key) or {}).get("html_url")
        if url:
            return url
    return None


def with_triggering_link(description):
    """Append "Requested in <link>" (see triggering_link) unless it is already there."""
    url = triggering_link()
    if not url or url in description:
        return description
    return f"{description}\n\nRequested in {url}".strip()


def upload_video(path, title, description="", privacy="public", tags=None, category_id="28", source_link=True):
    """Resumable upload; returns the new video id.

    Defaults to public (sgbaird, 2026-11-19); pass privacy="unlisted" or
    "private" when asked. Since 2026-11-02 YouTube no longer locks uploads
    from unverified API projects to private, so the privacy set here sticks:
    https://developers.google.com/youtube/v3/revision_history

    In GitHub Actions, the link to the comment that started the run is
    appended to the description (source_link=False skips it).
    """
    if source_link:
        description = with_triggering_link(description)
    youtube = get_youtube_service()
    body = {
        "snippet": {"title": title, "description": description, "tags": tags or [], "categoryId": category_id},
        "status": {"privacyStatus": privacy, "selfDeclaredMadeForKids": False},
    }
    media = MediaFileUpload(path, chunksize=8 * 1024 * 1024, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"uploaded {status.progress():.0%}", flush=True)
    return response["id"]


def main():
    parser = argparse.ArgumentParser(description="YouTube upload helper for the BYU VCL channel")
    sub = parser.add_subparsers(dest="cmd")
    up = sub.add_parser("upload")
    up.add_argument("path")
    up.add_argument("--title", required=True)
    up.add_argument("--description", default="")
    up.add_argument("--no-source-link", action="store_true",
                    help="do not append the link to the GitHub comment that started this run")
    up.add_argument("--privacy", choices=["private", "unlisted", "public"], default="public")
    args = parser.parse_args()

    if args.cmd == "upload":
        video_id = upload_video(args.path, args.title, args.description, args.privacy, source_link=not args.no_source_link)
        print(f"https://www.youtube.com/watch?v={video_id}")
        return

    creds = get_credentials()
    channel = build("youtube", "v3", credentials=creds).channels().list(part="snippet", mine=True).execute()["items"][0]
    print(f"{ENV_VAR} -> {channel['snippet']['title']} ({channel['id']})")
    print("scopes:", ", ".join(creds.scopes or []))


if __name__ == "__main__":
    main()
