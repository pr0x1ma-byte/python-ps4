PYTHON = "/usr/bin/python3.7"
clean:
	rm -rf env/

build: clean
	$(PYTHON) -m venv env/
	./env/bin/pip install .

run:
	./env/bin/python app.py
