.PHONY: run
run: emulator_up run_example emulator_down

.PHONY: run_example
run_example:
	pipenv run python examples/example.py

.PHONY: test
test: unit_test integration_test

.PHONY: unit_test
unit_test:
	pipenv run pytest tests/unit --cov python_publish_subscribe --cov-report term-missing

.PHONY: intergration_test
integration_test: emulator_down emulator_up
	pipenv run pytest tests/intergration
	$(MAKE) emulator_down

.PHONY: emulator_up
emulator_up:
	docker compose -f tests/intergration/docker-compose.yml up -d
	bash ./tests/intergration/wait_for_depencies.sh

.PHONY: emulator_down
emulator_down:
	docker compose -f tests/intergration/docker-compose.yml down


