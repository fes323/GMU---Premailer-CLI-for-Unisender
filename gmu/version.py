import typer

app = typer.Typer()


@app.command()
def version():
    print("Unisender CLI v1.0.0")
