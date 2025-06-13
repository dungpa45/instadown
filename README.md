# InstaDown

A simple Python script to download all images from a public Instagram user's timeline.

## Features

- Downloads all images (including carousels) from a specified Instagram user.
- Handles pagination to fetch all posts.
- Saves images in a directory named after the Instagram user.
- Command-line interface.

## Requirements

- Python 3.x
- `requests` library
- `python-dotenv` library
- Copy `.env-example` to `.env` and update with your Instagram cookie

Install dependencies with:

```sh
pip install requests python-dotenv
```

## Setup

1. Copy `.env-example` to `.env`:

    ```sh
    cp .env-example .env
    ```

2. Edit `.env` and set your `INSTAGRAM_COOKIE` value.

## Usage

### Command-line Example

```sh
python insta.py <instagram_username> [-o OUTPUT_DIR]
```

- `<instagram_username>`: Instagram user to download images from.
- `-o OUTPUT_DIR`: (Optional) Output directory for downloaded images.

Example:

```sh
python insta.py abcxyz
```

### How it works

- The script fetches posts using Instagram's internal GraphQL API.
- It downloads all images from both single-image and carousel (multi-image) posts.
- Images are saved in a folder named after the Instagram username (or the specified output directory).

### Troubleshooting

- If you get authentication or permission errors, update the `HEADERS` in [`insta.py`](insta.py) with your own Instagram session cookie.
- Instagram may change their API at any time, which could break this script.
- Make sure your account has access to the target user's posts (public or you follow them).

### License

MIT License

## Notes

The script uses a session cookie for authentication. You must update the `INSTAGRAM_COOKIE` in your `.env` file for the script to work.
Use responsibly and respect Instagram's terms of service.

## Disclaimer

This project is for educational purposes only. Downloading content from Instagram may violate their terms of service.
