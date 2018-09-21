VERSION=`cat pudgy/version.py | sed 's/__version__=//;s/"//g'`

build:
				python setup.py sdist build
				cp dist/pudgy-${VERSION}.tar.gz dist/pudgy-current.tar.gz

install:
				pip install dist/pudgy-${VERSION}.tar.gz

clean_cache:
				rm cache/jsx.cache/ -fr

.PHONY: build install

# EXAMPLES
pagelet_example:
				find ./pudgy/ -name "*.html" -o -name "*.jsx" -o -name "*.py" -o -name "*.sass" -o -name "*.mustache" | entr -r python -m examples.pagelet.demo

react_example:
				find ./pudgy/ -name "*.html" -o -name "*.jsx" -o -name "*.py" -o -name "*.sass" -o -name "*.mustache" | entr -r python -m examples.react.demo

basic_example:
				find ./pudgy/ -name "*.html" -o -name "*.js" -o -name "*.py" -o -name "*.sass" -o -name "*.mustache" | entr -r python -m examples.basic.demo

super_example:
				find ./pudgy/ -name "*.html" -o -name "*.js" -o -name "*.py" -o -name "*.sass" -o -name "*.mustache" | entr -r python -m examples.superfluous.demo


require_css:
				find ./pudgy/ -name "*.html" -o -name "*.js" -o -name "*.py" -o -name "*.sass" -o -name "*.mustache" | entr -r python -m examples.require_css.demo

