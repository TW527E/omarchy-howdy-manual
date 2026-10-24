CC ?= cc
CFLAGS ?= -O2 -Wall -Wextra -Werror

.PHONY: all test clean
all: build/pam_howdy_choice.so

build:
	mkdir -p build

build/pam_howdy_choice.so: pam/pam_howdy_choice.c | build
	$(CC) $(CFLAGS) -fPIC -shared -Wl,-z,relro,-z,now -o $@ $< -lpam

build/test_backend.so: tests/test_backend.c | build
	$(CC) $(CFLAGS) -fPIC -shared -o $@ $< -lpam

build/test_choice: tests/test_choice.c | build
	$(CC) $(CFLAGS) -o $@ $< -lpam

test: all build/test_backend.so build/test_choice
	python3 -m unittest discover -s tests -p 'test_*.py' -v
	node tests/model.test.cjs
	python3 tests/pam_stack.py

clean:
	rm -rf build
