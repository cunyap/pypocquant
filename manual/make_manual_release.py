import os

print('|-------------------------------------------------------------------------------------------------------------|')
print('| Start building UserInstructions.html from markdown file:')
print('|-------------------------------------------------------------------------------------------------------------|')
stream = os.popen('jupytext --to notebook UserInstructions.md')
output = stream.read()
print(output)
stream = os.popen('jupyter nbconvert UserInstructions.ipynb --to=html_embed --template toc2')
output = stream.read()
print(output)
print('|-------------------------------------------------------------------------------------------------------------|')
print('| Done.')
print('|-------------------------------------------------------------------------------------------------------------|')

