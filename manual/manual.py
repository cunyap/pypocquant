import os
from pathlib import Path
import shutil


def get_manual_folder() -> str:
    """Return the path of the folder containing the manual and the target (resource) folder."""
    source = (Path(__file__).parents[0]).resolve()
    target = (Path(__file__).parents[0] / "../../../../resources/base").resolve()
    return source, target


def build_manual() -> bool:
    """Build the manual.

    Return True if building and copying to the target folder was successful, false othewise.
    """

    # Get the manual source and targer folders
    work_dir, target_dir = get_manual_folder()

    # Does the markdown file exist?
    if not (work_dir / "UserInstructions.md").is_file():
        print(f"ERROR: Could not find 'UserInstructions.md' in {work_dir}.")
        return False

    print('|---------------------------------------------------------------------------------------------------|')
    print('| Start building UserInstructions.html from markdown file:')
    print('|---------------------------------------------------------------------------------------------------|')
    manual_file = work_dir / "UserInstructions.md"
    notebook_file = work_dir / "UserInstructions.ipynb"
    stream = os.popen(f"jupytext --to notebook {manual_file}")
    output = stream.read()
    print(output)
    template_file = work_dir / "toc2.tpl"
    stream = os.popen(f"jupyter nbconvert {notebook_file} --to=html_embed --template {template_file}")
    output = stream.read()
    print(output)

    # Copy the result
    html_file = work_dir / "UserInstructions.html"
    if html_file.is_file():
        newPath = shutil.copy(html_file, target_dir)

        print(f'Copied resulting file to {newPath}')
        print('|---------------------------------------------------------------------------------------------------|')
        print('| Done.')
        print('|---------------------------------------------------------------------------------------------------|')

        return True

    else:

        print(f'Failed building manual file {html_file}.')

        return False