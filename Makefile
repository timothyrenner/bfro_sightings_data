.PHONY: env dev-env lint format check

## Compile requirements.in into requirements.txt
deps/requirements.txt: deps/requirements.in
	uv pip compile deps/requirements.in --output-file deps/requirements.txt

## Compile dev-requirements.in into dev-requirements.txt
deps/dev-requirements.txt: deps/dev-requirements.in deps/requirements.txt
	uv pip compile deps/dev-requirements.in --output-file deps/dev-requirements.txt

## Install non-dev dependencies.
env: deps/requirements.txt
	uv pip sync deps/requirements.txt

## Install dev and non-dev dependencies.
dev-env: deps/dev-requirements.txt
	uv pip sync deps/dev-requirements.txt

## Lint project with ruff.
lint:
	python -m ruff check .

## Format imports and code.
format:
	python -m ruff format .

.PHONY: build-docker
## Build docker with local registry tag and push to local registry
build-docker:
	docker build --tag localhost:5000/bfro_pipeline:latest .
	docker push localhost:5000/bfro_pipeline:latest

.PHONY: pull-data
## Downloads the data locally for testing
pull-data:
	gsutil -m rsync -r gs://trenner-datasets/bigfoot pipeline/data

#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := help

# Inspired by <http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html>
# sed script explained:
# /^##/:
# 	* save line in hold space
# 	* purge line
# 	* Loop:
# 		* append newline + line to hold space
# 		* go to next line
# 		* if line starts with doc comment, strip comment character off and loop
# 	* remove target prerequisites
# 	* append hold space (+ newline) to line
# 	* replace newline plus comments by `---`
# 	* print line
# Separate expressions are necessary because labels cannot be delimited by
# semicolon; see <http://stackoverflow.com/a/11799865/1968>
.PHONY: help
help:
	@echo "$$(tput bold)Available commands:$$(tput sgr0)"
	@sed -n -e "/^## / { \
		h; \
		s/.*//; \
		:doc" \
		-e "H; \
		n; \
		s/^## //; \
		t doc" \
		-e "s/:.*//; \
		G; \
		s/\\n## /---/; \
		s/\\n/ /g; \
		p; \
	}" ${MAKEFILE_LIST} \
	| awk -F '---' \
		-v ncol=$$(tput cols) \
		-v indent=19 \
		-v col_on="$$(tput setaf 6)" \
		-v col_off="$$(tput sgr0)" \
	'{ \
		printf "%s%*s%s ", col_on, -indent, $$1, col_off; \
		n = split($$2, words, " "); \
		line_length = ncol - indent; \
		for (i = 1; i <= n; i++) { \
			line_length -= length(words[i]) + 1; \
			if (line_length <= 0) { \
				line_length = ncol - indent - length(words[i]) - 1; \
				printf "\n%*s ", -indent, " "; \
			} \
			printf "%s ", words[i]; \
		} \
		printf "\n"; \
	}' \
	| more $(shell test $(shell uname) = Darwin && echo '--no-init --raw-control-chars')