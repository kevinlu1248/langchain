"""
Manage LangChain apps
"""

import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import typer
from langserve.packages import get_langserve_export
from typing_extensions import Annotated

from langchain_cli.utils.events import create_events
from langchain_cli.utils.git import (
    DependencySource,
    copy_repo,
    parse_dependencies,
    update_repo,
)
from langchain_cli.utils.packages import get_package_root

REPO_DIR = Path(typer.get_app_dir("langchain")) / "git_repos"

app_cli = typer.Typer(no_args_is_help=True, add_completion=False)


@app_cli.command()
def new(
    name: Annotated[str, typer.Argument(help="The name of the folder to create")],
    *,
    package: Annotated[
        Optional[List[str]],
        typer.Option(help="Packages to seed the project with"),
    ] = None,
):
    """
    Create a new LangServe application.
    """
    # copy over template from ../project_template
    project_template_dir = Path(__file__).parents[1] / "project_template"
    destination_dir = Path.cwd() / name if name != "." else Path.cwd()
    app_name = name if name != "." else Path.cwd().name
    shutil.copytree(project_template_dir, destination_dir, dirs_exist_ok=name == ".")

    readme = destination_dir / "README.md"
    readme_contents = readme.read_text()
    readme.write_text(readme_contents.replace("__app_name__", app_name))

    # add packages if specified
    if package is not None and len(package) > 0:
        add(package, project_dir=destination_dir)


@app_cli.command()
def add(
    dependencies: Annotated[
        Optional[List[str]], typer.Argument(help="The dependency to add")
    ] = None,
    *,
    api_path: Annotated[List[str], typer.Option(help="API paths to add")] = [],
    project_dir: Annotated[
        Optional[Path], typer.Option(help="The project directory")
    ] = None,
    repo: Annotated[
        List[str],
        typer.Option(help="Install templates from a specific github repo instead"),
    ] = [],
    branch: Annotated[
        List[str], typer.Option(help="Install templates from a specific branch")
    ] = [],
):
    """
# Test for parse_dependencies function
def test_parse_dependencies():
    dependencies = ["dep1", "dep2"]
    repo = ["repo1", "repo2"]
    branch = ["branch1", "branch2"]
    api_path = ["api_path1", "api_path2"]

    parsed_deps = parse_dependencies(dependencies, repo, branch, api_path)

    assert len(parsed_deps) == 2
    assert parsed_deps[0]["git"] == "dep1"
    assert parsed_deps[0]["ref"] == "branch1"
    assert parsed_deps[0]["subdirectory"] == "api_path1"
    assert parsed_deps[1]["git"] == "dep2"
    assert parsed_deps[1]["ref"] == "branch2"
    assert parsed_deps[1]["subdirectory"] == "api_path2"
    Adds the specified template to the current LangServe app.

    e.g.:
    langchain app add extraction-openai-functions
    langchain app add git+ssh://git@github.com/efriis/simple-pirate.git
    """

    parsed_deps = parse_dependencies(dependencies, repo, branch, api_path)

    project_root = get_package_root(project_dir)

    package_dir = project_root / "packages"

    create_events(
        [{"event": "serve add", "properties": dict(parsed_dep=d)} for d in parsed_deps]
    )

    # group by repo/ref
    grouped: Dict[Tuple[str, Optional[str]], List[DependencySource]] = {}
    for dep in parsed_deps:
        key_tup = (dep["git"], dep["ref"])
        lst = grouped.get(key_tup, [])
        lst.append(dep)
        grouped[key_tup] = lst

    installed_destination_paths: List[Path] = []
    installed_exports: List[Dict] = []

    for (git, ref), group_deps in grouped.items():
        if len(group_deps) == 1:
            typer.echo(f"Adding {git}@{ref}...")
        else:
            typer.echo(f"Adding {len(group_deps)} templates from {git}@{ref}")
        source_repo_path = update_repo(git, ref, REPO_DIR)

        for dep in group_deps:
            source_path = (
                source_repo_path / dep["subdirectory"]
                if dep["subdirectory"]
                else source_repo_path
            )
            pyproject_path = source_path / "pyproject.toml"
            if not pyproject_path.exists():
                typer.echo(f"Could not find {pyproject_path}")
                continue
            langserve_export = get_langserve_export(pyproject_path)

            # default path to package_name
            inner_api_path = dep["api_path"] or langserve_export["package_name"]

            destination_path = package_dir / inner_api_path
            if destination_path.exists():
# Test for install_packages function
def test_install_packages():
    grouped = {
        ("git1", "ref1"): [{"subdirectory": "sub1"}],
        ("git2", "ref2"): [{"subdirectory": "sub2"}],
    }

    installed_destination_paths, installed_exports = install_packages(grouped)

    assert len(installed_destination_paths) == 2
    assert len(installed_exports) == 2
    assert installed_destination_paths[0].exists()
    assert installed_destination_paths[1].exists()
    assert installed_exports[0]["package_name"] == "sub1"
    assert installed_exports[1]["package_name"] == "sub2"
