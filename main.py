__version__ = '1.2.5'

import logging
from logging.handlers import RotatingFileHandler
import hashlib
import argparse
import requests
from requests.exceptions import HTTPError
import os
from apis.modrinth_api import ModrinthApi

# Set arguments:
# gameversion
# -p --path         - Add auto directory finding
# -k --keep
# -log --log-level
# -V --version
parser = argparse.ArgumentParser(
    prog='Minecraft Mod Updater',
    description='Updates all minecraft mods in a given directory through modrinth')
parser.add_argument(
    'gameversion', metavar='gameversion',
    action='store', type=str,
    help='Minecraft version to check updates for (e.g. 1.16.5 24w34a 1.21)')
parser.add_argument(
    '-p', '--path',
    metavar='path', action='store',
    type=str, help='Path to the .minecraft path, '
                   'if not used script will assume its in the .minecraft folder')
parser.add_argument(
    '-k', '--keep',
    action='store_true', help='Keep outdated mods')
parser.add_argument(
    '-log', '--log-level',
    action='store', default='INFO',
    type=str.lower, choices=['debug', 'info', 'warn', 'warning', 'error', 'critical'],
    metavar='\b', help='Set the log level '
         '(debug, info, warn(ing), error, critical) (default: INFO)')
parser.add_argument(
    '-V', '--version',
    action='version', version=__version__)
args = parser.parse_args()

log_levels = {
    'critical': logging.CRITICAL,
    'error': logging.ERROR,
    'warn': logging.WARNING,
    'warning': logging.WARNING,
    'info': logging.INFO,
    'debug': logging.DEBUG
}

logger = logging.getLogger(__name__)
logger.setLevel(log_levels[args.log_level])

modrinth_api_logger = logging.getLogger('apis.modrinth_api')
modrinth_api_logger.setLevel(log_levels[args.log_level])

log_file = './logs/mod-updater.log'
file_handler = RotatingFileHandler(
    log_file, mode='a',
    maxBytes=5*1024*1024, backupCount=2)
