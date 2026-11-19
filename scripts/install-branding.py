#!/usr/bin/env python3
"""Validate SUN branding ZIPs and prepare reversible asset-only installations."""
import argparse
from contextlib import contextmanager
from io import BytesIO
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import tempfile
import warnings
import zipfile

from PIL import Image

SIZES = (16, 24, 32, 48, 64, 128, 256, 512, 1024)
MAX_ZIP = 20_000_000
MAX_TOTAL = 64_000_000
MAX_FILE = 12_000_000
MAX_FILES = 256
Image.MAX_IMAGE_PIXELS = 16_000_000


def safe_path(name):
    path = PurePosixPath(name)
    if (not name or '\\' in name or ':' in name or name.startswith('/') or
            any(c in name for c in '\x00\r\n') or
            any(p in ('', '.', '..') for p in name.rstrip('/').split('/'))):
        raise ValueError(f'Unsafe ZIP path: {name!r}')
    return path


def read_zip(data):
    if len(data) > MAX_ZIP:
        raise ValueError('ZIP exceeds 20 MB')
    result = {}
    with zipfile.ZipFile(BytesIO(data)) as archive:
        entries = archive.infolist()
        if len(entries) > MAX_FILES or sum(i.file_size for i in entries) > MAX_TOTAL:
            raise ValueError('ZIP exceeds file-count or expanded-size limit')
        seen = set()
        for info in entries:
            path = safe_path(info.filename)
            key = str(path).casefold()
            if key in seen:
                raise ValueError('Duplicate ZIP entry')
            seen.add(key)
            kind = stat.S_IFMT(info.external_attr >> 16)
            if kind not in (0, stat.S_IFREG, stat.S_IFDIR) or info.flag_bits & 1:
                raise ValueError('Links, special files and encrypted entries are unsupported')
            if info.file_size > MAX_FILE:
                raise ValueError('ZIP entry exceeds 12 MB')
            if not info.is_dir():
                result[str(path)] = archive.read(info)
    return result


def png_size(data):
    with warnings.catch_warnings():
        warnings.simplefilter('error', Image.DecompressionBombWarning)
        with Image.open(BytesIO(data)) as image:
            if image.format != 'PNG' or getattr(image, 'n_frames', 1) != 1:
                raise ValueError('Expected a static PNG')
            image.verify()
        with Image.open(BytesIO(data)) as image:
            image.load()
            return image.size


def package_assets(data):
    entries = read_zip(data)
    # Packages may have a single enclosing export directory (e.g. Workbench).
    roots = {p[:-len('branding/assets/symbol.png')] for p in entries
             if p.endswith('branding/assets/symbol.png')}
    if len(roots) != 1:
        raise ValueError('Package needs exactly one branding/assets/symbol.png')
    root = roots.pop()
    if root and (not root.endswith('/') or len(PurePosixPath(root).parts) != 1):
        raise ValueError('Only one optional enclosing directory is supported')
    result = {}
    for path, content in entries.items():
        if not path.startswith(root):
            raise ValueError('Files outside the package root')
        relative = path[len(root):]
        if relative in ('README.md', 'manifest.json'):
            continue  # Informational export metadata never overwrites repository files.
        if relative in ('preview.png', 'PREVIEW.png', 'branding/assets/preview.png'):
            name = 'concept-artwork.png'
        elif relative.startswith('branding/assets/'):
            name = relative[len('branding/assets/'):]
        else:
            raise ValueError(f'Unsupported package file: {relative}')
        if name in result:
            raise ValueError(f'Duplicate installed asset: {name}')
        icon = re.fullmatch(r'icons/icon-([0-9]+)\.png', name)
        allowed = (name in ('symbol.png', 'readme-banner.png', 'concept-artwork.png',
                            'social-card.png', 'social-preview.png')
                   or icon or (name.startswith('refs/') and name.endswith('.png')))
        if not allowed:
            raise ValueError(f'Unsupported asset: {name}')
        width, height = png_size(content)
        if name == 'symbol.png' and (width != height or not 128 <= width <= 4096):
            raise ValueError('Symbol must be square, 128–4096 px')
        if name == 'readme-banner.png' and (width <= height or width > 8192):
            raise ValueError('README banner must be landscape, at most 8192 px wide')
        if icon and (not 1 <= int(icon[1]) <= 1024 or (width, height) != (int(icon[1]),) * 2):
            raise ValueError(f'Icon dimensions do not match {name}')
        result[name] = content
    required = {'symbol.png', 'readme-banner.png', *(f'icons/icon-{s}.png' for s in SIZES)}
    if required - result.keys():
        raise ValueError(f'Missing required assets: {sorted(required - result.keys())}')
    return result


def files_under(directory):
    result = {}
    if directory.is_symlink():
        raise ValueError('Symlinked asset directory is unsupported')
    if directory.exists():
        for path in directory.rglob('*'):
            if path.is_symlink():
                raise ValueError('Symlinks are unsupported in branding')
            if path.is_file():
                result[path.relative_to(directory).as_posix()] = path.read_bytes()
    return result


def snapshot(assets):
    if len(assets) > MAX_FILES or sum(map(len, assets.values())) > MAX_TOTAL:
        raise ValueError('Existing assets exceed revision limits')
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name, content in sorted(assets.items()):
            safe_path(name)
            if len(content) > MAX_FILE:
                raise ValueError('Existing asset exceeds file-size limit')
            info = zipfile.ZipInfo('branding/assets/' + name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, content)
    data = buffer.getvalue()
    if len(data) > MAX_ZIP:
        raise ValueError('Revision exceeds ZIP size limit')
    read_zip(data)  # A backup must be readable by the same rollback validator.
    return data


