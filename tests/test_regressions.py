import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch

import requests
from typer.testing import CliRunner

from gmu.main import app
from gmu.utils.GmuConfig import GmuConfig
from gmu.utils.HTMLprocessor import HTMLProcessor
from gmu.utils.message_upload import upload_message
from gmu.utils.project_lock import project_lock
from gmu.utils.Unisender import UnisenderAPIError, UnisenderClient
from gmu.utils.user_settings import is_git_auto_sync_enabled


class ProjectTest(unittest.TestCase):
    def setUp(self):
        self.original_cwd = Path.cwd()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        os.chdir(self.temp.name)
        self.addCleanup(os.chdir, self.original_cwd)
        self.user_dir = Path(self.temp.name) / 'user'
        self.settings_patch = patch('gmu.utils.user_settings.user_config_dir', return_value=self.user_dir)
        self.settings_patch.start()
        self.addCleanup(self.settings_patch.stop)

    def save(self, **data):
        GmuConfig(data=data).save()

    def load(self):
        return json.loads(Path('gmu.json').read_text(encoding='utf-8'))


class SettingsTests(ProjectTest):
    def test_global_enable_disable_survives_project_change(self):
        runner = CliRunner()
        result = runner.invoke(app, ['cfg', 'git', '--enable'])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertFalse(Path('gmu.json').exists())
        Path('second').mkdir()
        os.chdir('second')
        self.save(settings={'git_auto_sync': False})
        self.assertTrue(is_git_auto_sync_enabled())
        result = runner.invoke(app, ['cfg', 'git', '--disable'])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertFalse(is_git_auto_sync_enabled())
        self.assertEqual(json.loads((self.user_dir / 'settings.json').read_text())['git_auto_sync'], False)

    def test_conflicting_flags_do_not_write_configuration(self):
        result = CliRunner().invoke(app, ['cfg', 'git', '--enable', '--disable'])
        self.assertNotEqual(result.exit_code, 0)
        self.assertFalse(Path('gmu.json').exists())
        self.assertFalse(self.user_dir.exists())

    def test_atomic_save_keeps_original_on_replace_failure(self):
        self.save(message_id=10)
        with patch('gmu.utils.GmuConfig.os.replace', side_effect=PermissionError):
            with self.assertRaises(PermissionError):
                GmuConfig().update({'message_id': 20})
        self.assertEqual(self.load()['message_id'], 10)
        self.assertEqual(list(Path('.').glob('.gmu.json.*.tmp')), [])


class HTMLTests(ProjectTest):
    def processor(self, html):
        Path('letter.html').write_text(html, encoding='utf-8')
        processor = HTMLProcessor('letter.html')
        processor._get_soup()
        return processor

    def test_formatted_title_and_preheader(self):
        processor = self.processor('''<title> Очень длинная\n   тема\tписьма </title>
        <div style="display:none!important">Первое\n  предложение <span>и второе</span></div>''')
        processor._extract_subject()
        processor._extract_preheader()
        self.assertEqual(processor.subject, 'Очень длинная тема письма')
        self.assertEqual(processor.preheader, 'Первое предложение и второе')

    def test_padding_does_not_hide_real_preheader_or_consume_letters(self):
        processor = self.processor('''<div style="display: none">&zwnj;&nbsp;&#8203;</div>
        <div style="DISPLAY : NONE">news</div>''')
        processor._extract_preheader()
        self.assertEqual(processor.preheader, 'news')

    def test_external_and_missing_src_are_preserved(self):
        processor = self.processor('<img src="https://example.com/a.png"><img><img src="images/a.png">')
        processor._find_images()
        processor.image_renames = {'a.png': 'renamed.png'}
        processor._update_image_sources()
        tags = processor.soup.find_all('img')
        self.assertEqual(tags[0]['src'], 'https://example.com/a.png')
        self.assertNotIn('src', tags[1].attrs)
        self.assertEqual(tags[2]['src'], 'renamed.png')

    def test_missing_local_attachment_fails(self):
        processor = self.processor('<img src="images/missing.png">')
        processor._find_images()
        with self.assertRaises(FileNotFoundError):
            processor._process_attachments()

    def test_multiple_html_files_require_selection(self):
        Path('a.html').write_text('a')
        Path('b.html').write_text('b')
        with self.assertRaisesRegex(ValueError, 'несколько'):
            HTMLProcessor(None)

    def test_archive_uses_selected_file_and_resolvable_image_paths(self):
        from gmu.archive import archive
        Path('a.html').write_text('other')
        Path('chosen.html').write_text('''<title>Test</title><img src="assets/a.png">''')
        Path('assets').mkdir()
        from PIL import Image
        Image.new('RGB', (10, 10)).save('assets/a.png')
        with patch('gmu.utils.HTMLprocessor.inline_css_custom', side_effect=lambda html: html):
            archive(html_filename='chosen.html', images_folder='assets')
        with zipfile.ZipFile('chosen.zip') as zipped:
            html = zipped.read('index.html').decode('utf-8')
            from bs4 import BeautifulSoup
            src = BeautifulSoup(html, 'html.parser').img['src']
            self.assertIn(src, zipped.namelist())


