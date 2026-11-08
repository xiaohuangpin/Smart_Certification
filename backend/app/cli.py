import click

from app.seed import init_database


@click.group()
def cli() -> None:
    """Smart Certification 命令行工具。"""


@cli.command("init-db")
def init_db() -> None:
    """建表并导入基础种子数据（启动时也会自动执行）。"""
    init_database()
    click.echo("数据库初始化完成。")


@cli.command("cleanup-sources")
def cleanup_sources() -> None:
    """清理超过保留期的上传源文件及其元数据记录。"""
    from app.services import generation_service

    removed = generation_service.cleanup_sources()
    click.echo(f"已清理 {removed} 个过期源文件。")


if __name__ == "__main__":
    cli()