def restore_assets(data):
    result = {}
    for path, content in read_zip(data).items():
        if not path.startswith('branding/assets/'):
            raise ValueError('Revision contains files outside branding/assets')
        name = path[len('branding/assets/'):]
        safe_path(name)
        result[name] = content
    return result


def prepare_assets(repository, source, rollback):
    """Plan imagery changes without reading or writing revision history."""
    branding = Path(repository) / 'branding'
    if branding.is_symlink():
        raise ValueError('Symlinks are unsupported in branding')
    old = files_under(branding / 'assets')
    if Path(source).stat().st_size > MAX_ZIP:
        raise ValueError("ZIP exceeds 20 MB")
    if (not rollback and Path(source).resolve().parent == (branding / 'revisions').resolve()
            and re.fullmatch(r'v[1-9][0-9]*\.zip', Path(source).name)):
        raise ValueError('Numbered revisions are immutable; use rollback to restore one')
    incoming = Path(source).read_bytes()
    if rollback:
        new = restore_assets(incoming)
    else:
        new = {**old, **package_assets(incoming)}
    for name in new:
        if any(str(parent) in new for parent in PurePosixPath(name).parents if str(parent) != "."):
            raise ValueError("Asset path conflicts with a parent file")
    changed = sorted(p for p in old.keys() | new.keys() if old.get(p) != new.get(p))
    return old, new, {'changed': changed, 'operation': 'rollback' if rollback else 'install',
                      'source': Path(source).name}


def plan_revisions(revisions, old, new, report):
    if revisions.is_symlink() or any(path.is_symlink() for path in revisions.rglob('*')):
        raise ValueError('Symlinks are unsupported in revision history')
    versions = sorted(int(p.stem[1:]) for p in revisions.glob('v*.zip')
                      if re.fullmatch(r'v[1-9][0-9]*', p.stem))
    if versions and versions != list(range(1, len(versions) + 1)):
        raise ValueError('Revision history is not contiguous; inspect it before proceeding')
    number = max(versions, default=1) + 1
    if not report['changed']:
        return {}, None
    additions = {} if versions else {'v1.zip': snapshot(old)}
    revision = f'v{number}.zip'
    additions[revision] = snapshot(new)
    return additions, revision


def stage_assets(stage, assets):
    stage.mkdir()
    for name, content in assets.items():
        destination = stage / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)


@contextmanager
def swap_directory(stage, target, backup):
    existed = target.exists()
    if existed:
        os.replace(target, backup)
    swapped = False
    try:
        os.replace(stage, target)
        swapped = True
        yield
    except BaseException:
        if swapped:
            os.replace(target, stage)
        if existed:
            os.replace(backup, target)
        raise


def install(repository, source, rollback=False, apply=False):
    """Preview or apply imagery only, including restores from a legacy snapshot."""
    repository = Path(repository).resolve()
    _, new, report = prepare_assets(repository, source, rollback)
    if not apply or not report['changed']:
        return report
    branding = repository / 'branding'
    with tempfile.TemporaryDirectory(prefix='.branding-stage-', dir=repository) as directory:
        stage = Path(directory)
        stage_assets(stage / 'new-assets', new)
        branding.mkdir(exist_ok=True)
        with swap_directory(stage / 'new-assets', branding / 'assets', stage / 'old-assets'):
            pass
    return report


def install_with_revision(repository, source, rollback=False, apply=False):
    """Coordinate imagery and revision recording for the branch and PR workflows."""
    repository = Path(repository).resolve()
    branding = repository / 'branding'
    revisions = branding / 'revisions'
    old, new, report = prepare_assets(repository, source, rollback)
    additions, report['revision'] = plan_revisions(revisions, old, new, report)
    if not apply or not report['changed']:
        return report
    source_path = Path(source).resolve()
    with tempfile.TemporaryDirectory(prefix='.branding-stage-', dir=repository) as directory:
        stage = Path(directory)
        stage_assets(stage / 'new-assets', new)
        staged_history = stage / 'new-revisions'
        if revisions.exists():
            shutil.copytree(revisions, staged_history)
        else:
            staged_history.mkdir()
        for name, content in additions.items():
            with (staged_history / name).open('xb') as stream:
                stream.write(content)
        (staged_history / 'current.json').write_text(json.dumps(report, indent=2) + '\n')
        if not rollback and source_path.parent == revisions:
            (staged_history / source_path.name).unlink()
        branding.mkdir(exist_ok=True)
        with swap_directory(stage / 'new-assets', branding / 'assets', stage / 'old-assets'):
            with swap_directory(staged_history, revisions, stage / 'old-revisions'):
                if not rollback and source_path.parent == branding / 'inbox':
                    source_path.unlink()
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository-root', type=Path, required=True)
    parser.add_argument('--zip', type=Path, required=True)
    parser.add_argument('--rollback', action='store_true')
    parser.add_argument('--apply', action='store_true', help='Write locally; the workflow only pushes a PR branch')
    parser.add_argument('--record-revision', action='store_true', help='Also record numbered snapshot history')
    args = parser.parse_args()
    operation = install_with_revision if args.record_revision else install
    print(json.dumps(operation(args.repository_root, args.zip, args.rollback, args.apply), indent=2))


if __name__ == '__main__':
    main()