# Test for group_dependencies function
def test_group_dependencies():
    parsed_deps = [
        {"git": "git1", "ref": "ref1"},
        {"git": "git1", "ref": "ref1"},
        {"git": "git2", "ref": "ref2"},
    ]

    grouped = group_dependencies(parsed_deps)

    assert len(grouped) == 2
    assert len(grouped[("git1", "ref1")]) == 2
    assert len(grouped[("git2", "ref2")]) == 1
            typer.echo(f"Adding {git}@{ref}...")
        else:
            typer.echo(f"Adding {len(group_deps)} templates from {git}@{ref}")
        source_repo_path = update_repo(git, ref, REPO_DIR)

        for dep in group_deps:
            source_path = (
                source_repo_path / dep["subdirectory"]
                if dep["subdirectory"]
                else source_repo_path
            )
            pyproject_path = source_path / "pyproject.toml"
            if not pyproject_path.exists():
                typer.echo(f"Could not find {pyproject_path}")
                continue
            langserve_export = get_langserve_export(pyproject_path)

            # default path to package_name
            inner_api_path = dep["api_path"] or langserve_export["package_name"]

            destination_path = package_dir / inner_api_path
            if destination_path.exists():
                typer.echo(
                    f"Folder {str(inner_api_path)} already exists. " "Skipping...",
                )
                continue
            copy_repo(source_path, destination_path)
            typer.echo(f" - Downloaded {dep['subdirectory']} to {inner_api_path}")
            installed_destination_paths.append(destination_path)
            installed_exports.append(langserve_export)
            # Test for generate_route_code function
            def test_generate_route_code():
            installed_exports = [
            {"package_name": "sub1", "module": "module1", "attr": "attr1"},
            {"package_name": "sub2", "module": "module2", "attr": "attr2"},
            ]
            installed_destination_paths = [Path("packages/sub1"), Path("packages/sub2")]
            
            imports, routes = generate_route_code(installed_exports, installed_destination_paths)
            
            assert len(imports) == 2
            assert len(routes) == 2
            assert imports[0] == "from module1 import attr1 as sub1_chain"
            assert imports[1] == "from module2 import attr2 as sub2_chain"
            assert routes[0] == 'add_routes(app, sub1_chain, path="/sub1")'
            assert routes[1] == 'add_routes(app, sub2_chain, path="/sub2")'

    if len(installed_destination_paths) == 0:
        typer.echo("No packages installed. Exiting.")
        return

    cwd = Path.cwd()
    installed_desination_strs = [
        str(p.relative_to(cwd)) for p in installed_destination_paths
    ]
    cmd = ["pip", "install", "-e"] + installed_desination_strs
    cmd_str = " \\\n  ".join(installed_desination_strs)
    install_str = f"To install:\n\npip install -e \\\n  {cmd_str}"
    typer.echo(install_str)

    if typer.confirm("Run it?"):
        subprocess.run(cmd, cwd=cwd)

    if typer.confirm("\nGenerate route code for these packages?", default=True):
        chain_names = []
        for e in installed_exports:
            original_candidate = f'{e["package_name"].replace("-", "_")}_chain'
            candidate = original_candidate
            i = 2
            while candidate in chain_names:
                candidate = original_candidate + "_" + str(i)
                i += 1
            chain_names.append(candidate)

        api_paths = [
            str(Path("/") / path.relative_to(package_dir))
            for path in installed_destination_paths
        ]

        imports = [
            f"from {e['module']} import {e['attr']} as {name}"
            for e, name in zip(installed_exports, chain_names)
        ]
        routes = [
            f'add_routes(app, {name}, path="{path}")'
            for name, path in zip(chain_names, api_paths)
        ]

        lines = (
            ["", "Great! Add the following to your app:\n\n```", ""]
            + imports
            + [""]
            + routes
            + ["```"]
        )
        typer.echo("\n".join(lines))


@app_cli.command()
def remove(
    api_paths: Annotated[List[str], typer.Argument(help="The API paths to remove")],
):
    """
    Removes the specified package from the current LangServe app.
    """
    for api_path in api_paths:
        package_dir = Path.cwd() / "packages" / api_path
        if not package_dir.exists():
            typer.echo(f"Endpoint {api_path} does not exist. Skipping...")
            continue
        pyproject = package_dir / "pyproject.toml"
        langserve_export = get_langserve_export(pyproject)
        typer.echo(f"Removing {langserve_export['package_name']}...")

        shutil.rmtree(package_dir)


@app_cli.command()
def serve(
    *,
    port: Annotated[
        Optional[int], typer.Option(help="The port to run the server on")
    ] = None,
    host: Annotated[
        Optional[str], typer.Option(help="The host to run the server on")
    ] = None,
    app: Annotated[
        Optional[str], typer.Option(help="The app to run, e.g. `app.server:app`")
    ] = None,
) -> None:
    """
    Starts the LangServe app.
    """

    app_str = app if app is not None else "app.server:app"
    port_str = str(port) if port is not None else "8000"
    host_str = host if host is not None else "127.0.0.1"

    cmd = ["uvicorn", app_str, "--reload", "--port", port_str, "--host", host_str]
    subprocess.run(cmd)
