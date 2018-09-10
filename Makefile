react_example:
				find ./pudgy/ -name "*.html" -o -name "*.jsx" -o -name "*.py" -o -name "*.sass" -o -name "*.mustache" | entr -r python -m examples.react.demo

basic_example:
				find ./pudgy/ -name "*.html" -o -name "*.js" -o -name "*.py" -o -name "*.sass" -o -name "*.mustache" | entr -r python -m examples.basic.demo

build:
				python setup.py sdist build

install:
				python setup.py sdist install dist/pudgy-0.0.1.tar.gz

.PHONY: build install
