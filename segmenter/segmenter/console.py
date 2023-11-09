import click


@click.command()
@click.option("-in", "--input-queue")
def main(input_queue):
    click.echo("hello from within the segmenter!")
    click.echo(f"we will be processing: {input_queue}")
