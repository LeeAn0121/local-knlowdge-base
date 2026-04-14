import typer

from cli.commands import chat, index, query, search, serve, status

app = typer.Typer(
    name="rag",
    help="Local RAG Knowledge Base CLI",
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
)

app.add_typer(index.app, name="index")
app.command("query")(query.query)
app.command("chat")(chat.chat)
app.command("search")(search.search)
app.command("status")(status.status)
app.command("serve")(serve.serve)

if __name__ == "__main__":
    app()