class UploadTests(ProjectTest):
    def setUp(self):
        super().setUp()
        Path('letter.zip').write_bytes(b'archive')
        result = {'data': {'sender_name': 'Sender', 'sender_email': 's@example.com',
                           'subject': 'Title', 'preheader': 'Preview', 'language': 'en'},
                  'inlined_html': '<html></html>', 'attachments': {}}
        self.processor = Mock(html_filename='letter.html')
        self.processor.process.side_effect = lambda: copy.deepcopy(result)
        self.client = Mock()
        self.client.delete_message.return_value = True
        self.client.create_email_message.return_value = {'message_id': 22}
        for target, kwargs in [
            ('HTMLProcessor', {'return_value': self.processor}),
            ('archive_email', {'return_value': str(Path('letter.zip').resolve())}),
            ('UnisenderClient', {'return_value': self.client}),
            ('run_git_auto_sync', {'return_value': False}),
            ('pyperclip.copy', {'return_value': None}),
        ]:
            mock_patch = patch(f'gmu.utils.message_upload.{target}', **kwargs)
            mock_patch.start()
            self.addCleanup(mock_patch.stop)

    def upload(self, **kwargs):
        return upload_message(123, 'letter.html', 'images', **kwargs)

    def test_existing_empty_config_saves_without_prompt_and_preserves_state(self):
        self.save(webletter_id='wl-1', letter_version=7)
        with patch('builtins.input', side_effect=AssertionError('Unexpected prompt')):
            self.upload()
        data = self.load()
        self.assertEqual(data['message_id'], 22)
        self.assertEqual(data['webletter_id'], 'wl-1')
        self.assertEqual(data['letter_version'], 7)
        self.assertEqual(data['lang'], 'en')
        self.assertFalse(data['message_creation_pending'])
        self.client.create_email_message.assert_called_once()

    def test_first_upload_persists_id(self):
        self.upload()
        self.assertEqual(self.load()['message_id'], 22)

    def test_force_replaces_instead_of_duplicating(self):
        for mode in ('create', 'upsert'):
            with self.subTest(mode=mode):
                self.save(message_id=11, actual_version_id=11)
                self.client.reset_mock()
                self.upload(mode=mode, force=True)
                self.client.delete_message.assert_called_once_with(11)
                self.client.create_email_message.assert_called_once()
                self.assertIsNone(self.load()['actual_version_id'])

    def test_create_does_not_duplicate_existing_message(self):
        self.save(message_id=11)
        self.upload(mode='create')
        self.client.create_email_message.assert_not_called()

    def test_invalid_html_does_not_delete_existing_message(self):
        self.save(message_id=11)
        self.processor.process.side_effect = FileNotFoundError('HTML')
        with self.assertRaises(FileNotFoundError):
            self.upload(mode='update')
        self.client.delete_message.assert_not_called()
        self.client.create_email_message.assert_not_called()
        self.assertEqual(self.load()['message_id'], 11)

    def test_missing_subject_does_not_delete_existing_message(self):
        self.save(message_id=11)
        self.processor.process.side_effect = None
        self.processor.process.return_value = {'data': {'sender_name': 'S', 'sender_email': 's@x', 'subject': ''}}
        with self.assertRaisesRegex(ValueError, 'subject'):
            self.upload()
        self.client.delete_message.assert_not_called()

    def test_failed_deletion_does_not_create(self):
        self.save(message_id=11)
        self.client.delete_message.side_effect = UnisenderAPIError('failure')
        with self.assertRaises(UnisenderAPIError):
            self.upload()
        self.client.create_email_message.assert_not_called()
        self.assertEqual(self.load()['message_id'], 11)

    def test_ambiguous_timeout_blocks_retry_even_with_force(self):
        self.client.create_email_message.side_effect = requests.Timeout()
        with self.assertRaises(requests.Timeout):
            self.upload()
        self.assertTrue(self.load()['message_creation_pending'])
        with self.assertRaisesRegex(ValueError, 'неизвестен'):
            self.upload(force=True)
        self.client.create_email_message.assert_called_once()

    def test_explicit_rejection_allows_retry_and_clears_deleted_id(self):
        self.save(message_id=11)
        self.client.create_email_message.side_effect = UnisenderAPIError('invalid sender')
        with self.assertRaises(UnisenderAPIError):
            self.upload()
        self.assertFalse(self.load()['message_creation_pending'])
        self.assertIsNone(self.load()['message_id'])
        self.client.create_email_message.side_effect = None
        self.upload()
        self.client.delete_message.assert_called_once_with(11)
        self.assertEqual(self.load()['message_id'], 22)

    def test_missing_response_id_blocks_retry(self):
        self.client.create_email_message.return_value = {}
        with self.assertRaisesRegex(RuntimeError, 'message_id'):
            self.upload()
        self.assertTrue(self.load()['message_creation_pending'])

    def test_initial_config_write_failure_prevents_remote_create(self):
        with patch.object(GmuConfig, 'save', side_effect=PermissionError):
            with self.assertRaises(PermissionError):
                self.upload()
        self.client.create_email_message.assert_not_called()

    def test_final_save_failure_keeps_pending_and_reports_created_id(self):
        original_update = GmuConfig.update
        def fail_final_save(cfg, data):
            if data.get('message_id') == 22:
                raise PermissionError('disk')
            return original_update(cfg, data)
        with patch.object(GmuConfig, 'update', fail_final_save):
            with self.assertRaisesRegex(RuntimeError, 'ID 22'):
                self.upload()
        self.assertTrue(self.load()['message_creation_pending'])
        with self.assertRaises(ValueError):
            self.upload()
        self.client.create_email_message.assert_called_once()

    def test_info_save_recovers_pending_id(self):
        self.save(message_creation_pending=True)
        with patch('gmu.message.get_message.UnisenderClient') as client:
            client.return_value.get_message.return_value = {'id': 22, 'subject': 'Hello\nworld'}
            result = CliRunner().invoke(app, ['m', 'info', '--id', '22', '--save'])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(self.load()['message_id'], 22)
        self.assertFalse(self.load()['message_creation_pending'])
        self.assertEqual(self.load()['subject'], 'Hello world')

    def test_cli_short_update_alias_uses_shared_workflow(self):
        self.save(message_id=11)
        result = CliRunner().invoke(app, ['m', 'upd'])
        self.assertEqual(result.exit_code, 0, result.output)
        self.client.delete_message.assert_called_once_with(11)


