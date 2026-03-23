__version__ = '1.3.2'

import logging
from logging.config import dictConfig
from datetime import datetime
import hashlib
import argparse
import requests
from requests.exceptions import HTTPError
import os
from apis.modrinth_api import ModrinthApi

# Program setup:
# - Accept the Minecraft version and .minecraft path as required arguments.
# - Optional flags control whether old mods are kept and where logs go.
parser = argparse.ArgumentParser(
    prog='Minecraft Mod Updater',
    description='Updates all minecraft mods in '
                'a given directory through modrinth')
parser.add_argument(
    'gameversion',
    action='store',
    type=str,
    help='Minecraft version to check updates for (e.g. 1.16.5 24w34a 1.21)')
parser.add_argument(
    'path',
    action='store',
    type=str,
    help='Path to the .minecraft directory')
parser.add_argument(
    '-k', '--keep',
    action='store_true',
    help='Keep outdated mods')
parser.add_argument(
    '--log-dir',
    type=str,
    default='./log',
    help='set the directory to store logs in (default: ./log)')
parser.add_argument(
    '--log-level',
    action='store',
    type=str.upper,
    default='INFO',
    choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
    help='Set the log level '
         '(DEBUG, INFO, WARNING, ERROR, CRITICAL) (default: INFO)')
parser.add_argument(
    '-V', '--version',
    action='version', version=__version__)
args = parser.parse_args()

# Make sure the log directory exists before configuring file logging.
if not os.path.exists(args.log_dir):
    os.makedirs(args.log_dir)

# Configure logging:
# - console output is short and readable
# - file output is more detailed and rotated to avoid huge log files
logging.config.dictConfig({
    'version': 1,
    'formatters': {
        'brief': {
            'format': '%(levelname)s: %(message)s',
        },
        'precise': {
            'format': '[%(asctime)s]:%(levelname)s:%(module)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'brief',
            'stream': 'ext://sys.stdout'
        },
        'outputFile': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'precise',
            'maxBytes': 4 * 1024 * 1000,
            'backupCount': 10,
            'filename': os.path.join(
                args.log_dir,
                f'{datetime.now().strftime("%Y-%m-%d")}-mc-mod-helper.log'
            )
        }
    },
    'loggers': {
        '': {
            'level': args.log_level,
            'handlers': ['console', 'outputFile']
        }
    }
})

logger = logging.getLogger(__name__)


def get_sha1(
        filepath,
        buffer_size=65536) -> str:
    """Return the SHA-1 hash for a file."""
    sha1 = hashlib.sha1()
    with open(filepath, 'rb') as f:
        while True:
            data = f.read(buffer_size)
            if not data:
                break
            sha1.update(data)
    logger.debug(f'Gotten sha1 hash: {sha1.hexdigest()} from {filepath}')
    return sha1.hexdigest()


