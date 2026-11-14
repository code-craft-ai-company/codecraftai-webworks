
# The test targets expect the project environment to be active:
#     source .venv/bin/activate

test:
	testbase testing run --root source/testroots/ccai --includes=ccai.tests.singlehost --output=./.output/singlehost

# The browser suite of the testcomponents site. Needs the 'test' extra and
# the browser: python -m playwright install chromium
test-components:
	testbase testing run --root ./source/testsites/testcomponents --includes=testcomponents.tests --output=./.output/testcomponents-tests

# Needs ruff on the path; the merge gate runs it with 'pipx run ruff'.
lint:
	ruff check .

dist-clean:
	rm -fr dist

dist-build:
	poetry build 

dist-publish:
	poetry publish