class OtherRegressionTests(ProjectTest):
    def test_git_sync_in_letter_repository_excludes_active_and_nested_locks(self):
        from gmu.utils.git_sync import run_git_auto_sync

        def git(*args):
            result = subprocess.run(['git', *args], capture_output=True, text=True,
                                    encoding='utf-8', errors='replace')
            self.assertEqual(result.returncode, 0, result.stderr)
            return result.stdout

        remote = Path('remote.git').resolve()
        git('init', '--bare', str(remote))
        Path('letters').mkdir()
        os.chdir('letters')
        git('init', '-b', 'main')
        git('config', 'user.name', 'GMU test')
        git('config', 'user.email', 'gmu-test@example.com')
        git('config', 'commit.gpgsign', 'false')
        git('remote', 'add', 'origin', str(remote))
        Path('README.md').write_text('Test repository')
        git('add', 'README.md')
        git('commit', '-m', 'Initial commit')
        git('push', '-u', 'origin', 'main')
        project = Path('2026/Rosmould Rosplast 3D/10) October/RMRP-0610-2257')
        project.mkdir(parents=True)
        os.chdir(project)
        Path('index.html').write_text('<title>Test</title>')
        Path('nested').mkdir()
        Path('nested/.gmu.lock').write_bytes(b'0')
        with patch('gmu.utils.git_sync.is_git_auto_sync_enabled', return_value=True), project_lock():
            self.assertTrue(run_git_auto_sync())
        self.assertEqual(git('ls-files', '.gmu.lock', 'nested/.gmu.lock').strip(), '')
        self.assertIn('index.html', git('ls-files'))
        self.assertIn('gmu.json', git('ls-files'))
        self.assertEqual(self.load()['letter_version'], 1)
        self.assertEqual(git('rev-parse', 'HEAD').strip(), git('rev-parse', 'origin/main').strip())

    def test_webletter_success_prints_saved_url_with_separator(self):
        Path('letter.zip').write_bytes(b'zip')
        processor = Mock(html_filename='index.html')
        processor.process.return_value = {'data': {'language': 'ru'}, 'inlined_html': '<html/>', 'attachments': {}}
        with patch.dict(os.environ, {'WL_AUTH_TOKEN': 'test', 'WL_ENDPOINT': 'https://example.com/api',
                                     'WL_URL': 'https://wl.gefera.ru'}), \
                patch('gmu.webletter.upsert.HTMLProcessor', return_value=processor), \
                patch('gmu.webletter.upsert.archive_email', return_value='letter.zip'), \
                patch('gmu.webletter.upsert.requests.post') as post, \
                patch('gmu.webletter.upsert.run_git_auto_sync', return_value=False):
            post.return_value.json.return_value = {'data': {'id': '1791146826642'}}
            result = CliRunner().invoke(app, ['wl', 'u'])
        self.assertEqual(result.exit_code, 0, result.output)
        expected_url = 'https://wl.gefera.ru/1791146826642'
        self.assertEqual(self.load()['webletter_url'], expected_url)
        self.assertIn(expected_url, result.output)

    def test_deleting_explicit_other_message_keeps_project_binding(self):
        self.save(message_id=11, message_url='url')
        with patch('gmu.message.delete_message.UnisenderClient') as client:
            client.return_value.delete_message.return_value = True
            result = CliRunner().invoke(app, ['m', 'd', '--id', '99'])
        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(self.load()['message_id'], 11)

    def test_failed_webletter_delete_keeps_binding(self):
        self.save(webletter_id='wl-1')
        with patch.dict(os.environ, {'WL_AUTH_TOKEN': 'test'}), patch('gmu.webletter.delete_to_wl.requests.delete') as delete:
            delete.return_value.raise_for_status.side_effect = requests.HTTPError()
            result = CliRunner().invoke(app, ['wl', 'd'])
        self.assertNotEqual(result.exit_code, 0)
        self.assertEqual(self.load()['webletter_id'], 'wl-1')

    def test_campaign_rejects_now_and_start_time_before_network(self):
        self.save(message_id=11)
        with patch('gmu.campaign.create_campaign.UnisenderClient') as client:
            result = CliRunner().invoke(app, ['c', 'c', '--now', '--start-time', '2026-10-05 10:00'])
        self.assertNotEqual(result.exit_code, 0)
        client.assert_not_called()

    def test_compressed_request_log_does_not_contain_api_key(self):
        with patch.dict(os.environ, {'UNISENDER_API_KEY': 'secret-test-key', 'UNISENDER_API_URL': 'https://example.com/api/'}):
            client = UnisenderClient()
        with patch.object(client, '_get_log_file_path', return_value=Path('requests.log')), patch('gmu.utils.Unisender.requests.post') as post:
            post.return_value.json.return_value = {'result': {}}
            client.u_request('method', {'value': 1}, request_compression='gzip')
        self.assertNotIn('secret-test-key', Path('requests.log').read_text())
        self.assertIn('api_key=%2A%2A%2A', Path('requests.log').read_text())
        self.assertEqual(post.call_args.kwargs['timeout'], (10, 120))

    def test_os_lock_blocks_other_process_and_releases(self):
        code = "from gmu.utils.project_lock import project_lock\nwith project_lock():\n print('locked')"
        env = {**os.environ, 'PYTHONPATH': str(self.original_cwd)}
        with project_lock():
            result = subprocess.run([sys.executable, '-c', code], env=env, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
        result = subprocess.run([sys.executable, '-c', code], env=env, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
