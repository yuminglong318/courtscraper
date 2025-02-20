SHELL 			:= /bin/bash
CMD 			:= python3
VENV 			:= test -d venv || python3 -m venv venv
ACTIVATE 		:= . venv/bin/activate
INSTALL  		:= python3 -m pip install
IMAGE_NAME		:= webapp

# Check if the .env exists otherwise create it
ifeq (,$(wildcard .env))
$(shell touch .env)
endif

include .env

.DEFAULT_GOAL := help

help: ## Show this help
	@echo "Usage: make <target>"
	@echo "Available targets:"
	@echo
	@awk -F':.*##' '/^[^.#][a-z_-]+:.*?##/ {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST) | sort
	@echo

all: ## Run the server
	@echo "run server"
	@gunicorn --config  scripts/wsgi.py app:server
	@echo "Server stopped"


# Unit tests
test:
	@echo "Running tests..."
	@pytest  --verbose --cov=webapp
	@echo "Done."

coverage:
	@pytest --cov=webapp
	coverage report


install: ## Install dependencies
	: # Activate venv and install smthing inside
	@echo "Installing..."
	@$(INSTALL) --upgrade pip
	@$(INSTALL) -r requirements.txt --no-cache-dir
	@$(INSTALL) -r requirements_dev.txt --no-cache-dir
	@echo "Done."

venv: ## Create virtual environment
	#: # Create venv if it doesn't exist
	@echo "Creating venv..."
	@$(VENV)
	@echo "Virtual environment is ready."

clean: ## Remove generated files and directories
	@echo "Removing generated files and directories..."
	@rm -rf venv
	@rm -rf dist build *.egg-info
	@find . -name "*.pyc" -exec rm {} \;
	@find . | grep -E '(__pycache__|\.pyc|\.pyo$$)' | xargs rm -rf


build: ## Build Docker image
	@echo "build image staging "
	echo ${GITHUB_TOKEN}
	@docker build -t ${ECR_REGISTRY}/${ECR_REPOSITORY}:${IMAGE_TAG}  . --build-arg GITHUB_TOKEN=${GITHUB_TOKEN} --build-arg USERNAME_REPO=${USERNAME_REPO} --build-arg EMAIL_REPO=${EMAIL_REPO}
	@docker tag ${ECR_REGISTRY}/${ECR_REPOSITORY}:${IMAGE_TAG} ${ECR_REGISTRY}/${ECR_REPOSITORY}:latest
	@docker push ${ECR_REGISTRY}/${ECR_REPOSITORY}:${IMAGE_TAG}
	@docker push ${ECR_REGISTRY}/${ECR_REPOSITORY}:latest
	@echo "deploy image $(IMAGE_NAME)"


lint:  ## Linter the code.
	@echo "🚨 Linting code"
	pre-commit run --all-files

chrome:
	@brew upgrade --cask chromedriver

re:  clean venv install

casenet: 
	@echo "Running Casenet Scrapper for Missouri"
	@python3 main.py retrieve-cases 

package:
	rm -rf dist
	$(CMD) setup.py develop
	$(CMD) setup.py bdist_wheel

beenverified:
	@echo "Running BeenVerified Scrapper for Missouri"
	@python3 main.py retrieve-leads

.PHONY: all test coverage help install venv clean build lint re chrome casenet package
