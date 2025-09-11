from pathlib import Path

import pdfkit
import typer

app = typer.Typer()
path_wkhtmltopdf = r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe'  # на Windows
config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)


@app.command(name="pdf")
def create_pdf():

    html_files = list(Path(".").glob("*.html"))
    if not html_files:
        raise FileNotFoundError(
            "HTML не найден в рабочей директории. Проверьте, что вы в корректной директории.")
    name = html_files[0].stem
    pdfkit.from_file(input=str(html_files[0]),
                     output_path=f"{name}.pdf", configuration=config, options={"enable-local-file-access": "", "viewport-size": "1280x1024", })
