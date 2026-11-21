import base64
import hashlib
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch


def load(name):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).resolve().parents[1] / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


renderer = load('render-repository-gallery')
sync = load('sync-approved-symbol')
reconcile = load('reconcile-approved-symbols')
TARGET = 'sunstriker2009/sun-product'
LIVE = 'sunstriker2009/sun-live'
PENDING = 'sunstriker2009/sun-pending'
PNG = bytes.fromhex('89504e470d0a1a0a')
ICON = 'gallery/sun-product.png'
DIGEST = hashlib.sha256(PNG).hexdigest()


def listing(mode, repository=TARGET, **fields):
    return dict(repository=repository, registryId='SUN-P001', classification='product',
                name='Product', summary='Summary', symbolMode=mode, **fields)


def catalog(*rows):
    return dict(schemaVersion=1, galleryDirectory='gallery', repositories=list(rows))


class GallerySymbolModeTests(unittest.TestCase):
    def test_render_live_text_and_copied_tiles(self):
        authority = dict(products=[dict(id='SUN-P001', repository='sun-product', status='CONFIRMED',
                                        name='Product', family='productivity')], infrastructure=[])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / ICON
            path.parent.mkdir()
            path.write_bytes(PNG)
            for row, expected in [
                (listing('live'), f'https://raw.githubusercontent.com/{TARGET}/main/branding/assets/symbol.png'),
                (listing('text'), '<strong>Product</strong>'),
                (listing('copy'), '<strong>Product</strong>'),
                (listing('copy', icon=ICON, iconSha256=DIGEST), f'src="../{ICON}"'),
            ]:
                with self.subTest(row=row):
                    self.assertIn(expected, renderer.render(root, catalog(row), authority))
            for row in (listing('live', icon=ICON, iconSha256=DIGEST),
                        listing('copy', icon=ICON, iconSha256='0' * 64)):
                with self.assertRaises(ValueError):
                    renderer.render(root, catalog(row), authority)

    def test_copy_reads_only_canonical_png_of_approved_private_member(self):
        manifest = json.dumps(dict(type='file', size=len(PNG), encoding='base64',
                                   content=base64.b64encode(PNG).decode()))
        args = ['sync', '--repository', TARGET, '--confirm', TARGET, '--mode', 'preview']
        with patch.object(sys, 'argv', args), patch.dict(sync.os.environ, {'GH_TOKEN': 'test'}):
            for mode, visibility, expected_calls in [('live', 'public', 1), ('text', 'private', 1),
                                                      ('copy', 'public', 2), ('copy', 'private', 3)]:
                with self.subTest(mode=mode, visibility=visibility), patch.object(sync, 'gh', side_effect=[
                    json.dumps(catalog(listing(mode))),
                    json.dumps(dict(full_name=TARGET, visibility=visibility)), manifest,
                ]) as api:
                    if mode == 'copy' and visibility == 'public':
                        with self.assertRaisesRegex(SystemExit, 'require a private'):
                            sync.main()
                    else:
                        sync.main()
                    self.assertEqual(api.call_count, expected_calls)
                    if expected_calls == 3:
                        self.assertEqual(api.call_args.args, (f'repos/{TARGET}/contents/{sync.SOURCE}?ref=main',))

    def test_reconciliation_only_visits_copy_approved_members(self):
        rows = catalog(listing('copy'), listing('live', LIVE),
                       dict(repository=PENDING, classification='pending', symbolMode='copy'))
        with patch.object(reconcile.subprocess, 'check_output', return_value=json.dumps(rows)), \
             patch.object(reconcile.subprocess, 'run', return_value=CompletedProcess([], 0)) as run:
            for selection, expected in [('', [TARGET]), (TARGET, [TARGET]), (LIVE, [])]:
                run.reset_mock()
                with patch.object(sys, 'argv', ['reconcile', f'--repository={selection}']):
                    reconcile.main()
                self.assertEqual([call.args[0][3] for call in run.call_args_list], expected)
            for selection in (PENDING, 'other/unknown'):
                run.reset_mock()
                with patch.object(sys, 'argv', ['reconcile', f'--repository={selection}']), \
                     self.assertRaisesRegex(SystemExit, 'confirmed Foundry repository'):
                    reconcile.main()
                run.assert_not_called()

    def test_large_png_api_fallback_and_invalid_blob(self):
        data = PNG + b'x' * 1_100_000
        encoded = base64.b64encode(data).decode()
        meta = dict(type='file', size=len(data), encoding='none', sha='blob-id')
        with patch.object(sync.subprocess, 'check_output', return_value=json.dumps(dict(
                encoding='base64', content=encoded))) as api:
            self.assertEqual(sync.read_png_blob(TARGET, sync.SOURCE, meta), data)
            self.assertEqual(api.call_args.args[0], ['gh', 'api', f'repos/{TARGET}/git/blobs/blob-id'])
        for bad in (dict(meta, size=2_000_001), dict(meta, size=0),
                    dict(meta, encoding='base64', content='YmFk', size=3)):
            with self.assertRaises(SystemExit):
                sync.read_png_blob(TARGET, sync.SOURCE, bad)


if __name__ == '__main__':
    unittest.main()
