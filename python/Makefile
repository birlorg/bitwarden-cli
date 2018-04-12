release: test
	echo "run inside of a pipenv shell"
	python3 setup.py --command-packages=click_man.commands man_pages
	python3 setup.py sdist
	python3 setup.py bdist_wheel
	twine upload -u birlorg -s -i 0x24DC8628B3667566 dist/*
	echo "also run ../docs/make html"
	echo "also fsl tag!"
clean:
	rm -rf bitwarden/__pycache__
	rm -rf tests/__pycache__
	rm -rf dist/
	rm -rf build/
test:
	pytest

.PHONY: release test
