import typer

VERSION_TEXT = "Unisender CLI v2.0.0"

app = typer.Typer()


@app.command(name="v", hidden=True)
@app.command()
def version():
    return print(VERSION_TEXT)
