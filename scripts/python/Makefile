.DEFAULT_GOAL=lint

modules:= flake8 autoflake black isort unify

install:
	@for mod in $(modules); do \
		echo $$mod; \
		if [[ $$(pip list | grep $$mod | awk '{print $1}' | wc -l) == 0 ]]; then \
			pip install $$mod; \
		fi \
	done


format: install
	autoflake --in-place --remove-unused-variables --remove-all-unused-imports -r .
	black --config .black --fast --skip-string-normalization .
	isort .
