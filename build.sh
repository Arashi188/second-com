#!/usr/bin/env bash
pip install -r requirements.txt
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"