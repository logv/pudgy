web:
				find ./ -name "*.html" -o -name "*.js" -o -name "*.py" -o -name "*.sass" -o -name "*.mustache" | entr -r python pydgeon/demo.py
