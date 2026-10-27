SHELL := /bin/bash
COMPOSE := docker compose
WPCLI := $(COMPOSE) run --rm wpcli

.PHONY: test jwt-keys lib-test browser-check node help up down restart logs reset wp bootstrap dump status

help:
	@echo "Targets:"
	@echo "  up              Start the whole stack"
	@echo "  down            Stop containers (preserve data)"
	@echo "  reset           Stop containers AND wipe DB volume (full cold start on next 'up')"
	@echo "  logs            Tail wordpress + db logs"
	@echo "  wp ARGS=\"...\" Run wp-cli inside the stack (e.g. make wp ARGS=\"plugin list\")"
	@echo "  bootstrap       One-shot: install WP core + plugins + seed all content"
	@echo "  dump            Export current DB to db/dump.sql"
	@echo "  status          Show running services"

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

reset:
	$(COMPOSE) down -v
	@echo "Volume wiped. Run 'make up' to start fresh from db/dump.sql"

logs:
	$(COMPOSE) logs -f wordpress db

wp:
	$(WPCLI) $(ARGS)

bootstrap:
	$(COMPOSE) run --rm --entrypoint bash wpcli /scripts/seed.sh

dump:
	@mkdir -p db
	$(COMPOSE) exec db sh -c 'mariadb-dump -u root -p"$$MYSQL_ROOT_PASSWORD" --default-character-set=utf8mb4 --add-drop-table --skip-extended-insert "$$MYSQL_DATABASE"' > db/dump.sql
	@echo "Wrote db/dump.sql ($$(wc -l < db/dump.sql) lines)"

status:
	$(COMPOSE) ps

# Node tooling (bundle, SCSS) runs in Docker: make node ARGS="npm run build"
node:
	$(COMPOSE) run --rm node $(ARGS)

# Headless-browser checks (focus ring, axe); screenshots land in scripts/browser-out/
browser-check:
	@mkdir -p scripts/browser-out
	$(COMPOSE) run --rm browser

# Shared library tests: plain python container, no Django or Ninja
lib-test:
	$(COMPOSE) run --rm lib-test

# Dev RS256 keypair into .env: AUTH_JWT_PRIVATE_KEY (auth service) and APP_JWT_PUBLIC_KEY (main app, later).
# Never overwrites existing keys; .env is git-ignored.
jwt-keys:
	@touch .env
	@if grep -q '^AUTH_JWT_PRIVATE_KEY=' .env; then echo "AUTH_JWT_PRIVATE_KEY already in .env, not overwriting"; else \
	  $(COMPOSE) run --rm -T --no-deps auth python /scripts/gen_jwt_keys.py >> .env && echo "Wrote AUTH_JWT_PRIVATE_KEY and APP_JWT_PUBLIC_KEY to .env; run 'docker compose up -d auth' to apply"; fi

# All suites: main app, auth service, shared library, frontend
test:
	$(COMPOSE) up -d --wait app
	$(COMPOSE) exec -T app python manage.py test
	$(COMPOSE) run --rm auth python manage.py test
	$(COMPOSE) run --rm lib-test
	$(COMPOSE) run --rm node npm test
