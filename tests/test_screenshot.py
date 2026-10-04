import os
import tempfile
import unittest
from pathlib import Path

from PIL import Image
from typer.testing import CliRunner

from gmu.main import app
from gmu.utils.letter_screenshot import screenshot_letter


class ScreenshotTests(unittest.TestCase):
    def setUp(self):
        self.original_cwd = Path.cwd()
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        os.chdir(self.temp.name)
        self.addCleanup(os.chdir, self.original_cwd)

    def test_full_height_jpeg_includes_footer_lazy_image_and_local_css(self):
        Path('images').mkdir()
        Image.new('RGB', (640, 80), (0, 255, 0)).save('images/bottom.png')
        Path('style.css').write_text('body{margin:0} .content{height:2500px;background:red} img{display:block} footer{height:120px;background:blue}')
        Path('long letter.html').write_text('''<!doctype html><html><head>
            <link rel="stylesheet" href="style.css"></head><body>
            <div class="content">Top</div><img loading="lazy" src="images/bottom.png" width="640" height="80">
            <footer>Last content</footer></body></html>''')
        target = screenshot_letter('long letter.html', width=640)
        with Image.open(target) as image:
            self.assertEqual(image.format, 'JPEG')
            self.assertEqual(image.size, (640, 2700))
            self.assertGreater(image.getpixel((320, 2530))[1], 240)
            self.assertGreater(image.getpixel((320, 2650))[2], 240)

    def test_old_pdf_command_writes_jpeg_with_requested_output(self):
        Path('letter.html').write_text('<html><body><p>Letter content</p></body></html>')
        result = CliRunner().invoke(app, ['pdf', '--output', 'preview/test.jpeg', '--width', '700'])
        self.assertEqual(result.exit_code, 0, result.output)
        with Image.open('preview/test.jpeg') as image:
            self.assertEqual(image.format, 'JPEG')
            self.assertEqual(image.width, 700)
        self.assertFalse(Path('letter.pdf').exists())

    def test_multiple_html_files_require_explicit_selection(self):
        Path('a.html').write_text('a')
        Path('b.html').write_text('b')
        result = CliRunner().invoke(app, ['jpeg'])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn('--html-filename', result.output)

    def test_no_html_reports_error(self):
        result = CliRunner().invoke(app, ['jpeg'])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn('не найден', result.output)

    def test_missing_images_do_not_overwrite_existing_jpeg(self):
        Path('letter.html').write_text('<img src="images/missing.png">')
        Path('letter.jpg').write_bytes(b'existing preview')
        result = CliRunner().invoke(app, ['jpeg'])
        self.assertNotEqual(result.exit_code, 0)
        self.assertIn('Не загрузились изображения', result.output)
        self.assertEqual(Path('letter.jpg').read_bytes(), b'existing preview')

    def test_jpeg_output_cannot_overwrite_source_html(self):
        Path('letter.html').write_text('original')
        result = CliRunner().invoke(app, ['jpeg', '--output', 'letter.html'])
        self.assertNotEqual(result.exit_code, 0)
        self.assertEqual(Path('letter.html').read_text(), 'original')

    def test_invalid_width_quality_and_browser(self):
        for args in (['--width', '0'], ['--quality', '101'], ['--browser', 'unknown']):
            with self.subTest(args=args):
                result = CliRunner().invoke(app, ['jpeg', *args])
                self.assertNotEqual(result.exit_code, 0)


if __name__ == '__main__':
    unittest.main()
