SHELL := /bin/zsh

.PHONY: help check build preview push

help:  ## Show this help
	@grep -E '^[a-z-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

check:  ## Validate typography and slide contract
	sh scripts/check-dashes.sh
	uv run render figures
	uv run render check

build: check  ## Build PowerPoint, PDF, previews and contact sheets
	uv run render all

preview:  ## Re-render PDF and preview images
	uv run render preview

push:  ## Push the current branch to GitHub
	git push $(PUSH_FLAGS) github $$(git branch --show-current)
