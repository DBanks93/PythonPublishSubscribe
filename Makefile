.PHONY: run
run: integration_up run_example integration_down

.PHONY: run_example
run_example:
	pipenv run python examples/example.py

.PHONY: test
test: unit_test integration_test

.PHONY: unit_test
unit_test:
	pipenv run pytest tests/unit --cov python_publish_subscribe --cov-report term-missing

.PHONY: integration_test
integration_test: integration_down integration_up
	pipenv run pytest tests/intergration --cov python_publish_subscribe --cov-report term-missing
	$(MAKE) integration_down

.PHONY: integration_up
integration_up:
	docker compose -f tests/intergration/docker-compose.yml up -d
	bash ./tests/intergration/wait_for_depencies.sh

.PHONY: integration_down
integration_down:
	docker compose -f tests/intergration/docker-compose.yml down


