
# === NEW FRONTEND APIs ===
try:
    from system_api import router as system_router
    app.include_router(system_router)
    print("✓ System API loaded")
except ImportError as e:
    print(f"⚠ System API not loaded: {e}")

try:
    from files_api import router as files_router
    app.include_router(files_router)
    print("✓ Files API loaded")
except ImportError as e:
    print(f"⚠ Files API not loaded: {e}")

try:
    from sessions_api import router as sessions_router
    app.include_router(sessions_router)
    print("✓ Sessions API loaded")
except ImportError as e:
    print(f"⚠ Sessions API not loaded: {e}")

try:
    from analytics_api import router as analytics_router
    app.include_router(analytics_router)
    print("✓ Analytics API loaded")
except ImportError as e:
    print(f"⚠ Analytics API not loaded: {e}")
