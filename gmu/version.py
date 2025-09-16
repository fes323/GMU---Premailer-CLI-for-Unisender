import typer

app = typer.Typer()


@app.command()
def version():
    return print("Unisender CLI v1.1.0")