def download_file(url, path='./') -> str:
    """Download a file from a URL into the target directory."""
    filename = url.split('/')[-1]
    logger.info(f'Downloading {filename}')
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(os.path.join(path, filename), 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return filename


def main():
    # Log startup info and show the parsed command-line arguments.
    logger.debug(f'Script args: {args}')
    logger.info(f'Auto mod updater script started! Version {__version__}')

    # Resolve the Minecraft directory and the mods folder inside it.
    minecraft_dir = os.path.abspath(args.path)
    mod_dir = os.path.join(minecraft_dir, 'mods')
    logger.debug(f'Current minecraft directory: {minecraft_dir}')
    logger.debug(f'Minecraft mod directory: {mod_dir}')

    # Stop early if the mods directory doesn't exist.
    if not os.path.isdir(mod_dir):
        logger.critical('Mod folder does not exist')
        exit()

    # Create the API wrapper used for Modrinth lookups.
    modrinth = ModrinthApi()

    # Read all files in the mods folder.
    mod_dir_item_list = os.listdir(mod_dir)
    logger.debug(f'Mod dir set to: {mod_dir}')

    # Track each mod by its SHA-1 so we can match it against Modrinth data.
    mods_filename_dict = {}
    mod_hash_list = []
    for item in mod_dir_item_list:
        # Only jar files are treated as mods.
        if item.split('.')[-1] != 'jar':
            logger.info(f'Ignoring {item}')
            continue
        logger.debug(f'Getting {item} hash')
        mod_hash = get_sha1(os.path.join(mod_dir, item))
        mods_filename_dict[mod_hash] = item
        mod_hash_list.append(mod_hash)

    # If there are no mods, there is nothing to update.
    if not mod_hash_list:
        logger.warning('No mods found!')
        exit()

    # Ask Modrinth which mods match the local hashes.
    mods_info_dict = modrinth.get_multiple_mods_details(mod_hash_list)
    if 'error' in mods_info_dict.keys():
        logger.critical(f'No updates can be performed quitting, '
                        f'error output:\n{mods_info_dict["error"]}')
        exit()
    logger.debug(f'Bulk mods info: {mods_info_dict}')

    # Group mods by loader because update queries are loader-specific.
    loader_mods_dict = {}
    mods_loader_dict = {}
    mods_update_info = {}
    for mod in mods_info_dict:
        loader = mods_info_dict[mod]['loaders'][0]
        loader_mods_dict.setdefault(loader, []).append(mod)
        mods_loader_dict[mod] = loader
    logger.debug(f'Loader mods dict: {loader_mods_dict}')
    logger.debug(f'Mods loader dict: {mods_loader_dict}')

    # Fetch update info for each loader group.
    for loader in loader_mods_dict:
        mods_update_info[loader] = modrinth.get_multiple_mods_update_info(
            loader_mods_dict[loader],
            game_version=args.gameversion,
            loader=loader)
        logger.debug(f'Bulk updated mods info for {loader}: {mods_update_info[loader]}')
        if 'error' in mods_info_dict.keys():
            logger.critical(f'No updates can be performed quitting, '
                            f'error output:\n{mods_info_dict["error"]}')
            exit()
    logger.debug(f'Mods update info: {mods_update_info}')

    # Count update results for the final summary.
    mods_updated_count = 0
    no_new_version_count = 0
    for mod in mod_hash_list:
        logger.info(f'Checking {mods_filename_dict[mod]} ({mod}) for updates')

        # If the API did not return info for this hash, skip it.
        if mod not in mods_loader_dict.keys():
            logger.warning(f'Skipping {mods_filename_dict[mod]} ({mod}) '
                           f'no results from apis')
            no_new_version_count += 1
            continue

        # If this mod has no compatible version for the requested game version, skip it.
        if mod not in mods_update_info[mods_loader_dict[mod]]:
            logger.warning(f'Skipping {mods_filename_dict[mod]} ({mod}) '
                           f'does not have a version for {args.gameversion}')
            no_new_version_count += 1
            continue

        mod_update_files = mods_update_info[mods_loader_dict[mod]][mod]['files']
        mod_dl_url = mod_update_files[0]['url']
        new_mod_filename = mod_update_files[0]['filename']

        # If the SHA-1 already matches, the mod is already up to date.
        if mod == mod_update_files[0]['hashes']['sha1']:
            logger.info(f'Skipping {mods_filename_dict[mod]} is already updated')
            continue

        logger.debug(f'Update link for {mods_filename_dict[mod]}: '
                     f'{mod_update_files[0]["url"]}')
        logger.info(f'Updating {mods_filename_dict[mod]} to {new_mod_filename}')

        try:
            # Download the updated mod file.
            download_file(mod_dl_url, mod_dir)

            # Optionally, delete the old file after the new one is downloaded.
            if not args.keep:
                os.remove(os.path.join(mod_dir, mods_filename_dict[mod]))
                logger.info(f'Deleted old mod file: {mods_filename_dict[mod]}')
        except HTTPError as err:
            logger.error(f'HTTP error occurred: {err}')
        except Exception as err:
            logger.critical(f'Unexpected error occurred: {err}')
            exit()

        mods_updated_count += 1

    # Final summary so the user knows what happened.
    logger.info(f'{mods_updated_count} mods updated successfully')
    logger.info(f'{no_new_version_count} mods have no version for {args.gameversion}')


if __name__ == '__main__':
    main()
