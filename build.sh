
#!/bin/bash
cd `dirname $0`

rm -rf ./dist/*
python3 setup.py sdist
twine upload -r local dist/*
