release: test
	echo "run inside of a pipenv shell"
	python setup.py sdist
	python setup.py bdist_wheel
	twine upload dist/*
clean:
	rm -rf bitwarden/__pycache__
	rm -rf tests/__pycache__
	rm -rf dist/
	rm -rf build/
test:
	pytest

.PHONY: release test
