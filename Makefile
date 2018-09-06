web:
				find ./pydgeon/ -name "*.html" -o -name "*.js" -o -name "*.py" -o -name "*.sass" -o -name "*.mustache" | entr -r python -m pydgeon.demo
