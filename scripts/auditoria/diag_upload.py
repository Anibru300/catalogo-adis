# -*- coding: utf-8 -*-
"""Diagnostico: llamada directa a upload_foto contra el backend desplegado."""
import sys, json, base64
from playwright.sync_api import sync_playwright

URL_BACKEND = "https://script.google.com/macros/s/AKfycbxq47t5I3eSqPmJ7zCnk47_RlHGfIwov8mcI1tJ92yNVvSsUXHU5Pe7DQ2Nx_h1wPP2/exec"

# dataURL JPEG 1x1 minimo
JPEG_B64 = ("/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAMCAgICAgMCAgIDAwMDBAYEBAQEBAgGBgUGCQgKCgkICQkK"
            "DA8MCgsOCwkJDRENDg8QEBEQCgwSExIQEw8QEBD/2wBDAQMDAwQDBAgEBAgQCAkICBAQEBAQEBAQEBAQ"
            "EBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBD/wAARCAABAAEDASIAAhEBAxEB/8QAHwAA"
            "AQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEG"
            "E1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZ"
            "WmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJ"
            "ytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcI"
            "CQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLR"
            "ChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaH"
            "iImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP0"
            "9fb3+Pn6/9oADAMBAAIRAxEAPwD3+iikozXTYQUUUUAFFFFABRRRQB//2Q==")

with sync_playwright() as pw:
    b = pw.chromium.launch()
    pg = b.new_page()
    pg.goto("about:blank")

    def post(payload):
        r = pg.evaluate("""async ({URL, payload}) => {
          const res = await fetch(URL, {method:'POST', headers:{'Content-Type':'text/plain;charset=utf-8'}, body: JSON.stringify(payload)});
          return await res.text();
        }""", {"URL": URL_BACKEND, "payload": payload})
        return r

    login = json.loads(post({"tipo": "login", "usuario": "Adis", "clave": "Adisdiseño2026"}))
    print("login:", login.get("ok"))
    token = login.get("token", "")
    r = post({"tipo": "upload_foto", "token": token, "nombre": "DIAGNOSTICO",
              "foto_base64": "data:image/jpeg;base64," + JPEG_B64})
    print("upload_foto respuesta:", r[:600])
    b.close()
