# What is this?
A simple to use tool to help you save time by updating all your minecraft mods (using modrinth) for you.
Mainly to be used for server mod management.

# How to use
1. Clone or download this repository.
2. Install the dependencies with `pip install -r requirements.txt`.
3. Run the script through your terminal:

   ```
   python main.py <MCVERSION> <MINECRAFT_FOLDER_PATH>
   ```

   For example: `python main.py 1.21 ~/.minecraft`

4. It then checks each `.jar` file in the `mods` folder and installs the latest compatible version for your game version and mod loader from Modrinth.

## Options
| Flag | Description |
| --- | --- |
| `-k`, `--keep` | Keep outdated mod files instead of deleting them |
| `--log-dir DIR` | Directory to store logs in (default: `./log`) |
| `--log-level LEVEL` | Log verbosity: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` (default: `INFO`) |
| `-V`, `--version` | Show the script version |

# Running the tests
```
pip install pytest
pytest
```
