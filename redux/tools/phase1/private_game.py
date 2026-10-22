"""Private writable game roots for GUI callbacks that save configuration.

Asset directories are junctions/symlinks, not copies. This is write isolation for
known root config writes, not a filesystem security boundary. Source root hashes
and recursive names/size/mtime inventory detect unexpected source changes.
"""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess

ASSET_DIRECTORIES = {'data', 'lang', 'manuals', 'movies', 'music', 'scripts',
                     'override', 'sounds', 'portraits', 'characters', 'fonts', 'dlc'}
ALLOWED_ROOT_WRITES = {'gem-baldur.ini', 'gemrb.log', 'gemrb_console.txt', 'gemrb_path.txt'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_inventory(game):
    game = Path(game)
    roots = {p.name: sha(p) for p in game.iterdir() if p.is_file()}
    tree = {}
    for parent, directories, files in os.walk(game, followlinks=False):
        for name in directories + files:
            path = Path(parent) / name
            stat = path.stat()
            tree[str(path.relative_to(game)).replace('\\', '/')] = dict(
                kind='directory' if path.is_dir() else 'file', size=stat.st_size if path.is_file() else None,
                mtime_ns=stat.st_mtime_ns if path.is_file() else None)
    return dict(root_sha256=roots, recursive_inventory=tree)


def link_directory(destination, source):
    if os.name == 'nt':
        result = subprocess.run(['cmd.exe', '/d', '/c', 'mklink', '/J', str(destination), str(source)],
                                capture_output=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        if result.returncode:
            raise OSError('Cannot create private asset junction: ' + result.stderr.decode(errors='replace'))
    else:
        destination.symlink_to(source, target_is_directory=True)


def prepare(game, destination):
    game, destination = Path(game).resolve(), Path(destination).absolute()
    if destination.exists() or not (game / 'chitin.key').is_file():
        raise ValueError('Private game must be a new directory; source KEY required')
    if game == destination or game in destination.parents:
        raise ValueError('Private game must be outside the protected source game')
    entries = list(game.iterdir())
    for path in entries:
        if path.is_dir() and path.name.lower() not in ASSET_DIRECTORIES:
            raise ValueError('Unapproved source directory (possible writable save/cache): ' + path.name)
        if path.is_symlink():
            raise ValueError('Source root symlink requires explicit review: ' + path.name)
    source_before = source_inventory(game)
    destination.mkdir(parents=True, exist_ok=False)
    files, links = {}, {}
    for path in entries:
        target = destination / path.name
        if path.is_dir():
            link_directory(target, path)
            links[path.name] = str(path.resolve())
        else:
            shutil.copy2(path, target)
            files[path.name] = sha(target)
    return dict(schema='bg-redux-private-game/1', source=str(game), game=str(destination),
                copied_root_sha256=files, asset_links=links, source_before=source_before,
                allowed_root_writes=sorted(ALLOWED_ROOT_WRITES), security_boundary=False)


def validate(receipt):
    root = Path(receipt['game'])
    if source_inventory(receipt['source']) != receipt['source_before']:
        raise ValueError('Protected clean-game inventory/root hashes changed')
    links, initial = receipt['asset_links'], receipt['copied_root_sha256']
    changes = {}
    seen = set()
    for path in root.iterdir():
        name = path.name
        seen.add(name)
        if name in links:
            if not path.is_dir() or str(path.resolve()) != links[name]:
                raise ValueError('Private game asset link changed: ' + name)
            continue
        if not path.is_file() or path.is_symlink():
            raise ValueError('Unexpected private game node: ' + name)
        digest = sha(path)
        if digest != initial.get(name):
            if name.lower() not in ALLOWED_ROOT_WRITES:
                raise ValueError('Unexpected private game write: ' + name)
            changes[name] = dict(before_sha256=initial.get(name), after_sha256=digest)
    if (set(initial) | set(links)) - seen:
        raise ValueError('Private game input/link disappeared')
    return dict(clean_game_inventory_unchanged=True, clean_game_root_hashes_unchanged=True,
                copied_immutable_inputs_unchanged=True, allowed_private_root_changes=changes,
                linked_asset_content_fully_hashed=False)
