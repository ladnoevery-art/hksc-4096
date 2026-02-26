"""Flask bridge for Electron/Desktop integration."""

from __future__ import annotations

import base64
from dataclasses import asdict
from flask import Flask, jsonify, request

from hksc4096 import HKSC4096Cipher, HKSCPlanner, PlannerConfig, _parse_dynamic_schedule


def _planner_from_json(payload: dict) -> PlannerConfig:
    dynamic = payload.get("dynamic_schedule")
    if isinstance(dynamic, str):
        dynamic_schedule = _parse_dynamic_schedule(dynamic)
    elif isinstance(dynamic, list):
        dynamic_schedule = tuple(tuple(int(v) for v in seg) for seg in dynamic)
    else:
        dynamic_schedule = PlannerConfig().dynamic_schedule

    return PlannerConfig(
        piece=payload.get("piece", "knight"),
        agents=int(payload.get("agents", 1)),
        ratio_mode=payload.get("ratio_mode", "equal"),
        ratio_num=int(payload.get("ratio_num", 1)),
        ratio_den=int(payload.get("ratio_den", 1)),
        dynamic_schedule=dynamic_schedule,
        adversarial_interval=int(payload.get("adversarial_interval", 50)),
        adversarial_chance_pct=int(payload.get("adversarial_chance_pct", 7)),
    )


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.post("/api/simulate")
    def api_simulate():
        body = request.get_json(force=True)
        cfg = _planner_from_json(body)
        seed = body.get("seed", "demo-seed").encode("utf-8")
        cells = int(body.get("cells", 4096))
        digest = HKSCPlanner(seed, cfg).run_transcript(cells)
        return jsonify({"digest": digest.hex(), "planner": asdict(cfg), "cells": cells})

    @app.post("/api/encrypt")
    def api_encrypt():
        body = request.get_json(force=True)
        planner = _planner_from_json(body)
        cipher = HKSC4096Cipher(body["passphrase"], planner_config=planner)
        plaintext = base64.b64decode(body["plaintext_b64"])
        ciphertext = cipher.encrypt(plaintext)
        return jsonify({"ciphertext_b64": base64.b64encode(ciphertext).decode("ascii")})

    @app.post("/api/decrypt")
    def api_decrypt():
        body = request.get_json(force=True)
        planner = _planner_from_json(body)
        cipher = HKSC4096Cipher(body["passphrase"], planner_config=planner)
        ciphertext = base64.b64decode(body["ciphertext_b64"])
        plaintext = cipher.decrypt(ciphertext)
        return jsonify({"plaintext_b64": base64.b64encode(plaintext).decode("ascii")})

    return app
