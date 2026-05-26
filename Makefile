BACK_DIR  := back
FRONT_DIR := front
VENV_BACK := $(BACK_DIR)/.venv
PYTHON    := python3

DB_CONTAINER := cifrados_back
DB_PATH      := /app/data/app.db

.PHONY: help \
        install install-back install-front \
        back front \
        db-reset db-shell \
        up down build logs \
        docker-db-shell docker-db-tables docker-db-schema docker-db-query docker-db-dump \
        test clean

help:
	@echo ""
	@echo "╔══════════════════════════════════════════════════╗"
	@echo "║              Comandos disponibles                ║"
	@echo "╚══════════════════════════════════════════════════╝"
	@echo ""
	@echo "  Setup local"
	@echo "    make install        Instala dependencias de back y front"
	@echo "    make install-back   Instala dependencias del backend (venv)"
	@echo "    make install-front  Instala dependencias del frontend (npm)"
	@echo ""
	@echo "  Ejecución local"
	@echo "    make back           Levanta el backend  (http://localhost:8000)"
	@echo "    make front          Levanta el frontend (http://localhost:3000)"
	@echo ""
	@echo "  Docker"
	@echo "    make up             docker compose up -d (detached)"
	@echo "    make down           docker compose down"
	@echo "    make build          docker compose build --no-cache"
	@echo "    make logs           Sigue los logs de todos los servicios"
	@echo ""
	@echo "  Base de datos (Docker)"
	@echo "    make docker-db-shell    Shell interactivo de SQLite en el contenedor"
	@echo "    make docker-db-tables   Lista todas las tablas"
	@echo "    make docker-db-schema   Muestra el esquema completo"
	@echo "    make docker-db-dump     Exporta un dump SQL a ./db-dump.sql"
	@echo "    make docker-db-query Q=\"SELECT ...\"  Ejecuta una query ad-hoc"
	@echo ""
	@echo "  Base de datos (local)"
	@echo "    make db-reset       Elimina y recrea la base de datos local"
	@echo "    make db-shell       Shell interactivo de SQLite local"
	@echo ""
	@echo "  Desarrollo"
	@echo "    make test           Corre los tests del backend"
	@echo "    make clean          Elimina cachés y entornos virtuales"
	@echo ""

# ─── Setup ────────────────────────────────────────────────────────────────────

install: install-back install-front

install-back:
	$(PYTHON) -m venv $(VENV_BACK)
	$(VENV_BACK)/bin/pip install --upgrade pip -q
	$(VENV_BACK)/bin/pip install -r $(BACK_DIR)/requirements.txt

install-front:
	cd $(FRONT_DIR) && npm install

# ─── Ejecución local ──────────────────────────────────────────────────────────

back:
	cd $(BACK_DIR) && ../$(VENV_BACK)/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8000

front:
	cd $(FRONT_DIR) && npm run dev

# ─── Docker ───────────────────────────────────────────────────────────────────

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build --no-cache

logs:
	docker compose logs -f

# ─── Base de datos (Docker) ───────────────────────────────────────────────────

docker-db-shell:
	@echo "Abriendo SQLite en el contenedor $(DB_CONTAINER)..."
	docker exec -it $(DB_CONTAINER) sqlite3 $(DB_PATH)

docker-db-tables:
	@echo "Tablas en la base de datos:"
	@docker exec $(DB_CONTAINER) sqlite3 $(DB_PATH) ".tables"

docker-db-schema:
	@echo "Esquema de la base de datos:"
	@docker exec $(DB_CONTAINER) sqlite3 $(DB_PATH) ".schema"

docker-db-dump:
	@echo "Exportando dump a db-dump.sql..."
	@docker exec $(DB_CONTAINER) sqlite3 $(DB_PATH) ".dump" > db-dump.sql
	@echo "Guardado en db-dump.sql"

docker-db-query:
	@if [ -z "$(Q)" ]; then \
		echo 'Uso: make docker-db-query Q="SELECT * FROM users LIMIT 5;"'; \
	else \
		docker exec $(DB_CONTAINER) sqlite3 -column -header $(DB_PATH) "$(Q)"; \
	fi

# ─── Base de datos (local) ────────────────────────────────────────────────────

db-reset:
	rm -f $(BACK_DIR)/app.db
	cd $(BACK_DIR) && ../$(VENV_BACK)/bin/python -c \
		"from database import engine, Base; import models; Base.metadata.create_all(bind=engine)"
	@echo "Base de datos recreada en $(BACK_DIR)/app.db"

db-shell:
	sqlite3 $(BACK_DIR)/app.db

# ─── Desarrollo ───────────────────────────────────────────────────────────────

test:
	cd $(BACK_DIR) && ../$(VENV_BACK)/bin/pytest tests/ -v

clean:
	rm -rf $(VENV_BACK)
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