formatter = logging.Formatter(
    '[%(asctime)s]:[%(levelname)s]: %(message)s',
    '%Y-%m-%d %H:%M:%S')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def get_sha1(
        filepath,
        buffer_size=65536) -> str:
    """Gets the sha1 hash of a file."""
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
    """Downloads a file from a URL."""
    filename = url.split('/')[-1]
    logger.info(f'Downloading {filename}')
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(os.path.join(path, filename), 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    return filename

def download_mod(
        update_link: str,
        mod_dir='./mods') -> None:
    """Downloads a mod"""
    try:
        download_file(update_link, path=mod_dir)
    except HTTPError as err:
        logger.error(f'HTTP error occurred: {err}')
        print(f'[Error] HTTP error occurred: {err}')
    except Exception as err:
        logger.critical(f'Unexpected error occurred: {err}')
        print(f'[Critical] Unexpected error occurred: {err}')

def main():
    logger.info('Script started')
    print(f'Auto mod updater script started! Version {__version__}')
    logger.debug(f'Script args: {args}')

    script_dir = os.path.split(os.path.realpath(__file__))[0]
    minecraft_dir = os.path.abspath(os.path.join(script_dir, '..'))
    if args.path is not None:
        minecraft_dir = os.path.abspath(args.path)
    mod_dir = os.path.join(minecraft_dir, 'mods')
    logger.debug(f'Current script directory: {script_dir}')
    logger.debug(f'Current minecraft directory: {minecraft_dir}')
    logger.debug(f'Minecraft mod directory: {mod_dir}')

    if minecraft_dir.split(os.sep)[-1] != '.minecraft' and args.path is None:
        logger.critical('Either script folder must be in the .minecraft directory or -p must be set. '
                        f'Was set to: {minecraft_dir}')
        print('[Error] Script folder must be in the .minecraft directory or -p must be set. '
              f'Was set to: {minecraft_dir}')
        exit()
    if not os.path.isdir(mod_dir):
        logger.critical('Mod folder not found')
        print('[Error] Mod folder does not exist.')
        exit()

    modrinth = ModrinthApi()

    mod_dir_list = os.listdir(mod_dir)
    logger.debug(f'Mod dir set to: {mod_dir}')

    mods_fname_dict = {}
    mod_hash_list = []
    for mod in mod_dir_list:
        if mod.split('.')[-1] != 'jar':
            logger.info(f'Ignoring {mod}')
            print(f'Ignoring {mod}')
            continue
        logger.debug(f'Getting {mod} hash')
        print(f'Checking {mod} for updates')
        mod_hash = get_sha1(os.path.join(mod_dir, mod))
        mods_fname_dict[mod_hash] = mod
        mod_hash_list.append(mod_hash)

    if not mod_hash_list:
        logger.warning('No mods found!')
        print('No mods found!')
        exit()

    mods_info_dict = modrinth.get_multiple_mods_details(mod_hash_list)
    if 'error' in mods_info_dict.keys():
        print(f'[Error] {mods_info_dict['error']}\nNo updates can be performed quitting.')
        exit()
    logger.debug(f'Bulk mods info: {mods_info_dict}')

    loader_mods_dict = {}
    mods_loader_dict = {}
    mods_update_info = {}
    for mod in mods_info_dict:
        loader = mods_info_dict[mod]['loaders'][0]
        if loader not in loader_mods_dict:
            loader_mods_dict[loader] = [mod]
            mods_update_info[loader] = {}
        else:
            loader_mods_dict[loader].append(mod)
        mods_loader_dict[mod] = loader
    logger.debug(f'Loader mods dict: {loader_mods_dict}')
    logger.debug(f'Mods loader dict: {mods_loader_dict}')

    for loader in loader_mods_dict:
        mods_update_info[loader] = modrinth.get_multiple_mods_update_info(
            loader_mods_dict[loader],
            game_version=args.gameversion,
            loader=loader)
        logger.debug(f'Bulk updated mods info for {loader}: {mods_update_info[loader]}')
        if 'error' in mods_info_dict.keys():
            print(f'[Error] {mods_update_info[loader]}\nNo updates can be performed quitting.')
            exit()
    logger.debug(f'Mods update info: {mods_update_info}')

    mods_updated_count = 0
    no_new_version_count = 0
    for mod in mod_hash_list:
        logger.info(f'Checking {mods_fname_dict[mod]} ({mod}) for updates')
        if mod not in mods_update_info[mods_loader_dict[mod]]:
            logger.warning(f'Skipping {mods_fname_dict[mod]} ({mod}) does not have a version for {args.gameversion}')
            print(f'[Warning] Skipping {mods_fname_dict[mod]} ({mod}) does not have a version for {args.gameversion}')
            no_new_version_count += 1
            continue

        mod_update_files = mods_update_info[mods_loader_dict[mod]][mod]['files']
        mod_dl_url = mod_update_files[0]['url']
        new_mod_filename = mod_update_files[0]['filename']

        if mod == mod_update_files[0]['hashes']['sha1']:
            logger.info(f'Skipping {mods_fname_dict[mod]} is already updated')
            print(f'Skipping {mods_fname_dict[mod]} is already updated')
            continue

        logger.debug(f'Update link for {mods_fname_dict[mod]}: {mod_update_files[0]['url']}')
        print(f'Updating {mods_fname_dict[mod]} to {new_mod_filename}')

        download_mod(mod_dl_url, mod_dir)

        if not args.keep:
            os.remove(os.path.join(mod_dir, mods_fname_dict[mod]))
            logger.info(f'Deleted old mod file: {mods_fname_dict[mod]}')
            print(f'Deleted old mod file: {mods_fname_dict[mod]}')

        mods_updated_count += 1

    logger.info(f'{mods_updated_count} mods updated successfully')
    print(f'{mods_updated_count} mods updated successfully')
    logger.info(f'{no_new_version_count} mods have no version for {args.gameversion}')
    print(f'{no_new_version_count} mods have no version for {args.gameversion}')


if __name__ == '__main__':
    main()
